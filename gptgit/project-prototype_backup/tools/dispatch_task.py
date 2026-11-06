"""Master-owned Herdr launch adapter. A receipt is admission evidence, not success."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
from task_packet import validate


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
    if os.environ.get('HERDR_ENV') != '1' or not os.environ.get('HERDR_PANE_ID'):
        raise ValueError('Herdr caller context required')
    def call(*argv):
        result = subprocess.run([config['herdr'], *argv], capture_output=True, text=True, encoding='utf-8', timeout=45)
        if result.returncode:
            raise RuntimeError('herdr failed; inspect actual state before any new dispatch')
        return json.loads(result.stdout)['result']
    panes = call('pane', 'list')['panes']
    caller = next((p for p in panes if p.get('pane_id') == os.environ['HERDR_PANE_ID']), None)
    if not caller or Path(caller.get('cwd', '')).resolve() != root:
        raise ValueError('caller pane project mismatch; start prototype master first')
    known_panes = {p['pane_id'] for p in panes}
    # Approval is evaluated by the master. This tool validates structure, not authority.
    receipt_dir = root / '.local/dispatch'
    receipt_dir.mkdir(parents=True, exist_ok=True)
    import hashlib
    receipt = receipt_dir / (hashlib.sha256(packet['task_id'].encode()).hexdigest() + '.json')
    state = {'task_id': packet['task_id'], 'packet_hash': hashlib.sha256(packet_path.read_bytes()).hexdigest(), 'status': 'claimed', 'pane_id': None}
    with receipt.open('x', encoding='utf-8') as stream:
        json.dump(state, stream)
    def save():
        receipt.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    try:
        split = call('pane', 'split', '--current', '--direction', 'right', '--cwd', str(root), '--no-focus')
        pane = split['pane']['pane_id']
        if not isinstance(pane, str) or not pane or pane in known_panes:
            raise RuntimeError('split did not return a new pane identity')
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
