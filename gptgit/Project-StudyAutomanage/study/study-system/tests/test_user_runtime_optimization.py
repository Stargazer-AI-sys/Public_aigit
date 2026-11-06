"""Run against user_app via an isolated runner; offline regression oracles."""
import copy
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import random
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from analyzer import classification, workspace, notion_intake, notion_front, notion_reader
from analyzer.cache import processing_digest
from analyzer.core import AnalysisError

ROOT = Path(__file__).resolve().parents[3]
USER = ROOT/'user_app'
RUNTIME = USER/'study/study-system'
BACKUP = ROOT/'archive/versions/2026-10-22_user_optimization/analyzer'


def baseline(name):
    spec = importlib.util.spec_from_file_location('analyzer._before_'+name, BACKUP/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UserRuntimeOptimizationTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(Path(workspace.__file__).is_relative_to(RUNTIME))
        self.store = workspace.Workspace(RUNTIME/'output/knowledge_base', read_only=True)

    def test_catalog_approvals_and_locations_match_baseline(self):
        old = baseline('workspace').Workspace(self.store.root, read_only=True)
        self.assertEqual(self.store.list(current=False), old.list(current=False))
        self.assertEqual(self.store.catalog(), old.catalog())
        self.assertEqual(self.store.approved(), old.approved())

    def test_relation_order_and_duplicates_match_baseline(self):
        rng = random.Random(14)
        base = self.store.list()[0]
        old = baseline('classification')
        for size in (0, 1, 8, 80):
            records = []
            for n in range(size):
                record = copy.deepcopy(base)
                record['id'] = 'id'+str(n)
                record['analysis']['source']['material_id'] = str(rng.randrange(12))
                record['analysis']['concepts'] = [{'name': rng.choice(['SSH', 'ssh', 'routing', 'unique'+str(n)]),
                                                   'description': str(rng.randrange(4))} for _ in range(3)]
                records.append(record)
            self.assertEqual(classification.knowledge_index(records, self.store.policy()),
                             old.knowledge_index(records, self.store.policy()))

    def test_intake_uses_two_connections_and_no_relationship_index(self):
        connect = workspace.sqlite3.connect
        with patch.object(workspace.sqlite3, 'connect', wraps=connect) as calls, \
             patch.object(workspace, 'knowledge_index', side_effect=AssertionError('unused index')):
            result, _ = notion_intake.inspect(USER/'study/sourcefile', self.store.root)
        self.assertEqual(result['counts'], {'approved': 11})
        self.assertEqual(calls.call_count, 2)

    def test_policy_recomputed_once_and_changed_policy_blocks(self):
        records = self.store.list()
        policy = self.store.policy()
        with patch.object(workspace.Workspace, 'policy_effect', wraps=workspace.Workspace.policy_effect) as calls:
            approved = self.store.approved_records(records=records, policy=policy)
        self.assertEqual(calls.call_count, len(approved))
        changed = copy.deepcopy(policy)
        name = approved[0]['analysis']['concepts'][0]['name']
        changed['concept_aliases'][name] = '사용자가 변경한 개념명'
        tracked = copy.deepcopy(approved[0])
        tracked['policy_effect'] = workspace.Workspace.policy_effect(tracked['analysis'], policy)
        self.assertFalse(self.store.approved_records(records=[tracked], policy=changed))
        # An unrelated record must not acquire approval through a supplied list.
        record = copy.deepcopy(approved[0])
        record['approved_snapshot'] = 'stale'
        self.assertEqual(self.store.approved_records(records=[record], policy=changed), [])
        record = copy.deepcopy(approved[0]); record['current'] = False
        self.assertEqual(self.store.approved_records(records=[record], policy=policy), [])

    def test_reusable_keeps_content_and_integrity_checks(self):
        _, rows = notion_intake.inspect(USER/'study/sourcefile', self.store.root)
        data = notion_intake.from_collector(rows[0])
        record = self.store.reusable(data)
        self.assertEqual(record, self.store.validate_reusable(data, record))
        changed = copy.deepcopy(data); changed['extracted_text'] += 'changed'
        with self.assertRaises(AnalysisError):
            self.store.validate_reusable(changed, record)
        corrupt = copy.deepcopy(record); corrupt['snapshot'] = 'wrong'
        with self.assertRaises(AnalysisError):
            self.store.validate_reusable(data, corrupt)

    def test_next_request_observes_external_hold(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'output') as directory:
            target = Path(directory)/'library.sqlite3'
            with closing(sqlite3.connect(self.store.path.as_uri()+'?mode=ro', uri=True)) as source:
                with closing(sqlite3.connect(target)) as db:
                    source.backup(db)
            copied = workspace.Workspace(directory, read_only=True)
            first, _ = notion_intake.inspect(USER/'study/sourcefile', directory)
            self.assertEqual(first['counts'], {'approved': 11})
            with closing(sqlite3.connect(target)) as db:
                mid, raw = db.execute('SELECT id,record FROM materials LIMIT 1').fetchone()
                record = json.loads(raw); record['status'] = 'held'
                db.execute('UPDATE materials SET record=? WHERE id=?', (json.dumps(record), mid))
                db.commit()
            second, _ = notion_intake.inspect(USER/'study/sourcefile', directory)
            self.assertEqual(second['counts']['held'], 1)

    def test_analysis_processing_identity_unchanged(self):
        import hashlib
        development = ROOT/'study/study-system/analyzer'
        files = ['core.py','quality.py','concept_refs.py','knowledge.py','schemas.py','comment_review.py','auxiliary.py']
        for provider in ('mock-file', 'openai'):
            names = files + (['openai_provider.py','evidence.py'] if provider == 'openai' else [])
            self.assertEqual(processing_digest(provider), hashlib.sha256(b''.join((development/name).read_bytes() for name in names)).hexdigest())

    def test_front_pages_and_reader_equal_baseline(self):
        from analyzer.notion_sync import make_plan
        from analyzer.notion_reader import refresh_reader_target
        runtime = RUNTIME
        target = json.loads((runtime/'config/notion_target.json').read_text(encoding='utf-8'))
        target = refresh_reader_target(target, runtime/'output/notion_live/outbox')
        home = json.loads((runtime/'config/notion_home.json').read_text(encoding='utf-8'))
        plan = make_plan(self.store, target=target)
        expected = baseline('notion_front').render_front_pages(plan, self.store, target, home)
        self.assertEqual(notion_front.render_front_pages(plan, self.store, target, home), expected)
        old_reader = baseline('notion_reader')
        with patch.object(notion_reader, 'build_reader', old_reader.build_reader):
            self.assertEqual(notion_front.render_front_pages(plan, self.store, target, home), expected)


if __name__ == '__main__':
    unittest.main()
