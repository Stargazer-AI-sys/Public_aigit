"""Read-only project handoff and approval summary; standard library only."""
import argparse
from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / 'docs/04_records/학습내용정리_작업기록.md'
DEFAULT_DB = ROOT / 'study/study-system/output/knowledge_base/library.sqlite3'


def notion_status(approval_db):
    path = Path(approval_db).parent.parent/'notion_live/outbox/delivery.sqlite3'
    if not path.is_file():
        return {'ledger_available': False, 'reason': '실제 전송 이력 없음/조회 불가'}
    try:
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True)) as db:
            receipts = [json.loads(r[0]) for r in db.execute('SELECT record FROM receipts')]
            pending = db.execute("SELECT COUNT(*) FROM operations WHERE state!='success'").fetchone()[0]
        return {'ledger_available': True,
                'material_pages': sum(r['document']['kind'] == 'material' for r in receipts),
                'all_pages': len(receipts), 'unfinished_operations': pending,
                'basis': 'local-confirmed-receipts'}
    except (sqlite3.Error, ValueError, KeyError, TypeError):
        return {'ledger_available': False, 'reason': '실제 전송 이력 조회 실패'}


def handoff(path=RECORD, section=None):
    text = Path(path).read_text(encoding='utf-8-sig')
    if section:
        pattern = r'^#{2,3} ' + re.escape(section) + r'(?=[. ]|$).*'
        match = re.search(pattern, text, re.M)
        if not match:
            raise ValueError('해당 절을 찾지 못했습니다: ' + section)
        level = len(match[0]) - len(match[0].lstrip('#'))
        end = re.search(r'^#{2,' + str(level) + r'} ', text[match.end():], re.M)
        return text[match.start():match.end()+end.start() if end else len(text)].strip()
    headings = list(re.finditer(r'^## [0-9]+\. .*', text, re.M))
    if not headings:
        raise ValueError('인계 제목을 찾지 못했습니다.')
    latest = text[headings[-1].start():]
    lines = latest.splitlines()
    selected = [lines[0]]
    for line in lines[1:]:
        if re.match(r'^[1-4]\. ', line) or line.startswith('상태·재사용 개선 후'):
            selected.append(line)
    return '\n'.join(selected)


def approval_status(path=DEFAULT_DB):
    path = Path(path).resolve()
    if not path.is_file():
        return {'available': False, 'reason': '승인 DB 없음'}
    try:
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
            records = [json.loads(r[0]) for r in db.execute('SELECT record FROM materials')]
            active = {r[0] for r in db.execute('SELECT material_id FROM locations')}
            located = {r[0] for r in db.execute("SELECT value FROM settings WHERE key LIKE 'located:%'")}
            jobs = dict(db.execute('SELECT state,COUNT(*) FROM jobs GROUP BY state'))
        records = [r for r in records if r['id'] in active or r['id'] not in located]
        counts = Counter(r['status'] for r in records)
        return {'available': True, 'materials': len(records),
                'approved': counts['approved'], 'pending': counts['pending'], 'held': counts['held'],
                'publication_holds': sum(bool(r['holds']) for r in records), 'jobs': jobs,
                'notion_delivery': notion_status(path)}
    except (sqlite3.Error, ValueError, KeyError, TypeError):
        return {'available': False, 'reason': '승인 DB 조회 실패'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--section', help='공식 기록의 특정 절 (예: 19.3)')
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    try:
        print(handoff(section=args.section))
    except (OSError, ValueError) as error:
        print('인계 조회 불가: ' + str(error))
        return 1
    status = approval_status(args.db)
    print('승인 상태: ' + json.dumps(status, ensure_ascii=False))
    return 0 if status['available'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
