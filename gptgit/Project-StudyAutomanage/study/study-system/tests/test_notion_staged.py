import copy
import unittest
from collections import Counter

from analyzer.notion_publisher import NotionPublisher, publish_staged
from analyzer.notion_reader import refresh_reader_target
from analyzer.notion_sync import DeliveryError, make_plan
import test_notion_publisher as fixtures
from test_organizer import material


class StagedPublicationTests(unittest.TestCase):
    setUp = fixtures.LocalPublicationTests.setUp

    def send(self, retry=False):
        self.target = refresh_reader_target(self.target, self.directory)
        remote = NotionPublisher(self.target, self.directory, self.plugin)
        plan = make_plan(self.store, target=self.target)
        self.plan, self.target, self.remote, report = publish_staged(
            plan, self.store, remote, self.directory, target=self.target, retry=retry)
        return report

    def seed(self):
        self.target['reader'] = {'version': 1, 'pages': {}, 'indexes': {}}
        self.plugin = fixtures.PublicationPlugin(self.target)
        report = self.send()
        self.assertFalse(report['errors'])

    def verify_final_documents(self):
        receipts = self.remote.outbox.records('receipts')
        for entity in self.plan['entities']:
            desired = {'kind': entity['kind'], 'properties': entity['properties'], 'body': entity['body'],
                       'relations': {name: [receipts[k]['id'] for k in keys]
                                     for name, keys in entity['relations'].items()}}
            self.assertEqual(receipts[entity['key']]['document'], desired)
        self.assertTrue(all(op['state'] == 'success' for op in self.remote.outbox.records('operations').values()))

    def test_new_ids_then_one_final_body_and_property_update_per_page(self):
        self.seed()
        old_ids = {p['properties']['sync_key']: pid for pid, p in self.plugin.pages.items()}
        data, analysis = material('second.txt', 'second source')
        r = self.store.ingest(analysis, data)
        self.store.decide(r['id'], r['snapshot'], 'approve')
        approvals = self.store.path.read_bytes()
        self.plugin.details.clear()
        report = self.send()
        self.assertFalse(report['errors'])
        writes = Counter((args['page_id'], args['command']) for tool, args in self.plugin.details
                         if tool == 'notion_update_page')
        self.assertTrue(writes)
        self.assertTrue(all(n == 1 for n in writes.values()))
        for tool, args in self.plugin.details:
            if tool == 'notion_create_pages':
                self.assertTrue(all(not page['content'].strip() for page in args['pages']))
        self.assertEqual(report['initial_pass']['transport_metrics']['tool_calls']['query_data_sources'], 4)
        self.assertEqual(report['initial_pass']['transport_metrics']['exchanges'], 2)
        self.assertEqual(report['transport_metrics']['exchanges'], 2)
        self.assertEqual(report['initial_pass']['transport_metrics']['body_read_pages'], 0)
        self.assertEqual(report['transport_metrics']['body_read_pages'], 0)
        ids = {p['properties']['sync_key']: pid for pid, p in self.plugin.pages.items()}
        self.assertEqual({k: ids[k] for k in old_ids}, old_ids)
        self.assertEqual(len(ids), len(self.plugin.pages))
        self.assertEqual(self.store.path.read_bytes(), approvals)
        self.verify_final_documents()
        repeat = self.send()
        self.assertFalse(repeat['errors'])
        self.assertEqual(repeat['initial_pass']['transport_metrics']['tool_calls'], {'query_data_sources': 4})
        self.assertEqual(repeat['transport_metrics']['tool_calls'], {})
        self.assertEqual(repeat['writes'] + repeat['initial_pass']['writes'], 0)

    def test_partial_final_body_recovers_without_rewrite(self):
        self.seed()
        self.record = self.store.get(self.record['id'])
        fixtures.LocalPublicationTests.revise(self)
        original = self.plugin
        def fail(tool, args):
            if tool == 'notion_update_page' and args['command'] == 'update_properties':
                raise DeliveryError('RESPONSE_LOST')
            return original(tool, args)
        self.plugin = fail
        self.assertEqual(self.send()['errors'][0]['code'], 'RESPONSE_LOST')
        self.plugin = original
        self.assertEqual(self.send()['errors'][0]['code'], 'EXPLICIT_RETRY_REQUIRED')
        original.details.clear()
        self.assertFalse(self.send(retry=True)['errors'])
        self.assertFalse(any(t == 'notion_update_page' and a['command'] == 'replace_content'
                             for t, a in original.details))
        self.verify_final_documents()

    def test_interrupted_allocation_reconciles_ids_without_duplicate(self):
        self.target['reader'] = {'version': 1, 'pages': {}, 'indexes': {}}
        original = fixtures.PublicationPlugin(self.target)
        def lose(tool, args):
            result = original(tool, args)
            if tool == 'notion_create_pages':
                raise DeliveryError('RESPONSE_LOST')
            return result
        self.plugin = lose
        self.assertEqual(self.send()['errors'][0]['code'], 'RESPONSE_LOST')
        self.plugin = original
        self.assertFalse(self.send(retry=True)['errors'])
        keys = [p['properties']['sync_key'] for p in original.pages.values()]
        self.assertEqual(len(keys), len(set(keys)))
        self.verify_final_documents()

    def test_manual_edit_during_interruption_still_blocks(self):
        self.seed()
        self.record = self.store.get(self.record['id'])
        fixtures.LocalPublicationTests.revise(self)
        original = self.plugin
        def fail(tool, args):
            if tool == 'notion_update_page' and args['command'] == 'update_properties':
                raise DeliveryError('RESPONSE_LOST')
            return original(tool, args)
        self.plugin = fail
        self.assertEqual(self.send()['errors'][0]['code'], 'RESPONSE_LOST')
        self.plugin = original
        pid = next(pid for pid, p in original.pages.items()
                   if p['source'] == self.target['collections']['material']['data_source_id'])
        original.pages[pid]['body'] += '\nmanual change'
        original.touch(pid)
        before = original.writes
        self.assertEqual(self.send(retry=True)['errors'][0]['code'], 'REMOTE_CONFLICT')
        self.assertEqual(original.writes, before)

    def test_partial_allocation_resumes_old_intent_after_reader_digest_changes(self):
        self.target['reader'] = {'version': 1, 'pages': {}, 'indexes': {}}
        original = fixtures.PublicationPlugin(self.target)
        count = 0
        def incomplete(tool, args):
            nonlocal count
            if tool == 'notion_create_pages':
                count += 1
                if count == 2:
                    return {'pages': []}
            return original(tool, args)
        self.plugin = incomplete
        self.assertEqual(self.send()['errors'][0]['code'], 'NOTION_CREATE_UNCERTAIN')
        self.assertTrue(self.remote.outbox.records('receipts'))
        self.plugin = original
        report = self.send(retry=True)
        self.assertFalse(report['errors'])
        keys = [p['properties']['sync_key'] for p in original.pages.values()]
        self.assertEqual(len(keys), len(set(keys)))
        self.verify_final_documents()
