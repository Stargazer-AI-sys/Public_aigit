import contextlib
import copy
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from analyzer.core import AnalysisError
from analyzer.notion_front import refresh_front
from analyzer.notion_mcp import NotionMCP, main
from analyzer.notion_publisher import NotionPublisher, publish_staged
from analyzer.notion_sync import DeliveryError, make_plan
import test_notion_publisher as fixtures
from test_organizer import material


class ReviewRegressionTests(unittest.TestCase):
    setUp = fixtures.LocalPublicationTests.setUp

    def test_front_knowledge_index_excludes_approved_but_unselected_material(self):
        data, analysis = material('unselected.txt', 'unpublished source')
        r = self.store.ingest(analysis, data)
        self.store.decide(r['id'], r['snapshot'], 'approve')
        self.target['reader'] = {'version': 1, 'pages': {}, 'indexes': {}}
        plan = make_plan(self.store, target=self.target, material_ids=[self.record['id']])
        front = self.root/'front'
        front.mkdir()
        (front/'state.json').write_text('{}', encoding='utf-8')
        def inspect(plan, approved, policy, target, home, *, navigation_plan=None):
            self.assertEqual([m['id'] for m in approved['materials']], [self.record['id']])
            self.assertTrue(all(s['material_id'] == self.record['id']
                                for c in approved['concepts'] for s in c['sources']))
            if navigation_plan is not None:
                self.assertEqual(set(navigation_plan['approvals']), {self.record['id']})
            return []
        with patch('analyzer.notion_front.build_front_pages', side_effect=inspect):
            report = refresh_front(plan, self.store, self.target, self.root, SimpleNamespace(local_source=True))
        self.assertFalse(report['errors'])

    def test_plan_failure_after_allocation_retains_success_and_metrics(self):
        self.plugin = fixtures.PublicationPlugin(self.target)
        remote = NotionPublisher(self.target, self.directory, self.plugin)
        plan = make_plan(self.store, target=self.target)
        from analyzer import notion_sync
        original = notion_sync.make_plan
        calls = 0
        def changed(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:  # Allocation verify succeeds; final-plan rebuild fails.
                raise AnalysisError('PUBLISH_STALE', 'test stale approval')
            return original(*args, **kwargs)
        with patch('analyzer.notion_sync.make_plan', side_effect=changed):
            _, _, _, report = publish_staged(plan, self.store, remote, self.directory, target=self.target)
        self.assertEqual(report['errors'][0]['code'], 'PUBLISH_STALE')
        self.assertTrue(report['notion_sent'])
        self.assertGreater(report['initial_pass']['writes'], 0)
        self.assertGreater(report['initial_pass']['transport_metrics']['tool_calls']['notion_create_pages'], 0)
        self.assertTrue(remote.outbox.records('receipts'))

    def test_front_failure_preserves_successful_database_report(self):
        self.target['material_database']['name'] = 'Mock library'
        self.target['reader'] = {'version': 1, 'pages': {}, 'indexes': {}}
        target = self.root/'target.json'
        target.write_text(json.dumps(self.target), encoding='utf-8')
        output = self.root/'publication'
        plugin = fixtures.PublicationPlugin(self.target)
        argv = ['notion_mcp', '--workspace', str(self.store.root), '--target', str(target),
                '--output-dir', str(output), '--material-id', self.record['id'], '--allow-notion-write']
        with patch('sys.argv', argv), patch('analyzer.notion_mcp.rpc_many',
                side_effect=lambda requests: [plugin(r['tool'], r['args']) for r in requests]), \
                patch('analyzer.notion_front.refresh_front', side_effect=DeliveryError('FRONT_UNAVAILABLE')), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(), 1)
        report_file = next((output/'runs').glob('*/report.json'))
        report = json.loads(report_file.read_text(encoding='utf-8'))
        self.assertEqual(report['errors'][0]['code'], 'FRONT_UNAVAILABLE')
        self.assertTrue(report['notion_sent'])
        self.assertGreater(report['writes'], 0)
        self.assertGreater(report['initial_pass']['writes'], 0)
        self.assertIn('transport_metrics', report)
        self.assertIn('front', report['phase_seconds'])
        self.assertEqual(report['front_completion'], 'incomplete')
        self.assertTrue(report['approval_db_unchanged'])

    def test_public_single_write_cannot_create_over_existing_page(self):
        plugin = fixtures.PublicationPlugin(self.target)
        plan = make_plan(self.store, target=self.target)
        remote = NotionPublisher(self.target, self.directory, plugin)
        _, _, remote, report = publish_staged(plan, self.store, remote, self.directory, target=self.target)
        self.assertFalse(report['errors'])
        eid, receipt = next(iter(remote.outbox.records('receipts').items()))
        before = plugin.writes
        with self.assertRaises(DeliveryError) as error:
            remote.write(eid, receipt['document'], None, 'unexpected-create')
        self.assertEqual(error.exception.code, 'REMOTE_CONFLICT')
        self.assertEqual(plugin.writes, before)

    def test_strict_single_write_uses_create_and_readback_with_no_duplicate(self):
        plugin = fixtures.PublicationPlugin(self.target)
        remote = NotionMCP(self.target, self.directory, plugin)
        plan = make_plan(self.store, target=self.target)
        remote.prepare_plan(plan)
        entity = plan['entities'][0]
        doc = {'kind': entity['kind'], 'properties': entity['properties'], 'body': entity['body'], 'relations': {}}
        result = remote.write(entity['key'], doc, None, 'direct-create')
        self.assertEqual(len(plugin.pages), 1)
        self.assertTrue(result['remote_revision'])
        self.assertEqual(result['document'], doc)
        before = plugin.writes
        with self.assertRaises(DeliveryError):
            remote.write(entity['key'], copy.deepcopy(doc), None, 'duplicate-create')
        self.assertEqual(plugin.writes, before)
