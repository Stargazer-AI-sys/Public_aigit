"""Management project's launch backend: new worker tab, explicit model, no Task injection."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from check_agent_model import validate

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'project-management'
ROLES = {'planner', 'researcher', 'writer', 'developer', 'reviewer', 'qa'}
KEYS = ('OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_API_BASE')


def plan(role, model, name):
    errors = validate(role, 'codex', model)
    if role not in ROLES:
        errors.append('unsupported management worker role')
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', name):
        errors.append('invalid agent name')
    if errors:
        raise ValueError('; '.join(errors))
    native = ['--model', model, '-c', 'forced_login_method="chatgpt"']
    if role in {'reviewer', 'qa'}:
        native += ['--sandbox', 'read-only', '-c', 'approval_policy="on-request"',
                   '-c', 'approvals_reviewer="auto_review"']
    else:
        native += ['--approve-for-me']
    return native


def launch(role, model, name, check_only=False):
    native = plan(role, model, name)
    if check_only:
        return {'role': role, 'model': model, 'native_args': native, 'topology': 'new-worker-tab',
                'task_sent': False, 'model_called': False}
    if os.environ.get('HERDR_ENV') != '1' or not os.environ.get('HERDR_PANE_ID'):
        raise ValueError('Herdr caller context required')
    if any(os.environ.get(k) for k in KEYS):
        raise ValueError('API/provider override present; no paid fallback allowed')
    herdr = shutil.which('herdr')
    if not herdr:
        raise ValueError('herdr is not installed')
    codex = shutil.which('codex.cmd') if os.name == 'nt' else shutil.which('codex')
    if not codex:
        raise ValueError('codex is not installed')
    auth = subprocess.run([codex, 'login', 'status'], capture_output=True, text=True,
                          encoding='utf-8', timeout=30)
    if auth.returncode or 'Logged in using ChatGPT' not in auth.stdout + auth.stderr:
        raise ValueError('ChatGPT login not confirmed; no agent started')
    def call(*args):
        r = subprocess.run([herdr, *args], capture_output=True, text=True, encoding='utf-8', timeout=45)
        if r.returncode:
            raise RuntimeError(r.stderr or r.stdout)
        return json.loads(r.stdout)['result']
    caller = call('pane', 'current', '--current')['pane']
    if Path(caller.get('cwd', '')).resolve() != PROJECT.resolve():
        raise ValueError('caller cwd does not match management project')
    known_tabs = {t['tab_id'] for t in call('tab', 'list', '--workspace', caller['workspace_id'])['tabs']}
    try:
        made = call('tab', 'create', '--workspace', caller['workspace_id'], '--cwd', str(PROJECT),
                    '--label', name, '--no-focus')
    except Exception as exc:
        raise RuntimeError(f'tab creation outcome uncertain; inspect workspace {caller["workspace_id"]} '
                           f'for label {name} before retry: {exc}') from exc
    pane = made['root_pane']['pane_id']
    tab = made['tab']['tab_id']
    if tab in known_tabs or tab == caller['tab_id'] or Path(made['root_pane']['cwd']).resolve() != PROJECT.resolve():
        raise RuntimeError(f'new worker topology mismatch: tab {tab}, pane {pane}; inspect before retrying')
    try:
        result = call('agent', 'start', name, '--kind', 'codex', '--pane', pane, '--', *native)
    except Exception as exc:
        raise RuntimeError(f'worker tab {tab}, pane {pane}: inspect existing state before retry: {exc}') from exc
    return {'status': 'awaiting_model_verification', 'role': role, 'requested_model': model,
            'tab_id': tab, 'pane_id': pane, 'agent': result.get('agent'), 'task_sent': False,
            'next': 'Verify live model and permissions in CLI before sending any Task.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('role', 'model', 'name'):
        p.add_argument('--' + key, required=True)
    p.add_argument('--check-only', action='store_true')
    a = p.parse_args()
    try:
        print(json.dumps(launch(a.role, a.model, a.name, a.check_only), ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({'status': 'blocked_or_uncertain', 'error': str(exc), 'retry_automatically': False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
