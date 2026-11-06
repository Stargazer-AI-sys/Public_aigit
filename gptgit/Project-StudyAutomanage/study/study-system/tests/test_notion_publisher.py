import copy
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

from analyzer.notion_publisher import NotionPublisher
from analyzer.notion_reader import refresh_reader_target
from analyzer.notion_sync import DeliveryError, deliver_plan, make_plan
import test_notion_delta as delta
from test_organizer import material


class PublicationPlugin(delta.RevisionPlugin):
    def __call__(self, tool, args):
        result = super().__call__(tool, args)
        if tool == 'notion_create_pages':
            # Actual saved MCP responses include properties. Reverse order to
            # prove IDs are associated by sync key, never by response position.
            for page in result['pages']:
                page['properties'] = copy.deepcopy(self.pages[page['id']]['properties'])
            result['pages'].reverse()
        return result


class LocalPublicationTests(unittest.TestCase):
    setUp = delta.DeltaPublicationTests.setUp

    def send(self, retry=False, previous=None):
        remote = NotionPublisher(self.target, self.directory, self.plugin)
        if previous:
            remote.reuse_inventory(previous)
        plan = make_plan(self.store, target=self.target)
        report = deliver_plan(plan, self.store, remote, self.directory,
                              target=self.target, retry=retry)
        self.remote = remote
        return report

    def seed(self):
        self.plugin = PublicationPlugin(self.target)
        report = self.send()
        self.assertFalse(report['errors'])
        self.assertEqual(report['transport_metrics']['body_read_pages'], 0)

    def revise(self):
        r = self.store.revise(self.record['id'], self.record['snapshot'],
                              [{'path': '/summary', 'value': '로컬에서 검토하고 승인한 변경 요약이다.'}])
        self.store.decide(r['id'], r['snapshot'], 'approve')

    def test_create_and_repeat_use_only_lists_without_body_reads(self):
        self.seed()
        approvals = self.store.path.read_bytes()
        before = self.plugin.writes
        report = self.send()
        self.assertFalse(report['errors'])
        self.assertEqual(report['transport_metrics']['tool_calls'], {'query_data_sources': 4})
        self.assertEqual(report['writes'], 0)
        self.assertEqual(before, self.plugin.writes)
        self.assertEqual(self.store.path.read_bytes(), approvals)
        receipts = self.remote.outbox.records('receipts')
        self.assertTrue(all(r['confirmation'] == 'write-response' for r in receipts.values()))
        self.assertTrue(all(r['remote_revision'] for r in receipts.values()))

    def test_local_change_has_no_body_reads_and_updates_same_ids(self):
        self.seed()
        self.send()  # Establish native revisions from the next list observation.
        ids = set(self.plugin.pages)
        self.revise()
        report = self.send()
        self.assertFalse(report['errors'])
        self.assertEqual(report['transport_metrics']['body_read_pages'], 0)
        self.assertEqual(report['writes'], 1)
        self.assertEqual(ids, set(self.plugin.pages))
        self.assertEqual(self.send()['writes'], 0)

    def test_new_reader_material_finalization_reuses_four_lists_and_preserves_approvals(self):
        self.plugin = PublicationPlugin(self.target)
        self.target['reader'] = {'version': 1, 'pages': {}, 'indexes': {}}
        self.assertFalse(self.send()['errors'])
        previous = self.remote
        self.target = refresh_reader_target(self.target, self.directory)
        self.assertFalse(self.send(previous=previous)['errors'])
        old = {p['properties']['sync_key']: pid for pid, p in self.plugin.pages.items()}
        data, analysis = material('second.txt', 'second source')
        r = self.store.ingest(analysis, data)
        self.store.decide(r['id'], r['snapshot'], 'approve')
        approvals = self.store.path.read_bytes()
        first = self.send()
        previous = self.remote
        self.target = refresh_reader_target(self.target, self.directory)
        final = self.send(previous=previous)
        self.assertFalse(first['errors'] or final['errors'])
        self.assertEqual(first['transport_metrics']['tool_calls']['query_data_sources'], 4)
        self.assertNotIn('query_data_sources', final['transport_metrics']['tool_calls'])
        self.assertEqual(first['transport_metrics']['body_read_pages'] + final['transport_metrics']['body_read_pages'], 0)
        ids = {p['properties']['sync_key']: pid for pid, p in self.plugin.pages.items()}
        self.assertEqual({k: ids[k] for k in old}, old)
        self.assertEqual(len(ids), len(self.plugin.pages))
        self.assertEqual(self.store.path.read_bytes(), approvals)
        self.assertEqual(self.send()['transport_metrics']['tool_calls'], {'query_data_sources': 4})

    def test_changed_native_revision_reads_only_exception_and_preserves_manual_body(self):
        self.seed()
        self.send()
        pid = next(iter(self.plugin.pages))
        self.plugin.pages[pid]['body'] += '\nmanual change'
        self.plugin.touch(pid)
        before = self.plugin.writes
        report = self.send()
        self.assertEqual(report['errors'][0]['code'], 'REMOTE_CONFLICT')
        self.assertEqual(report['transport_metrics']['body_read_pages'], 1)
        self.assertEqual(self.plugin.writes, before)

    def test_missing_revision_is_an_exception_not_evidence_of_no_change(self):
        self.seed()
        pid = next(iter(self.plugin.pages))
        self.plugin.pages[pid]['properties'].pop('native_revision')
        report = self.send()
        self.assertFalse(report['errors'])
        self.assertEqual(report['transport_metrics']['body_read_pages'], 1)
        self.assertEqual(report['writes'], 0)

    def test_old_verified_receipts_are_reused_without_migration_writes(self):
        self.plugin = PublicationPlugin(self.target)
        self.assertFalse(delta.DeltaPublicationTests.send(self)['errors'])
        before = self.plugin.writes
        report = self.send()
        self.assertFalse(report['errors'])
        self.assertEqual(report['transport_metrics']['tool_calls'], {'query_data_sources': 4})
        self.assertEqual(self.plugin.writes, before)

    def test_lost_create_response_requires_retry_and_does_not_duplicate(self):
        original = PublicationPlugin(self.target)
        def lose(tool, args):
            result = original(tool, args)
            if tool == 'notion_create_pages':
                raise DeliveryError('RESPONSE_LOST')
            return result
        self.plugin = lose
        self.assertEqual(self.send()['errors'][0]['code'], 'RESPONSE_LOST')
        self.plugin = original
        self.assertEqual(self.send()['errors'][0]['code'], 'EXPLICIT_RETRY_REQUIRED')
        self.assertFalse(self.send(retry=True)['errors'])
        keys = [p['properties']['sync_key'] for p in original.pages.values()]
        self.assertEqual(len(keys), len(set(keys)))

    def interrupt_properties(self, committed=False):
        self.seed()
        self.revise()
        original = self.plugin
        def fail(tool, args):
            if tool == 'notion_update_page' and args['command'] == 'update_properties':
                if committed:
                    original(tool, args)
                raise DeliveryError('RESPONSE_LOST')
            return original(tool, args)
        self.plugin = fail
        self.assertEqual(self.send()['errors'][0]['code'], 'RESPONSE_LOST')
        self.plugin = original
        self.assertEqual(self.send()['errors'][0]['code'], 'EXPLICIT_RETRY_REQUIRED')
        original.details.clear()
        return original

    def test_body_success_then_property_failure_recovers_without_body_rewrite(self):
        plugin = self.interrupt_properties()
        report = self.send(retry=True)
        self.assertFalse(report['errors'])
        self.assertEqual(report['transport_metrics']['body_read_pages'], 1)
        self.assertFalse(any(t == 'notion_update_page' and a['command'] == 'replace_content'
                             for t, a in plugin.details))

    def test_lost_property_success_is_reconciled_without_rewriting(self):
        plugin = self.interrupt_properties(committed=True)
        before = plugin.writes
        report = self.send(retry=True)
        self.assertFalse(report['errors'])
        self.assertGreater(report['reconciled'], 0)
        self.assertEqual(plugin.writes, before)

    def test_manual_edit_after_interruption_is_preserved(self):
        plugin = self.interrupt_properties()
        pid = next(pid for pid, p in plugin.pages.items()
                   if p['source'] == self.target['collections']['material']['data_source_id'])
        plugin.pages[pid]['body'] += '\nmanual edit'
        plugin.touch(pid)
        before = plugin.writes
        self.assertEqual(self.send(retry=True)['errors'][0]['code'], 'REMOTE_CONFLICT')
        self.assertEqual(plugin.writes, before)

    def test_deleted_and_duplicate_entries_block_publication(self):
        self.seed()
        pid = next(iter(self.plugin.pages))
        page = self.plugin.pages.pop(pid)
        self.assertEqual(self.send()['errors'][0]['code'], 'REMOTE_MISSING')
        self.plugin.pages[pid] = page
        self.plugin.pages['f'*32] = copy.deepcopy(page)
        self.assertEqual(self.send()['errors'][0]['code'], 'REMOTE_DUPLICATE')

    def test_create_without_response_identity_is_not_accepted_as_success(self):
        original = PublicationPlugin(self.target)
        def no_identity(tool, args):
            result = original(tool, args)
            if tool == 'notion_create_pages':
                for page in result['pages']:
                    page.pop('properties')
            return result
        self.plugin = no_identity
        self.assertEqual(self.send()['errors'][0]['code'], 'NOTION_CREATE_UNCERTAIN')
        self.plugin = original
        self.assertFalse(self.send(retry=True)['errors'])

    def test_lost_body_response_recovers_exact_applied_body_without_resending(self):
        self.seed()
        self.revise()
        original = self.plugin
        def lose(tool, args):
            result = original(tool, args)
            if tool == 'notion_update_page' and args['command'] == 'replace_content':
                raise DeliveryError('RESPONSE_LOST')
            return result
        self.plugin = lose
        self.assertEqual(self.send()['errors'][0]['code'], 'RESPONSE_LOST')
        self.plugin = original
        original.details.clear()
        self.assertFalse(self.send(retry=True)['errors'])
        self.assertFalse(any(t == 'notion_update_page' and a['command'] == 'replace_content'
                             for t, a in original.details))

    def test_paginated_lists_include_all_entries_without_body_reads(self):
        self.seed()
        original = self.plugin
        def paginated(tool, args):
            result = original(tool, args)
            if tool == 'query_data_sources' and len(result['results']) > 1:
                if args['data'].get('start_cursor'):
                    return {'results': result['results'][1:], 'has_more': False}
                return {'results': result['results'][:1], 'has_more': True, 'next_cursor': 'next'}
            return result
        self.plugin = paginated
        report = self.send()
        self.assertFalse(report['errors'])
        self.assertGreater(report['transport_metrics']['tool_calls']['query_data_sources'], 4)
        self.assertEqual(report['transport_metrics']['body_read_pages'], 0)

    def test_negative_or_async_ack_leaves_pending_work(self):
        for response in ({'success': False}, {'async_task': {'id': 'pending'}}, {}):
            original = PublicationPlugin(self.target)
            def bad(tool, args):
                result = original(tool, args)
                if tool == 'notion_update_page':
                    return response
                return result
            # Separate outboxes for each uncertain-response scenario.
            self.directory = self.root/str(len(list(self.root.iterdir())))
            self.plugin = bad
            report = self.send()
            self.assertEqual(report['errors'][0]['code'], 'NOTION_WRITE_UNCERTAIN')
            self.assertTrue(any(op['state'] != 'success' for op in self.remote.outbox.records('operations').values()))

    def test_cli_uses_local_source_through_real_file_bridge(self):
        self.target['material_database']['name'] = 'Mock study library'
        plugin = PublicationPlugin(self.target)
        target = self.root/'target.json'
        target.write_text(json.dumps(self.target), encoding='utf-8')
        output = self.root/'cli'
        output.mkdir()
        project = Path(__file__).resolve().parents[1]
        env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(project/'.test-deps'), str(project)]))
        approvals = self.store.path.read_bytes()
        process = subprocess.Popen([sys.executable, '-B', '-X', 'utf8', '-m', 'analyzer.notion_mcp',
            '--workspace', str(self.store.path.parent), '--target', str(target),
            '--output-dir', str(output), '--material-id', self.record['id'], '--allow-notion-write'],
            cwd=project, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        try:
            seen = set()
            deadline = time.monotonic()+30
            while process.poll() is None and time.monotonic() < deadline:
                request = output/'bridge/request.json'
                if request.is_file():
                    try:
                        data = json.loads(request.read_text(encoding='utf-8'))
                    except (FileNotFoundError, PermissionError):
                        # Windows may temporarily deny an open during the
                        # worker's atomic request-file replacement.
                        time.sleep(0.01)
                        continue
                    rid = data['request_id']
                    if rid not in seen:
                        results = [{'structuredContent': plugin(r['tool'], r['args'])} for r in data['requests']]
                        response = output/'bridge'/f'{rid}.json'
                        temp = response.with_suffix('.tmp')
                        temp.write_text(json.dumps({'request_id': rid, 'results': results}), encoding='utf-8')
                        temp.replace(response)
                        seen.add(rid)
                time.sleep(0.01)
            self.assertIsNotNone(process.poll(), 'CLI did not complete the file bridge')
            stdout, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, stderr+stdout)
            reports = list((output/'runs').glob('*/report.json'))
            self.assertEqual(len(reports), 1)
            report = json.loads(reports[0].read_text(encoding='utf-8'))
            self.assertEqual(report['transport_metrics']['publication_policy'], 'local-source')
            self.assertEqual(report['transport_metrics']['body_read_pages'], 0)
            self.assertTrue(report['approval_db_unchanged'])
            self.assertEqual(self.store.path.read_bytes(), approvals)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()

    def test_offline_audit_supports_ack_receipts_and_still_detects_body_edits(self):
        from tools.notion_bridge.verify import audit
        self.seed()
        target = self.root/'target.json'
        target.write_text(json.dumps(self.target), encoding='utf-8')
        readback = self.root/'snapshot.json'
        def save():
            rows = [{'structuredContent': self.plugin('fetch', {'id': pid})} for pid in self.plugin.pages]
            readback.write_text(json.dumps(rows), encoding='utf-8')
        save()
        before = (self.directory/'delivery.sqlite3').read_bytes()
        report = audit(target, self.directory, readback)
        self.assertTrue(report['ok'], report)
        self.assertEqual(report['physical_stamp_checked_entities'], 0)
        self.assertEqual((self.directory/'delivery.sqlite3').read_bytes(), before)
        next(iter(self.plugin.pages.values()))['body'] += '\nmanual edit'
        save()
        report = audit(target, self.directory, readback)
        self.assertIn('BODY_MISMATCH', {e['code'] for e in report['errors']})


if __name__ == '__main__':
    unittest.main()
