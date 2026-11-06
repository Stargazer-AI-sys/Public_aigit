import copy
import json
import unittest
from unittest.mock import patch

from analyzer.notion_front import refresh_local
from analyzer.notion_publisher import NotionPublisher, publish_staged
from analyzer.notion_reader import build_front_pages, refresh_reader_target
from analyzer.notion_sync import DeliveryError, enable_material_publication, make_plan
import test_notion_publisher as fixtures
from test_organizer import material
from tools.notion_bridge.verify import audit


class MaterialPublicationTests(unittest.TestCase):
    setUp = fixtures.LocalPublicationTests.setUp

    def send(self, retry=False):
        self.target = refresh_reader_target(self.target, self.directory)
        remote = NotionPublisher(self.target, self.directory, self.plugin)
        self.plan, self.target, self.remote, report = publish_staged(
            make_plan(self.store, target=self.target), self.store, remote, self.directory,
            target=self.target, retry=retry)
        return report

    def seed(self):
        self.target['reader'] = {'version': 1, 'pages': {}, 'indexes': {'학습자료': '1'*32}}
        self.plugin = fixtures.PublicationPlugin(self.target)
        self.assertFalse(self.send()['errors'])
        self.target = enable_material_publication(self.target, self.directory)
        self.plugin.details.clear()

    def new_material(self):
        data, analysis = material('second.txt', 'second source')
        r = self.store.ingest(analysis, data)
        return self.store.decide(r['id'], r['snapshot'], 'approve')

    def test_switch_preserves_all_legacy_pages_and_relations_without_writes(self):
        self.seed()
        before = copy.deepcopy(self.plugin.pages)
        approvals = self.store.path.read_bytes()
        report = self.send()
        self.assertFalse(report['errors'])
        self.assertEqual(report['writes'], 0)
        self.assertEqual(report['transport_metrics']['tool_calls'], {'query_data_sources': 1})
        self.assertEqual(self.plugin.pages, before)
        self.assertEqual(self.store.path.read_bytes(), approvals)
        self.assertEqual({e['kind'] for e in self.plan['entities']}, {'material'})

    def test_new_material_creates_only_one_page_and_repeat_writes_nothing(self):
        self.seed()
        old = copy.deepcopy(self.plugin.pages)
        self.new_material()
        approvals = self.store.path.read_bytes()
        report = self.send()
        self.assertFalse(report['errors'])
        created = [p for tool, args in self.plugin.details if tool == 'notion_create_pages' for p in args['pages']]
        self.assertEqual(len(created), 1)
        self.assertEqual(len(self.plugin.pages), len(old)+1)
        self.assertEqual({pid: self.plugin.pages[pid] for pid in old}, old)
        self.assertEqual(report['transport_metrics']['body_read_pages'], 0)
        self.assertTrue(created[0]['content'].strip())
        self.assertFalse(any(tool == 'notion_update_page' for tool, args in self.plugin.details))
        body = next(e['body'] for e in self.plan['entities'] if e['properties']['name'] == 'second.txt')
        self.assertIn('## 분류', body)
        self.assertNotIn('notion.com/p/None', body)
        self.assertEqual(self.store.path.read_bytes(), approvals)
        repeat = self.send()
        self.assertFalse(repeat['errors'])
        self.assertEqual(repeat['writes'], 0)

    def test_changed_legacy_material_keeps_its_id_and_previous_relations(self):
        self.seed()
        old_receipts = self.remote.outbox.records('receipts')
        old = next(r for r in old_receipts.values() if r['document']['kind'] == 'material')
        r = self.store.revise(self.record['id'], self.record['snapshot'],
                              [{'path': '/summary', 'value': '로컬에서 승인한 변경된 핵심 정리입니다.'}])
        self.store.decide(r['id'], r['snapshot'], 'approve')
        before = set(self.plugin.pages)
        report = self.send()
        self.assertFalse(report['errors'])
        self.assertEqual(set(self.plugin.pages), before)
        new = next(r for r in self.remote.outbox.records('receipts').values() if r['document']['kind'] == 'material')
        self.assertEqual(new['id'], old['id'])
        self.assertEqual(new['document']['relations'], old['document']['relations'])
        self.assertIn('변경된 핵심 정리', new['document']['body'])
        self.assertEqual(self.send()['writes'], 0)

    def test_only_material_index_is_rendered_and_unchanged_front_is_skipped(self):
        self.seed()
        self.new_material()
        self.assertFalse(self.send()['errors'])
        pages = build_front_pages(self.plan, self.store.approved(), self.store.policy(), self.target, {})
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]['page_id'], '1'*32)
        self.assertIn('second.txt', pages[0]['body'])
        baseline = {'1'*32: {'expected_body': pages[0]['body'], 'observed_body': pages[0]['body']}}
        report = refresh_local(pages, baseline, self.remote, lambda state: None)
        self.assertEqual(report['writes'], 0)
        self.assertEqual(report['reads'], 0)

    def test_material_mode_renders_home_and_domains_without_creating_extra_entities(self):
        from analyzer.notion_front import normalized_body
        self.seed()
        self.target['reader']['indexes'].update({'개념 찾아보기': '2'*32, '실습 찾아보기': '3'*32})
        self.assertFalse(self.send()['errors'])
        home = {'navigation_pages': [
            {'id': str(i)*32, 'url': 'https://app.notion.com/p/'+str(i)*32,
             'properties': {'title': d['title']}}
            for i, d in enumerate(self.store.policy()['curriculum']['domains'], 4)]}
        def render():
            navigation_target = copy.deepcopy(self.target)
            navigation_target['publication'] = {'mode': 'full'}
            navigation_plan = make_plan(self.store, target=navigation_target)
            return {p['page_id'].replace('-', ''): p['body'] for p in build_front_pages(
                self.plan, self.store.approved(), self.store.policy(), self.target, home,
                navigation_plan=navigation_plan)}
        before = render()
        self.new_material()
        self.assertFalse(self.send()['errors'])
        ids = set(self.plugin.pages)
        approvals = self.store.path.read_bytes()
        after = render()
        self.assertEqual(len(after), 8)
        root = self.target['parent_page']['id'].replace('-', '')
        self.assertIn('second.txt', after[root])
        affected = [pid for pid, body in after.items() if 'second.txt' in body and pid != root and pid != '1'*32]
        self.assertEqual(len(affected), 1)
        for pid in before.keys()-{root, '1'*32, *affected}:
            self.assertEqual(normalized_body(before[pid]), normalized_body(after[pid]))
        self.assertEqual({e['kind'] for e in self.plan['entities']}, {'material'})
        self.assertNotIn('notion.com/p/None', '\n'.join(after.values()))
        self.assertEqual(set(self.plugin.pages), ids)
        self.assertEqual(self.store.path.read_bytes(), approvals)

    def test_deleted_legacy_material_is_not_recreated(self):
        self.seed()
        pid = next(pid for pid,p in self.plugin.pages.items()
                   if p['source'] == self.target['collections']['material']['data_source_id'])
        del self.plugin.pages[pid]
        before = len(self.plugin.pages)
        report = self.send()
        self.assertEqual(report['errors'][0]['code'], 'REMOTE_MISSING')
        self.assertEqual(len(self.plugin.pages), before)

    def test_manual_edit_to_preserved_material_stops_publication(self):
        self.seed()
        self.assertFalse(self.send()['errors'])
        pid = next(pid for pid,p in self.plugin.pages.items()
                   if p['source'] == self.target['collections']['material']['data_source_id'])
        self.plugin.pages[pid]['body'] += '\nmanual edit'
        self.plugin.touch(pid)
        before = self.plugin.writes
        self.assertEqual(self.send()['errors'][0]['code'], 'REMOTE_CONFLICT')
        self.assertEqual(self.plugin.writes, before)

    def test_duplicate_material_stops_without_writes(self):
        self.seed()
        pid = next(pid for pid,p in self.plugin.pages.items()
                   if p['source'] == self.target['collections']['material']['data_source_id'])
        self.plugin.pages['f'*32] = copy.deepcopy(self.plugin.pages[pid])
        before = self.plugin.writes
        self.assertEqual(self.send()['errors'][0]['code'], 'REMOTE_DUPLICATE')
        self.assertEqual(self.plugin.writes, before)

    def test_legacy_body_then_property_failure_resumes_without_rewriting_body(self):
        self.seed()
        r = self.store.revise(self.record['id'], self.record['snapshot'],
                              [{'path': '/summary', 'value': '중단 복구를 확인하는 승인된 변경 요약입니다.'}])
        self.store.decide(r['id'], r['snapshot'], 'approve')
        original = self.plugin
        def fail(tool, args):
            if tool == 'notion_update_page' and args['command'] == 'update_properties':
                raise DeliveryError('RESPONSE_LOST')
            return original(tool, args)
        self.plugin = fail
        self.assertEqual(self.send()['errors'][0]['code'], 'RESPONSE_LOST')
        original.details.clear()
        self.plugin = original
        self.assertFalse(self.send(retry=True)['errors'])
        self.assertFalse(any(tool == 'notion_update_page' and args['command'] == 'replace_content'
                             for tool,args in original.details))

    def test_reader_failure_keeps_successful_material_report(self):
        self.seed()
        self.new_material()
        remote = NotionPublisher(self.target, self.directory, self.plugin)
        plan = make_plan(self.store, target=self.target)
        with patch('analyzer.notion_reader.refresh_reader_target', side_effect=DeliveryError('READER_FAILURE')):
            _, _, _, report = publish_staged(plan, self.store, remote, self.directory, target=self.target)
        self.assertEqual(report['errors'][0]['code'], 'READER_FAILURE')
        self.assertEqual(report['writes'], 1)
        self.assertTrue(report['notion_sent'])

    def test_uncertain_new_create_recovers_without_duplicate_or_body_rewrite(self):
        self.seed()
        self.new_material()
        original = self.plugin
        def fail(tool, args):
            if tool == 'notion_create_pages':
                original(tool, args)
                raise DeliveryError('RESPONSE_LOST')
            return original(tool, args)
        self.plugin = fail
        self.assertEqual(self.send()['errors'][0]['code'], 'RESPONSE_LOST')
        before = len(original.pages)
        self.plugin = original
        original.details.clear()
        report = self.send(retry=True)
        self.assertFalse(report['errors'])
        self.assertEqual(len(original.pages), before)
        self.assertFalse(any(tool == 'notion_update_page' and args['command'] == 'replace_content'
                             for tool,args in original.details))
        self.assertEqual(self.send()['writes'], 0)

    def test_selected_readback_audit_does_not_require_untouched_pages(self):
        self.seed()
        self.new_material()
        self.assertFalse(self.send()['errors'])
        receipts = self.remote.outbox.records('receipts')
        eid = next(k for k,r in receipts.items() if r['document']['properties']['name'] == 'second.txt')
        target_file, readback = self.root/'target.json', self.root/'readback.json'
        target_file.write_text(json.dumps(self.target), encoding='utf-8')
        response = self.plugin('fetch', {'id': receipts[eid]['id']})
        readback.write_text(json.dumps([{'structuredContent': response}]), encoding='utf-8')
        front = self.root/'front.json'
        front.write_text(json.dumps([{'structuredContent': {'id': '1'*32,
                         'text': '<content>자료 목록</content>'}}]), encoding='utf-8')
        selected = audit(target_file, self.directory, readback, front, entity_keys=[eid])
        self.assertTrue(selected['ok'], selected)
        self.assertEqual(selected['expected_entities'], 1)
        self.assertEqual(selected['scope'], 'selected')
        full = audit(target_file, self.directory, readback, front)
        self.assertTrue(any(e['code'] == 'MISSING_READBACK' for e in full['errors']))
        with self.assertRaises(DeliveryError):
            audit(target_file, self.directory, readback, entity_keys=['material:unknown'])


if __name__ == '__main__':
    unittest.main()
