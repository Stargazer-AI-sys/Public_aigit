"""Shared role/model admission check. No model calls, approvals or record writes."""
import argparse
import json
import re

CODEX_WORKERS = frozenset({'gpt-6-luna', 'gpt-6.1-terra'})
CODEX_MASTER = 'gpt-6-astra'


def validate(role, provider, model):
    if not isinstance(role, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,39}', role):
        return ['invalid role']
    if provider not in {'codex', 'claude', 'hermes'}:
        return ['unsupported provider']
    if not isinstance(model, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,119}', model):
        return ['explicit valid model ID required']
    if provider == 'codex':
        allowed = {CODEX_MASTER} if role == 'master' else CODEX_WORKERS
        return [] if model in allowed else ['model is not allowed for this role']
    if role == 'master':
        return ['master must use Codex Astra']
    if 'astra' in model.lower() or model.lower().startswith('gpt-'):
        return ['provider/model mismatch or reserved master model']
    return []  # Provider availability is checked by its project adapter, not inferred here.


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--role', required=True)
    p.add_argument('--provider', required=True)
    p.add_argument('--model', required=True)
    a = p.parse_args()
    errors = validate(a.role, a.provider, a.model)
    print(json.dumps({'valid': not errors, 'errors': errors, 'model_called': False}))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
