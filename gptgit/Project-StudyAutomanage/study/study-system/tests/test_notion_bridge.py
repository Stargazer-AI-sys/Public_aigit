import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from analyzer.notion_mcp import NotionMCP
from analyzer.notion_sync import DeliveryError, deliver_plan, make_plan
from analyzer.workspace import Workspace
from test_notion_mcp import FakePlugin, binding
from test_organizer import material

SPEC = importlib.util.spec_from_file_location('bridge_verify', Path(__file__).resolve().parents[1]/'tools/notion_bridge/verify.py')
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class BridgeVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Workspace(self.root/'library')
        data, analysis = material()
        record = self.store.ingest(analysis, data)
        self.store.decide(record['id'], record['snapshot'], 'approve')
        self.target = binding()
        self.plugin = FakePlugin(self.target)
        self.outbox = self.root/'outbox'
        remote = NotionMCP(self.target, self.outbox, self.plugin)
        report = deliver_plan(make_plan(self.store, target=self.target), self.store, remote,
                              self.outbox, target=self.target)
        self.assertFalse(report['errors'])
        self.target_file = self.root/'target.json'
        self.target_file.write_text(json.dumps(self.target), encoding='utf-8')
        self.readback = self.root/'readback.json'
        self.save_snapshot()

    def save_snapshot(self):
        rows = [{'structuredContent': self.plugin('fetch', {'id': pid})} for pid in self.plugin.pages]
        self.readback.write_text(json.dumps(rows), encoding='utf-8')
        return rows

    def audit(self):
        return VERIFY.audit(self.target_file, self.outbox, self.readback)

    def test_saved_snapshot_audit_does_not_write_ledger_or_call_plugin(self):
        before = (self.outbox/'delivery.sqlite3').read_bytes()
        calls = len(self.plugin.calls)
        report = self.audit()
        self.assertTrue(report['ok'], report)
        self.assertFalse(report['remote_freshness_checked'])
        self.assertEqual(len(self.plugin.calls), calls)
        self.assertEqual((self.outbox/'delivery.sqlite3').read_bytes(), before)

    def test_body_edit_is_detected_even_when_managed_digest_did_not_change(self):
        next(iter(self.plugin.pages.values()))['body'] += '\nmanual edit'
        self.save_snapshot()
        report = self.audit()
        self.assertFalse(report['ok'])
        codes = {x['code'] for x in report['errors']}
        self.assertIn('STAMP_MISMATCH', codes)
        self.assertIn('BODY_MISMATCH', codes)

    def test_missing_duplicate_and_destination_mismatch_are_not_success(self):
        rows = self.save_snapshot()
        self.readback.write_text(json.dumps(rows[:-1]+[rows[0]]), encoding='utf-8')
        report = self.audit()
        codes = {x['code'] for x in report['errors']}
        self.assertIn('MISSING_READBACK', codes)
        self.assertIn('DUPLICATE_SYNC_KEY', codes)
        self.target['collections']['material']['data_source_id'] = 'different'
        self.target_file.write_text(json.dumps(self.target), encoding='utf-8')
        with self.assertRaises(DeliveryError):
            self.audit()

    def test_native_format_normalization_preserves_code_indentation(self):
        written = '\t```text\n\tfirst\n\t  indented\n\t```'
        fetched = '\t```plain text\nfirst\n  indented\n\t```'
        self.assertEqual(VERIFY.body_normalized(written), VERIFY.body_normalized(fetched))
        self.assertNotEqual(VERIFY.body_normalized(fetched),
                            VERIFY.body_normalized(fetched.replace('  indented', 'indented')))
