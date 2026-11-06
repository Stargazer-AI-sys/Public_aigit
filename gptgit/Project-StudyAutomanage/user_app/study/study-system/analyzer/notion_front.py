"""Refresh existing learning navigation after publication, with conflict guards."""
import copy
import json
import re
from pathlib import Path
from types import SimpleNamespace

from .notion_mcp import DeliveryError, NotionMCP, page_id
from .notion_reader import build_front_pages
from tools.notion_bridge.verify import body_normalized, responses


def normalized_body(body):
    body = body_normalized(body)
    def table(match):
        value = re.sub(r'>\s+<', '><', match[0])
        return re.sub(r'<table\b([^>]*)>', lambda m: '<table ' + ' '.join(sorted(re.findall(r'[\w-]+="[^"]*"', m[1]))) + '>', value)
    return re.sub(r'<table\b[^>]*>[\s\S]*?</table>', table, body)


def refresh(pages, baseline, remote, checkpoint, *, guard_changes=False):
    """Read only changed fronts; never replace a manually edited baseline."""
    if getattr(remote, 'local_source', False):
        return refresh_local(pages, baseline, remote, checkpoint, guard_changes=guard_changes)
    state = copy.deepcopy(baseline)
    report = {'total': len(pages), 'unchanged': 0, 'reads': 0, 'writes': 0,
              'recovered': 0, 'errors': [], 'verified_page_ids': []}
    changed = []
    for page in pages:
        pid = page_id(page['page_id'])
        saved = state.get(pid)
        if saved and normalized_body(saved['expected_body']) == normalized_body(page['body']):
            report['unchanged'] += 1
        else:
            changed.append((pid, page['body'], saved))
    if not changed:
        return report
    def fetch(ids):
        result = remote.calls([{'tool': 'fetch', 'args': {'id': pid}} for pid in ids])
        report['reads'] += len(ids)
        return {pid: remote.parse_page(pid, item) for pid, item in zip(ids, result)}
    observed = fetch([pid for pid, _, _ in changed])
    pending = []
    for pid, desired, saved in changed:
        current = observed[pid]['body']
        if normalized_body(current) == normalized_body(desired):
            report['recovered'] += 1
            state[pid] = {'expected_body': desired, 'observed_body': current}
            checkpoint(state)
            report['verified_page_ids'].append(pid)
        elif not saved or normalized_body(current) != normalized_body(saved['observed_body']):
            report['errors'].append({'code': 'FRONT_REMOTE_CONFLICT', 'page_id': pid})
        else:
            pending.append((pid, desired))
    if pending:
        remote.calls([{'tool': 'notion_update_page', 'args': {
            'page_id': pid, 'command': 'replace_content', 'new_str': desired,
            'allow_async': False}} for pid, desired in pending])
        report['writes'] += len(pending)
        observed = fetch([pid for pid, _ in pending])
        for pid, desired in pending:
            current = observed[pid]['body']
            if normalized_body(current) != normalized_body(desired):
                report['errors'].append({'code': 'FRONT_READBACK_MISMATCH', 'page_id': pid})
                continue
            state[pid] = {'expected_body': desired, 'observed_body': current}
            checkpoint(state)
            report['verified_page_ids'].append(pid)
    return report


def refresh_local(pages, baseline, remote, checkpoint, *, guard_changes=False):
    """Generated navigation is local-owned; read only an uncertain prior write."""
    from .notion_publisher import require_ack
    state = copy.deepcopy(baseline)
    report = {'total': len(pages), 'unchanged': 0, 'reads': 0, 'writes': 0,
              'recovered': 0, 'errors': [], 'verified_page_ids': [],
              'acknowledged_page_ids': [], 'publication_policy': 'local-source'}
    pending = []
    for page in pages:
        pid, desired = page_id(page['page_id']), page['body']
        saved = state.get(pid)
        if not saved:
            report['errors'].append({'code': 'FRONT_BASELINE_MISSING', 'page_id': pid})
            continue
        if saved.get('pending_body') is not None:
            raw = remote.parse_page(pid, remote.calls([{'tool': 'fetch', 'args': {'id': pid}}])[0])
            report['reads'] += 1
            if normalized_body(raw['body']) == normalized_body(saved['pending_body']):
                saved = {'expected_body': saved['pending_body'], 'observed_body': raw['body'],
                         'confirmation': 'readback'}
                state[pid] = saved
                checkpoint(state)
                report['recovered'] += 1
                report['verified_page_ids'].append(pid)
            elif (not getattr(remote, 'retry_requested', False)
                  or normalized_body(raw['body']) != normalized_body(saved['observed_body'])):
                report['errors'].append({'code': 'FRONT_UNRESOLVED_WRITE', 'page_id': pid})
                continue
            else:
                saved = dict(saved)
                saved.pop('pending_body', None)
                state[pid] = saved
                checkpoint(state)
        if normalized_body(saved['expected_body']) == normalized_body(desired):
            report['unchanged'] += 1
            continue
        if guard_changes:
            raw = remote.parse_page(pid, remote.calls([{'tool': 'fetch', 'args': {'id': pid}}])[0])
            report['reads'] += 1
            if normalized_body(raw['body']) == normalized_body(desired):
                state[pid] = {'expected_body': desired, 'observed_body': raw['body'],
                              'confirmation': 'readback'}
                checkpoint(state)
                report['recovered'] += 1
                report['verified_page_ids'].append(pid)
                continue
            if normalized_body(raw['body']) != normalized_body(saved['observed_body']):
                report['errors'].append({'code': 'FRONT_REMOTE_CONFLICT', 'page_id': pid})
                continue
        state[pid] = dict(saved, pending_body=desired)
        pending.append((pid, desired))
    if pending:
        checkpoint(state)  # Persist every intent before submitting the batch.
        results = remote.calls([{'tool': 'notion_update_page', 'args': {
            'page_id': pid, 'command': 'replace_content', 'new_str': desired,
            'allow_async': False}} for pid, desired in pending])
        if len(results) != len(pending):
            raise DeliveryError('NOTION_WRITE_UNCERTAIN')
        for (pid, desired), result in zip(pending, results):
            require_ack(result, pid)
            report['writes'] += 1
            state[pid] = {'expected_body': desired, 'observed_body': desired,
                          'confirmation': 'write-response'}
            checkpoint(state)
            report['acknowledged_page_ids'].append(pid)
    return report


def render_front_pages(plan, store, target, home):
    """Pure local rendering shared by preparation, validation and delivery."""
    from .notion_sync import material_key, make_plan
    policy = store.policy()
    approved = {'materials': store.approved_records(policy=policy)}
    selected = {e['key'] for e in plan['entities'] if e['kind'] == 'material'}
    approved['materials'] = [r for r in approved['materials'] if material_key(r) in selected]
    from .classification import knowledge_index
    approved.update(knowledge_index(approved['materials'], policy))
    navigation_plan = None
    if plan.get('publication_mode') == 'materials':
        navigation_target = copy.deepcopy(target)
        navigation_target['publication'] = {'mode': 'full'}
        navigation_plan = make_plan(store, target=navigation_target,
                                    material_ids=[r['id'] for r in approved['materials']])
    return build_front_pages(plan, approved, policy, target, home,
                             navigation_plan=navigation_plan)


def refresh_front(plan, store, target, directory, remote, *, home_file=None, prepared_pages=None):
    from .main import write_json
    root = Path(directory)
    home_file = Path(home_file) if home_file else Path(__file__).resolve().parents[1]/'config/notion_home.json'
    if not target.get('reader') or not home_file.is_file():
        raise DeliveryError('FRONT_CONFIG_MISSING')
    home = json.loads(home_file.read_text(encoding='utf-8-sig'))
    pages = render_front_pages(plan, store, target, home)
    if prepared_pages is not None and pages != prepared_pages:
        raise DeliveryError('PUBLISH_STALE')
    folder = root/'front'
    folder.mkdir(parents=True, exist_ok=True)
    state_file = folder/'state.json'
    if state_file.is_file():
        baseline = json.loads(state_file.read_text(encoding='utf-8-sig'))
    else:
        if not (root/'reader/front_pages.json').is_file() or not (root/'reader/front_readback.json').is_file():
            raise DeliveryError('FRONT_BASELINE_MISSING')
        expected = {page_id(p['page_id']): p['body'] for p in json.loads(
            (root/'reader/front_pages.json').read_text(encoding='utf-8-sig'))}
        baseline = {}
        for result in responses(root/'reader/front_readback.json'):
            # Parsing historical files is local I/O, not a current remote read.
            raw = NotionMCP.parse_page(SimpleNamespace(target=target), result['id'], result)
            pid = raw['id']
            if pid in expected:
                baseline[pid] = {'expected_body': expected[pid], 'observed_body': raw['body']}
    def checkpoint(state):
        temp = folder/'state.tmp'
        write_json(temp, state)
        temp.replace(state_file)
    # Persist the verified historical baseline before any remote writes.
    checkpoint(baseline)
    write_json(folder/'desired_pages.json', pages)
    report = refresh(pages, baseline, remote, checkpoint,
                     guard_changes=plan.get('publication_mode') == 'materials')
    write_json(folder/'report.json', report)
    return report
