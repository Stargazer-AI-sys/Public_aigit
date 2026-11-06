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
            'expected_output': 'fixture plan', 'session': {'provider': 'codex', 'model': 'gpt-6-luna', 'actual_id': None},
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
            result = {'panes': [{'pane_id': 'w1:p1', 'tab_id': 't1', 'cwd': str(self.root)}]}
        elif command[1:3] == ['tab', 'create']:
            result = {'tab': {'tab_id': 't2'}, 'root_pane': {'pane_id': 'w2:p1', 'cwd': str(self.root)}}
        elif command[1:3] == ['pane', 'process-info']:
            result = {'process_info': {'pane_id': 'w2:p1', 'shell_pid': 123, 'foreground_processes': [{'pid': 123, 'name': 'pwsh.exe', 'cwd': str(self.root)}]}}
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
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        self.assertEqual(self.call_main(True, env, self.success)[:2], (0, 4))
        self.assertEqual(self.receipt()['status'], 'submitted_unverified')
        self.assertEqual(self.receipt()['tab_id'], 't2')
        with self.assertRaises(FileExistsError):
            self.call_main(True, env, self.success)
        self.assertEqual(self.receipt()['status'], 'submitted_unverified')

    def test_timeout_records_uncertain_and_no_retry(self):
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
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
            self.call_main(True, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'})
        self.assertFalse((self.root / '.local').exists())

    def test_nonidle_new_pane_receipt_uncertain_no_run(self):
        calls = []
        def nonidle(*args, **kwargs):
            calls.append(args[0][1:3])
            if args[0][1:3] == ['pane', 'process-info']:
                return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': {'process_info': {'shell_pid': 123, 'foreground_processes': [{'pid': 999, 'name': 'claude.exe'}]}}}), '')
            return self.success(*args, **kwargs)
        with self.assertRaisesRegex(RuntimeError, 'not an idle PowerShell'):
            self.call_main(True, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}, nonidle)
        self.assertNotIn(['pane', 'run'], calls)
        self.assertEqual(self.receipt()['status'], 'uncertain_inspect_required')


    def test_mismatched_caller_project_blocks_before_claim(self):
        calls = []
        def mismatch(*args, **kwargs):
            calls.append(args[0][1:3])
            return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': {'panes': [{'pane_id': 'w1:p1', 'cwd': str(self.root / 'other')} ]}}), '')
        with self.assertRaisesRegex(ValueError, 'caller pane project mismatch'):
            self.call_main(True, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}, mismatch)
        self.assertEqual(calls, [['pane', 'list']])
        self.assertFalse((self.root / '.local').exists())

    def test_tab_creation_uses_new_tab_and_checks_cwd(self):
        calls = []
        def wrong_cwd(*args, **kwargs):
            cmd = args[0]
            calls.append(cmd)
            if cmd[1:3] == ['pane', 'process-info']:
                result = {'process_info': {'pane_id': 'w2:p1', 'shell_pid': 123, 'foreground_processes': [{'pid': 123, 'name': 'pwsh.exe', 'cwd': str(self.root / 'other')}]}}
                return subprocess.CompletedProcess(cmd, 0, json.dumps({'result': result}), '')
            return self.success(*args, **kwargs)
        with self.assertRaisesRegex(RuntimeError, 'not an idle PowerShell'):
            self.call_main(True, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}, wrong_cwd)
        creates = [c for c in calls if c[1:3] == ['tab', 'create']]
        self.assertEqual(len(creates), 1)
        self.assertEqual(creates[0][3:], ['--workspace', 'w1', '--cwd', str(self.root), '--no-focus'])
        self.assertFalse(any(c[1:3] in (['pane', 'split'], ['pane', 'run']) for c in calls))
        self.assertEqual(self.receipt()['status'], 'uncertain_inspect_required')

    def test_missing_root_pane_blocks_run(self):
        calls = []
        def missing(*args, **kwargs):
            calls.append(args[0][1:3])
            if args[0][1:3] == ['tab', 'create']:
                return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': {}}), '')
            return self.success(*args, **kwargs)
        with self.assertRaises(KeyError):
            self.call_main(True, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}, missing)
        self.assertNotIn(['pane', 'run'], calls)
        self.assertEqual(self.receipt()['status'], 'uncertain_inspect_required')

    def test_invalid_model_rejected_before_any_herdr_or_receipt(self):
        for model in (None, 'gpt-6-astra', ''):
            with self.subTest(model=model):
                self.packet['session']['model'] = model
                self.write_packet()
                for apply in (False, True):
                    with self.assertRaisesRegex(ValueError, 'model validation failed'):
                        self.call_main(apply, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'})
                self.assertFalse((self.root / '.local').exists())

    def test_invalid_tab_identity_or_returned_root_cwd_blocks_run(self):
        for tab_id, cwd in [('t1', str(self.root)), ('t2', str(self.root / 'other'))]:
            with self.subTest(tab_id=tab_id, cwd=cwd):
                # Independent task IDs avoid a previous uncertain receipt.
                self.packet['task_id'] = 'CASE-' + ('same' if tab_id == 't1' else 'cwd')
                self.write_packet()
                calls = []
                def invalid(*args, **kwargs):
                    calls.append(args[0][1:3])
                    if args[0][1:3] == ['tab', 'create']:
                        result = {'tab': {'tab_id': tab_id}, 'root_pane': {'pane_id': 'w2:p1', 'cwd': cwd}}
                        return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': result}), '')
                    return self.success(*args, **kwargs)
                with self.assertRaises(RuntimeError):
                    self.call_main(True, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}, invalid)
                self.assertNotIn(['pane', 'run'], calls)

    def test_existing_other_tab_or_missing_tab_identity_is_rejected(self):
        for missing in (False, True):
            with self.subTest(missing=missing):
                self.packet['task_id'] = 'MISSING' if missing else 'EXISTING'
                self.write_packet()
                calls = []
                def existing(*args, **kwargs):
                    cmd = args[0]
                    calls.append(cmd[1:3])
                    if cmd[1:3] == ['pane', 'list']:
                        other = {'pane_id': 'w1:p3', 'cwd': str(self.root)}
                        if not missing:
                            other['tab_id'] = 't3'
                        result = {'panes': [{'pane_id': 'w1:p1', 'tab_id': 't1', 'cwd': str(self.root)}, other]}
                    elif cmd[1:3] == ['tab', 'create']:
                        result = {'tab': {'tab_id': 't3'}, 'root_pane': {'pane_id': 'w1:p4', 'cwd': str(self.root)}}
                    else:
                        return self.success(*args, **kwargs)
                    return subprocess.CompletedProcess(cmd, 0, json.dumps({'result': result}), '')
                with self.assertRaisesRegex((ValueError, RuntimeError), 'tab identity'):
                    self.call_main(True, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}, existing)
                self.assertNotIn(['pane', 'run'], calls)
                if missing:
                    self.assertNotIn(['tab', 'create'], calls)
                else:
                    self.assertEqual(self.receipt()['status'], 'uncertain_inspect_required')

    def test_tab_existing_identity_is_uncertain_without_command(self):
        calls = []
        def reused(*args, **kwargs):
            calls.append(args[0][1:3])
            if args[0][1:3] == ['tab', 'create']:
                return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': {'tab': {'tab_id': 't2'}, 'root_pane': {'pane_id': 'w1:p1', 'cwd': str(self.root)}}}), '')
            return self.success(*args, **kwargs)
        with self.assertRaisesRegex(RuntimeError, 'new pane identity'):
            self.call_main(True, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}, reused)
        self.assertNotIn(['pane', 'run'], calls)
        self.assertEqual(self.receipt()['status'], 'uncertain_inspect_required')

if __name__ == '__main__':
    unittest.main()

