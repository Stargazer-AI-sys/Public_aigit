"""Local library, revision-bound approval and durable batch checkpoints."""
import copy
import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .cache import digest
from .classification import DEFAULT_POLICY, concept_name, knowledge_index, suggest, validate_paths, validate_policy
from .core import AnalysisError, schema_errors, validate_input, SOURCE_KEYS
from .quality import quality_errors
from .schemas import schema_for


def now():
    return datetime.now(timezone.utc).isoformat()


class Workspace:
    def __init__(self, directory, *, read_only=False):
        self.root = Path(directory).resolve()
        self.path = self.root / 'library.sqlite3'
        self.read_only = read_only
        if read_only:
            if not self.path.is_file():
                raise AnalysisError('LIBRARY_NOT_FOUND', '승인 DB가 없습니다.')
            return
        self.root.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS materials (id TEXT PRIMARY KEY, record TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS revisions (material_id TEXT NOT NULL, snapshot TEXT NOT NULL, record TEXT NOT NULL, PRIMARY KEY(material_id,snapshot));
                CREATE TABLE IF NOT EXISTS locations (path TEXT PRIMARY KEY, material_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS decisions (id INTEGER PRIMARY KEY, material_id TEXT NOT NULL, snapshot TEXT NOT NULL, action TEXT NOT NULL, note TEXT NOT NULL, created TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, state TEXT NOT NULL, record TEXT NOT NULL);
            ''')
            db.execute('INSERT OR IGNORE INTO settings VALUES (?,?)', ('policy', json.dumps(DEFAULT_POLICY, ensure_ascii=False)))

    @contextmanager
    def db(self):
        db = (sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True, timeout=15)
              if self.read_only else sqlite3.connect(self.path, timeout=15))
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback(); raise
        finally:
            db.close()

    def policy(self):
        with self.db() as db:
            return validate_policy(json.loads(db.execute("SELECT value FROM settings WHERE key='policy'").fetchone()[0]))

    def _get(self, db, mid):
        row = db.execute('SELECT record FROM materials WHERE id=?', (mid,)).fetchone()
        if not row:
            raise AnalysisError('LIBRARY_NOT_FOUND', '자료를 찾지 못했습니다.')
        return json.loads(row[0])

    def _save(self, db, record):
        db.execute('INSERT OR REPLACE INTO materials VALUES (?,?)', (record['id'], json.dumps(record, ensure_ascii=False)))
        db.execute('INSERT OR IGNORE INTO revisions VALUES (?,?,?)', (record['id'], record['snapshot'], json.dumps(record, ensure_ascii=False)))

    @staticmethod
    def snapshot(record):
        return digest({k: record[k] for k in ('analysis', 'classification', 'holds', 'policy_digest', 'revision')})

    @staticmethod
    def policy_effect(analysis, policy):
        classification = suggest(analysis, policy)
        return {'paths': classification['paths'], 'scope_confirmed': classification['scope_confirmed'],
                'concepts': [concept_name(c['name'], policy) for c in analysis['concepts']],
                'hold': policy['publication_holds'].get(analysis['source']['filename'])}

    def releases(self, db, record):
        releases = list(record.get('hold_releases', []))
        # Adopt old explicit releases from immutable revision/decision history.
        history = [json.loads(row[0]) for row in db.execute(
            'SELECT record FROM revisions WHERE material_id=?', (record['id'],))]
        snapshots = {row[0] for row in db.execute(
            "SELECT snapshot FROM decisions WHERE material_id=? AND action='release-hold'", (record['id'],))}
        for released in history:
            if released['snapshot'] not in snapshots:
                continue
            previous = [r for r in history if r['revision'] < released['revision']]
            if not previous:
                continue
            previous = max(previous, key=lambda r: r['revision'])
            for reason in previous['holds']:
                entry = {'reason': reason, 'input_digest': released['input_digest'],
                         'analysis_digest': digest(released['analysis'])}
                if entry not in releases:
                    releases.append(entry)
        return releases

    @staticmethod
    def policy_holds(record, policy):
        reason = policy['publication_holds'].get(record['analysis']['source']['filename'])
        released = {'reason': reason, 'input_digest': record['input_digest'],
                    'analysis_digest': digest(record['analysis'])}
        return [reason] if reason and released not in record.get('hold_releases', []) else []

    def ingest(self, analysis, data, *, origin='', location=None, analysis_context=None):
        data = validate_input(data)
        if analysis.get('source') != {key: data[key] for key in SOURCE_KEYS}:
            raise AnalysisError('LIBRARY_SOURCE_ERROR', '분석 결과와 원본 식별정보가 다릅니다.')
        errors = schema_errors(analysis, schema_for(analysis))
        if errors or quality_errors(analysis, data['extracted_text']):
            raise AnalysisError('LIBRARY_VALIDATION_ERROR', '분석 구조·본문 근거·단락 연결을 확인하세요.')
        policy = self.policy()
        mid = digest(analysis['source'])
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT record FROM materials WHERE id=?', (mid,)).fetchone()
            old = json.loads(row[0]) if row else None
            same = old and old.get('base_analysis_digest', digest(old['analysis'])) == digest(analysis) and old['input_digest'] == digest(data) and old.get('policy_effect', self.policy_effect(old['analysis'], policy)) == self.policy_effect(old['analysis'], policy)
            if same:
                record = old
            else:
                record = {'id': mid, 'analysis': copy.deepcopy(analysis), 'base_analysis_digest': digest(analysis),
                          'content_edits': [], 'input_digest': digest(data),
                          'classification': suggest(analysis, policy), 'policy_digest': digest(policy),
                          'policy_effect': self.policy_effect(analysis, policy),
                          'holds': ([policy['publication_holds'][data['filename']]] if data['filename'] in policy['publication_holds'] else []),
                          'status': 'pending', 'note': '', 'origin': origin, 'revision': (old['revision'] + 1 if old else 1),
                          'approved_snapshot': None, 'updated_at': now()}
                # Re-ingestion cannot silently clear an existing publication hold.
                if old:
                    record['hold_releases'] = self.releases(db, old)
                    record['holds'] = list(dict.fromkeys(self.policy_holds(record, policy) + old['holds']))
                record['snapshot'] = self.snapshot(record)
                self._save(db, record)
            if analysis_context is not None:
                record['analysis_context'] = copy.deepcopy(analysis_context)
                self._save(db, record)
            if location:
                db.execute('INSERT OR REPLACE INTO locations VALUES (?,?)', (str(Path(location).resolve()), mid))
                db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', ('located:'+mid, mid))
        return record

    def list(self, *, current=True):
        with self.db() as db:
            records = [json.loads(row[0]) for row in db.execute('SELECT record FROM materials ORDER BY id')]
            locations = dict(db.execute('SELECT path,material_id FROM locations'))
        active = set(locations.values())
        for r in records:
            r['locations'] = [p for p, mid in locations.items() if mid == r['id']]
        # A located revision superseded at every path is excluded from the active catalog.
        # Track location history explicitly instead of deleting old results.
        with self.db() as db:
            located = {row[0] for row in db.execute("SELECT value FROM settings WHERE key LIKE 'located:%'")}
        for r in records:
            r['current'] = r['id'] in active or r['id'] not in located
        return [r for r in records if r['current'] or not current]

    def observe(self, location, mid):
        with self.db() as db:
            self._get(db, mid)
            db.execute('INSERT OR REPLACE INTO locations VALUES (?,?)', (str(Path(location).resolve()), mid))
            db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', ('located:'+mid, mid))

    def get(self, mid):
        with self.db() as db:
            return self._get(db, mid)

    def reusable(self, data):
        mid = digest({key: data[key] for key in SOURCE_KEYS})
        try:
            record = self.get(mid)
        except AnalysisError as error:
            if error.code == 'LIBRARY_NOT_FOUND':
                return None
            raise
        if record['input_digest'] != digest(data):
            raise AnalysisError('LIBRARY_INTEGRITY_ERROR', '동일 원본 식별자의 추출 내용이 변경됐습니다. 원본과 수집 결과를 확인하세요.')
        if (record['snapshot'] != self.snapshot(record) or schema_errors(record['analysis'], schema_for(record['analysis']))
                or quality_errors(record['analysis'], data['extracted_text'])):
            raise AnalysisError('LIBRARY_INTEGRITY_ERROR', '저장 결과 검증이 실패했습니다. 자동 재호출하지 않습니다.')
        return record

    def history(self, mid):
        with self.db() as db:
            rows = [json.loads(r[0]) for r in db.execute('SELECT record FROM revisions WHERE material_id=?', (mid,))]
        return sorted(rows, key=lambda r: r['revision'])

    def decide(self, mid, expected, action, *, paths=None, note='', confirm_partial_scope=False):
        if action not in ('approve', 'hold', 'edit') or not isinstance(note, str) or len(note) > 10000:
            raise AnalysisError('REVIEW_ERROR', '검토 동작·메모를 확인하세요.')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            record = self._get(db, mid)
            if expected != record['snapshot']:
                raise AnalysisError('REVIEW_STALE', '검토 중 자료가 변경됐습니다. 새로 확인하세요.')
            if confirm_partial_scope:
                classification = record['classification']
                known = [p for p in classification['paths'] if '관련성 미확인' not in p
                         and any(reason.get('path') == p for reason in classification.get('reasons', []))]
                if (confirm_partial_scope is not True or action != 'approve' or paths is not None
                        or record['holds'] or not known or not classification.get('unclassified_topics')):
                    raise AnalysisError('PUBLICATION_HOLD', '확인된 분류가 없거나 별도 게시 보류가 있어 승인할 수 없습니다.')
                # The user acknowledges unmatched topics; do not invent their
                # mapping, change the analysis, or auto-approve on ingestion.
                classification['paths'] = validate_paths(known)
                classification['scope_confirmed'] = True
                classification['reviewed_by_user'] = True
                classification['partial_scope_confirmed_by_user'] = True
            if paths is not None:
                record['classification']['paths'] = validate_paths(paths)
                record['classification']['scope_confirmed'] = not any('관련성 미확인' in p for p in paths)
                record['classification']['reviewed_by_user'] = True
            if action == 'approve' and (record['holds'] or not record['classification']['scope_confirmed']):
                raise AnalysisError('PUBLICATION_HOLD', '게시 보류 또는 관련성 미확인 자료는 승인할 수 없습니다.')
            record['revision'] += 1
            record['snapshot'] = self.snapshot(record)
            record['status'] = {'approve': 'approved', 'hold': 'held', 'edit': 'pending'}[action]
            record['approved_snapshot'] = record['snapshot'] if action == 'approve' else None
            record['note'] = note
            record['updated_at'] = now()
            db.execute('INSERT INTO decisions(material_id,snapshot,action,note,created) VALUES (?,?,?,?,?)',
                       (mid, record['snapshot'], action, note, now()))
            self._save(db, record)
            return record

    def release_hold(self, mid, expected, reason):
        if not isinstance(reason, str) or not reason.strip():
            raise AnalysisError('REVIEW_ERROR', '게시 보류 해제 근거가 필요합니다.')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            record = self._get(db, mid)
            if record['snapshot'] != expected:
                raise AnalysisError('REVIEW_STALE', '자료가 변경됐습니다.')
            record['hold_releases'] = self.releases(db, record)
            for hold in record['holds']:
                entry = {'reason': hold, 'input_digest': record['input_digest'],
                         'analysis_digest': digest(record['analysis'])}
                if entry not in record['hold_releases']:
                    record['hold_releases'].append(entry)
            record['holds'] = []; record['status'] = 'pending'; record['approved_snapshot'] = None
            record['revision'] += 1; record['snapshot'] = self.snapshot(record)
            record['note'] = reason; record['updated_at'] = now()
            db.execute('INSERT INTO decisions(material_id,snapshot,action,note,created) VALUES (?,?,?,?,?)',
                       (mid, record['snapshot'], 'release-hold', reason, now()))
            self._save(db, record)
            return record

    def revise(self, mid, expected, changes, note=''):
        """Edit prose only. Source identity, evidence, links and raw AI runs are immutable."""
        if not isinstance(changes, list) or not 1 <= len(changes) <= 64 or not isinstance(note, str) or len(note) > 10000:
            raise AnalysisError('REVIEW_ERROR', '본문 수정 목록·메모를 확인하세요.')
        allowed = r'^/(summary|concepts/[0-9]+/description|practice/[0-9]+/description|relationships/[0-9]+/description|theory/(definitions|principles)/[0-9]+/content|sections/[0-9]+/title)$'
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            r = self._get(db, mid)
            if r['snapshot'] != expected:
                raise AnalysisError('REVIEW_STALE', '검토 중 자료가 변경됐습니다.')
            edited = copy.deepcopy(r['analysis'])
            edits = []
            try:
                for change in changes:
                    pointer, value = change['path'], change['value']
                    if not isinstance(pointer, str) or not re.fullmatch(allowed, pointer) or not isinstance(value, str) or not value.strip() or len(value) > 20000:
                        raise ValueError()
                    parts, parent = pointer.split('/')[1:], edited
                    for part in parts[:-1]:
                        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
                    old = parent[parts[-1]]
                    parent[parts[-1]] = value
                    edits.append({'path': pointer, 'before': old, 'after': value, 'note': note, 'created': now()})
            except (KeyError, IndexError, TypeError, ValueError):
                raise AnalysisError('REVIEW_ERROR', '수정 가능한 설명 경로·값을 확인하세요. 원문·인용·연결은 수정할 수 없습니다.') from None
            evidence = [v['evidence'] for group in edited.get('theory', {}).values() for v in group]
            evidence += [v['evidence'] for v in edited.get('practice', [])]
            if schema_errors(edited, schema_for(edited)) or quality_errors(edited, '\n'.join(evidence)):
                raise AnalysisError('REVIEW_ERROR', '수정한 내용이 구조·요약·연결 기준을 벗어납니다.')
            r['analysis'] = edited; r.setdefault('content_edits', []).extend(edits)
            policy = validate_policy(json.loads(db.execute("SELECT value FROM settings WHERE key='policy'").fetchone()[0]))
            r['hold_releases'] = self.releases(db, r)
            r['holds'] = list(dict.fromkeys(r['holds'] + self.policy_holds(r, policy)))
            r['revision'] += 1; r['snapshot'] = self.snapshot(r)
            r['status'] = 'pending'; r['approved_snapshot'] = None
            r['updated_at'] = now(); self._save(db, r)
            db.execute('INSERT INTO decisions(material_id,snapshot,action,note,created) VALUES (?,?,?,?,?)',
                       (mid, r['snapshot'], 'revise', note, now()))
            return r

    def set_policy(self, policy):
        policy = validate_policy(policy)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            old_policy = validate_policy(json.loads(db.execute("SELECT value FROM settings WHERE key='policy'").fetchone()[0]))
            db.execute('UPDATE settings SET value=? WHERE key=?', (json.dumps(policy, ensure_ascii=False), 'policy'))
            for row in db.execute('SELECT record FROM materials').fetchall():
                r = json.loads(row[0])
                before = self.policy_effect(r['analysis'], old_policy)
                after = self.policy_effect(r['analysis'], policy)
                r['hold_releases'] = self.releases(db, r)
                holds = list(dict.fromkeys(r['holds'] + self.policy_holds(r, policy)))
                changed = any(before[k] != after[k] for k in ('paths', 'scope_confirmed', 'concepts')) or holds != r['holds']
                r['policy_effect'] = after
                if changed:
                    if before['paths'] != after['paths'] or before['scope_confirmed'] != after['scope_confirmed']:
                        r['classification'] = suggest(r['analysis'], policy)
                    r['holds'] = holds
                    r['policy_digest'] = digest(policy); r['revision'] += 1; r['snapshot'] = self.snapshot(r)
                    r['status'] = 'pending'; r['approved_snapshot'] = None
                    r['updated_at'] = now()
                self._save(db, r)

    def catalog(self):
        materials = self.list()
        index = knowledge_index(materials, self.policy())
        from .curriculum import learning_view
        curriculum = self.policy().get('curriculum')
        return {'format_version': 1, 'materials': materials,
                'curriculum': learning_view(materials, index['concepts'], curriculum) if curriculum else None, **index}

    def approved(self):
        policy = self.policy()
        records = [r for r in self.list() if r['status'] == 'approved' and not r['holds']
                   and r['approved_snapshot'] == self.snapshot(r)
                   and r.get('policy_effect', self.policy_effect(r['analysis'], policy)) == self.policy_effect(r['analysis'], policy)]
        return {'format_version': 1, 'destination': 'local-approved-snapshot', 'notion_sent': False,
                'materials': records, **knowledge_index(records, policy)}

    def claim_job(self, key, details, *, retry=False, reanalyze=False):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT state,record FROM jobs WHERE id=?', (key,)).fetchone()
            if old and (old[0] == 'running' or (old[0] == 'success' and not reanalyze)
                        or (old[0] != 'success' and not retry)):
                return False, {'state': old[0], **json.loads(old[1])}
            record = dict(details, started_at=now())
            db.execute('INSERT OR REPLACE INTO jobs VALUES (?,?,?)', (key, 'running', json.dumps(record, ensure_ascii=False)))
            return True, record

    def finish_job(self, key, state, details):
        if state not in ('success', 'failed'):
            raise ValueError('Invalid job state')
        with self.db() as db:
            row = db.execute('SELECT state FROM jobs WHERE id=?', (key,)).fetchone()
            if not row or row[0] != 'running':
                raise AnalysisError('JOB_STATE_ERROR', '작업 상태가 변경됐습니다.')
            db.execute('UPDATE jobs SET state=?,record=? WHERE id=?', (state, json.dumps(dict(details, ended_at=now()), ensure_ascii=False), key))

    def recover_jobs(self):
        with self.db() as db:
            # Caller must hold the workspace batch lock, so these are interrupted jobs.
            db.execute("UPDATE jobs SET state='interrupted' WHERE state='running'")
