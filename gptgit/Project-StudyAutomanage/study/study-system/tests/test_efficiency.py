from contextlib import closing
import copy
import hashlib
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.batch import run_batch
from analyzer.cache import context_for, digest
from analyzer.core import load_schema
from analyzer.openai_provider import OpenAIProvider
from analyzer.schemas import DEFAULT_SCHEMA
from analyzer.workspace import Workspace
from smoke_check import OfflineProvider
from test_organizer import material
import test_organizer

PROJECT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('project_status', PROJECT/'tools/project_status.py')
status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status)


class EfficiencyTests(unittest.TestCase):
    inventory = test_organizer.OrganizerTests.inventory

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = Workspace(self.root/'library')
        self.data, self.analysis = material()
        self.schema = load_schema(DEFAULT_SCHEMA)

    def approve(self, data=None, analysis=None):
        r = self.store.ingest(analysis or self.analysis, data or self.data)
        return self.store.decide(r['id'], r['snapshot'], 'approve')

    def release(self):
        policy = self.store.policy()
        policy['publication_holds'][self.data['filename']] = 'review reason'
        self.store.set_policy(policy)
        r = self.store.ingest(self.analysis, self.data)
        r = self.store.release_hold(r['id'], r['snapshot'], 'verified original')
        return self.store.decide(r['id'], r['snapshot'], 'approve')

    def test_release_survives_unrelated_policy_and_import(self):
        r = self.release()
        policy = self.store.policy(); policy['concept_aliases']['unrelated'] = 'unused'
        self.store.set_policy(policy)
        same = self.store.ingest(self.analysis, self.data)
        self.assertEqual(same['snapshot'], r['snapshot'])
        self.assertEqual(same['holds'], [])
        self.assertEqual(len(self.store.approved()['materials']), 1)

    def test_legacy_release_is_adopted_from_history(self):
        r = self.release()
        with self.store.db() as db:
            for table in ('materials', 'revisions'):
                rows = db.execute('SELECT rowid,record FROM '+table).fetchall()
                for rowid, raw in rows:
                    record = json.loads(raw); record.pop('hold_releases', None)
                    db.execute('UPDATE '+table+' SET record=? WHERE rowid=?', (json.dumps(record), rowid))
        policy = self.store.policy(); policy['concept_aliases']['unrelated'] = 'unused'
        self.store.set_policy(policy)
        same = self.store.get(r['id'])
        self.assertEqual(same['snapshot'], r['snapshot'])
        self.assertEqual(same['holds'], [])
        self.assertTrue(same['hold_releases'])

    def test_new_reason_and_new_analysis_require_review(self):
        r = self.release()
        policy = self.store.policy(); policy['publication_holds'][self.data['filename']] = 'new reason'
        self.store.set_policy(policy)
        self.assertEqual(self.store.get(r['id'])['holds'], ['new reason'])
        self.assertEqual(self.store.approved()['materials'], [])
        r = self.store.get(r['id'])
        self.store.release_hold(r['id'], r['snapshot'], 'verified')
        changed = copy.deepcopy(self.analysis); changed['summary'] = 'VLAN 10 설정을 확인한다.'
        r = self.store.ingest(changed, self.data)
        self.assertEqual(r['holds'], ['new reason'])

    def test_released_hold_reappears_after_user_content_change(self):
        r = self.release()
        revised = self.store.revise(r['id'], r['snapshot'], [{'path': '/summary', 'value': '검토 이후 변경한 VLAN 설정이다.'}])
        self.assertEqual(revised['holds'], ['review reason'])
        self.assertEqual(revised['status'], 'pending')
        self.assertEqual(self.store.approved()['materials'], [])

    def test_changed_original_reapplies_hold_and_keeps_history(self):
        old = self.release()
        data, analysis = material(extra='new original')
        r = self.store.ingest(analysis, data)
        self.assertTrue(r['holds']); self.assertNotEqual(r['id'], old['id'])
        self.assertEqual(self.store.get(old['id'])['status'], 'approved')

    def test_only_affected_concept_is_invalidated(self):
        first = self.approve()
        data, analysis = material('second.txt', 'second source')
        analysis['concepts'][0]['name'] = 'OTHER'
        analysis['practice'][0]['related_concepts'] = ['OTHER']
        second = self.approve(data, analysis)
        policy = self.store.policy(); policy['concept_aliases']['VLAN'] = 'Virtual LAN'
        self.store.set_policy(policy)
        self.assertEqual(self.store.get(first['id'])['status'], 'pending')
        self.assertEqual(self.store.get(second['id'])['snapshot'], second['snapshot'])
        self.assertEqual([r['id'] for r in self.store.approved()['materials']], [second['id']])

    def test_actual_classification_change_invalidates_without_analysis(self):
        r = self.approve()
        policy = self.store.policy(); policy.pop('curriculum')
        self.store.set_policy(policy)
        changed = self.store.get(r['id'])
        self.assertEqual(changed['status'], 'pending')
        self.assertEqual(changed['analysis'], r['analysis'])
        self.assertNotEqual(changed['classification']['paths'], r['classification']['paths'])

    def test_display_metadata_preserves_approval_and_user_content(self):
        r = self.approve()
        r = self.store.revise(r['id'], r['snapshot'], [{'path': '/summary', 'value': '사용자가 검토한 VLAN 설정이다.'}])
        r = self.store.decide(r['id'], r['snapshot'], 'approve')
        policy = self.store.policy(); policy['curriculum']['title'] += ' updated'
        self.store.set_policy(policy)
        same = self.store.ingest(self.analysis, self.data)
        self.assertEqual(same['snapshot'], r['snapshot'])
        self.assertEqual(same['analysis'], r['analysis'])
        self.assertEqual(len(self.store.approved()['materials']), 1)

    def test_same_conditions_reuse_and_changed_prompt_block(self):
        inventory = self.inventory([(self.data, self.analysis)])
        engine = OfflineProvider(self.analysis)
        self.assertEqual(run_batch(inventory, self.store.root, provider_factory=lambda d: engine)['new_successes'], 1)
        r = self.store.list()[0]; self.store.decide(r['id'], r['snapshot'], 'approve')
        again = run_batch(inventory, self.store.root, provider_factory=lambda d: engine)
        self.assertEqual(again['reused'], 1); self.assertEqual(engine.calls, 1)
        with patch('analyzer.cache.build_prompt', return_value=[{'role': 'user', 'content': 'changed'}]):
            changed = run_batch(inventory, self.store.root, provider_factory=lambda d: engine)
            saved = run_batch(inventory, self.store.root)
        self.assertEqual(changed['blocked'], 1); self.assertEqual(saved['blocked'], 1)
        self.assertEqual(engine.calls, 1); self.assertEqual(changed['new_api_attempts'], 0)
        self.assertEqual(len(self.store.approved()['materials']), 1)

    def test_changed_model_schema_processing_and_unknown_conditions_block(self):
        inventory = self.inventory([(self.data, self.analysis)])
        engine = OpenAIProvider(self.schema)
        context, _ = context_for(self.data, engine, self.schema)
        r = self.store.ingest(self.analysis, self.data, analysis_context=context)
        with patch.object(OpenAIProvider, 'generate', side_effect=AssertionError('API forbidden')):
            same = run_batch(inventory, self.store.root, provider='openai')
            changed = run_batch(inventory, self.store.root, provider='openai', model='gpt-6.1-sol')
            with patch('analyzer.cache.processing_digest', return_value='changed'):
                processing = run_batch(inventory, self.store.root, provider='openai')
            schema = copy.deepcopy(self.schema); schema['title'] = 'changed'
            with patch('analyzer.batch.load_schema', return_value=schema):
                schema_report = run_batch(inventory, self.store.root, provider='openai')
            with self.store.db() as db:
                r.pop('analysis_context'); self.store._save(db, r)
            unknown = run_batch(inventory, self.store.root, provider='openai')
        self.assertEqual(same['reused'], 1)
        for report in (changed, processing, schema_report, unknown):
            self.assertEqual(report['blocked'], 1); self.assertEqual(report['new_api_attempts'], 0)

    def test_explicit_reanalysis_updates_context_and_content(self):
        inventory = self.inventory([(self.data, self.analysis)])
        engine = OfflineProvider(self.analysis)
        run_batch(inventory, self.store.root, provider_factory=lambda d: engine)
        r = self.store.list()[0]; self.store.decide(r['id'], r['snapshot'], 'approve')
        changed = copy.deepcopy(self.analysis); changed['summary'] = 'VLAN 10 설정을 확인한다.'
        new_engine = OfflineProvider(changed)
        report = run_batch(inventory, self.store.root, provider_factory=lambda d: new_engine, reanalyze=True, retry_failed=True)
        self.assertEqual(report['new_successes'], 1)
        self.assertEqual(self.store.get(r['id'])['status'], 'pending')
        same = run_batch(inventory, self.store.root)
        self.assertEqual(same['reused'], 1); self.assertEqual(new_engine.calls, 1)

    def test_status_is_read_only_and_missing_is_not_zero(self):
        self.approve(); before = self.store.path.read_bytes()
        self.assertEqual(status.approval_status(self.store.path)['approved'], 1)
        self.assertEqual(before, self.store.path.read_bytes())
        missing = self.root/'missing.sqlite3'
        self.assertFalse(status.approval_status(missing)['available'])
        self.assertFalse(missing.exists())
        self.assertNotIn('approved', status.approval_status(missing))
        section = status.handoff(section='19.3')
        self.assertTrue(section.startswith('### 19.3'))
        self.assertNotIn('### 19.4', section)

    def test_real_database_copy_metrics_and_original_unchanged(self):
        original = status.DEFAULT_DB
        if not original.is_file():
            self.skipTest('local approval database unavailable')
        before = hashlib.sha256(original.read_bytes()).hexdigest()
        copied = self.root/'copy'; copied.mkdir()
        with closing(sqlite3.connect(original.as_uri()+'?mode=ro', uri=True)) as source:
            with closing(sqlite3.connect(copied/'library.sqlite3')) as target:
                source.backup(target)
        store = Workspace(copied)
        records = store.list()
        snapshots = {r['id']: r['snapshot'] for r in records}
        baseline_approved = sum(r['status'] == 'approved' for r in records)
        policy = store.policy(); policy['concept_aliases']['unused-efficiency-probe'] = 'unused-value'
        legacy_reholds = sum(r['analysis']['source']['filename'] in policy['publication_holds'] and not r['holds'] for r in records)
        store.set_policy(policy)
        updated = store.list()
        invalidated = sum(r['snapshot'] != snapshots[r['id']] for r in updated)
        reholds = sum(bool(r['holds']) for r in updated)
        self.assertEqual(invalidated, 0); self.assertEqual(reholds, 0)
        self.assertEqual(len(store.approved()['materials']), baseline_approved)
        full = status.handoff(section='19'); short = status.handoff()
        self.assertEqual(before, hashlib.sha256(original.read_bytes()).hexdigest())
        print('EFFICIENCY_METRICS '+json.dumps({
            'copied_materials': len(records), 'unrelated_policy_reapprovals_before': baseline_approved,
            'unrelated_policy_reapprovals_after': invalidated,
            'same_reason_reholds_before': legacy_reholds, 'same_reason_reholds_after': reholds,
            'handoff_full_lines': len(full.splitlines()), 'handoff_short_lines': len(short.splitlines()),
            'handoff_full_chars': len(full), 'handoff_short_chars': len(short),
            'original_db_sha256_unchanged': True, 'paid_api_calls': 0}, ensure_ascii=False))
