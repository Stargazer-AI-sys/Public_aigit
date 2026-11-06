"""Approved publication plans and durable offline delivery simulation.

No network adapter or credentials. Logical properties/relations are a proposal;
real Notion data sources and connector capabilities must be bound separately.
"""
import copy
import json
import os
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from uuid import uuid4
from uuid import UUID

from .cache import digest
from .classification import knowledge_index
from .core import AnalysisError
from .render import redact, render_markdown


MAPPING = {
    'version': 1,
    'binding_status': 'unbound',
    'conflict_policy': 'stop-and-review',
    'source_revision_policy': 'update-existing-page',
    'collections': {
        'category': {'title': '분야', 'properties': {'name': 'title', 'path': 'rich_text'},
                     'relations': {'parent': 'category'}},
        'concept': {'title': '개념', 'properties': {'name': 'title'},
                    'relations': {'materials': 'material', 'categories': 'category'}},
        'material': {'title': '학습자료', 'properties': {'name': 'title', 'source_hash': 'rich_text',
                     'approval_snapshot': 'rich_text', 'source_locations': 'rich_text'},
                     'relations': {'categories': 'category', 'concepts': 'concept',
                                   'related': 'material', 'practice': 'practice'}},
        'practice': {'title': '실습 / 프로젝트',
                     'properties': {'name': 'title', 'source_pointer': 'rich_text'},
                     'relations': {'material': 'material', 'concepts': 'concept'}},
    },
    'required_binding_inputs': ['target_page_or_data_sources', 'property_and_relation_ids',
                                'connection_permissions', 'source_revision_policy_confirmation'],
}
for _collection in MAPPING['collections'].values():
    _collection['properties']['sync_key'] = 'rich_text'


def fail(code, message):
    raise AnalysisError(code, message)


def key(kind, identity):
    return kind + ':' + digest(identity)


def material_key(record):
    # A content hash identifies a revision, not the continuing source document.
    # Explicit overrides resolve same-name sources; ambiguous defaults fail below.
    source = record['analysis']['source']
    identity = record.get('publication_identity') or [source['filename'], source['extension']]
    return key('material', identity)


def publication_mode(target):
    mode = (target or {}).get('publication', {}).get('mode', 'full')
    if mode not in ('full', 'materials'):
        fail('PUBLISH_TARGET_ERROR', '지원하지 않는 게시 모드입니다.')
    return mode


def enable_material_publication(target, directory):
    """Keep legacy approved pages untouched when first opting into minimal mode."""
    from .notion_reader import refresh_reader_target
    result = refresh_reader_target(target, directory)
    result = copy.deepcopy(result)
    if publication_mode(result) == 'materials':
        return result
    legacy = {}
    ledger = Path(directory)/'delivery.sqlite3'
    if ledger.is_file():
        with closing(sqlite3.connect(ledger.resolve().as_uri()+'?mode=ro', uri=True)) as db:
            for eid, raw in db.execute('SELECT entity_key,record FROM receipts'):
                record = json.loads(raw)
                if record['document']['kind'] == 'material':
                    legacy[eid] = record['document']['properties']['approval_snapshot']
    result['publication'] = {'mode': 'materials', 'legacy_snapshots': legacy}
    return result


def mapping_for(target=None):
    mapping = copy.deepcopy(MAPPING)
    if target is None:
        return mapping
    try:
        material = target['material_database']
        for value in (target['parent_page']['id'], material['id'], material['data_source_id']):
            UUID(value)
        if target['format_version'] != 1 or target['live_write_enabled'] is not False:
            raise ValueError()
        properties = material['property_mapping']
        if properties.get('name') is None:
            raise ValueError()
        for logical, actual in properties.items():
            if material['observed_properties'].get(actual) != mapping['collections']['material']['properties'][logical]:
                raise ValueError()
    except (KeyError, TypeError, ValueError, AttributeError):
        fail('PUBLISH_TARGET_ERROR', '대상 ID·기존 속성 형식·모의 전송 제한을 확인하세요.')
    mapping['binding_status'] = 'partial'
    mapping['target'] = copy.deepcopy(target)
    mapping['missing_material_properties'] = sorted(set(mapping['collections']['material']['properties']) - set(properties))
    mapping['unbound_collections'] = ['category', 'concept', 'practice']
    mapping['material_relations_ready'] = False
    if 'collections' in target:
        unbound = []
        for kind, spec in mapping['collections'].items():
            binding = target['collections'].get(kind)
            if not binding:
                unbound.append(kind); continue
            try:
                UUID(binding['data_source_id'])
                for logical, expected in spec['properties'].items():
                    actual = binding['property_mapping'][logical]
                    if binding['observed_properties'].get(actual) != expected:
                        raise ValueError()
                for logical, destination in spec['relations'].items():
                    actual = binding['relation_mapping'][logical]
                    if binding['observed_relations'].get(actual) != target['collections'][destination]['data_source_id']:
                        raise ValueError()
                for actual in binding['system_properties'].values():
                    if binding['observed_properties'].get(actual) != 'rich_text':
                        raise ValueError()
            except (KeyError, TypeError, ValueError):
                fail('PUBLISH_TARGET_ERROR', '실제 DB 속성·관계 대상이 매핑과 다릅니다.')
        mapping['unbound_collections'] = unbound
        mapping['material_relations_ready'] = not unbound
        if not unbound:
            mapping['binding_status'] = 'bound'
            mapping['missing_material_properties'] = []
    return mapping


def make_plan(store, *, target=None, material_ids=None):
    """Build all desired logical entities only from currently valid approvals."""
    approved = store.approved()
    if material_ids is not None:
        selected = set(material_ids)
        approved['materials'] = [r for r in approved['materials'] if r['id'] in selected]
        if {r['id'] for r in approved['materials']} != selected:
            fail('PUBLISH_STALE', '선택 자료의 현재 승인을 확인할 수 없습니다.')
        approved.update(knowledge_index(approved['materials'], store.policy()))
    records = approved['materials']
    material_keys = {r['id']: material_key(r) for r in records}
    if len(set(material_keys.values())) != len(material_keys):
        fail('PUBLISH_SOURCE_AMBIGUOUS', '동일 이름의 원본이 여러 건입니다. 원본별 지속 식별값 지정이 필요합니다.')
    entities = {}

    def add(eid, kind, properties, body, relations):
        properties = dict(properties, sync_key=eid)
        entities[eid] = {'key': eid, 'kind': kind, 'properties': properties,
                         'body': redact(body), 'relations': relations}

    if publication_mode(target) == 'materials':
        from .notion_reader import material_body, material_navigation
        legacy = target.get('publication', {}).get('legacy_snapshots', {})
        preserved = []
        for r in records:
            analysis = r['analysis']; eid = material_keys[r['id']]
            render_markdown(analysis)  # Keep the same schema/content-link gate as full mode.
            add(eid, 'material',
                {'name': analysis['source']['filename'], 'source_hash': analysis['source']['material_id'],
                 'approval_snapshot': r['snapshot'], 'source_locations': '\n'.join(r.get('locations', []))},
                material_body(r, material_navigation(target)), {})
            if legacy.get(eid) == r['snapshot']:
                preserved.append(eid)
        plan = {'format_version': 1, 'mode': 'offline-plan', 'notion_sent': False,
                'publication_mode': 'materials', 'preserved_materials': sorted(preserved),
                'mapping': mapping_for(target), 'approvals': {r['id']: r['snapshot'] for r in records},
                'entities': sorted(entities.values(), key=lambda e: e['key'])}
        plan['plan_digest'] = digest(plan)
        return plan

    material_concepts = {r['id']: [] for r in records}
    categories = {}
    for r in records:
        mids = []
        for path in r['classification']['paths']:
            for depth in range(2, len(path)+1):
                prefix = path[:depth]
                cid = key('category', prefix)
                add(cid, 'category', {'name': prefix[-1], 'path': ' / '.join(prefix)}, '',
                    {'parent': [key('category', prefix[:-1])] if depth > 2 else []})
                mids.append(cid)
        categories[r['id']] = sorted(set(mids))
    for concept in approved['concepts']:
        cid = 'concept:' + concept['id']
        sources = concept['sources']
        for source in sources:
            material_concepts[source['material_id']].append(cid)
        add(cid, 'concept', {'name': concept['name']},
            '\n\n'.join(redact(s['filename']) + '\n' + redact(s['description']) for s in sources),
            {'materials': sorted({material_keys[s['material_id']] for s in sources}),
             'categories': sorted({c for s in sources for c in categories[s['material_id']]})})
    for r in records:
        mid = r['id']
        practices = []
        analysis = r['analysis']
        for index, item in enumerate(analysis.get('practice', [])):
            pid = key('practice', [material_keys[mid], index])
            practices.append(pid)
            add(pid, 'practice', {'name': item['title'], 'source_pointer': f'/practice/{index}'},
                item['description'] + '\n\n원문 근거\n' + item['evidence'],
                {'material': [material_keys[mid]], 'concepts': sorted(material_concepts[mid])})
        add(material_keys[mid], 'material',
            {'name': analysis['source']['filename'], 'source_hash': analysis['source']['material_id'],
             'approval_snapshot': r['snapshot'], 'source_locations': '\n'.join(r.get('locations', []))},
            render_markdown(analysis),
            {'categories': categories[mid], 'concepts': sorted(material_concepts[mid]),
             'related': sorted(material_keys[v['material_id']] for v in approved['related'][mid]),
             'practice': practices})
    # Redact display properties too; source hashes/snapshots remain unchanged.
    for entity in entities.values():
        entity['properties'] = {k: redact(v) for k, v in entity['properties'].items()}
        for relation in entity['relations'].values():
            if any(v not in entities for v in relation):
                fail('PUBLISH_PLAN_ERROR', '관계 대상이 계획에 없습니다.')
    if target and target.get('reader', {}).get('version') == 1:
        from .notion_reader import apply_reader
        apply_reader(entities, approved, store.policy(), target, material_keys)
    plan = {'format_version': 1, 'mode': 'offline-plan', 'notion_sent': False,
            'mapping': mapping_for(target),
            'approvals': {r['id']: r['snapshot'] for r in records},
            'entities': sorted(entities.values(), key=lambda e: e['key'])}
    plan['plan_digest'] = digest(plan)
    return plan


def verify_plan(plan, store, target=None, material_ids=None):
    if plan != make_plan(store, target=target, material_ids=material_ids):
        fail('PUBLISH_STALE', '승인·정책·대상 또는 계획이 변경됐습니다. 미리보기를 다시 만드세요.')


def verify_approvals(plan, store, target=None, material_ids=None):
    # The full content plan was verified once at entry. Recheck approval/version
    # guards per operation without re-rendering every material for every entity.
    current = {r['id']: r['snapshot'] for r in store.approved()['materials']}
    if material_ids is not None:
        current = {mid: snapshot for mid, snapshot in current.items() if mid in set(material_ids)}
    if current != plan['approvals'] or plan['mapping'] != mapping_for(target):
        fail('PUBLISH_STALE', '전송 중 승인 버전 또는 게시 조건이 변경됐습니다.')


def preview(plan):
    lines = ['# Notion 전송 미리보기', '',
             ('로컬 계획 · 실제 전송 없음 · DB 속성/관계 바인딩 확인' if plan['mapping']['binding_status'] == 'bound'
              else '로컬 계획 · 실제 전송 없음 · DB 속성/관계 바인딩 미확정'), '',
             '충돌 시 중지 · 승인된 원본 변경은 기존 페이지 갱신', '',
             f"승인 자료 {len(plan['approvals'])}건 · 게시 객체 {len(plan['entities'])}개", '']
    if 'target' in plan['mapping']:
        target = plan['mapping']['target']
        lines += ['대상 페이지: ' + target['parent_page']['name'],
                  '학습자료 DB: ' + target['material_database']['name'],
                  '제목 속성: ' + target['material_database']['property_mapping']['name'],
                  '연결 상태: ' + plan['mapping']['binding_status'] + ' · 실제 전송은 별도 명시 실행', '']
    for entity in plan['entities']:
        lines += ['## ' + entity['kind'] + ' · ' + entity['properties']['name'], '',
                  entity['body'], '', '연결: ' + json.dumps(entity['relations'], ensure_ascii=False), '']
    return '\n'.join(lines)


class DeliveryError(Exception):
    def __init__(self, code='TRANSPORT_FAILED', retry_after=None):
        self.code, self.retry_after = code, retry_after


class MockNotion:
    """Persistent simulated remote. Its IDs and receipt markers are mock-only.

    A future live adapter must implement lookup with full pagination, retrieve
    complete managed content, detect edit stamps, and reconcile uncertain writes.
    """
    mode = 'mock'

    def __init__(self, path):
        self.path = Path(path).resolve()
        if self.path.is_file():
            with closing(sqlite3.connect(self.path.as_uri()+'?mode=ro', uri=True)) as db:
                if not db.execute("SELECT name FROM sqlite_master WHERE name='mock_identity'").fetchone():
                    fail('PUBLISH_PATH_ERROR', '기존 일반 DB를 모의 대상으로 사용할 수 없습니다.')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.writes = 0
        with closing(sqlite3.connect(self.path)) as db:
            db.executescript('CREATE TABLE IF NOT EXISTS mock_identity (id TEXT PRIMARY KEY);'
                             'CREATE TABLE IF NOT EXISTS pages (id TEXT PRIMARY KEY, entity_key TEXT NOT NULL,'
                             'document TEXT NOT NULL, stamp TEXT NOT NULL, operation_id TEXT NOT NULL);')
            if not db.execute('SELECT id FROM mock_identity').fetchone():
                db.execute('INSERT INTO mock_identity VALUES (?)', (uuid4().hex,))
            self.identity = db.execute('SELECT id FROM mock_identity').fetchone()[0]
            db.commit()

    def lookup(self, entity_key):
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute('SELECT id,document,stamp,operation_id FROM pages WHERE entity_key=?', (entity_key,))
            return [{'id': r[0], 'document': json.loads(r[1]), 'stamp': r[2], 'operation_id': r[3]} for r in rows]

    def write(self, entity_key, document, expected_stamp, operation_id):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('BEGIN IMMEDIATE')
            rows = db.execute('SELECT id,stamp FROM pages WHERE entity_key=?', (entity_key,)).fetchall()
            if len(rows) > 1 or (rows and rows[0][1] != expected_stamp) or (not rows and expected_stamp is not None):
                raise DeliveryError('REMOTE_CONFLICT')
            page_id = rows[0][0] if rows else 'mock-'+uuid4().hex
            stamp = uuid4().hex
            db.execute('INSERT OR REPLACE INTO pages VALUES (?,?,?,?,?)',
                       (page_id, entity_key, json.dumps(document, ensure_ascii=False), stamp, operation_id))
            db.commit()
        self.writes += 1
        return self.lookup(entity_key)[0]


class Outbox:
    def __init__(self, directory, remote_identity):
        self.root = Path(directory).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root/'delivery.sqlite3'
        self.identity = remote_identity
        if self.path.is_file():
            with closing(sqlite3.connect(self.path.as_uri()+'?mode=ro', uri=True)) as db:
                if not db.execute("SELECT name FROM sqlite_master WHERE name='destination'").fetchone():
                    fail('PUBLISH_PATH_ERROR', '기존 일반 DB를 전송 이력으로 사용할 수 없습니다.')
        with closing(sqlite3.connect(self.path)) as db:
            db.executescript('CREATE TABLE IF NOT EXISTS destination (id TEXT PRIMARY KEY);'
                             'CREATE TABLE IF NOT EXISTS receipts (entity_key TEXT PRIMARY KEY, record TEXT NOT NULL);'
                             'CREATE TABLE IF NOT EXISTS operations (id TEXT PRIMARY KEY, state TEXT NOT NULL, record TEXT NOT NULL);')
            existing = db.execute('SELECT id FROM destination').fetchone()
            if existing and existing[0] != remote_identity:
                fail('PUBLISH_DESTINATION_MISMATCH', '다른 모의 대상의 전송 이력입니다.')
            db.execute('INSERT OR IGNORE INTO destination VALUES (?)', (remote_identity,))
            db.commit()

    def read(self, table, value):
        column = 'entity_key' if table == 'receipts' else 'id'
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute('SELECT record FROM '+table+' WHERE '+column+'=?', (value,)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, table, value, record, state=None):
        with closing(sqlite3.connect(self.path)) as db:
            if table == 'receipts':
                db.execute('INSERT OR REPLACE INTO receipts VALUES (?,?)', (value, json.dumps(record, ensure_ascii=False)))
            else:
                db.execute('INSERT OR REPLACE INTO operations VALUES (?,?,?)',
                           (value, state, json.dumps(dict(record, state=state), ensure_ascii=False)))
            db.commit()

    def pending(self, eid):
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute("SELECT id,record FROM operations WHERE state!='success'").fetchall()
        return [(opid, json.loads(raw)) for opid, raw in rows if json.loads(raw)['entity_key'] == eid]

    def records(self, table):
        """Read one local snapshot for candidate selection, without remote calls."""
        if table not in ('receipts', 'operations'):
            raise ValueError('unsupported outbox table')
        column = 'entity_key' if table == 'receipts' else 'id'
        with closing(sqlite3.connect(self.path.as_uri()+'?mode=ro', uri=True)) as db:
            return {key: json.loads(raw) for key, raw in db.execute('SELECT '+column+',record FROM '+table)}


def deliver_mock(plan, store, remote, directory, *, retry=False, recover_interrupted=False, target=None, material_ids=None):
    """Two-phase mock delivery: content first, then resolved relations. No retries.

    Failed/uncertain operations need explicit retry. A surviving lock can only be
    removed after the caller confirms the previous worker has stopped.
    """
    if not isinstance(remote, MockNotion) or remote.mode != 'mock':
        fail('PUBLISH_MODE_ERROR', '이번 명령은 로컬 모의 대상만 허용합니다.')
    return deliver_plan(plan, store, remote, directory, retry=retry, recover_interrupted=recover_interrupted,
                        target=target, material_ids=material_ids)


def deliver_plan(plan, store, remote, directory, *, retry=False, recover_interrupted=False, target=None, material_ids=None,
                 phases=('content', 'relations')):
    verify_plan(plan, store, target, material_ids)
    outbox_path = Path(directory).resolve()/'delivery.sqlite3'
    if outbox_path == remote.path or outbox_path == store.path or remote.path == store.path:
        fail('PUBLISH_PATH_ERROR', '승인 DB·전송 이력·모의 DB 경로를 분리하세요.')
    outbox = Outbox(directory, remote.identity)
    lock = outbox.root/'delivery.lock'
    if recover_interrupted:
        lock.unlink(missing_ok=True)
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        fail('PUBLISH_LOCKED', '전송 실행 중 또는 중단 잠금입니다. 종료 확인 후 명시적으로 복구하세요.')
    os.close(fd)
    report = {'mode': remote.mode, 'notion_sent': False, 'writes': 0, 'skipped': 0,
              'reconciled': 0, 'errors': [], 'plan_digest': plan['plan_digest']}
    if getattr(remote, 'local_source', False):
        report.update(publication_policy='local-source', normal_write_confirmation='tool-response')
    started = time.monotonic()
    report['phase_seconds'] = {}
    if hasattr(remote, 'write_many'):
        remote.before_write = lambda: verify_approvals(plan, store, target, material_ids)
    try:
        if hasattr(remote, 'prepare_plan'):
            remote.retry_requested = retry
            try:
                remote.prepare_plan(plan)
            except DeliveryError as error:
                report['errors'].append({'code': error.code})
                return report
        for phase in phases:
            phase_started = time.monotonic()
            queued = []
            for entity in plan['entities']:
                verify_approvals(plan, store, target, material_ids)
                eid = entity['key']
                matches = remote.lookup(eid)
                if len(matches) > 1:
                    report['errors'].append({'key': eid, 'code': 'REMOTE_DUPLICATE'}); return report
                current = matches[0] if matches else None
                receipt = outbox.read('receipts', eid)
                # A previous relation write can have committed with its response
                # lost. Reconcile that receipt before the next run's content
                # phase checks the edit stamp, otherwise it looks like a user edit.
                pending = outbox.read('operations', current['operation_id']) if current else None
                if pending and pending['state'] != 'success':
                    if not retry:
                        report['errors'].append({'key': eid, 'code': 'EXPLICIT_RETRY_REQUIRED'}); return report
                    if pending['entity_key'] == eid and current['document'] == pending['desired']:
                        outbox.save('receipts', eid, current)
                        outbox.save('operations', current['operation_id'], pending, 'success')
                        receipt = current
                        report['reconciled'] += 1
                operation_id = digest([remote.identity, plan['plan_digest'], phase, eid])
                operation = outbox.read('operations', operation_id)
                if operation and operation['state'] != 'success':
                    if not retry:
                        report['errors'].append({'key': eid, 'code': 'EXPLICIT_RETRY_REQUIRED'}); return report
                    if (current and current['document'] == operation['desired']
                            and current['operation_id'] == operation_id):
                        outbox.save('receipts', eid, current)
                        outbox.save('operations', operation_id, operation, 'success')
                        receipt = current
                        report['reconciled'] += 1
                    elif (current['stamp'] if current else None) != operation['before_stamp']:
                        report['errors'].append({'key': eid, 'code': 'REMOTE_CONFLICT'}); return report
                if current and (not receipt or current['id'] != receipt['id'] or current['stamp'] != receipt['stamp']):
                    report['errors'].append({'key': eid, 'code': 'REMOTE_CONFLICT'}); return report
                if receipt and not current:
                    report['errors'].append({'key': eid, 'code': 'REMOTE_MISSING'}); return report
                if eid in plan.get('preserved_materials', []):
                    if (not current or not receipt or current['document']['properties'].get('approval_snapshot')
                            != entity['properties']['approval_snapshot']):
                        report['errors'].append({'key': eid, 'code': 'REMOTE_CONFLICT'}); return report
                    report['skipped'] += 1; continue
                if phase == 'allocate' and current:
                    report['skipped'] += 1; continue
                desired = copy.deepcopy(current['document']) if current else {'relations': {}}
                if phase == 'allocate':
                    desired = {'kind': entity['kind'], 'properties': entity['properties'], 'body': '', 'relations': {}}
                if phase in ('content', 'complete'):
                    desired.update(kind=entity['kind'], properties=entity['properties'], body=entity['body'])
                if phase in ('relations', 'complete'):
                    relations = (copy.deepcopy(current['document']['relations'])
                                 if current and plan.get('publication_mode') == 'materials' else {})
                    for name, keys in entity['relations'].items():
                        relations[name] = []
                        for relation_target in keys:
                            found = (remote.resolve(relation_target) if hasattr(remote, 'resolve')
                                     else remote.lookup(relation_target))
                            if len(found) != 1:
                                report['errors'].append({'key': eid, 'code': 'RELATION_TARGET_ERROR'}); return report
                            relations[name].append(found[0]['id'])
                    desired['relations'] = relations
                if current and current['document'] == desired:
                    report['skipped'] += 1; continue
                if phase == 'allocate' and retry:
                    # Partial ID allocation can change the reader map and hence
                    # the plan digest. Resume the original missing-page intent,
                    # rather than leaving an older uncertain operation behind.
                    candidates = [(oid, op) for oid, op in outbox.pending(eid)
                                  if op.get('phase') == 'allocate' and op.get('before_stamp') is None
                                  and op.get('desired') == desired]
                    if len(candidates) > 1:
                        report['errors'].append({'key': eid, 'code': 'REMOTE_CONFLICT'}); return report
                    if candidates:
                        operation_id = candidates[0][0]
                checkpoint = outbox.read('operations', operation_id)
                operation = (dict(checkpoint) if checkpoint and checkpoint.get('desired') == desired else {})
                operation.update(entity_key=eid, phase=phase, desired=desired,
                                 before_stamp=current['stamp'] if current else None)
                if hasattr(remote, 'write_many'):
                    queued.append(dict(operation, operation_id=operation_id))
                    continue
                outbox.save('operations', operation_id, operation, 'inflight')
                try:
                    result = remote.write(eid, desired, operation['before_stamp'], operation_id)
                    outbox.save('receipts', eid, result)
                    outbox.save('operations', operation_id, operation, 'success')
                    report['writes'] += 1
                    report['notion_sent'] = remote.mode == 'notion-mcp'
                except (DeliveryError, OSError) as error:
                    # Never persist exception text; it may contain tokens or response bodies.
                    code = error.code if isinstance(error, DeliveryError) else 'DELIVERY_IO_ERROR'
                    operation = outbox.read('operations', operation_id) or operation
                    outbox.save('operations', operation_id, operation, 'failed')
                    report['errors'].append({'key': eid, 'code': code,
                                             'retry_after': getattr(error, 'retry_after', None)})
                    return report
            if queued:
                verify_approvals(plan, store, target, material_ids)
                for item in queued:
                    outbox.save('operations', item['operation_id'], item, 'inflight')
                try:
                    for item, result in remote.write_many(queued):
                        outbox.save('receipts', item['entity_key'], result)
                        outbox.save('operations', item['operation_id'], item, 'success')
                        report['writes'] += 1
                        report['notion_sent'] = remote.mode == 'notion-mcp'
                except (DeliveryError, OSError) as error:
                    code = error.code if isinstance(error, DeliveryError) else 'DELIVERY_IO_ERROR'
                    report['errors'].append({'code': code, 'phase': phase})
                    return report
            report['phase_seconds'][phase] = round(time.monotonic()-phase_started, 3)
        return report
    finally:
        report['elapsed_seconds'] = round(time.monotonic()-started, 3)
        if hasattr(remote, 'metrics'):
            report['transport_metrics'] = remote.metrics
        lock.unlink(missing_ok=True)
