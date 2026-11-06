"""Polling stays light; explicit inspection and publication keep content checks."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import analyzer.notion_intake as intake
import collector.main as collector
from analyzer.management import Manager
from analyzer.workspace import Workspace
from test_management import FakeKeys
from test_organizer import OrganizerTests


class StatusIntakeEfficiencyTests(unittest.TestCase):
    def setUp(self):
        OrganizerTests.setUp(self)
        self.source = self.root/'source'
        self.source.mkdir()
        self.file = self.source/self.data['filename']
        self.file.write_bytes(self.data['extracted_text'].encode('utf-8'))
        record = self.store.ingest(self.analysis, self.data)
        self.store.decide(record['id'], record['snapshot'], 'approve')
        self.manager = Manager(self.store.root, self.source, self.root/'publication', keys=FakeKeys())

    def test_initial_poll_requires_full_inspection(self):
        self.assertTrue(self.manager.progress()['refresh_required'])
        self.manager.status()
        self.assertFalse(self.manager.progress()['refresh_required'])

    def test_idle_poll_does_not_read_bodies_validate_library_or_read_keys(self):
        self.manager.status()
        with (patch('analyzer.management.inspect', side_effect=AssertionError('inspection')),
             patch.object(collector, 'extract_text', side_effect=AssertionError('extraction')),
             patch.object(intake, 'calculate_sha256', side_effect=AssertionError('hash')),
             patch.object(Workspace, 'reusable', side_effect=AssertionError('validation')),
             patch.object(self.manager.keys, 'read', side_effect=AssertionError('key')),
             patch('sqlite3.connect', side_effect=AssertionError('DB read'))):
            for _ in range(5):
                result = self.manager.get('/api/manage/progress')
                self.assertFalse(result['refresh_required'])
                self.assertNotIn('intake', result)
                self.assertNotIn('key_saved', result)

    def test_added_modified_renamed_deleted_and_unsupported_inputs_trigger_refresh(self):
        self.manager.status()
        added = self.source/'new.txt'
        added.write_text('new data', encoding='utf-8')
        self.assertTrue(self.manager.progress()['refresh_required'])
        self.assertEqual(self.manager.status()['intake']['counts']['new'], 1)
        added.write_text('modified data longer', encoding='utf-8')
        self.assertTrue(self.manager.progress()['refresh_required'])
        self.manager.status()
        renamed = self.source/'renamed.txt'
        added.rename(renamed)
        self.assertTrue(self.manager.progress()['refresh_required'])
        self.manager.status()
        renamed.unlink()
        self.assertTrue(self.manager.progress()['refresh_required'])
        self.manager.status()
        (self.source/'nested').mkdir()
        (self.source/'nested'/'notes.pdf').write_bytes(b'unsupported input')
        self.assertTrue(self.manager.progress()['refresh_required'])
        self.assertEqual(self.manager.status()['intake']['counts']['unsupported'], 1)

    def test_external_approval_change_and_wal_hint_trigger_refresh(self):
        self.manager.status()
        record = self.store.list()[0]
        self.store.decide(record['id'], record['snapshot'], 'hold')
        self.assertTrue(self.manager.progress()['refresh_required'])
        self.assertEqual(self.manager.status()['intake']['counts'], {'held': 1})
        Path(str(self.store.path)+'-wal').write_bytes(b'test metadata only')
        self.assertTrue(self.manager.progress()['refresh_required'])

    def test_changes_during_full_inspection_are_not_acknowledged_as_fresh(self):
        original = intake.inspect
        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            (self.source/'arrived.txt').write_text('arrived during inspection', encoding='utf-8')
            return result
        with patch('analyzer.management.inspect', side_effect=changed):
            self.manager.status()
        self.assertTrue(self.manager.progress()['refresh_required'])
        self.assertEqual(self.manager.status()['intake']['counts']['new'], 1)
        self.assertFalse(self.manager.progress()['refresh_required'])

    def test_inspection_reuses_collector_hashes_and_enumerates_once(self):
        with (patch.object(collector, 'calculate_sha256', wraps=collector.calculate_sha256) as hashes,
             patch.object(intake, 'calculate_sha256', wraps=intake.calculate_sha256) as manifest_hashes,
             patch.object(intake, 'scan_all_files', wraps=intake.scan_all_files) as scans):
            report, _ = intake.inspect(self.source, self.store.root)
        self.assertEqual(hashes.call_count, 2)  # before/after extraction remain
        self.assertEqual(manifest_hashes.call_count, 0)
        self.assertEqual(scans.call_count, 1)
        self.assertEqual(report['source_manifest'], intake.source_manifest(self.source))

    def test_fresh_manifest_detects_same_size_content_change_with_restored_mtime(self):
        before = intake.source_manifest(self.source)
        stat = self.file.stat()
        original = self.file.read_bytes()
        self.file.write_bytes(original.replace(b'vlan', b'VLAN', 1))
        os.utime(self.file, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        self.assertEqual(self.file.stat().st_size, stat.st_size)
        self.assertNotEqual(before, intake.source_manifest(self.source))

    def test_changed_after_extraction_does_not_enter_the_same_manifest(self):
        original = intake.process_file
        def changed(path):
            row = original(path)
            path.write_text('changed after extraction', encoding='utf-8')
            return row
        with patch.object(intake, 'process_file', side_effect=changed):
            report, _ = intake.inspect(self.source, self.store.root)
        self.assertNotEqual(report['source_manifest'], intake.source_manifest(self.source))

    def test_prepare_reuses_initial_collection_without_a_paid_call(self):
        (self.source/'unprocessed.txt').write_text('no cached result', encoding='utf-8')
        before = self.store.path.read_bytes()
        with (patch.object(intake, 'collect', wraps=intake.collect) as collects,
             patch('analyzer.openai_provider.OpenAIProvider.generate', side_effect=AssertionError('paid call'))):
            result = intake.prepare_sources(self.store.root, self.root/'unused_target.json',
                self.root/'unused_home.json', self.root/'publication', self.root/'prepared', self.source)
        self.assertIsNone(result['package'])
        self.assertEqual(collects.call_count, 1)
        self.assertEqual(result['new_api_attempts'], 0)
        self.assertEqual(self.store.path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
