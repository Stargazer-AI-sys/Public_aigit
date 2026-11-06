"""Credential-free UTF-8 file bridge to the connected Notion plugin.

Run only with an authorized dispatcher. The process emits a tool request and
waits for the dispatcher to return its result; it has no network client/token.
"""
import argparse
import copy
import json
import re
import sys
import os
import time
from pathlib import Path
from uuid import uuid4

from .cache import digest
from .core import AnalysisError, strict_json
from .notion_sync import DeliveryError, Outbox, make_plan, mapping_for, preview
from .workspace import Workspace


ALLOWED = {'fetch', 'query_data_sources', 'notion_create_pages', 'notion_update_page'}
BRIDGE_DIRECTORY = None
BRIDGE_PACKAGE = None


def bridge_preflight():
    if BRIDGE_PACKAGE is None:
        return {}
    return {'preflight': {'package': str(Path(BRIDGE_PACKAGE).resolve()),
                         'python': sys.executable, 'root': str(Path(__file__).resolve().parents[1]),
                         'python_path': os.environ.get('PYTHONPATH', '')}}


def rpc_many(requests):
    """One file exchange for independent calls; dispatcher preserves result order."""
    if any(r['tool'] not in ALLOWED for r in requests):
        raise DeliveryError('NOTION_TOOL_DENIED')
    if BRIDGE_DIRECTORY is None:
        raise DeliveryError('NOTION_DISPATCHER_REQUIRED')
    directory = Path(BRIDGE_DIRECTORY)
    directory.mkdir(parents=True, exist_ok=True)
    request_id = uuid4().hex
    temporary = directory/'request.tmp'
    temporary.write_text(json.dumps({'request_id': request_id, 'requests': requests, **bridge_preflight()}, ensure_ascii=False), encoding='utf-8')
    temporary.replace(directory/'request.json')
    response = directory/(request_id+'.json')
    print('NOTION_RPC '+request_id, flush=True)
    deadline = time.monotonic()+max(180, len(requests)*15)
    while not response.exists():
        if time.monotonic() > deadline:
            raise DeliveryError('NOTION_DISPATCHER_TIMEOUT')
        time.sleep(0.1)
    result = strict_json(response.read_text(encoding='utf-8-sig'))
    if result['request_id'] != request_id or len(result.get('results', [])) != len(requests):
        raise DeliveryError('NOTION_DISPATCHER_MISMATCH')
    return [unpack(value) for value in result['results']]


def unpack(result):
    if result.get('isError'):
        raise DeliveryError('NOTION_TOOL_ERROR')
    if result.get('structuredContent') is not None:
        return result['structuredContent']
    for item in result.get('content', []):
        if item.get('type') == 'text':
            try:
                return json.loads(item['text'])
            except ValueError:
                return {'text': item['text']}
    return result


def rpc(tool, args):
    if tool not in ALLOWED:
        raise DeliveryError('NOTION_TOOL_DENIED')
    if BRIDGE_DIRECTORY is None:
        raise DeliveryError('NOTION_DISPATCHER_REQUIRED')
    # ConPTY repaint sequences can corrupt long JSON if stdout is parsed as a
    # transcript. Exchange exact UTF-8 files instead; stdout carries only IDs.
    directory = Path(BRIDGE_DIRECTORY)
    directory.mkdir(parents=True, exist_ok=True)
    request_id = uuid4().hex
    temporary = directory/'request.tmp'
    temporary.write_text(json.dumps({'request_id': request_id, 'rpc': tool, 'args': args, **bridge_preflight()}, ensure_ascii=False), encoding='utf-8')
    temporary.replace(directory/'request.json')
    response = directory/(request_id+'.json')
    print('NOTION_RPC '+request_id, flush=True)
    deadline = time.monotonic()+180
    while not response.exists():
        if time.monotonic() > deadline:
            raise DeliveryError('NOTION_DISPATCHER_TIMEOUT')
        time.sleep(0.1)
    result = strict_json(response.read_text(encoding='utf-8-sig'))
    if result['request_id'] != request_id:
        raise DeliveryError('NOTION_DISPATCHER_MISMATCH')
    return unpack(result['result'])


def page_id(value):
    text = str(value).split('?')[0].replace('-', '')
    match = re.search(r'([a-f0-9]{32})$', text, re.I)
    if not match:
        raise DeliveryError('NOTION_PAGE_ID_ERROR')
    return match[1].lower()


def content_for(document):
    body = document['body']
    # Notion renders the title separately. Do not repeat the material title.
    if document['kind'] == 'material' and body.startswith('# '):
        body = body.split('\n', 1)[1].lstrip('\n')
    return body


def canonical_body(body):
    return '\n'.join(line.rstrip() for line in body.splitlines() if line.strip())


def inline_text(value):
    # The plugin interprets title/rich-text values as inline Notion Markdown.
    # In particular an unescaped Windows path loses its backslashes on save.
    return re.sub(r'([\\*~`$\[\]<>{}|^])', r'\\\1', value)


def inline_value(value):
    return re.sub(r'\\([\\*~`$\[\]<>{}|^])', r'\1', value)


def check_scope(plan, directory):
    path = Path(directory)/'published_scope.json'
    material_keys = sorted(e['key'] for e in plan['entities'] if e['kind'] == 'material')
    if path.is_file():
        previous = strict_json(path.read_text(encoding='utf-8'))
        if not set(previous['material_keys']) <= set(material_keys):
            raise AnalysisError('PUBLISH_SCOPE_INCOMPLETE', '기존 게시 자료를 포함한 계획이 필요합니다. 공유 개념의 다른 원문 설명을 보존하세요.')
    return {'material_keys': material_keys}


class NotionMCP:
    mode = 'notion-mcp'

    def __init__(self, target, directory, call=rpc, call_many=None):
        if mapping_for(target)['binding_status'] != 'bound':
            raise DeliveryError('NOTION_TARGET_UNBOUND')
        self.target, self.call = target, call
        self.call_many = call_many or (rpc_many if call is rpc else
                                      lambda requests: [call(r['tool'], r['args']) for r in requests])
        self.metrics = {'tool_calls': {}, 'tool_seconds': {}, 'exchanges': 0, 'batch_creates': 0,
                        'request_json_bytes': 0, 'response_json_bytes': 0,
                        'local_changed_entities': 0, 'revision_reused_pages': 0,
                        'changed_revision_reused_pages': 0,
                        'body_read_pages': 0, 'revision_bootstrap_pages': 0}
        self.identity = 'notion-mcp:'+digest({k: v['data_source_id'] for k, v in target['collections'].items()})
        self.path = Path(directory).resolve()/'transport.marker'
        self.outbox = Outbox(directory, self.identity)
        self.index = {}
        self.cache = {}
        self.trusted = {}
        self.local_receipts = {}
        self.local_changed = set()
        self.local_pending = set()

    def prepare_plan(self, plan):
        """Determine local changes, including resolved shared relations, first."""
        self.local_receipts = self.outbox.records('receipts')
        self.local_pending = {op['entity_key'] for op in self.outbox.records('operations').values()
                              if op.get('state') != 'success'}
        self.local_changed = set()
        for entity in plan['entities']:
            eid = entity['key']
            receipt = self.local_receipts.get(eid)
            if not receipt:
                self.local_changed.add(eid)
                continue
            if (eid in plan.get('preserved_materials', []) and
                    receipt['document']['properties'].get('approval_snapshot') == entity['properties']['approval_snapshot']):
                continue
            relations = (copy.deepcopy(receipt['document']['relations'])
                         if plan.get('publication_mode') == 'materials' else {})
            unresolved = False
            for name, keys in entity['relations'].items():
                if any(key not in self.local_receipts for key in keys):
                    unresolved = True
                    break
                relations[name] = [self.local_receipts[key]['id'] for key in keys]
            desired = {'kind': entity['kind'], 'properties': entity['properties'],
                       'body': entity['body'], 'relations': relations}
            if unresolved or desired != receipt['document']:
                self.local_changed.add(eid)
        self.metrics['local_changed_entities'] = len(self.local_changed)

    def calls(self, requests):
        if any(r['tool'] in ('notion_create_pages', 'notion_update_page') for r in requests):
            guard = getattr(self, 'before_write', None)
            if guard:
                guard()
        started = time.monotonic()
        self.metrics['request_json_bytes'] += len(json.dumps(requests, ensure_ascii=False).encode('utf-8'))
        self.metrics['exchanges'] += 1
        for request in requests:
            name = request['tool']
            self.metrics['tool_calls'][name] = self.metrics['tool_calls'].get(name, 0)+1
        try:
            results = self.call_many(requests)
            self.metrics['response_json_bytes'] += len(json.dumps(results, ensure_ascii=False).encode('utf-8'))
            return results
        finally:
            label = '+'.join(sorted({r['tool'] for r in requests}))
            self.metrics['tool_seconds'][label] = self.metrics['tool_seconds'].get(label, 0)+time.monotonic()-started

    def one(self, tool, args):
        return self.calls([{'tool': tool, 'args': args}])[0]

    def fetch(self, url):
        return self.parse_page(url, self.calls([{'tool': 'fetch', 'args': {'id': url}}])[0])

    def parse_page(self, url, result):
        if result.get('truncated') or result.get('unknown_block_count') or result.get('unknown_block_ids'):
            raise DeliveryError('NOTION_INCOMPLETE_READ')
        text = result.get('text', '')
        properties = re.search(r'<properties>\s*([\s\S]*?)\s*</properties>', text)
        content = re.search(r'<content>\n?([\s\S]*?)\n?</content>', text)
        if not properties:
            raise DeliveryError('NOTION_PAGE_PARSE_ERROR')
        props = strict_json(properties[1])
        raw = {'id': page_id(result.get('id', url)), 'properties': props,
               'body': content[1] if content else '', 'url': result.get('url', url)}
        # Native revision is observation metadata, not a writable managed value.
        # Exclude it from the existing stamp so adding the read-only column does
        # not invalidate old receipts or cause a one-time content rewrite.
        revision_property = next((binding.get('revision_property') for binding in self.target['collections'].values()
                                  if binding.get('revision_property') in props), None)
        stamp_properties = {key: value for key, value in props.items() if key != revision_property}
        raw['remote_revision'] = props.get(revision_property) if revision_property else None
        raw['stamp'] = digest({'properties': stamp_properties, 'body': raw['body'],
                               'icon': result.get('icon'), 'cover': result.get('cover')})
        if hasattr(self, 'metrics'):
            self.metrics['body_read_pages'] += 1
        return raw

    def inventory(self, kind):
        if kind in self.index:
            return
        binding = self.target['collections'][kind]
        self.index[kind] = {}
        cursor = None
        while True:
            args = {'mode': 'view', 'view_url': binding['view_url'], 'page_size': 100}
            if cursor:
                args['start_cursor'] = cursor
            result = self.calls([{'tool': 'query_data_sources', 'args': {'data': args}}])[0]
            urls = []
            for row in result.get('results', []):
                if not isinstance(row, dict) or not (row.get('url') or row.get('id')):
                    raise DeliveryError('NOTION_INVENTORY_ERROR')
                url = row.get('url') or row['id']
                pid = page_id(url)
                sync_value = row.get(binding['property_mapping']['sync_key'])
                eid = inline_value(sync_value) if isinstance(sync_value, str) else ''
                receipt = self.local_receipts.get(eid)
                revision_property = binding.get('revision_property')
                revision = row.get(revision_property) if revision_property else None
                # A local change does not invalidate the observed remote state.
                # Reuse that state for planning; write_many/write still fetch the
                # current body before any update and compare the physical stamp.
                # Pending operations must keep the full recovery read instead.
                reusable = (receipt and eid not in self.local_pending
                            and revision_property and binding['observed_properties'].get(revision_property) == 'last_edited_time'
                            and isinstance(revision, str) and revision
                            and receipt.get('remote_revision') == revision
                            and page_id(receipt['id']) == pid
                            and row.get(binding['system_properties']['digest']) == digest(receipt['document'])
                            and row.get(binding['system_properties']['operation']) == receipt['operation_id'])
                if reusable:
                    self.index[kind].setdefault(eid, []).append(pid)
                    self.trusted[pid] = copy.deepcopy(receipt)
                    self.metrics['revision_reused_pages'] += 1
                    if eid in self.local_changed:
                        self.metrics['changed_revision_reused_pages'] += 1
                else:
                    urls.append(url)
                    if receipt and revision and not receipt.get('remote_revision'):
                        self.metrics['revision_bootstrap_pages'] += 1
            responses = self.calls([{'tool': 'fetch', 'args': {'id': url}} for url in urls]) if urls else []
            for url, response in zip(urls, responses):
                raw = self.parse_page(url, response)
                eid = raw['properties'].get(binding['property_mapping']['sync_key'])
                if eid:
                    self.index[kind].setdefault(eid, []).append(raw['id'])
                    self.cache[raw['id']] = raw
            if not result.get('has_more'):
                break
            cursor = result.get('next_cursor')
            if not cursor:
                raise DeliveryError('NOTION_INCOMPLETE_READ')

    def write_many(self, items):
        """Group new pages by destination; keep per-page durable checkpoints.

        Yield each result immediately so a later failure cannot lose its receipt.
        Existing-page updates retain the guarded single-page recovery path.
        """
        groups = {}
        updates = []
        for item in items:
            if item['before_stamp'] is None:
                groups.setdefault(item['desired']['kind'], []).append(item)
            else:
                updates.append(item)
        for kind, group in groups.items():
            binding = self.target['collections'][kind]
            for offset in range(0, len(group), 20):
                chunk = group[offset:offset+20]
                pages = []
                for item in chunk:
                    document = item['desired']
                    props = self.projected_properties(document, encode=True)
                    props[binding['system_properties']['digest']] = digest(document)
                    props[binding['system_properties']['operation']] = item['operation_id']
                    pages.append({'properties': props, 'content': content_for(document)})
                self.metrics['batch_creates'] += 1
                result = self.calls([{'tool': 'notion_create_pages', 'args': {
                    'allow_async': False, 'parent': {'data_source_id': binding['data_source_id']}, 'pages': pages}}])[0]
                created = result.get('pages', [])
                if len(created) != len(chunk):
                    raise DeliveryError('NOTION_CREATE_UNCERTAIN')
                ids = [page_id(p.get('id') or p.get('url')) for p in created]
                responses = self.calls([{'tool': 'fetch', 'args': {'id': pid}} for pid in ids])
                expected = {item['entity_key']: item for item in chunk}
                seen = set()
                for pid, response in zip(ids, responses):
                    raw = self.parse_page(pid, response)
                    eid = inline_value(raw['properties'].get(binding['property_mapping']['sync_key'], ''))
                    item = expected.get(eid)
                    if not item or eid in seen or not self.properties_match(raw, item['desired']):
                        raise DeliveryError('NOTION_READBACK_ERROR')
                    seen.add(eid)
                    self.index[kind].setdefault(eid, []).append(pid)
                    self.cache[pid] = raw
                    yield item, {'id': pid, 'document': copy.deepcopy(item['desired']),
                                 'stamp': raw['stamp'], 'operation_id': item['operation_id'],
                                 'remote_revision': raw.get('remote_revision')}
        if not updates:
            return
        # Guard all existing pages once, then submit independent updates together.
        ids = [self.lookup(item['entity_key'])[0]['id'] for item in updates]
        responses = self.calls([{'tool': 'fetch', 'args': {'id': pid}} for pid in ids])
        bodies = []
        observed = {}
        for item, pid, response in zip(updates, ids, responses):
            raw = self.parse_page(pid, response)
            observed[pid] = raw
            pending = self.outbox.read('operations', item['operation_id']) or {}
            body_applied = pending.get('body_stage_stamp') == raw['stamp']
            if raw['stamp'] != item['before_stamp'] and not body_applied:
                raise DeliveryError('REMOTE_CONFLICT')
            previous = self.lookup(item['entity_key'])[0]
            if previous['document'].get('body') != item['desired']['body'] and not body_applied:
                bodies.append((item, pid))
        if bodies:
            self.calls([{'tool': 'notion_update_page', 'args': {'page_id': pid,
                'command': 'replace_content', 'new_str': content_for(item['desired']),
                'allow_async': False}} for item, pid in bodies])
            staged = self.calls([{'tool': 'fetch', 'args': {'id': pid}} for _, pid in bodies])
            for (item, pid), response in zip(bodies, staged):
                pending = self.outbox.read('operations', item['operation_id']) or {}
                pending['body_stage_stamp'] = self.parse_page(pid, response)['stamp']
                self.outbox.save('operations', item['operation_id'], pending, 'inflight')
        requests = []
        for item, pid in zip(updates, ids):
            document = item['desired']
            binding = self.target['collections'][document['kind']]
            props = self.projected_properties(document, encode=True)
            props[binding['system_properties']['digest']] = digest(document)
            props[binding['system_properties']['operation']] = item['operation_id']
            props = self.changed_properties(observed[pid], props)
            requests.append({'tool': 'notion_update_page', 'args': {'page_id': pid,
                'command': 'update_properties', 'properties': props, 'allow_async': False}})
        self.calls(requests)
        responses = self.calls([{'tool': 'fetch', 'args': {'id': pid}} for pid in ids])
        for item, pid, response in zip(updates, ids, responses):
            raw = self.parse_page(pid, response)
            if not self.properties_match(raw, item['desired']):
                raise DeliveryError('NOTION_READBACK_ERROR')
            self.cache[pid] = raw
            yield item, {'id': pid, 'document': copy.deepcopy(item['desired']), 'stamp': raw['stamp'],
                         'operation_id': item['operation_id'], 'remote_revision': raw.get('remote_revision')}

    def canonical(self, eid, raw):
        binding = self.target['collections'][eid.split(':', 1)[0]]
        opid = raw['properties'].get(binding['system_properties']['operation'], '')
        managed_digest = raw['properties'].get(binding['system_properties']['digest'])
        receipt = self.outbox.read('receipts', eid)
        if receipt:
            for _, pending in self.outbox.pending(eid):
                if pending.get('body_stage_stamp') == raw['stamp']:
                    # The body write was durably observed, while the following
                    # property write failed. Expose the prior logical state so
                    # an explicit retry resumes that operation without rewriting
                    # the body. write() checks the observed physical stamp again.
                    return copy.deepcopy(receipt)
        if receipt and receipt['stamp'] == raw['stamp']:
            document = receipt['document']
        else:
            pending = self.outbox.read('operations', opid)
            # On an uncertain write, adopt only exact managed properties and
            # normalized content; otherwise require review, never create again.
            if (pending and pending['state'] != 'success' and pending['entity_key'] == eid
                    and managed_digest == digest(pending['desired'])
                    and canonical_body(raw['body']) == canonical_body(content_for(pending['desired']))
                    and self.properties_match(raw, pending['desired'])):
                document = pending['desired']
            else:
                document = {'kind': eid.split(':', 1)[0], 'properties': raw['properties'],
                            'body': raw['body'], 'relations': {}}
        result = {'id': raw['id'], 'document': document, 'stamp': raw['stamp'], 'operation_id': opid,
                  'remote_revision': raw.get('remote_revision')}
        if (receipt and receipt['stamp'] == raw['stamp'] and result['remote_revision']
                and receipt.get('remote_revision') != result['remote_revision']):
            # Bootstrap or harmless native timestamp change: the complete fetched
            # body and properties still match the receipt. Update local evidence.
            self.outbox.save('receipts', eid, result)
        return result

    def lookup(self, eid):
        kind = eid.split(':', 1)[0]
        self.inventory(kind)
        return [(self.canonical(eid, self.cache[pid]) if pid in self.cache else copy.deepcopy(self.trusted[pid]))
                for pid in self.index[kind].get(eid, [])]

    def resolve(self, eid):
        # Dependency IDs do not require repeated content fetches.
        return self.lookup(eid)

    def projected_properties(self, document, *, encode=False):
        binding = self.target['collections'][document['kind']]
        props = {binding['property_mapping'][k]: v for k, v in document['properties'].items()}
        if encode:
            props = {k: inline_text(v) if isinstance(v, str) else v for k, v in props.items()}
        props.update({binding['relation_mapping'][k]: values for k, values in document['relations'].items()})
        return props

    def properties_match(self, raw, document):
        for name, expected in self.projected_properties(document).items():
            actual = raw['properties'].get(name)
            if isinstance(expected, list):
                if isinstance(actual, str):
                    try:
                        actual = json.loads(actual)
                    except ValueError:
                        return False
                if sorted(page_id(v) for v in (actual or [])) != sorted(page_id(v) for v in expected):
                    return False
            elif inline_value(actual or '') != expected:
                return False
        return True

    @staticmethod
    def changed_properties(raw, properties):
        """Do not resend unchanged titles, identities or relation arrays."""
        changed = {}
        for name, expected in properties.items():
            actual = raw['properties'].get(name)
            if isinstance(expected, list):
                if isinstance(actual, str):
                    try:
                        actual = json.loads(actual)
                    except ValueError:
                        actual = []
                equal = sorted(page_id(v) for v in (actual or [])) == sorted(page_id(v) for v in expected)
            else:
                equal = inline_value(actual or '') == inline_value(expected) if isinstance(expected, str) else actual == expected
            if not equal:
                changed[name] = expected
        return changed

    def write(self, eid, document, expected_stamp, operation_id):
        """Compatibility adapter; share the tested batch/checkpoint path."""
        matches = self.lookup(eid)
        if len(matches) > 1:
            raise DeliveryError('REMOTE_DUPLICATE')
        if (matches[0]['stamp'] if matches else None) != expected_stamp:
            raise DeliveryError('REMOTE_CONFLICT')
        item = {'entity_key': eid, 'desired': document, 'before_stamp': expected_stamp,
                'operation_id': operation_id}
        return next(self.write_many([item]))[1]


def main():
    global BRIDGE_DIRECTORY
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument('--workspace', type=Path, default=root/'output/knowledge_base')
    parser.add_argument('--target', type=Path, default=root/'config/notion_target.json')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--material-id', action='append', required=True)
    parser.add_argument('--allow-notion-write', action='store_true', required=True)
    parser.add_argument('--retry', action='store_true')
    parser.add_argument('--publication-mode', choices=['full', 'materials'],
                        help='자료 중심 materials 또는 기존 full 게시')
    parser.add_argument('--recover-interrupted', action='store_true',
                        help='Confirm the previous publication worker has stopped before recovering its lock')
    args = parser.parse_args()
    BRIDGE_DIRECTORY = args.output_dir/'bridge'
    from .main import new_run, write_json
    store = Workspace(args.workspace, read_only=True)
    target_bytes = args.target.read_bytes()
    target = strict_json(target_bytes.decode('utf-8-sig'))
    from .notion_reader import refresh_reader_target
    target = refresh_reader_target(target, args.output_dir/'outbox')
    if args.publication_mode == 'materials':
        from .notion_sync import enable_material_publication
        target = enable_material_publication(target, args.output_dir/'outbox')
    elif args.publication_mode == 'full':
        target = copy.deepcopy(target)
        target['publication'] = {'mode': 'full'}
    plan = make_plan(store, target=target, material_ids=args.material_id)
    scope = check_scope(plan, args.output_dir)
    output = new_run(args.output_dir/'runs')
    write_json(output/'plan.json', plan)
    (output/'preview.md').write_text(preview(plan), encoding='utf-8')
    from .notion_publisher import NotionPublisher, publish_staged
    remote = NotionPublisher(target, args.output_dir/'outbox', call=rpc, call_many=rpc_many)
    before = store.path.read_bytes()
    report = {'mode': 'notion-mcp', 'errors': [], 'notion_sent': False}
    try:
        plan, target, remote, report = publish_staged(plan, store, remote, args.output_dir/'outbox',
            target=target, material_ids=args.material_id, retry=args.retry,
            recover_interrupted=args.recover_interrupted)
        write_json(output/'plan.json', plan)
        if not report['errors'] and target.get('reader') and args.target.read_bytes() == target_bytes:
            write_json(args.target, target)
        if not report['errors'] and target.get('reader'):
            from .notion_front import refresh_front
            remote.retry_requested = args.retry
            front_started = time.monotonic()
            report['entity_notion_sent'] = report['notion_sent']
            report['front_completion'] = 'incomplete'
            try:
                report['front_pages'] = refresh_front(plan, store, target, args.output_dir, remote)
                report['front_completion'] = 'complete'
            finally:
                report['phase_seconds']['front'] = round(time.monotonic() - front_started, 3)
                report['elapsed_seconds'] = round(report['elapsed_seconds'] + report['phase_seconds']['front'], 3)
            report['notion_sent'] = report['notion_sent'] or bool(report['front_pages']['writes'])
            report['errors'].extend(report['front_pages']['errors'])
    except (AnalysisError, DeliveryError) as error:
        # Keep earlier DB results/metrics if navigation refresh fails later.
        report['errors'].append({'code': error.code})
        if not report.get('notion_sent'):
            report['notion_sent'] = None
    report['approval_db_unchanged'] = before == store.path.read_bytes()
    report['total_elapsed_seconds'] = round(report.get('elapsed_seconds', 0)
                                           + report.get('initial_pass', {}).get('elapsed_seconds', 0), 3)
    if not report['errors']:
        write_json(args.output_dir/'published_scope.json', scope)
    report['result_path'] = str(output/'report.json')
    write_json(output/'report.json', report)
    print('NOTION_DONE '+json.dumps({'done': report}, ensure_ascii=False), flush=True)
    return int(bool(report['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
