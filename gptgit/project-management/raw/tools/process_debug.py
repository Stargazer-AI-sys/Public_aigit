"""Local, opt-in response diagnostics. No transcript or billing collection."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

FIELDS = ('input_tokens', 'cached_input_tokens', 'output_tokens',
          'reasoning_output_tokens', 'total_tokens')
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$')
SECRET = re.compile(r'(?i)(?:\b(?:sk-|ghp_|github_pat_)[a-z0-9_-]{12,}|'
                    r'-----BEGIN .*PRIVATE KEY|'
                    r'\b(?:password|api[_-]?key|access[_-]?token|authorization)\s*[:=]\s*["\']?[^\s"\']{8,})')


def now():
    return datetime.now(timezone.utc).isoformat()


def safe_text(value):
    if not isinstance(value, str) or len(value) > 2000 or SECRET.search(value):
        raise ValueError('Text is invalid or contains a suspected credential; remove it first.')
    return value


def identifier(value):
    if not ID.fullmatch(value) or value.endswith('.') or SECRET.search(value):
        raise ValueError('IDs must use letters, digits, underscore, dot or hyphen.')
    if value.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(10)), *('LPT'+str(i) for i in range(10))}:
        raise ValueError('Reserved identifier.')
    return value


def local_path(root, relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or ':' in relative or '\\' in relative:
        raise ValueError('Use a project-relative path with forward slashes, without traversal.')
    result = (root / p).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError('Path escapes the project.')
    return result


@contextmanager
def state_file(root, run):
    directory = local_path(root, 'docs/workflows/' + identifier(run) + '/debug')
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / '.lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError('Debug state is locked. Check the active process before removing a stale lock.') from None
    try:
        os.close(fd)
        path = directory / 'state.json'
        if path.is_symlink():
            raise ValueError('State symlinks are not supported.')
        state = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'version': 1, 'responses': {}}
        yield state
        handle, temporary = tempfile.mkstemp(prefix='.state-', dir=directory)
        try:
            with os.fdopen(handle, 'w', encoding='utf-8') as stream:
                json.dump(state, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    finally:
        lock.unlink()


def number(value):
    return value if type(value) is int and value >= 0 else None


def counters(value):
    value = value if isinstance(value, dict) else {}
    return {key: number(value.get(key)) for key in FIELDS}


def clean_usage(value):
    value = value if isinstance(value, dict) else {}
    return {'total': counters(value.get('total')), 'last': counters(value.get('last')),
            'context_window': number(value.get('context_window'))}


def codex_usage(path, expected_session=None):
    """Stream bounded lines; retain only whitelisted numeric token_count fields."""
    result = clean_usage({})
    seen = False
    session_id = None
    # Never return source content, messages, paths, or parse exceptions.
    with Path(path).open('rb') as stream:
        while True:
            line = stream.readline(1024 * 1024 + 1)
            if not line:
                break
            if len(line) > 1024 * 1024:
                while line and not line.endswith(b'\n'):
                    line = stream.readline(1024 * 1024 + 1)
                continue
            try:
                record = json.loads(line)
            except (ValueError, UnicodeError):
                continue
            if not isinstance(record, dict):
                continue
            if record.get('type') == 'session_meta' and isinstance(record.get('payload'), dict):
                session_id = record['payload'].get('id')
            if record.get('type') != 'event_msg':
                continue
            payload = record.get('payload')
            if not isinstance(payload, dict) or payload.get('type') != 'token_count':
                continue
            info = payload.get('info')
            if not isinstance(info, dict):
                continue
            result = clean_usage({'total': info.get('total_token_usage'),
                                  'last': info.get('last_token_usage'),
                                  'context_window': info.get('model_context_window')})
            seen = True
    if expected_session is not None and session_id != expected_session:
        return clean_usage({}), 'unknown_session_mismatch_or_missing'
    return result, 'collected' if seen else 'unknown'


def delta(start, end):
    result = {}
    for key in FIELDS:
        a, b = start.get(key), end.get(key)
        result[key] = b - a if type(a) is int and type(b) is int and b >= a else None
    if (result['cached_input_tokens'] is not None and result['input_tokens'] is not None
            and result['cached_input_tokens'] > result['input_tokens']):
        result['cached_input_tokens'] = None
    if (result['reasoning_output_tokens'] is not None and result['output_tokens'] is not None
            and result['reasoning_output_tokens'] > result['output_tokens']):
        result['reasoning_output_tokens'] = None
    return result


def load_proxy(total):
    return {'level': 'unknown' if total is None else ('low' if total < 10000 else 'medium' if total < 50000 else 'high'),
            'basis': 'Cumulative total-token delta: low <10000; medium 10000..49999; high >=50000. Provisional thresholds, not billing or quality.'}


def report(response, enabled):
    if not enabled:
        return {'enabled': False, 'summary': 'off', 'existing_logs': 'unchanged'}
    sessions = []
    for alias, session in response['sessions'].items():
        snapshots = session.get('snapshots', {})
        start, end = snapshots.get('start', {}), snapshots.get('end', {})
        comparable = (start.get('enabled') is True and end.get('enabled') is True
                      and start.get('mode_epoch') == end.get('mode_epoch')
                      and start.get('source') == end.get('source')
                      and start.get('status') == end.get('status')
                      and start.get('status') in ('collected', 'manual_unverified'))
        usage = delta(start.get('total', {}), end.get('total', {})) if comparable else counters({})
        sessions.append({'alias': alias, **{k: session[k] for k in ('session_id', 'task', 'provider')},
                         'usage_delta': usage, 'usage_status': 'known' if usage['total_tokens'] is not None else 'unknown',
                         'snapshot_status': {'start': start.get('status', 'unknown'), 'end': end.get('status', 'unknown')},
                         'snapshots': {phase: {k: snap.get(k) for k in ('source', 'at', 'enabled', 'mode_epoch')} for phase, snap in (('start', start), ('end', end))},
                         'interval_comparable': comparable,
                         'provisional_load_proxy': load_proxy(usage['total_tokens']),
                         'context': {'last_input_tokens': end.get('last', {}).get('input_tokens') if comparable else None,
                                     'window_tokens': end.get('context_window') if comparable else None,
                                     'observed_start_end_max_input_tokens': max((s.get('last', {}).get('input_tokens') for s in (start, end) if s.get('last', {}).get('input_tokens') is not None), default=None) if comparable else None,
                                     'note': 'Only start/end observations, not the interval maximum or measured current context occupancy.'}})
    aggregate = {key: sum(s['usage_delta'][key] for s in sessions)
                 if sessions and all(s['usage_delta'][key] is not None for s in sessions) else None for key in FIELDS}
    known_count = {key: sum(s['usage_delta'][key] is not None for s in sessions) for key in FIELDS}
    known = {key: sum(s['usage_delta'][key] for s in sessions if s['usage_delta'][key] is not None) if known_count[key] else None for key in FIELDS}
    total = aggregate['total_tokens']
    return {'enabled': True, 'sessions': sessions, 'aggregate_usage_delta': aggregate,
            'known_partial_usage_delta': known, 'known_session_count': known_count, 'reads': response['reads'],
            'provisional_load_proxy': load_proxy(total),
            'limitations': ['Cached input is a subset of input; reasoning output is a subset of output. Do not add these to total.',
                            'Snapshots cover a session interval, not provably only this response. Concurrent or overlapping sessions may overcount.',
                            'No exact monetary cost, account quota, or current context occupancy is inferred.']}


def execute(args, root=None):
    root = Path(root or Path(__file__).resolve().parents[1]).resolve()
    identifier(args.response)
    with state_file(root, args.run) as state:
        response = state['responses'].setdefault(args.response, {'sessions': {}, 'reads': [], 'events': []})
        cmd = args.command
        if cmd in ('on', 'off'):
            enabled = cmd == 'on'
            if state.get('enabled', False) != enabled:
                state['mode_epoch'] = state.get('mode_epoch', 0) + 1
            state['enabled'] = enabled
            response['events'].append({'at': now(), 'mode': cmd, 'mode_epoch': state.get('mode_epoch', 0)})
            result = {'enabled': enabled, 'response': args.response, 'existing_logs': 'unchanged'}
        elif cmd == 'status':
            result = {'enabled': state.get('enabled', False), 'response': args.response, 'sessions': list(response['sessions'])}
        elif cmd == 'bind':
            alias = identifier(args.session)
            binding = {'session_id': identifier(args.session_id), 'task': identifier(args.task), 'provider': args.provider}
            old = response['sessions'].get(alias)
            if old and any(old[k] != binding[k] for k in binding):
                raise ValueError('Alias is already bound; use a new alias.')
            if any(s['session_id'] == binding['session_id'] and s['provider'] == binding['provider'] for a, s in response['sessions'].items() if a != alias):
                raise ValueError('Actual session already has an alias in this response.')
            response['sessions'].setdefault(alias, {**binding, 'snapshots': {}})
            result = {'alias': alias, **binding}
        elif cmd == 'read':
            session = response['sessions'].get(args.session)
            if not session:
                raise ValueError('Bind the session alias first.')
            path = local_path(root, safe_text(args.path))
            if path.suffix.lower() not in ('.md', '.txt') or any(p.startswith('.') or p.lower() in ('secrets', 'credentials') for p in Path(args.path).parts):
                raise ValueError('Only non-hidden documentation .md/.txt outside secrets/credentials is readable.')
            if path.stat().st_size > 2 * 1024 * 1024:
                raise ValueError('Document exceeds 2 MiB.')
            raw = path.read_bytes()
            lines = raw.decode('utf-8-sig').splitlines()
            if not 1 <= args.start <= args.end <= len(lines) or args.end - args.start >= 200:
                raise ValueError('Select an existing range of at most 200 lines.')
            excerpt = '\n'.join(lines[args.start-1:args.end])
            if SECRET.search(excerpt):
                raise ValueError('Selected range contains suspected credentials; no content emitted.')
            record = {'path': args.path, 'session': args.session, 'session_id': session['session_id'], 'task': session['task'],
                      'start': args.start, 'end': args.end, 'section': safe_text(args.section),
                      'sha256': hashlib.sha256(raw).hexdigest(), 'reason': safe_text(args.reason), 'at': now()}
            recorded = state.get('enabled', False)
            if recorded:
                response['reads'].append(record)
            result = {**record, 'content': excerpt, 'debug_recorded': recorded}
        elif cmd == 'snapshot':
            session = response['sessions'].get(args.session)
            if not session:
                raise ValueError('Bind the session alias first.')
            if args.phase in session['snapshots']:
                raise ValueError('Snapshot phase already recorded; use a new response for a new interval.')
            if args.phase == 'end' and 'start' not in session['snapshots']:
                raise ValueError('Record a start snapshot first (unknown is allowed).')
            usage, status, source = clean_usage({}), 'unknown', 'unavailable'
            if not state.get('enabled', False):
                source = 'debug_off'
            elif args.codex_log:
                if session['provider'] != 'codex':
                    raise ValueError('Codex log requires provider codex.')
                try:
                    usage, status = codex_usage(args.codex_log, session['session_id'])
                    source = 'codex_token_count'
                except OSError:
                    source = 'codex_log_unavailable'
            elif args.manual:
                path = local_path(root, args.manual)
                if path.suffix.lower() != '.json' or path.stat().st_size > 65536:
                    raise ValueError('Manual usage requires a JSON file of at most 64 KiB.')
                usage = clean_usage(json.loads(path.read_text(encoding='utf-8-sig')))
                status, source = 'manual_unverified', 'manual'
            snapshot = {**usage, 'status': status, 'source': source, 'at': now(),
                        'enabled': state.get('enabled', False), 'mode_epoch': state.get('mode_epoch', 0)}
            session['snapshots'][args.phase] = snapshot
            result = snapshot
        else:
            result = report(response, state.get('enabled', False))
    return result


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='command', required=True)
    for command in ('on', 'off', 'status', 'bind', 'read', 'snapshot', 'report'):
        sub = commands.add_parser(command)
        sub.add_argument('--run', required=True)
        sub.add_argument('--response', default='main')
        if command in ('bind', 'snapshot', 'read'):
            sub.add_argument('--session', required=True)
        if command == 'bind':
            sub.add_argument('--session-id', required=True)
            sub.add_argument('--task', required=True)
            sub.add_argument('--provider', choices=('codex', 'claude', 'hermes', 'other'), required=True)
        if command == 'read':
            sub.add_argument('--path', required=True)
            sub.add_argument('--start', required=True, type=int)
            sub.add_argument('--end', required=True, type=int)
            sub.add_argument('--section', default='')
            sub.add_argument('--reason', required=True)
        if command == 'snapshot':
            sub.add_argument('--phase', choices=('start', 'end'), required=True)
            source = sub.add_mutually_exclusive_group()
            source.add_argument('--codex-log')
            source.add_argument('--manual')
    return p


def main():
    try:
        result = execute(parser().parse_args())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except UnicodeError:
        print('Error: file encoding failure; no source content emitted.', file=sys.stderr)
        return 2
    except ValueError as error:
        # JSON decoding errors can include raw input; print only our controlled errors.
        print('Error: invalid JSON input.' if isinstance(error, json.JSONDecodeError) else 'Error: ' + str(error), file=sys.stderr)
        return 2
    except OSError:
        print('Error: file access or encoding failure; no source content emitted.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
