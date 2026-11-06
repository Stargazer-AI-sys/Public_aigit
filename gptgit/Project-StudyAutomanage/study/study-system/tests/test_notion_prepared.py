import copy
import json
import unittest
from pathlib import Path

from analyzer.learning_categories import GROUPS, grouped_materials
from analyzer.notion_front import render_front_pages
from analyzer.notion_prepared import prepare, validate, publish, load
from analyzer.notion_sync import DeliveryError, make_plan
import test_notion_materials as materials
import test_notion_publisher as fixtures


class PreparedTests(unittest.TestCase):
    send = materials.MaterialPublicationTests.send
    new_material = materials.MaterialPublicationTests.new_material

    def setUp(self):
        fixtures.LocalPublicationTests.setUp(self)
        materials.MaterialPublicationTests.seed(self)
        self.target['reader']['indexes'].update({'개념 찾아보기': '2'*32, '실습 찾아보기': '3'*32})
        self.assertFalse(self.send()['errors'])
        self.target['material_database']['name'] = '학습자료'
        self.target_file = self.root/'target.json'
        self.home_file = self.root/'home.json'
        self.target_file.write_text(json.dumps(self.target), encoding='utf-8')
        self.home = {'category_layout': 'ccna-basic-17', 'navigation_pages': [
            {'id': str(i)*32, 'url': 'https://app.notion.com/p/'+str(i)*32,
             'properties': {'title': d['title']}}
            for i, d in enumerate(self.store.policy()['curriculum']['domains'], 4)]}
        self.home_file.write_text(json.dumps(self.home), encoding='utf-8')
        initial = render_front_pages(make_plan(self.store, target=self.target), self.store, self.target, self.home)
        self.fronts = {p['page_id'].replace('-', ''): p['body'] for p in initial}
        (self.root/'front').mkdir()
        (self.root/'front/state.json').write_text(json.dumps({pid: {'expected_body': b, 'observed_body': b}
            for pid, b in self.fronts.items()}), encoding='utf-8')

    def prepare(self):
        result = prepare(self.store.root, self.target_file, self.home_file, self.root, self.root/'prepared')
        return Path(result['package'])

    def call(self, tool, args):
        pid = (args.get('id') or args.get('page_id') or '').replace('-', '')
        if pid in self.fronts:
            if tool == 'fetch':
                return {'id': pid, 'text': '<properties>\n{}\n</properties>\n<content>\n'+self.fronts[pid]+'\n</content>'}
            if tool == 'notion_update_page':
                self.fronts[pid] = args['new_str']
                return {'success': True, 'page_id': pid}
        return self.plugin(tool, args)

    def publish(self, package):
        return publish(package, call=self.call,
                       call_many=lambda requests: [self.call(r['tool'], r['args']) for r in requests])

    def test_prepare_contains_all_17_categories_including_empty_without_writes(self):
        before = self.store.path.read_bytes()
        remote = copy.deepcopy(self.plugin.pages)
        package = load(self.prepare())
        validate(package)
        domains = {p['page_id'].replace('-', ''): p['body'] for p in package['front_pages']}
        self.assertEqual(sum(len(d) for d in GROUPS), 17)
        for i, groups in enumerate(GROUPS, 4):
            for title, _, _ in groups:
                self.assertIn('## '+title+'\n', domains[str(i)*32])
        self.assertIn('학습자료 준비 중', domains['9'*32])
        self.assertEqual(self.store.path.read_bytes(), before)
        self.assertEqual(self.plugin.pages, remote)

    def test_setting_change_blocks_before_any_remote_call(self):
        package = self.prepare()
        self.home_file.write_text(self.home_file.read_text()+' ', encoding='utf-8')
        calls = []
        with self.assertRaises(DeliveryError) as error:
            publish(package, call=lambda *a: calls.append(a), call_many=lambda a: calls.append(a))
        self.assertEqual(error.exception.code, 'PUBLISH_STALE')
        self.assertFalse(calls)

    def test_approval_change_blocks_prepared_package(self):
        package = load(self.prepare())
        r = self.store.list()[0]
        self.store.decide(r['id'], r['snapshot'], 'hold')
        with self.assertRaises(DeliveryError):
            validate(package)

    def test_modified_package_is_rejected(self):
        package = load(self.prepare())
        package['front_pages'][0]['body'] += 'edited'
        with self.assertRaises(DeliveryError):
            validate(package)

    def test_remote_access_is_not_grouped_as_wireless_from_old_broad_heading(self):
        record = {'id': 'remote', 'classification': {'paths': [
            ['NETWORK', '2. 네트워크 접속', '무선 접속과 장비 관리']]},
            'analysis': {'topics': [{'name': '원격 접속', 'children': [{'name': 'Telnet 설정'}]}],
                         'concepts': [{'name': 'Telnet'}, {'name': '가상회선(VTY)'}]}}
        original = copy.deepcopy(record)
        groups = grouped_materials([record])
        self.assertEqual(groups[1][3], [])
        self.assertEqual(groups[3][1], [record])
        self.assertEqual(record, original)

    def test_policy_change_blocks_even_when_existing_approvals_survive(self):
        package = load(self.prepare())
        policy = self.store.policy()
        policy['concept_aliases']['future alias'] = 'future name'
        self.store.set_policy(policy)
        self.assertTrue(self.store.approved()['materials'])
        with self.assertRaises(DeliveryError):
            validate(package)

    def test_new_material_binds_returned_id_and_repeat_writes_nothing(self):
        self.new_material()
        package_file = self.prepare()
        package = load(package_file)
        self.assertEqual(len(package['unbound_material_keys']), 1)
        approvals = self.store.path.read_bytes()
        old_ids = set(self.plugin.pages)
        report = self.publish(package_file)
        self.assertFalse(report['errors'], report)
        self.assertEqual(report['entity_writes'], 1)
        self.assertTrue(report['approval_db_unchanged'])
        self.assertEqual(len(set(self.plugin.pages)-old_ids), 1)
        self.assertNotIn('__NEW_PAGE_', '\n'.join(self.fronts.values()))
        self.assertEqual(self.store.path.read_bytes(), approvals)
        again = self.publish(package_file)
        self.assertFalse(again['errors'], again)
        self.assertEqual(again['entity_writes'], 0)
        self.assertEqual((again['front_pages']['reads'], again['front_pages']['writes']), (0, 0))

    def test_manual_front_edit_is_preserved(self):
        self.new_material()
        package_file = self.prepare()
        self.fronts['5'*32] += '\n사용자 수정'
        report = self.publish(package_file)
        self.assertIn('FRONT_REMOTE_CONFLICT', [e['code'] for e in report['errors']])
        self.assertTrue(self.fronts['5'*32].endswith('사용자 수정'))

    def test_change_after_inventory_blocks_before_write(self):
        self.new_material()
        package_file = self.prepare()
        ids = set(self.plugin.pages)
        def calls(requests):
            values = [self.call(r['tool'], r['args']) for r in requests]
            if any(r['tool'] == 'query_data_sources' for r in requests):
                self.home_file.write_text(self.home_file.read_text()+' ', encoding='utf-8')
            return values
        report = publish(package_file, call=self.call, call_many=calls)
        self.assertIn('PUBLISH_STALE', [e['code'] for e in report['errors']])
        self.assertEqual(set(self.plugin.pages), ids)

    def test_lost_front_response_requires_explicit_retry_for_unsent_intents(self):
        self.new_material()
        package_file = self.prepare()
        lost = []
        def call(tool, args):
            result = self.call(tool, args)
            if tool == 'notion_update_page' and args['page_id'].replace('-', '') in self.fronts and not lost:
                lost.append(args['page_id'])
                raise DeliveryError('RESPONSE_LOST')
            return result
        first = publish(package_file, call=call,
                        call_many=lambda requests: [call(r['tool'], r['args']) for r in requests])
        self.assertIn('RESPONSE_LOST', [e['code'] for e in first['errors']])
        ids = set(self.plugin.pages)
        blocked = self.publish(package_file)
        self.assertIn('FRONT_UNRESOLVED_WRITE', [e['code'] for e in blocked['errors']])
        result = publish(package_file, call=self.call,
            call_many=lambda requests: [self.call(r['tool'], r['args']) for r in requests], retry=True)
        self.assertFalse(result['errors'], result)
        self.assertEqual(result['entity_writes'], 0)
        self.assertEqual(set(self.plugin.pages), ids)


if __name__ == '__main__':
    unittest.main()
