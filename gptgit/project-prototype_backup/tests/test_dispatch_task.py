"""Mock-only dispatcher checks. No Herdr, CLI, account, or model calls."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import dispatch_task


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dispatch-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'tools').mkdir()
        (self.root / 'config').mkdir()
        (self.root / 'spec.md').write_text('approved fixture, not real authorization\n', encoding='utf-8')
        (self.root / 'plan.md').write_text('fixture plan\n', encoding='utf-8')
        (self.root / 'config/runtime.example.json').write_text(json.dumps({'herdr': 'fake-herdr', 'powershell': 'fake-pwsh'}), encoding='utf-8')
        self.packet_path = self.root / 'packet.json'
        self.packet = {
            'task_id': 'TEST-1', 'role': 'planner', 'goal': 'fixture',
            'work_spec': 'spec.md', 'development_plan': None,
            'acceptance': ['fixture'], 'inputs': [{'path': 'spec.md', 'reason': 'fixture'}],
            'write_scope': ['plan.md'], 'constraints': ['no models'],
            'expected_output': 'fixture plan', 'session': {'provider': 'codex', 'actual_id': None},
        }
        self.write_packet()

    def write_packet(self):
        self.packet_path.write_text(json.dumps(self.packet), encoding='utf-8')

    def call_main(self, apply=False, env=None, effect=None):
        argv = ['dispatch_task.py', str(self.packet_path)] + (['--apply'] if apply else [])
        with patch.object(dispatch_task, '__file__', str(self.root / 'tools/dispatch_task.py')), \
             patch.object(sys, 'argv', argv), \
             patch.dict(dispatch_task.os.environ, env or {}, clear=True), \
             patch.object(dispatch_task.subprocess, 'run', side_effect=effect) as run, \
             contextlib.redirect_stdout(io.StringIO()) as out:
            code = dispatch_task.main()
            return code, run.call_count, out.getvalue()

    def receipt(self):
        files = list((self.root / '.local/dispatch').glob('*.json'))
        self.assertEqual(len(files), 1)
        return json.loads(files[0].read_text(encoding='utf-8'))

    def success(self, *args, **kwargs):
        command = args[0]
        if command[1:3] == ['pane', 'list']:
            result = {'panes': [{'pane_id': 'w1:p1', 'cwd': str(self.root)}]}
        elif command[1:3] == ['pane', 'split']:
            result = {'pane': {'pane_id': 'w1:p2'}}
        elif command[1:3] == ['pane', 'process-info']:
            result = {'process_info': {'pane_id': 'w1:p2', 'shell_pid': 123, 'foreground_processes': [{'pid': 123, 'name': 'pwsh.exe', 'cwd': str(self.root)}]}}
        else:
            result = {}
        return subprocess.CompletedProcess(command, 0, json.dumps({'result': result}), '')

    def test_dry_run_calls_no_herdr_and_creates_no_receipt(self):
        code, calls, output = self.call_main()
        self.assertEqual((code, calls), (0, 0))
        self.assertFalse(json.loads(output)['model_called'])
        self.assertFalse((self.root / '.local').exists())

    def test_apply_missing_caller_context_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Herdr caller context'):
            self.call_main(apply=True)
        self.assertFalse((self.root / '.local').exists())

    def test_duplicate_receipt_blocks_second_dispatch(self):
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1'}
        self.assertEqual(self.call_main(True, env, self.success)[:2], (0, 4))
        self.assertEqual(self.receipt()['status'], 'submitted_unverified')
        with self.assertRaises(FileExistsError):
            self.call_main(True, env, self.success)
        self.assertEqual(self.receipt()['status'], 'submitted_unverified')

    def test_timeout_records_uncertain_and_no_retry(self):
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1'}
        failure = subprocess.TimeoutExpired(['fake-herdr'], 45)
        with patch.object(dispatch_task.subprocess, 'run', side_effect=failure) as run:
            # call_main also patches run; count the nested failure callback.
            calls = []
            def timeout(*args, **kwargs):
                if args[0][1:3] == ['pane', 'list']:
                    return self.success(*args, **kwargs)
                calls.append(args)
                raise failure
            with self.assertRaises(subprocess.TimeoutExpired):
                self.call_main(True, env, timeout)
            self.assertEqual(len(calls), 1)
        self.assertEqual(self.receipt()['status'], 'uncertain_inspect_required')

    def test_documenter_is_blocked_before_receipt(self):
        self.packet.update(role='documenter', development_plan='plan.md', write_scope=[], session={'provider': 'hermes', 'actual_id': None})
        self.write_packet()
        with self.assertRaisesRegex(ValueError, 'Hermes adapter not yet implemented'):
            self.call_main(True, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1'})
        self.assertFalse((self.root / '.local').exists())

    def test_nonidle_new_pane_receipt_uncertain_no_run(self):
        calls = []
        def nonidle(*args, **kwargs):
            calls.append(args[0][1:3])
            if args[0][1:3] == ['pane', 'process-info']:
                return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': {'process_info': {'shell_pid': 123, 'foreground_processes': [{'pid': 999, 'name': 'claude.exe'}]}}}), '')
            return self.success(*args, **kwargs)
        with self.assertRaisesRegex(RuntimeError, 'not an idle PowerShell'):
            self.call_main(True, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1'}, nonidle)
        self.assertNotIn(['pane', 'run'], calls)
        self.assertEqual(self.receipt()['status'], 'uncertain_inspect_required')


    def test_mismatched_caller_project_blocks_before_claim(self):
        calls = []
        def mismatch(*args, **kwargs):
            calls.append(args[0][1:3])
            return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': {'panes': [{'pane_id': 'w1:p1', 'cwd': str(self.root / 'other')} ]}}), '')
        with self.assertRaisesRegex(ValueError, 'caller pane project mismatch'):
            self.call_main(True, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1'}, mismatch)
        self.assertEqual(calls, [['pane', 'list']])
        self.assertFalse((self.root / '.local').exists())

    def test_split_existing_identity_is_uncertain_without_command(self):
        calls = []
        def reused(*args, **kwargs):
            calls.append(args[0][1:3])
            if args[0][1:3] == ['pane', 'split']:
                return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': {'pane': {'pane_id': 'w1:p1'}}}), '')
            return self.success(*args, **kwargs)
        with self.assertRaisesRegex(RuntimeError, 'new pane identity'):
            self.call_main(True, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1'}, reused)
        self.assertNotIn(['pane', 'run'], calls)
        self.assertEqual(self.receipt()['status'], 'uncertain_inspect_required')

if __name__ == '__main__':
    unittest.main()

