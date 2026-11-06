import copy
import json
import tempfile
import unittest
from pathlib import Path

from analyzer.notion_mcp import NotionMCP
from analyzer.notion_sync import DeliveryError, deliver_plan, make_plan
from analyzer.workspace import Workspace
from test_notion_mcp import FakePlugin, binding
from test_organizer import material


class RevisionPlugin(FakePlugin):
    def __init__(self, target):
        super().__init__(target)
        self.clock = 0
        self.details = []

    def touch(self, pid):
        self.clock += 1
        self.pages[pid]['properties']['native_revision'] = f'2026-10-19T00:00:00.{self.clock:06d}Z'

    def __call__(self, tool, args):
        self.details.append((tool, copy.deepcopy(args)))
        if tool == 'query_data_sources':
            super().__call__(tool, args)
            source = next(b['data_source_id'] for b in self.target['collections'].values()
                          if b['view_url'] == args['data']['view_url'])
            return {'results': [dict(copy.deepcopy(p['properties']), id=pid, url=pid)
                                for pid, p in self.pages.items() if p['source'] == source], 'has_more': False}
        result = super().__call__(tool, args)
        if tool == 'notion_create_pages':
            for page in result['pages']:
                self.touch(page['id'])
        elif tool == 'notion_update_page':
            self.touch(args['page_id'])
        return result


class DeltaPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Workspace(self.root/'library')
        data, analysis = material()
        r = self.store.ingest(analysis, data)
        self.record = self.store.decide(r['id'], r['snapshot'], 'approve')
        self.target = binding()
        for b in self.target['collections'].values():
            b['revision_property'] = 'native_revision'
            b['observed_properties']['native_revision'] = 'last_edited_time'
        self.plugin = RevisionPlugin(self.target)
        self.directory = self.root/'outbox'

    def send(self, **kwargs):
        remote = NotionMCP(self.target, self.directory, self.plugin)
        plan = make_plan(self.store, target=self.target)
        return deliver_plan(plan, self.store, remote, self.directory, target=self.target, **kwargs)

    def test_unchanged_repeat_uses_metadata_only_and_records_payload_bytes(self):
        self.assertFalse(self.send()['errors'])
        before = self.plugin.writes
        report = self.send()
        self.assertFalse(report['errors'])
        metrics = report['transport_metrics']
        self.assertEqual(metrics['tool_calls'], {'query_data_sources': 4})
        self.assertEqual(metrics['local_changed_entities'], 0)
        self.assertEqual(metrics['revision_reused_pages'], len(self.plugin.pages))
        self.assertEqual(metrics['body_read_pages'], 0)
        self.assertGreater(metrics['response_json_bytes'], 0)
        self.assertEqual(self.plugin.writes, before)

    def test_local_material_change_does_not_read_unaffected_concepts_or_categories(self):
        self.send()
        r = self.store.revise(self.record['id'], self.record['snapshot'],
                              [{'path': '/summary', 'value': '승인한 변경 요약이다.'}])
        self.store.decide(r['id'], r['snapshot'], 'approve')
        self.plugin.details.clear()
        report = self.send()
        self.assertFalse(report['errors'])
        fetched = {args['id'] for tool, args in self.plugin.details if tool == 'fetch'}
        material_id = next(pid for pid, p in self.plugin.pages.items()
                           if p['source'] == self.target['collections']['material']['data_source_id'])
        self.assertEqual(fetched, {material_id})
        self.assertEqual(report['transport_metrics']['local_changed_entities'], 1)
        # Keep the pre-write guard, body-stage checkpoint and final readback;
        # the inventory must not fetch the same unchanged remote state first.
        self.assertEqual(report['transport_metrics']['body_read_pages'], 3)
        self.assertEqual(report['transport_metrics']['changed_revision_reused_pages'], 1)

    def test_reader_new_material_two_pass_read_budget_and_approval_preservation(self):
        from analyzer.notion_reader import refresh_reader_target
        self.target['reader'] = {'version': 1, 'pages': {}, 'indexes': {}}
        self.assertFalse(self.send()['errors'])
        self.target = refresh_reader_target(self.target, self.directory)
        self.assertFalse(self.send()['errors'])
        old_ids = {p['properties']['sync_key']: pid for pid, p in self.plugin.pages.items()}
        data, analysis = material('second.txt', 'second source')
        r = self.store.ingest(analysis, data)
        self.store.decide(r['id'], r['snapshot'], 'approve')
        approvals = self.store.path.read_bytes()
        first = self.send()
        self.assertFalse(first['errors'])
        self.target = refresh_reader_target(self.target, self.directory)
        final = self.send()
        self.assertFalse(final['errors'])
        # Same fixture previously needed 23 + 20 reads. All writes and their
        # guard/stage/readback reads remain; only redundant inventory reads go.
        for report, reads, reused in ((first, 19, 4), (final, 15, 5)):
            self.assertEqual(report['transport_metrics']['body_read_pages'], reads)
            self.assertEqual(report['transport_metrics']['changed_revision_reused_pages'], reused)
            self.assertEqual(report['transport_metrics']['tool_calls']['query_data_sources'], 4)
            self.assertEqual(report['transport_metrics']['tool_calls']['notion_update_page'], 10)
        ids = {p['properties']['sync_key']: pid for pid, p in self.plugin.pages.items()}
        self.assertEqual({key: ids[key] for key in old_ids}, old_ids)
        self.assertEqual(len(ids), len(self.plugin.pages))
        self.assertEqual(len(ids), len(make_plan(self.store, target=self.target)['entities']))
        repeat = self.send()
        self.assertFalse(repeat['errors'])
        self.assertEqual(repeat['transport_metrics']['tool_calls'], {'query_data_sources': 4})
        self.assertEqual(repeat['writes'], 0)
        operations = NotionMCP(self.target, self.directory, self.plugin).outbox.records('operations')
        self.assertTrue(all(op['state'] == 'success' for op in operations.values()))
        self.assertEqual(self.store.path.read_bytes(), approvals)

    def test_local_change_still_detects_edit_after_metadata_before_write(self):
        self.send()
        r = self.store.revise(self.record['id'], self.record['snapshot'],
                              [{'path': '/summary', 'value': '승인한 변경 요약이다.'}])
        self.store.decide(r['id'], r['snapshot'], 'approve')
        pid = next(pid for pid, p in self.plugin.pages.items()
                   if p['source'] == self.target['collections']['material']['data_source_id'])
        original = self.plugin
        before = original.writes
        def concurrent_edit(tool, args):
            if tool == 'fetch' and args['id'] == pid:
                original.pages[pid]['body'] += '\nmanual edit after inventory'
                original.touch(pid)
            return original(tool, args)
        self.plugin = concurrent_edit
        report = self.send()
        self.assertEqual(report['errors'][0]['code'], 'REMOTE_CONFLICT')
        self.assertEqual(report['transport_metrics']['changed_revision_reused_pages'], 1)
        self.assertEqual(original.writes, before)
        self.assertIn('manual edit after inventory', original.pages[pid]['body'])

    def test_local_change_with_missing_revision_keeps_inventory_read(self):
        self.send()
        r = self.store.revise(self.record['id'], self.record['snapshot'],
                              [{'path': '/summary', 'value': '수정 시각 없는 자료의 변경 요약이다.'}])
        self.store.decide(r['id'], r['snapshot'], 'approve')
        pid = next(pid for pid, p in self.plugin.pages.items()
                   if p['source'] == self.target['collections']['material']['data_source_id'])
        self.plugin.pages[pid]['properties'].pop('native_revision')
        report = self.send()
        self.assertFalse(report['errors'])
        self.assertEqual(report['transport_metrics']['changed_revision_reused_pages'], 0)
        self.assertEqual(report['transport_metrics']['body_read_pages'], 4)

    def test_remote_body_only_edit_with_unchanged_digest_is_preserved(self):
        self.send()
        pid = next(iter(self.plugin.pages))
        old_digest = self.plugin.pages[pid]['properties']['managed_digest']
        self.plugin.pages[pid]['body'] += '\nmanual edit'
        self.plugin.touch(pid)
        before = self.plugin.writes
        report = self.send()
        self.assertEqual(report['errors'][0]['code'], 'REMOTE_CONFLICT')
        self.assertEqual(self.plugin.pages[pid]['properties']['managed_digest'], old_digest)
        self.assertEqual(self.plugin.writes, before)

    def test_deleted_page_and_duplicate_sync_key_still_block_publication(self):
        self.send()
        pid = next(iter(self.plugin.pages))
        page = self.plugin.pages.pop(pid)
        self.assertEqual(self.send()['errors'][0]['code'], 'REMOTE_MISSING')
        self.plugin.pages[pid] = page
        self.plugin.pages['f'*32] = copy.deepcopy(page)
        self.assertEqual(self.send()['errors'][0]['code'], 'REMOTE_DUPLICATE')

    def test_old_receipts_bootstrap_once_without_notion_writes(self):
        self.send()
        remote = NotionMCP(self.target, self.directory, self.plugin)
        for eid, receipt in remote.outbox.records('receipts').items():
            receipt.pop('remote_revision', None)
            remote.outbox.save('receipts', eid, receipt)
        before = self.plugin.writes
        first = self.send()
        self.assertFalse(first['errors'])
        self.assertEqual(first['transport_metrics']['tool_calls']['fetch'], len(self.plugin.pages))
        self.assertEqual(self.send()['transport_metrics']['tool_calls'], {'query_data_sources': 4})
        self.assertEqual(self.plugin.writes, before)

    def test_missing_native_revision_falls_back_to_full_fetch(self):
        self.send()
        pid = next(iter(self.plugin.pages))
        self.plugin.pages[pid]['properties'].pop('native_revision')
        # A missing native field does not become evidence of an unchanged page.
        self.plugin.details.clear()
        self.send()
        self.assertIn(pid, {args['id'] for name, args in self.plugin.details if name == 'fetch'})

    def test_new_material_updates_shared_entities_but_preserves_unaffected_page_ids(self):
        self.send()
        old_ids = {p['properties']['sync_key']: pid for pid, p in self.plugin.pages.items()}
        data, analysis = material('second.txt', 'second source')
        r = self.store.ingest(analysis, data)
        self.store.decide(r['id'], r['snapshot'], 'approve')
        report = self.send()
        self.assertFalse(report['errors'])
        ids = {p['properties']['sync_key']: pid for pid, p in self.plugin.pages.items()}
        self.assertTrue(all(ids[key] == pid for key, pid in old_ids.items()))
        shared = next(p for p in self.plugin.pages.values()
                      if p['source'] == self.target['collections']['concept']['data_source_id'])
        self.assertEqual(len(shared['properties']['materials']), 2)
        self.assertEqual(self.send()['transport_metrics']['tool_calls'], {'query_data_sources': 4})

    def test_native_revision_path_keeps_partial_body_checkpoint_and_manual_edit_guard(self):
        self.send()
        r = self.store.revise(self.record['id'], self.record['snapshot'],
                              [{'path': '/summary', 'value': '중단 후 복구할 승인 요약이다.'}])
        self.store.decide(r['id'], r['snapshot'], 'approve')
        original = self.plugin
        def interrupted(tool, args):
            if tool == 'notion_update_page' and args['command'] == 'update_properties':
                raise DeliveryError('SERVICE_UNAVAILABLE')
            return original(tool, args)
        self.plugin = interrupted
        self.assertEqual(self.send()['errors'][0]['code'], 'SERVICE_UNAVAILABLE')
        self.plugin = original
        self.assertEqual(self.send()['errors'][0]['code'], 'EXPLICIT_RETRY_REQUIRED')
        original.details.clear()
        self.assertFalse(self.send(retry=True)['errors'])
        self.assertFalse(any(name == 'notion_update_page' and args['command'] == 'replace_content'
                             for name, args in original.details))
        self.assertEqual(self.send()['transport_metrics']['tool_calls'], {'query_data_sources': 4})

    def test_paginated_metadata_is_complete_without_reading_unchanged_bodies(self):
        self.send()
        original = self.plugin
        def paginated(tool, args):
            result = original(tool, args)
            if tool == 'query_data_sources' and len(result['results']) > 1:
                if args['data'].get('start_cursor'):
                    return {'results': result['results'][1:], 'has_more': False}
                return {'results': result['results'][:1], 'has_more': True, 'next_cursor': 'second-page'}
            return result
        self.plugin = paginated
        report = self.send()
        self.assertFalse(report['errors'])
        self.assertEqual(report['transport_metrics']['tool_calls'].get('fetch', 0), 0)
        self.assertEqual(report['transport_metrics']['revision_reused_pages'], len(original.pages))

    def test_unmanaged_row_with_empty_sync_key_is_not_treated_as_managed_or_rewritten(self):
        self.send()
        unmanaged = copy.deepcopy(next(iter(self.plugin.pages.values())))
        unmanaged['properties']['sync_key'] = None
        self.plugin.pages['e'*32] = unmanaged
        before = self.plugin.writes
        report = self.send()
        self.assertFalse(report['errors'])
        self.assertEqual(self.plugin.writes, before)
