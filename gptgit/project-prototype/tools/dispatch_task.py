"""Master-owned Herdr launch adapter. A receipt is admission evidence, not success."""
import argparse
import base64
import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from task_packet import validate

# Load the fixed sibling shared checker without modifying sys.path or accepting a
# module from the caller's current directory.
_checker_path = Path(__file__).resolve().parents[2] / 'tools' / 'check_agent_model.py'
_checker_spec = importlib.util.spec_from_file_location('_gptgit_shared_model_checker', _checker_path)
if _checker_spec is None or _checker_spec.loader is None:
    raise RuntimeError('shared model checker unavailable')
_checker = importlib.util.module_from_spec(_checker_spec)
_checker_spec.loader.exec_module(_checker)


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
    if packet['role'] in {'master', 'documenter'}:
        raise ValueError('master is existing coordinator; Hermes adapter not yet implemented')
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
        info = call('pane', 'process-info', '--pane', pane)['process_info']
        foreground = info.get('foreground_processes', [])
        if info.get('pane_id') != pane or len(foreground) != 1 or foreground[0]['pid'] != info.get('shell_pid') or foreground[0]['name'].lower().removesuffix('.exe') not in {'pwsh', 'powershell'} or Path(foreground[0].get('cwd', '')).resolve() != root:
            raise RuntimeError('new pane is not an idle PowerShell; no command sent')
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
