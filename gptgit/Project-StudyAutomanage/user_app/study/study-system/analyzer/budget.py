"""Persistent verification-stage allowance. Charges are estimates, not invoices."""
import math
import sqlite3
from pathlib import Path
from uuid import uuid4
from .core import AnalysisError

# Standard USD / 1M tokens, checked 2026-10-12. Explicit per-model price snapshot.
PRICES={'gpt-6-luna':(.10,.01,.125,.50),'gpt-6.1-sol':(2.0,.10,2.50,10.0)}
PRICE_DATE='2026-10-12'
DEFAULT_MAX_CALLS=100
DEFAULT_MAX_NANO=2000000000


def estimate_usage(model,usage):
    if not isinstance(usage,dict):return None
    i,o=usage.get('input_tokens'),usage.get('output_tokens')
    if not isinstance(i,int) or isinstance(i,bool) or not isinstance(o,int) or isinstance(o,bool) or min(i,o)<0:return None
    details=usage.get('input_tokens_details') or {}
    if not isinstance(details,dict):return None
    cached,writes=details.get('cached_tokens',0),details.get('cache_write_tokens',0)
    if any(not isinstance(n,int) or isinstance(n,bool) or n<0 for n in [cached,writes]) or cached+writes>i:return None
    inp,cache,write,out=PRICES[model]
    long=i>272000
    return math.ceil(((i-cached-writes)*inp+cached*cache+writes*write)*(2 if long else 1)*1000+o*out*(1.5 if long else 1)*1000)


def reservation(model,payload_bytes,max_output):
    _,_,write,out=PRICES[model]
    # UTF-8 payload bytes plus extra framing allowance exceed the expected text token count.
    # Use long-context rates and 10% headroom. This is a conservative price snapshot, not a provider hard cap.
    return math.ceil(((payload_bytes+2048)*write*2+max_output*out*1.5)*1100)


class Budget:
    def __init__(self,path=None):
        self.path=Path(path) if path is not None else Path.home()/'.study_analyzer'/'verification_budget.sqlite3'

    def connect(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        db=sqlite3.connect(self.path,timeout=10,isolation_level=None)
        try:
            db.execute('CREATE TABLE IF NOT EXISTS policy (id INTEGER PRIMARY KEY CHECK(id=1), max_calls INTEGER NOT NULL, max_nano INTEGER NOT NULL)')
            db.execute('INSERT OR IGNORE INTO policy VALUES (1,?,?)', (DEFAULT_MAX_CALLS,DEFAULT_MAX_NANO))
            db.execute('CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, reserved INTEGER NOT NULL, charged INTEGER NOT NULL, state TEXT NOT NULL, model TEXT NOT NULL, created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
        except Exception:
            db.close()
            raise
        return db

    def status(self):
        try:
            db=self.connect()
            try:
                max_calls,max_nano=db.execute('SELECT max_calls,max_nano FROM policy WHERE id=1').fetchone()
                calls,nano=db.execute('SELECT COUNT(*),COALESCE(SUM(charged),0) FROM attempts').fetchone()
                return {'stage':'representative_verification','call_limit':max_calls,'calls_used':calls,
                        'calls_remaining':max(0,max_calls-calls),'budget_usd':max_nano/1e9,
                        'estimated_or_reserved_usd':nano/1e9,'remaining_usd':max(0,max_nano-nano)/1e9,
                        'pricing_checked_at':PRICE_DATE,'billing_verified':False,'ledger_path':str(self.path.resolve())}
            finally:db.close()
        except (OSError,sqlite3.Error,TypeError,ValueError):
            raise AnalysisError('BUDGET_STORAGE_ERROR','예산 기록을 읽을 수 없어 새 API 호출을 차단합니다.') from None

    def reserve(self,model,nano):
        db=None
        try:
            db=self.connect();db.execute('BEGIN IMMEDIATE')
            max_calls,max_nano=db.execute('SELECT max_calls,max_nano FROM policy WHERE id=1').fetchone()
            calls,spent=db.execute('SELECT COUNT(*),COALESCE(SUM(charged),0) FROM attempts').fetchone()
            if calls>=max_calls or spent+nano>max_nano:
                raise AnalysisError('BUDGET_LIMIT_ERROR',f'검증 단계의 누적 {max_calls}회 또는 ${max_nano/1e9:g} 예산 한도에 도달했습니다. 추가 API 호출을 차단합니다.')
            ticket=uuid4().hex
            db.execute('INSERT INTO attempts(id,reserved,charged,state,model) VALUES (?,?,?,?,?)',(ticket,nano,nano,'reserved',model))
            db.execute('COMMIT');return ticket
        except AnalysisError:raise
        except (OSError,sqlite3.Error,TypeError,ValueError):
            raise AnalysisError('BUDGET_STORAGE_ERROR','예산 예약에 실패해 API 호출을 차단합니다.') from None
        finally:
            if db is not None:db.close()

    def finish(self,ticket,model,usage):
        amount=estimate_usage(model,usage)
        if amount is None:return  # Unknown/timeout: retain reservation and attempt count.
        db=self.connect()
        try:db.execute("UPDATE attempts SET charged=?,state='usage_estimated' WHERE id=?",(amount,ticket))
        finally:db.close()
