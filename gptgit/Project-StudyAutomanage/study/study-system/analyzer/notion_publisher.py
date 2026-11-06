"""Local approvals are authoritative; normal publication trusts tool receipts.

Schema/property conversion stays in NotionMCP. Bodies are fetched only for
unknown, remotely changed, or interrupted items. A tool receipt is deliberately
distinguished from a fetched/verified remote snapshot.
"""
import copy
import time

from .cache import digest
from .notion_mcp import NotionMCP, canonical_body, content_for, inline_value, page_id
from .notion_sync import DeliveryError
from .core import AnalysisError


def publish_staged(plan, store, remote, directory, *, target, material_ids=None, retry=False,
                   recover_interrupted=False):
    """Allocate identities, then submit each page's complete logical document."""
    from .notion_reader import refresh_reader_target
    from .notion_sync import deliver_plan, make_plan
    if plan.get('publication_mode') == 'materials':
        # Inline material bodies have no dependencies on newly allocated IDs.
        # Create each new page with its final content in one request.
        report = deliver_plan(plan, store, remote, directory, retry=retry, target=target,
                              material_ids=material_ids, phases=('complete',),
                              recover_interrupted=recover_interrupted)
        report['publication_sequence'] = 'complete-only'
        if not report['errors']:
            if any(op['state'] != 'success' for op in remote.outbox.records('operations').values()):
                report['errors'].append({'code': 'UNRESOLVED_OPERATIONS'})
            else:
                try:
                    target = refresh_reader_target(target, directory)
                except (AnalysisError, DeliveryError, OSError) as error:
                    report['errors'].append({'code': getattr(error, 'code', 'DELIVERY_IO_ERROR'),
                                             'phase': 'reader-links'})
        return plan, target, remote, report
    allocation = deliver_plan(plan, store, remote, directory, retry=retry, target=target,
                              material_ids=material_ids, phases=('allocate',),
                              recover_interrupted=recover_interrupted)
    if allocation['errors']:
        return plan, target, remote, allocation
    allocation = copy.deepcopy(allocation)
    final_started = time.monotonic()
    final_remote = None
    try:
        target = refresh_reader_target(target, directory)
        plan = make_plan(store, target=target, material_ids=material_ids)
        final_remote = NotionPublisher(target, directory, call=remote.call, call_many=remote.call_many)
        final_remote.reuse_inventory(remote, allow_pending=retry)
        report = deliver_plan(plan, store, final_remote, directory, retry=retry, target=target,
                              material_ids=material_ids, phases=('complete',))
    except (AnalysisError, DeliveryError, OSError) as error:
        report = {'mode': remote.mode, 'notion_sent': allocation['notion_sent'],
                  'writes': 0, 'skipped': 0, 'reconciled': 0, 'phase_seconds': {},
                  'errors': [{'code': getattr(error, 'code', 'DELIVERY_IO_ERROR'), 'phase': 'complete'}],
                  'elapsed_seconds': round(time.monotonic()-final_started, 3),
                  'transport_metrics': copy.deepcopy(final_remote.metrics) if final_remote else {}}
        final_remote = final_remote or remote
    report['initial_pass'] = allocation
    report['publication_sequence'] = 'allocate-then-complete'
    if not report['errors'] and any(op['state'] != 'success'
                                   for op in final_remote.outbox.records('operations').values()):
        report['errors'].append({'code': 'UNRESOLVED_OPERATIONS'})
    return plan, target, final_remote, report


def require_ack(result, pid):
    if (not isinstance(result, dict) or result.get('async_task') or result.get('error')
            or result.get('success') is False):
        raise DeliveryError('NOTION_WRITE_UNCERTAIN')
    returned = result.get('page_id') or result.get('id')
    if returned:
        if page_id(returned) != pid:
            raise DeliveryError('NOTION_WRITE_UNCERTAIN')
    elif result.get('success') is not True:
        raise DeliveryError('NOTION_WRITE_UNCERTAIN')


class NotionPublisher(NotionMCP):
    local_source = True

    def reuse_inventory(self, previous, *, allow_pending=False):
        """ID-link finalization in the same successful publication only."""
        if (self.identity != previous.identity
                or self.target['collections'] != previous.target['collections']):
            raise DeliveryError('PUBLISH_DESTINATION_MISMATCH')
        if not allow_pending and any(op['state'] != 'success' for op in previous.outbox.records('operations').values()):
            raise DeliveryError('EXPLICIT_RETRY_REQUIRED')
        self.index = copy.deepcopy(previous.index)
        self.cache = copy.deepcopy(previous.cache)
        self.trusted = copy.deepcopy(previous.trusted)

    def prepare_plan(self, plan):
        super().prepare_plan(plan)
        self.metrics['publication_policy'] = 'local-source'
        self.metrics['acknowledged_pages'] = 0
        if self.local_pending and not getattr(self, 'retry_requested', False):
            raise DeliveryError('EXPLICIT_RETRY_REQUIRED')
        # Independent collection listings share one bridge exchange. Pagination
        # and exceptional body reads are still handled by inventory per kind.
        kinds = sorted({e['kind'] for e in plan['entities']} - self.index.keys())
        requests = [{'tool': 'query_data_sources', 'args': {'data': {
            'mode': 'view', 'view_url': self.target['collections'][kind]['view_url'], 'page_size': 100}}}
            for kind in kinds]
        results = self.calls(requests) if requests else []
        if len(results) != len(kinds):
            raise DeliveryError('NOTION_INVENTORY_ERROR')
        self.inventory_seeds = dict(zip(kinds, results))

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
            seed = getattr(self, 'inventory_seeds', {}).pop(kind, None) if not cursor else None
            result = seed if seed is not None else self.one('query_data_sources', {'data': args})
            if not isinstance(result.get('results'), list):
                raise DeliveryError('NOTION_INVENTORY_ERROR')
            for row in result['results']:
                if not isinstance(row, dict) or not (row.get('url') or row.get('id')):
                    raise DeliveryError('NOTION_INVENTORY_ERROR')
                eid = inline_value(row.get(binding['property_mapping']['sync_key']) or '')
                if not eid:
                    continue  # Unmanaged rows are never published or overwritten.
                pid = page_id(row.get('url') or row['id'])
                self.index[kind].setdefault(eid, []).append(pid)
                receipt = self.local_receipts.get(eid)
                revision_name = binding.get('revision_property')
                revision = row.get(revision_name)
                native = (revision_name and binding['observed_properties'].get(revision_name) == 'last_edited_time'
                          and isinstance(revision, str) and bool(revision))
                same_managed = (receipt and page_id(receipt['id']) == pid
                                and inline_value(row.get(binding['system_properties']['digest']) or '') == digest(receipt['document'])
                                and inline_value(row.get(binding['system_properties']['operation']) or '') == receipt['operation_id'])
                # Write responses do not supply a native modification time.
                # The next inventory establishes that baseline, without claiming
                # to have read the body or detected edits before that baseline.
                first_observation = (receipt and receipt.get('confirmation') == 'write-response'
                                     and not receipt.get('remote_revision'))
                if (same_managed and native and eid not in self.local_pending
                        and (receipt.get('remote_revision') == revision or first_observation)):
                    trusted = copy.deepcopy(receipt)
                    trusted['remote_revision'] = revision
                    self.trusted[pid] = trusted
                    if first_observation:
                        self.outbox.save('receipts', eid, trusted)
                    self.metrics['revision_reused_pages'] += 1
                    if eid in self.local_changed:
                        self.metrics['changed_revision_reused_pages'] += 1
                else:
                    self.cache[pid] = self.fetch(pid)
            if not result.get('has_more'):
                break
            next_cursor = result.get('next_cursor')
            if not next_cursor or next_cursor == cursor:
                raise DeliveryError('NOTION_INCOMPLETE_READ')
            cursor = next_cursor

    def canonical(self, eid, raw):
        receipt = self.outbox.read('receipts', eid)
        binding = self.target['collections'][eid.split(':', 1)[0]]
        if receipt and receipt['id'] == raw['id'] and receipt.get('confirmation') == 'write-response':
            same_props = (inline_value(raw['properties'].get(binding['system_properties']['operation']) or '') == receipt['operation_id']
                          and inline_value(raw['properties'].get(binding['system_properties']['digest']) or '') == digest(receipt['document'])
                          and self.properties_match(raw, receipt['document']))
            if same_props and canonical_body(raw['body']) == canonical_body(content_for(receipt['document'])):
                result = copy.deepcopy(receipt)
                result['remote_revision'] = raw.get('remote_revision')
                self.outbox.save('receipts', eid, result)
                return result
        # Recover a successful body write followed by an interrupted property
        # write. This is an exception-only read, with the exact desired body and
        # previous properties checked before adopting the checkpoint.
        if receipt and receipt['id'] == raw['id']:
            for opid, pending in self.outbox.pending(eid):
                if (getattr(self, 'retry_requested', False)
                        and pending['desired']['body'] != receipt['document']['body']
                        and canonical_body(raw['body']) == canonical_body(content_for(pending['desired']))
                        and self.properties_match(raw, receipt['document'])
                        and inline_value(raw['properties'].get(binding['system_properties']['digest']) or '') == digest(receipt['document'])
                        and inline_value(raw['properties'].get(binding['system_properties']['operation']) or '') == receipt['operation_id']):
                    pending['body_stage_stamp'] = raw['stamp']
                    self.outbox.save('operations', opid, pending, pending['state'])
                    return copy.deepcopy(receipt)
        return super().canonical(eid, raw)

    def acknowledged(self, item, pid):
        result = {'id': pid, 'document': copy.deepcopy(item['desired']),
                  'stamp': digest(['write-response', pid, item['operation_id'], item['desired']]),
                  'operation_id': item['operation_id'], 'remote_revision': None,
                  'confirmation': 'write-response'}
        self.cache.pop(pid, None)
        self.trusted[pid] = copy.deepcopy(result)
        self.metrics['acknowledged_pages'] += 1
        return result

    def write_many(self, items):
        groups, updates = {}, []
        for item in items:
            if item['before_stamp'] is None:
                groups.setdefault(item['desired']['kind'], []).append(item)
            else:
                updates.append(item)
        creations = []
        for kind, group in groups.items():
            binding = self.target['collections'][kind]
            for start in range(0, len(group), 20):
                chunk = group[start:start+20]
                pages = []
                for item in chunk:
                    props = self.projected_properties(item['desired'], encode=True)
                    props[binding['system_properties']['digest']] = digest(item['desired'])
                    props[binding['system_properties']['operation']] = item['operation_id']
                    pages.append({'properties': props, 'content': content_for(item['desired'])})
                self.metrics['batch_creates'] += 1
                creations.append((kind, chunk, {'tool': 'notion_create_pages', 'args': {'allow_async': False,
                    'parent': {'data_source_id': binding['data_source_id']}, 'pages': pages}}))
        if creations:
            responses = self.calls([request for _, _, request in creations])
            if len(responses) != len(creations):
                raise DeliveryError('NOTION_CREATE_UNCERTAIN')
            for (kind, chunk, _), response in zip(creations, responses):
                binding = self.target['collections'][kind]
                created = response.get('pages', [])
                if response.get('async_task') or len(created) != len(chunk):
                    raise DeliveryError('NOTION_CREATE_UNCERTAIN')
                expected = {item['entity_key']: item for item in chunk}
                matched, seen_ids = {}, set()
                for page in created:
                    pid = page_id(page.get('id') or page.get('url'))
                    props = page.get('properties', {})
                    eid = inline_value(props.get(binding['property_mapping']['sync_key']) or '')
                    if eid not in expected or eid in matched or pid in seen_ids:
                        raise DeliveryError('NOTION_CREATE_UNCERTAIN')
                    matched[eid] = pid
                    seen_ids.add(pid)
                for eid, pid in matched.items():
                    self.index[kind].setdefault(eid, []).append(pid)
                    yield expected[eid], self.acknowledged(expected[eid], pid)
        bodies, properties = [], []
        for item in updates:
            previous = self.lookup(item['entity_key'])
            if len(previous) != 1 or previous[0]['stamp'] != item['before_stamp']:
                raise DeliveryError('REMOTE_CONFLICT')
            pid = previous[0]['id']
            pending = self.outbox.read('operations', item['operation_id']) or {}
            raw = self.cache.get(pid)
            body_applied = raw and pending.get('body_stage_stamp') == raw['stamp']
            if previous[0]['document']['body'] != item['desired']['body'] and not body_applied:
                bodies.append((item, pid))
            binding = self.target['collections'][item['desired']['kind']]
            props = self.projected_properties(item['desired'], encode=True)
            props[binding['system_properties']['digest']] = digest(item['desired'])
            props[binding['system_properties']['operation']] = item['operation_id']
            old = self.projected_properties(previous[0]['document'], encode=True)
            properties.append((item, pid, self.changed_properties({'properties': old}, props)))
        if bodies:
            results = self.calls([{'tool': 'notion_update_page', 'args': {'page_id': pid,
                'command': 'replace_content', 'new_str': content_for(item['desired']), 'allow_async': False}}
                for item, pid in bodies])
            if len(results) != len(bodies):
                raise DeliveryError('NOTION_WRITE_UNCERTAIN')
            for (item, pid), result in zip(bodies, results):
                require_ack(result, pid)
                pending = self.outbox.read('operations', item['operation_id']) or {}
                pending['body_acknowledged'] = True
                self.outbox.save('operations', item['operation_id'], pending, 'inflight')
        if properties:
            results = self.calls([{'tool': 'notion_update_page', 'args': {'page_id': pid,
                'command': 'update_properties', 'properties': props, 'allow_async': False}}
                for _, pid, props in properties])
            if len(results) != len(properties):
                raise DeliveryError('NOTION_WRITE_UNCERTAIN')
            for (item, pid, _), result in zip(properties, results):
                require_ack(result, pid)
                yield item, self.acknowledged(item, pid)

