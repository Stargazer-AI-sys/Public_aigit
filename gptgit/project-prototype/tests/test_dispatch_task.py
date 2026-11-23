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

    def test_documenter_dispatch_and_model_gate(self):
        self.packet.update(role='documenter', development_plan='plan.md', write_scope=['wiki/features/result.md'])
        self.write_packet()
        self.assertEqual(self.call_main()[:2], (0, 0))
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        self.assertEqual(self.call_main(True, env, self.success)[:2], (0, 4))
        self.packet['session']['model'] = 'gpt-6-astra'
        self.write_packet()
        with self.assertRaisesRegex(ValueError, 'model validation'):
            self.call_main()

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

    def test_hermes_documenter_is_blocked_before_receipt(self):
        self.packet.update(role='documenter', development_plan='plan.md', write_scope=[], session={'provider': 'hermes', 'actual_id': None})
        self.write_packet()
        with self.assertRaisesRegex(ValueError, 'documenter must use provider codex'):
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

    def test_process_info_retry_then_ready(self):
        """Incomplete startup on first process-info, valid shell on retry; command submitted once."""
        attempts = []
        def delayed_ready(*args, **kwargs):
            if args[0][1:3] == ['pane', 'process-info']:
                attempts.append(1)
                if len(attempts) == 1:
                    result = {'process_info': {'pane_id': 'w2:p1', 'shell_pid': None, 'foreground_processes': []}}
                    return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': result}), '')
            return self.success(*args, **kwargs)
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        with patch('time.sleep'):
            code, calls, _ = self.call_main(True, env, delayed_ready)
        self.assertEqual(code, 0)
        self.assertEqual(calls, 5)  # pane list, tab create, process-info×2, pane run
        self.assertEqual(self.receipt()['status'], 'submitted_unverified')

    def test_process_info_retry_exhausted_no_run(self):
        """All process-info attempts return incomplete; no command sent; receipt uncertain."""
        runs = []
        def always_incomplete(*args, **kwargs):
            runs.append(args[0][1:3])
            if args[0][1:3] == ['pane', 'process-info']:
                result = {'process_info': {'pane_id': 'w2:p1', 'foreground_processes': []}}
                return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': result}), '')
            return self.success(*args, **kwargs)
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        with patch('time.sleep'):
            with self.assertRaisesRegex(RuntimeError, 'startup incomplete'):
                self.call_main(True, env, always_incomplete)
        self.assertNotIn(['pane', 'run'], runs)
        self.assertEqual(runs.count(['pane', 'process-info']), dispatch_task._READY_MAX_ATTEMPTS)
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

    def test_missing_pane_id_process_info_never_ready(self):
        """process-info without pane_id never returns ready; eventually startup_incomplete."""
        runs = []
        def no_pane_id(*args, **kwargs):
            runs.append(args[0][1:3])
            if args[0][1:3] == ['pane', 'process-info']:
                result = {'process_info': {'shell_pid': 123,
                                           'foreground_processes': [{'pid': 123, 'name': 'pwsh.exe', 'cwd': str(self.root)}]}}
                return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': result}), '')
            return self.success(*args, **kwargs)
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        with patch('time.sleep'):
            with self.assertRaisesRegex(RuntimeError, 'startup incomplete'):
                self.call_main(True, env, no_pane_id)
        self.assertNotIn(['pane', 'run'], runs)
        self.assertEqual(runs.count(['pane', 'process-info']), dispatch_task._READY_MAX_ATTEMPTS)
        r = self.receipt()
        self.assertEqual(r['status'], 'uncertain_inspect_required')
        self.assertIsNone(r['diag']['pane_id'])
        self.assertEqual(r['diag']['reason'], 'startup_incomplete')

    def test_empty_cwd_process_info_never_ready(self):
        """process-info with explicit shell but empty cwd never returns ready."""
        runs = []
        def empty_cwd(*args, **kwargs):
            runs.append(args[0][1:3])
            if args[0][1:3] == ['pane', 'process-info']:
                result = {'process_info': {'pane_id': 'w2:p1', 'shell_pid': 123,
                                           'foreground_processes': [{'pid': 123, 'name': 'pwsh.exe', 'cwd': ''}]}}
                return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': result}), '')
            return self.success(*args, **kwargs)
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        with patch('time.sleep'):
            with self.assertRaisesRegex(RuntimeError, 'startup incomplete'):
                self.call_main(True, env, empty_cwd)
        self.assertNotIn(['pane', 'run'], runs)
        self.assertEqual(runs.count(['pane', 'process-info']), dispatch_task._READY_MAX_ATTEMPTS)
        r = self.receipt()
        self.assertIsNone(r['diag'].get('cwd_match'))
        self.assertEqual(r['diag']['reason'], 'startup_incomplete')

    def test_non_shell_without_shell_pid_hard_fail(self):
        """Explicit non-shell process with absent shell_pid is an immediate hard fail, not incomplete."""
        runs = []
        def claude_no_pid(*args, **kwargs):
            runs.append(args[0][1:3])
            if args[0][1:3] == ['pane', 'process-info']:
                result = {'process_info': {'pane_id': 'w2:p1',
                                           'foreground_processes': [{'pid': 999, 'name': 'claude.exe'}]}}
                return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': result}), '')
            return self.success(*args, **kwargs)
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        with self.assertRaisesRegex(RuntimeError, 'not an idle PowerShell'):
            self.call_main(True, env, claude_no_pid)
        self.assertNotIn(['pane', 'run'], runs)
        self.assertEqual(runs.count(['pane', 'process-info']), 1)
        r = self.receipt()
        self.assertEqual(r['status'], 'uncertain_inspect_required')
        self.assertEqual(r['diag']['reason'], 'proc_name')

    def test_ready_diag_persisted_to_receipt(self):
        """Successful dispatch records process_info stage, attempt count, and observed fields."""
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        self.call_main(True, env, self.success)
        r = self.receipt()
        self.assertEqual(r['status'], 'submitted_unverified')
        diag = r.get('diag', {})
        self.assertEqual(diag.get('stage'), 'process_info')
        self.assertEqual(diag.get('attempts'), 1)
        self.assertEqual(diag.get('reason'), 'ready')
        self.assertEqual(diag.get('pane_id'), 'w2:p1')
        self.assertTrue(diag.get('cwd_match'))

    def test_hard_fail_diag_persisted_to_receipt(self):
        """Hard fail in process-info records sanitized reason code and observed pane identity."""
        def wrong_pane_info(*args, **kwargs):
            if args[0][1:3] == ['pane', 'process-info']:
                result = {'process_info': {'pane_id': 'other:p1', 'shell_pid': 123,
                                           'foreground_processes': [{'pid': 123, 'name': 'pwsh.exe',
                                                                      'cwd': str(self.root)}]}}
                return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': result}), '')
            return self.success(*args, **kwargs)
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        with self.assertRaisesRegex(RuntimeError, 'not an idle PowerShell'):
            self.call_main(True, env, wrong_pane_info)
        r = self.receipt()
        self.assertEqual(r['status'], 'uncertain_inspect_required')
        diag = r.get('diag', {})
        self.assertEqual(diag.get('stage'), 'process_info')
        self.assertEqual(diag.get('attempts'), 1)
        self.assertEqual(diag.get('reason'), 'pane_id')

    def test_malformed_foreground_none_is_incomplete(self):
        """foreground_processes: null is treated as absent, not an error; becomes startup_incomplete."""
        runs = []
        def null_fg(*args, **kwargs):
            runs.append(args[0][1:3])
            if args[0][1:3] == ['pane', 'process-info']:
                result = {'process_info': {'pane_id': 'w2:p1', 'shell_pid': 123,
                                           'foreground_processes': None}}
                return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': result}), '')
            return self.success(*args, **kwargs)
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        with patch('time.sleep'):
            with self.assertRaisesRegex(RuntimeError, 'startup incomplete'):
                self.call_main(True, env, null_fg)
        self.assertNotIn(['pane', 'run'], runs)
        self.assertEqual(runs.count(['pane', 'process-info']), dispatch_task._READY_MAX_ATTEMPTS)
        self.assertEqual(self.receipt()['status'], 'uncertain_inspect_required')


    def test_query_failures_preserve_diagnosis_without_retry_or_run(self):
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        for kind in ('timeout', 'api', 'json', 'missing'):
            with self.subTest(kind=kind):
                self.packet['task_id'] = 'QUERY-' + kind
                self.write_packet()
                calls = []
                def failed_query(*args, **kwargs):
                    command = args[0]
                    calls.append(command[1:3])
                    if command[1:3] != ['pane', 'process-info']:
                        return self.success(*args, **kwargs)
                    if kind == 'timeout':
                        raise subprocess.TimeoutExpired(command, 45, output='SECRET-RAW')
                    if kind == 'api':
                        return subprocess.CompletedProcess(command, 1, '', 'SECRET-RAW')
                    return subprocess.CompletedProcess(command, 0, 'SECRET-RAW' if kind == 'json' else '{"result":{}}', '')
                with self.assertRaises(RuntimeError) as raised:
                    self.call_main(True, env, failed_query)
                self.assertNotIn('SECRET-RAW', str(raised.exception))
                self.assertNotIn(['pane', 'run'], calls)
                self.assertEqual(calls.count(['pane', 'process-info']), 1)
                import hashlib
                receipt = self.root / '.local/dispatch' / (hashlib.sha256(self.packet['task_id'].encode()).hexdigest() + '.json')
                state = json.loads(receipt.read_text())
                self.assertNotIn('SECRET-RAW', receipt.read_text())
                self.assertEqual(state['status'], 'uncertain_inspect_required')
                self.assertEqual(state['diag']['attempts'], 1)
                self.assertEqual(state['diag']['reason'], {'timeout': 'query_timeout', 'api': 'query_failed'}.get(kind, 'malformed_response'))

    def test_malformed_fields_and_untrusted_diagnostics_are_blocked(self):
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        cases = [('name', None), ('cwd', ['SECRET-RAW']), ('name', 'SECRET-RAW' * 100),
                 ('name', {'SECRET-RAW': True}), ('pid', True), ('cwd', 'relative')]
        for index, (field, value) in enumerate(cases):
            with self.subTest(field=field, value=value):
                self.packet['task_id'] = 'MALFORMED-' + str(index)
                self.write_packet()
                calls = []
                def malformed(*args, **kwargs):
                    calls.append(args[0][1:3])
                    if args[0][1:3] != ['pane', 'process-info']:
                        return self.success(*args, **kwargs)
                    proc = {'pid': 123, 'name': 'pwsh.exe', 'cwd': str(self.root)}
                    proc[field] = value
                    info = {'pane_id': 'w2:p1', 'shell_pid': 123, 'foreground_processes': [proc]}
                    return subprocess.CompletedProcess(args[0], 0, json.dumps({'result': {'process_info': info}}), '')
                with self.assertRaises(RuntimeError):
                    self.call_main(True, env, malformed)
                self.assertNotIn(['pane', 'run'], calls)
                self.assertEqual(calls.count(['pane', 'process-info']), 1)
                import hashlib
                receipt = self.root / '.local/dispatch' / (hashlib.sha256(self.packet['task_id'].encode()).hexdigest() + '.json')
                state = json.loads(receipt.read_text())
                self.assertEqual(state['diag']['stage'], 'process_info')
                self.assertNotIn('SECRET-RAW', receipt.read_text())
                self.assertEqual(state['status'], 'uncertain_inspect_required')

    def test_silent_successful_pane_run_is_admission_not_agent_success(self):
        calls = []
        def silent_run(*args, **kwargs):
            calls.append(args[0][1:3])
            if args[0][1:3] == ['pane', 'run']:
                return subprocess.CompletedProcess(args[0], 0, '', '')
            return self.success(*args, **kwargs)
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        code, _, _ = self.call_main(True, env, silent_run)
        self.assertEqual(code, 0)
        self.assertEqual(calls.count(['pane', 'run']), 1)
        self.assertEqual(self.receipt()['status'], 'submitted_unverified')

    def test_silent_query_and_failed_or_malformed_run_are_not_success(self):
        env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_WORKSPACE_ID': 'w1', 'HERDR_TAB_ID': 't1'}
        for kind in ('query', 'run_failed', 'run_malformed', 'run_whitespace'):
            with self.subTest(kind=kind):
                self.packet['task_id'] = 'SILENT-' + kind
                self.write_packet()
                calls = []
                def response(*args, **kwargs):
                    cmd = args[0]
                    calls.append(cmd[1:3])
                    if kind == 'query' and cmd[1:3] == ['pane', 'process-info']:
                        return subprocess.CompletedProcess(cmd, 0, '', '')
                    if kind != 'query' and cmd[1:3] == ['pane', 'run']:
                        return subprocess.CompletedProcess(cmd, 1 if kind == 'run_failed' else 0,
                                                           '' if kind == 'run_failed' else ' ' if kind == 'run_whitespace' else 'invalid', '')
                    return self.success(*args, **kwargs)
                with self.assertRaises((RuntimeError, ValueError)):
                    self.call_main(True, env, response)
                self.assertEqual(calls.count(['pane', 'run']), 0 if kind == 'query' else 1)
                import hashlib
                path = self.root / '.local/dispatch' / (hashlib.sha256(self.packet['task_id'].encode()).hexdigest() + '.json')
                self.assertEqual(json.loads(path.read_text())['status'], 'uncertain_inspect_required')

if __name__ == '__main__':
    unittest.main()

