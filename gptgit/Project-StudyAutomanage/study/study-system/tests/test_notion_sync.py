import copy
import hashlib
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from analyzer.core import AnalysisError
from analyzer.notion_sync import DeliveryError, MockNotion, deliver_mock, make_plan, mapping_for, preview
from analyzer.workspace import Workspace
from test_organizer import material


class NotionSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = Workspace(self.root/'library')
        self.data, self.analysis = material()
        self.record = self.store.ingest(self.analysis, self.data)
        self.record = self.store.decide(self.record['id'], self.record['snapshot'], 'approve')
        self.plan = make_plan(self.store)
        self.remote = MockNotion(self.root/'remote.sqlite3')
        self.outbox = self.root/'outbox'

    def send(self, **kwargs):
        return deliver_mock(self.plan, self.store, self.remote, self.outbox, **kwargs)

    def target(self):
        return {'format_version': 1, 'live_write_enabled': False,
                'parent_page': {'id': '11111111-1111-4111-8111-111111111111', 'name': 'test parent'},
                'material_database': {'id': '22222222-2222-4222-8222-222222222222', 'name': 'test DB',
                                     'data_source_id': '33333333-3333-4333-8333-333333333333',
                                     'observed_properties': {'이름': 'title'}, 'property_mapping': {'name': '이름'}}}

    def test_target_mapping_records_missing_properties_without_claiming_ready(self):
        target = self.target(); mapping = mapping_for(target)
        self.assertEqual(mapping['binding_status'], 'partial')
        self.assertIn('sync_key', mapping['missing_material_properties'])
        self.assertEqual(len(mapping['unbound_collections']), 3)
        self.assertFalse(mapping['material_relations_ready'])
        plan = make_plan(self.store, target=target)
        self.assertIn('test DB', preview(plan))
        first = deliver_mock(plan, self.store, self.remote, self.outbox, target=target)
        second = deliver_mock(plan, self.store, self.remote, self.outbox, target=target)
        self.assertFalse(first['errors']); self.assertEqual(second['writes'], 0)

    def test_target_change_requires_new_preview(self):
        target = self.target(); plan = make_plan(self.store, target=target)
        target['material_database']['data_source_id'] = '44444444-4444-4444-8444-444444444444'
        self.assert_code('PUBLISH_STALE', lambda: deliver_mock(plan, self.store, self.remote, self.outbox, target=target))
        self.assertEqual(self.remote.writes, 0)

    def test_invalid_target_property_type_or_live_flag_is_rejected(self):
        for change in ('id', 'property', 'live'):
            target = self.target()
            if change == 'id':
                target['parent_page']['id'] = 'invalid'
            elif change == 'property':
                target['material_database']['observed_properties']['이름'] = 'rich_text'
            else:
                target['live_write_enabled'] = True
            self.assert_code('PUBLISH_TARGET_ERROR', lambda: mapping_for(target))

    def assert_code(self, code, action):
        with self.assertRaises(AnalysisError) as error:
            action()
        self.assertEqual(error.exception.code, code)

    def test_only_valid_approvals_and_relations_are_planned(self):
        d2, a2 = material('pending.txt', 'pending'); self.store.ingest(a2, d2)
        d3, a3 = material('held.txt', 'held'); r = self.store.ingest(a3, d3)
        self.store.decide(r['id'], r['snapshot'], 'hold')
        plan = make_plan(self.store)
        self.assertEqual(len(plan['approvals']), 1)
        self.assertEqual({e['kind'] for e in plan['entities']}, {'category', 'concept', 'material', 'practice'})
        keys = {e['key'] for e in plan['entities']}
        for entity in plan['entities']:
            for values in entity['relations'].values():
                self.assertTrue(set(values) <= keys)
        self.assertFalse(plan['notion_sent'])
        self.assertIn('바인딩 미확정', preview(plan))

    def test_read_only_workspace_never_creates_or_writes_database(self):
        missing = self.root/'missing'
        self.assert_code('LIBRARY_NOT_FOUND', lambda: Workspace(missing, read_only=True))
        self.assertFalse(missing.exists())
        before = self.store.path.read_bytes()
        readonly = Workspace(self.store.root, read_only=True)
        self.assertEqual(make_plan(readonly), self.plan)
        with self.assertRaises(sqlite3.OperationalError):
            readonly.set_policy(readonly.policy())
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_two_phase_delivery_and_second_run_has_zero_writes(self):
        first = self.send(); second = self.send()
        self.assertFalse(first['errors']); self.assertFalse(second['errors'])
        self.assertEqual(second['writes'], 0)
        self.assertEqual(second['skipped'], 2*len(self.plan['entities']))
        for entity in self.plan['entities']:
            pages = self.remote.lookup(entity['key']); self.assertEqual(len(pages), 1)
            self.assertEqual(pages[0]['document']['body'], entity['body'])
            for values in pages[0]['document']['relations'].values():
                self.assertTrue(all(v.startswith('mock-') for v in values))

    def test_stale_or_tampered_plan_blocks_before_writes(self):
        changed = copy.deepcopy(self.plan); changed['entities'][0]['body'] = 'tampered'
        self.assert_code('PUBLISH_STALE', lambda: deliver_mock(changed, self.store, self.remote, self.outbox))
        self.store.decide(self.record['id'], self.record['snapshot'], 'hold')
        self.assert_code('PUBLISH_STALE', self.send)
        self.assertEqual(self.remote.writes, 0)

    def test_approval_change_during_delivery_stops_next_operation(self):
        original = self.remote.write
        def change(*args):
            result = original(*args)
            self.store.decide(self.record['id'], self.record['snapshot'], 'hold')
            return result
        with patch.object(self.remote, 'write', side_effect=change):
            self.assert_code('PUBLISH_STALE', self.send)
        self.assertEqual(self.remote.writes, 1)

    def test_manual_remote_edit_blocks_even_same_plan(self):
        self.send()
        eid = self.plan['entities'][0]['key']; page = self.remote.lookup(eid)[0]
        changed = copy.deepcopy(page['document']); changed['body'] = 'manual user edit'
        self.remote.write(eid, changed, page['stamp'], 'manual')
        before = self.remote.writes
        report = self.send()
        self.assertEqual(report['errors'][0]['code'], 'REMOTE_CONFLICT')
        self.assertEqual(self.remote.writes, before)
        self.assertEqual(self.remote.lookup(eid)[0]['document']['body'], 'manual user edit')

    def test_uncertain_create_readback_recovers_without_duplicate(self):
        original = self.remote.write
        calls = []
        def lose_response(*args):
            result = original(*args); calls.append(result)
            raise DeliveryError('RESPONSE_LOST')
        with patch.object(self.remote, 'write', side_effect=lose_response):
            first = self.send()
        self.assertEqual(first['errors'][0]['code'], 'RESPONSE_LOST')
        blocked = self.send()
        self.assertEqual(blocked['errors'][0]['code'], 'EXPLICIT_RETRY_REQUIRED')
        again = self.send(retry=True)
        self.assertFalse(again['errors']); self.assertEqual(again['reconciled'], 1)
        self.assertEqual(len(self.remote.lookup(self.plan['entities'][0]['key'])), 1)
        self.assertEqual(self.send()['writes'], 0)

    def test_partial_failure_resume_preserves_successes(self):
        original = self.remote.write
        count = 0
        def partial(*args):
            nonlocal count
            count += 1
            if count == 3:
                raise DeliveryError('SERVICE_UNAVAILABLE')
            return original(*args)
        with patch.object(self.remote, 'write', side_effect=partial):
            first = self.send()
        self.assertEqual(first['writes'], 2)
        self.assertTrue(first['errors'])
        resumed = self.send(retry=True)
        self.assertFalse(resumed['errors']); self.assertGreaterEqual(resumed['skipped'], 2)
        self.assertEqual(self.send()['writes'], 0)

    def test_relation_phase_failure_is_recoverable(self):
        original = self.remote.write
        def lose_links(eid, document, stamp, op):
            result = original(eid, document, stamp, op)
            if document['relations']:
                raise DeliveryError('RESPONSE_LOST')
            return result
        with patch.object(self.remote, 'write', side_effect=lose_links):
            first = self.send()
        self.assertTrue(first['errors'])
        resumed = self.send(retry=True)
        self.assertFalse(resumed['errors']); self.assertEqual(resumed['reconciled'], 1)

    def test_interrupt_after_remote_commit_is_explicitly_reconciled(self):
        original = self.remote.write
        def interrupt(*args):
            original(*args); raise KeyboardInterrupt()
        with patch.object(self.remote, 'write', side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.send()
        self.assertEqual(self.send()['errors'][0]['code'], 'EXPLICIT_RETRY_REQUIRED')
        self.assertFalse(self.send(retry=True)['errors'])

    def test_lock_requires_explicit_recovery(self):
        self.outbox.mkdir(); lock = self.outbox/'delivery.lock'; lock.write_text('stopped worker')
        self.assert_code('PUBLISH_LOCKED', self.send)
        self.assertFalse(self.send(recover_interrupted=True)['errors'])

    def test_changed_destination_or_missing_remote_is_blocked(self):
        self.send()
        other = MockNotion(self.root/'other.sqlite3')
        self.assert_code('PUBLISH_DESTINATION_MISMATCH', lambda: deliver_mock(self.plan, self.store, other, self.outbox))
        with closing(sqlite3.connect(self.remote.path)) as db:
            db.execute('DELETE FROM pages WHERE entity_key=?', (self.plan['entities'][0]['key'],)); db.commit()
        self.assertEqual(self.send()['errors'][0]['code'], 'REMOTE_MISSING')

    def test_remote_duplicate_blocks_before_mutation(self):
        self.send(); eid = self.plan['entities'][0]['key']; page = self.remote.lookup(eid)[0]
        with closing(sqlite3.connect(self.remote.path)) as db:
            db.execute('INSERT INTO pages VALUES (?,?,?,?,?)', ('duplicate', eid, json.dumps(page['document']), 'x', 'x')); db.commit()
        report = self.send()
        self.assertEqual(report['errors'][0]['code'], 'REMOTE_DUPLICATE'); self.assertEqual(report['writes'], 0)

    def test_rate_limit_auth_permission_errors_never_automatically_retry(self):
        for index, code in enumerate(('RATE_LIMITED', 'AUTHENTICATION_FAILED', 'PERMISSION_DENIED')):
            remote = MockNotion(self.root/f'failure{index}.sqlite3')
            with patch.object(remote, 'write', side_effect=DeliveryError(code, 30)) as write:
                result = deliver_mock(self.plan, self.store, remote, self.root/f'outbox{index}')
            self.assertEqual(write.call_count, 1)
            self.assertEqual(result['errors'][0]['retry_after'], 30)
            self.assertEqual(result['errors'][0]['code'], code)

    def test_new_approved_content_updates_without_duplicate_and_manual_edits_conflict(self):
        self.send()
        revised = self.store.revise(self.record['id'], self.record['snapshot'], [{'path': '/summary', 'value': '사용자가 검토한 VLAN 설정이다.'}])
        self.store.decide(revised['id'], revised['snapshot'], 'approve')
        self.plan = make_plan(self.store)
        report = self.send()
        self.assertFalse(report['errors']); self.assertGreater(report['writes'], 0)
        for entity in self.plan['entities']:
            self.assertEqual(len(self.remote.lookup(entity['key'])), 1)

    def test_unrelated_policy_preserves_plan_and_secrets_are_redacted(self):
        policy = self.store.policy(); policy['concept_aliases']['unused-key'] = 'unused-value'
        self.store.set_policy(policy)
        self.assertEqual(make_plan(self.store), self.plan)
        changed = self.store.revise(self.record['id'], self.record['snapshot'], [{'path': '/practice/0/description', 'value': 'token=sample-sensitive-value'}])
        self.store.decide(changed['id'], changed['snapshot'], 'approve')
        plan = make_plan(self.store)
        self.assertNotIn('sample-sensitive-value', json.dumps(plan))

    def test_existing_real_database_cannot_be_used_as_mock(self):
        before = self.store.path.read_bytes()
        self.assert_code('PUBLISH_PATH_ERROR', lambda: MockNotion(self.store.path))
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_real_approved_materials_offline_and_original_db_unchanged(self):
        directory = Path(__file__).resolve().parents[1]/'output/knowledge_base'
        if not (directory/'library.sqlite3').is_file():
            self.skipTest('approval DB unavailable')
        before = hashlib.sha256((directory/'library.sqlite3').read_bytes()).hexdigest()
        readonly = Workspace(directory, read_only=True)
        plan = make_plan(readonly)
        first = deliver_mock(plan, readonly, self.remote, self.outbox)
        second = deliver_mock(plan, readonly, self.remote, self.outbox)
        self.assertFalse(first['errors']); self.assertFalse(second['errors'])
        self.assertEqual(second['writes'], 0)
        self.assertEqual(before, hashlib.sha256(readonly.path.read_bytes()).hexdigest())
        print('NOTION_MOCK_METRICS '+json.dumps({'materials': len(plan['approvals']),
              'entities': len(plan['entities']), 'initial_writes': first['writes'],
              'repeat_writes': second['writes'], 'repeat_skips': second['skipped'],
              'actual_notion_writes': 0, 'paid_ai_calls': 0, 'approval_db_unchanged': True}))
