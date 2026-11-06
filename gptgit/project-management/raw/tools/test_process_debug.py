"""Offline behavioral tests; all records are created in temporary projects."""
import json
from pathlib import Path
import tempfile
import unittest

import process_debug as debug


class ProcessDebugTests(unittest.TestCase):
    def setUp(self):
        test_root = Path.cwd() / '.local' / 'test-tmp'
        self.assertTrue(test_root.resolve().is_relative_to(Path.cwd().resolve()))
        test_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='process-debug-', dir=test_root)
        self.root = Path(self.temp.name)
        self.assertTrue(self.root.resolve().is_relative_to(Path.cwd().resolve()))
        self.addCleanup(self.temp.cleanup)

    def call(self, command, *args, response='r1'):
        return debug.execute(debug.parser().parse_args([command, '--run', 'run1', '--response', response, *args]), self.root)

    def bind(self, alias='master', actual='session1', response='r1'):
        return self.call('bind', '--session', alias, '--session-id', actual, '--task', 'DEBUG-01', '--provider', 'codex', response=response)

    def manual(self, name, total):
        path = self.root / name
        path.write_text(json.dumps({'total': total, 'last': {'input_tokens': 700}, 'context_window': 100000}), encoding='utf-8')
        return name

    def snapshot(self, phase, file=None, alias='master'):
        args = ['--session', alias, '--phase', phase]
        if file:
            args += ['--manual', file]
        return self.call('snapshot', *args)

    def test_run_toggle_persists_and_off_preserves_records(self):
        self.call('on')
        self.assertTrue(self.call('status', response='r2')['enabled'])
        self.bind()
        self.snapshot('start')
        before = (self.root / 'docs/workflows/run1/debug/state.json').read_text(encoding='utf-8')
        self.call('off', response='r2')
        self.assertEqual(self.call('report')['summary'], 'off')
        saved = json.loads((self.root / 'docs/workflows/run1/debug/state.json').read_text(encoding='utf-8'))
        self.assertIn('start', saved['responses']['r1']['sessions']['master']['snapshots'])
        self.assertIn('snapshots', before)

    def test_document_exact_range_hash_and_session(self):
        self.call('on')
        self.bind()
        (self.root / 'guide.md').write_bytes(b'# Header\nFirst\nSecond\nThird\n')
        result = self.call('read', '--session', 'master', '--path', 'guide.md', '--start', '2', '--end', '3', '--section', 'Header', '--reason', 'Check instructions')
        self.assertEqual(result['content'], 'First\nSecond')
        self.assertEqual(result['task'], 'DEBUG-01')
        self.assertEqual(result['sha256'], debug.hashlib.sha256((self.root / 'guide.md').read_bytes()).hexdigest())
        state = json.loads((self.root / 'docs/workflows/run1/debug/state.json').read_text(encoding='utf-8'))
        self.assertNotIn('content', state['responses']['r1']['reads'][0])

    def test_path_traversal_and_secrets_refused_without_echo(self):
        self.bind()
        for path in ('../outside.md', '/outside.md', 'C:/outside.md', 'docs\\..\\outside.md'):
            with self.assertRaises(ValueError):
                self.call('read', '--session', 'master', '--path', path, '--start', '1', '--end', '1', '--reason', 'check')
        (self.root / 'bad.md').write_text('api_key=verysecret123456', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'suspected credentials'):
            self.call('read', '--session', 'master', '--path', 'bad.md', '--start', '1', '--end', '1', '--reason', 'check')
        with self.assertRaises(ValueError):
            debug.local_path(self.root, '../out')

    def test_stream_extracts_only_numeric_usage_and_verifies_session(self):
        self.call('on')
        log = self.root / 'log.jsonl'
        rows = [{'type': 'session_meta', 'payload': {'id': 'session1'}},
                {'type': 'response_item', 'payload': {'text': 'SECRET_TRANSCRIPT'}},
                {'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {
                    'total_token_usage': {'input_tokens': 100, 'output_tokens': 10, 'total_tokens': 110, 'secret': 'SECRET_VALUE'},
                    'last_token_usage': {'input_tokens': 80}, 'model_context_window': 1000}}}]
        log.write_text('\n'.join(json.dumps(row) for row in rows) + '\n{partial', encoding='utf-8')
        usage, status = debug.codex_usage(log, 'session1')
        self.assertEqual(status, 'collected')
        self.assertEqual(usage['total']['total_tokens'], 110)
        self.assertNotIn('SECRET', json.dumps(usage))
        self.assertEqual(debug.codex_usage(log, 'wrong')[1], 'unknown_session_mismatch_or_missing')
        self.bind()
        self.call('snapshot', '--session', 'master', '--phase', 'start', '--codex-log', str(log))
        self.assertNotIn('SECRET', (self.root / 'docs/workflows/run1/debug/state.json').read_text(encoding='utf-8'))

    def test_delta_subsets_context_and_no_double_count(self):
        self.call('on')
        self.bind()
        self.snapshot('start', self.manual('a.json', dict(zip(debug.FIELDS, (100, 40, 20, 5, 120)))))
        self.snapshot('end', self.manual('b.json', dict(zip(debug.FIELDS, (300, 100, 70, 25, 370)))))
        result = self.call('report')
        self.assertEqual(result['aggregate_usage_delta'], dict(zip(debug.FIELDS, (200, 60, 50, 20, 250))))
        self.assertEqual(result['sessions'][0]['context']['last_input_tokens'], 700)
        self.assertEqual(result['provisional_load_proxy']['level'], 'low')
        with self.assertRaisesRegex(ValueError, 'already recorded'):
            self.snapshot('end')

    def test_missing_or_reset_usage_is_unknown_not_zero(self):
        self.call('on')
        self.bind()
        self.snapshot('start')
        self.snapshot('end')
        result = self.call('report')
        self.assertIsNone(result['aggregate_usage_delta']['total_tokens'])
        self.assertEqual(result['provisional_load_proxy']['level'], 'unknown')
        self.assertIsNone(debug.delta({'total_tokens': 100}, {'total_tokens': 10})['total_tokens'])
        self.assertIsNone(debug.counters({'input_tokens': True})['input_tokens'])

    def test_alias_cannot_be_rebound_or_double_counted(self):
        self.bind()
        with self.assertRaisesRegex(ValueError, 'already bound'):
            self.bind(actual='changed')
        with self.assertRaisesRegex(ValueError, 'already has an alias'):
            self.bind(alias='duplicate')

    def test_lock_protects_state_and_failed_operation_is_atomic(self):
        self.call('on')
        directory = self.root / 'docs/workflows/run1/debug'
        before = (directory / 'state.json').read_bytes()
        with debug.state_file(self.root, 'run1'):
            with self.assertRaisesRegex(ValueError, 'locked'):
                self.call('off')
        before = (directory / 'state.json').read_bytes()
        with self.assertRaises(ValueError):
            self.call('snapshot', '--session', 'missing', '--phase', 'end')
        self.assertEqual(before, (directory / 'state.json').read_bytes())
        self.assertFalse((directory / '.lock').exists())

    def test_unknown_session_does_not_borrow_previous_response(self):
        self.bind()
        with self.assertRaises(ValueError):
            self.call('snapshot', '--session', 'master', '--phase', 'start', response='r2')

    def test_changed_source_is_unknown(self):
        self.call('on')
        self.bind()
        self.snapshot('start', self.manual('a.json', {'total_tokens': 150}))
        self.snapshot('end', self.manual('b.json', {'total_tokens': 1000}))
        with debug.state_file(self.root, 'run1') as state:
            snap = state['responses']['r1']['sessions']['master']['snapshots']['start']
            snap.update(source='codex_token_count', status='collected')
        result = self.call('report')
        self.assertIsNone(result['aggregate_usage_delta']['total_tokens'])
        self.assertIsNone(result['known_partial_usage_delta']['total_tokens'])
        self.assertEqual(result['known_session_count']['total_tokens'], 0)

    def test_off_snapshots_are_not_retroactively_counted(self):
        self.bind()
        self.snapshot('start', self.manual('a.json', {'total_tokens': 150}))
        self.snapshot('end', self.manual('b.json', {'total_tokens': 200}))
        self.call('on', response='r4')
        result = self.call('report')
        self.assertIsNone(result['aggregate_usage_delta']['total_tokens'])
        self.assertEqual(result['sessions'][0]['provisional_load_proxy']['level'], 'unknown')
        self.assertIsNone(result['sessions'][0]['context']['last_input_tokens'])

    def test_mid_response_toggle_keeps_baseline_but_invalidates_interval(self):
        self.call('on')
        self.bind()
        self.snapshot('start', self.manual('a.json', {'total_tokens': 150}))
        self.call('off', response='r2')
        self.call('on', response='r2')
        self.snapshot('end', self.manual('b.json', {'total_tokens': 200}))
        self.assertIsNone(self.call('report')['aggregate_usage_delta']['total_tokens'])
        with debug.state_file(self.root, 'run1') as state:
            self.assertEqual(state['responses']['r1']['sessions']['master']['snapshots']['start']['total']['total_tokens'], 150)

    def test_off_read_is_not_collected(self):
        self.bind()
        (self.root / 'guide.md').write_text('Example', encoding='utf-8')
        result = self.call('read', '--session', 'master', '--path', 'guide.md', '--start', '1', '--end', '1', '--reason', 'check')
        self.assertFalse(result['debug_recorded'])
        self.call('on')
        self.assertEqual(self.call('report')['reads'], [])


if __name__ == '__main__':
    unittest.main()
