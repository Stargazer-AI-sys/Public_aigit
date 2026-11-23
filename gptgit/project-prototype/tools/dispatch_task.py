"""Master-owned Herdr launch adapter. A receipt is admission evidence, not success."""
import argparse
import base64
import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time
from task_packet import validate

# Load the fixed sibling shared checker without modifying sys.path or accepting a
# module from the caller's current directory.
_checker_path = Path(__file__).resolve().parents[2] / 'tools' / 'check_agent_model.py'
_checker_spec = importlib.util.spec_from_file_location('_gptgit_shared_model_checker', _checker_path)
if _checker_spec is None or _checker_spec.loader is None:
    raise RuntimeError('shared model checker unavailable')
_checker = importlib.util.module_from_spec(_checker_spec)
_checker_spec.loader.exec_module(_checker)


_READY_MAX_ATTEMPTS = 3
_READY_RETRY_DELAY = 0.5


def _safe_observed(info, pane, root):
    """Only caller-owned identity, booleans and fixed labels; never response text."""
    if not isinstance(info, dict):
        return {}
    obs = {'pane_id': pane if info.get('pane_id') == pane else None,
           'pane_match': info.get('pane_id') == pane}
    foreground = info.get('foreground_processes')
    if isinstance(foreground, list):
        if len(foreground) == 1 and isinstance(foreground[0], dict):
            proc = foreground[0]
            name = proc.get('name')
            name = name.lower().removesuffix('.exe') if isinstance(name, str) else None
            obs['proc_name'] = name if name in {'pwsh', 'powershell'} else 'other'
            cwd = proc.get('cwd')
            if isinstance(cwd, str) and cwd.strip():
                try:
                    obs['cwd_match'] = Path(cwd).is_absolute() and Path(cwd).resolve() == root
                except Exception:
                    obs['cwd_match'] = False
            else:
                obs['cwd_match'] = None
        else:
            obs['foreground_count'] = min(len(foreground), 2)
    return obs


def _check_pane_ready(info, pane, root):
    """
    Return 'ready' or 'incomplete'; raise RuntimeError on a definite bad state.
    Never returns 'ready' without explicit matching pane_id, shell_pid, valid shell,
    and nonempty absolute cwd matching root.
    """
    def reject(reason):
        raise RuntimeError('new pane is not an idle PowerShell; no command sent; ' + reason)
    if not isinstance(info, dict):
        reject('malformed_response')
    actual_pane = info.get('pane_id')
    if actual_pane is not None and not isinstance(actual_pane, str):
        reject('malformed_pane_id')
    foreground = info.get('foreground_processes')
    if foreground is None:
        foreground = []
    if not isinstance(foreground, list):
        reject('malformed_foreground')
    shell_pid = info.get('shell_pid')
    if shell_pid is not None and (type(shell_pid) is not int or shell_pid <= 0):
        reject('malformed_shell_pid')
    if actual_pane is not None and actual_pane != pane:
        reject('pane_id')
    if foreground:
        if len(foreground) != 1:
            reject('foreground_count')
        proc = foreground[0]
        if not isinstance(proc, dict):
            reject('malformed_process')
        if not isinstance(proc.get('name'), str):
            reject('malformed_name')
        name = proc['name'].lower().removesuffix('.exe')
        if name not in {'pwsh', 'powershell'}:
            reject('proc_name')
        if type(proc.get('pid')) is not int or proc['pid'] <= 0:
            reject('malformed_pid')
        if shell_pid is not None and proc.get('pid') != shell_pid:
            raise RuntimeError('new pane is not an idle PowerShell; no command sent; pid_mismatch')
        cwd = proc.get('cwd')
        if cwd is not None and not isinstance(cwd, str):
            reject('malformed_cwd')
        if isinstance(cwd, str) and cwd.strip():
            if not Path(cwd).is_absolute():
                raise RuntimeError('new pane is not an idle PowerShell; no command sent; cwd_not_absolute')
            try:
                cwd_ok = Path(cwd).resolve() == root
            except Exception:
                cwd_ok = False
            if not cwd_ok:
                raise RuntimeError('new pane is not an idle PowerShell; no command sent; cwd_mismatch')
    if actual_pane is None or not shell_pid or not foreground:
        return 'incomplete'
    cwd = foreground[0].get('cwd') if isinstance(foreground[0], dict) else ''
    if not isinstance(cwd, str) or not cwd.strip():
        return 'incomplete'
    return 'ready'


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    packet_path = args.packet.resolve()
    if not packet_path.is_relative_to(root):
        raise ValueError('packet outside project')
    packet = json.loads(packet_path.read_text(encoding='utf-8-sig'))
    errors = validate(packet, root)
    if errors:
        raise ValueError('; '.join(errors))
    if packet['role'] == 'master':
        raise ValueError('master is existing coordinator')
    model_errors = _checker.validate(packet['role'], packet['session']['provider'], packet['session'].get('model'))
    if model_errors:
        raise ValueError('model validation failed: ' + '; '.join(model_errors))
    config_path = root / 'config/runtime.local.json'
    if not config_path.exists():
        config_path = root / 'config/runtime.example.json'
    config = json.loads(config_path.read_text(encoding='utf-8-sig'))
    command = '& ' + ps_quote(root / 'tools/start_role.ps1') + ' -Role ' + ps_quote(packet['role']) + ' -Packet ' + ps_quote(packet_path)
    encoded = base64.b64encode(command.encode('utf-16-le')).decode('ascii')
    shell_command = '& ' + ps_quote(config.get('powershell', 'pwsh.exe')) + ' -NoProfile -EncodedCommand ' + encoded
    if not args.apply:
        print(json.dumps({'task_id': packet['task_id'], 'role': packet['role'], 'cwd': str(root), 'model_called': False, 'apply': False}, ensure_ascii=False))
        return 0
    if os.environ.get('HERDR_ENV') != '1' or not all(os.environ.get(k) for k in ('HERDR_PANE_ID', 'HERDR_WORKSPACE_ID', 'HERDR_TAB_ID')):
        raise ValueError('Herdr caller context required')
    def call(*argv):
        result = subprocess.run([config['herdr'], *argv], capture_output=True, text=True, encoding='utf-8', timeout=45)
        if result.returncode:
            raise RuntimeError('herdr failed; inspect actual state before any new dispatch')
        # Herdr 0.9.5 pane run succeeds silently. This is command admission only;
        # all topology/process queries still require their structured response.
        if argv[:2] == ('pane', 'run') and result.stdout == '':
            return {}
        return json.loads(result.stdout)['result']
    workspace_id = os.environ['HERDR_WORKSPACE_ID']
    caller_tab_id = os.environ['HERDR_TAB_ID']
    panes = call('pane', 'list', '--workspace', workspace_id)['panes']
    caller = next((p for p in panes if p.get('pane_id') == os.environ['HERDR_PANE_ID']), None)
    if not caller or not caller.get('cwd') or Path(caller['cwd']).resolve() != root or (caller.get('tab_id') is not None and caller['tab_id'] != caller_tab_id) or (caller.get('workspace_id') is not None and caller['workspace_id'] != workspace_id):
        raise ValueError('caller pane project mismatch; start prototype master first')
    if any(not isinstance(p.get('tab_id'), str) or not p['tab_id'].strip() for p in panes):
        raise ValueError('workspace pane tab identity missing; cannot establish existing tabs')
    known_tabs = {p['tab_id'] for p in panes}
    known_panes = {p['pane_id'] for p in panes}
    # Approval is evaluated by the master. This tool validates structure, not authority.
    receipt_dir = root / '.local/dispatch'
    receipt_dir.mkdir(parents=True, exist_ok=True)
    import hashlib
    receipt = receipt_dir / (hashlib.sha256(packet['task_id'].encode()).hexdigest() + '.json')
    state = {'task_id': packet['task_id'], 'packet_hash': hashlib.sha256(packet_path.read_bytes()).hexdigest(), 'status': 'claimed', 'tab_id': None, 'pane_id': None}
    with receipt.open('x', encoding='utf-8') as stream:
        json.dump(state, stream)
    def save():
        receipt.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    try:
        created = call('tab', 'create', '--workspace', workspace_id, '--cwd', str(root), '--no-focus')
        tab = created['tab']['tab_id']
        root_pane = created['root_pane']
        pane = root_pane['pane_id']
        state.update(tab_id=tab, pane_id=pane)
        save()
        if not isinstance(tab, str) or not tab or tab == caller_tab_id or tab in known_tabs:
            raise RuntimeError('tab did not return a new tab identity')
        if not isinstance(root_pane.get('cwd'), str) or not root_pane['cwd'] or Path(root_pane['cwd']).resolve() != root:
            raise RuntimeError('new root pane cwd mismatch')
        if not isinstance(pane, str) or not pane or pane in known_panes:
            raise RuntimeError('tab did not return a new pane identity')
        state.update(pane_id=pane, status='created')
        save()
        _last_obs = {}
        for _attempt in range(_READY_MAX_ATTEMPTS):
            state['diag'] = {'stage': 'process_info', 'attempts': _attempt + 1,
                             'reason': 'querying'}
            save()
            try:
                info = call('pane', 'process-info', '--pane', pane)['process_info']
            except Exception as exc:
                reason = ('query_timeout' if isinstance(exc, subprocess.TimeoutExpired)
                          else 'query_failed' if isinstance(exc, (RuntimeError, OSError))
                          else 'malformed_response')
                state['diag']['reason'] = reason
                save()
                raise RuntimeError('process-info failed; no command sent; ' + reason) from None
            try:
                _last_obs = _safe_observed(info, pane, root)
                _readiness = _check_pane_ready(info, pane, root)
            except RuntimeError as exc:
                _reason = str(exc).partition('; no command sent; ')[2].split('=')[0] or 'check_failed'
                state['diag'] = {'stage': 'process_info', 'attempts': _attempt + 1,
                                 'reason': _reason, **_last_obs}
                save()
                raise
            if _readiness == 'ready':
                state['diag'] = {'stage': 'process_info', 'attempts': _attempt + 1,
                                 'reason': 'ready', **_last_obs}
                break
            if _attempt < _READY_MAX_ATTEMPTS - 1:
                time.sleep(_READY_RETRY_DELAY)
            else:
                state['diag'] = {'stage': 'process_info', 'attempts': _attempt + 1,
                                 'reason': 'startup_incomplete', **_last_obs}
                save()
                raise RuntimeError(
                    'new pane startup incomplete after ' + str(_READY_MAX_ATTEMPTS) +
                    ' attempts; no command sent'
                )
        state['status'] = 'dispatching'
        save()
        call('pane', 'run', pane, shell_command)
        state['status'] = 'submitted_unverified'
        save()
        print(json.dumps(state, ensure_ascii=False))
        return 0
    except Exception:
        state['status'] = 'uncertain_inspect_required'
        save()
        raise


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, RuntimeError, KeyError, subprocess.TimeoutExpired) as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(1)
