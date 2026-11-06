"""Reviewable local publication packages; delivery uses the connected MCP bridge."""
import copy
import hashlib
import html
import json
import re
from pathlib import Path

from .cache import digest
from .core import AnalysisError
from .main import new_run, write_json
from .notion_front import normalized_body, render_front_pages, refresh_front
from .notion_mcp import check_scope
from .notion_reader import refresh_reader_target
from .notion_sync import make_plan, preview, DeliveryError
from .workspace import Workspace

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('notion_prepared.py', 'notion_reader.py', 'notion_front.py',
           'learning_categories.py', 'notion_sync.py', 'notion_publisher.py', 'notion_mcp.py',
           'classification.py', 'curriculum.py', 'workspace.py', 'render.py')
SOURCES += ('notion_intake.py',)


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def guards(store, target_file, home_file):
    return {'materials': sorted([r['id'], r['snapshot'], r['status']] for r in store.list()),
            'policy': digest(store.policy()), 'target': file_digest(target_file),
            'home': file_digest(home_file),
            'sources': {name: file_digest(ROOT/'analyzer'/name) for name in SOURCES},
            'bridge_sources': {name: file_digest(ROOT/'tools/notion_bridge'/name)
                               for name in ('dispatch.js', 'run_dispatch.js', 'state.mjs')}}


def placeholder(key):
    return '__NEW_PAGE_'+key.replace(':', '_')+'__'


def readable_html(body):
    """Safe reading preview of the saved body; never execute embedded markup."""
    links = []
    def link(match):
        url, label = match.groups()
        if '__NEW_PAGE_' in url:
            return label+' (게시 후 연결)'
        if not url.startswith('https://'):
            return label
        links.append('<a href="'+html.escape(url, quote=True)+'">'+html.escape(label)+'</a>')
        return f'PREVIEWLINK{len(links)-1}END'
    body = re.sub(r'<(?:mention-page|page) url="([^"]+)"[^>]*>(.*?)</(?:mention-page|page)>', link, body)
    body = re.sub(r'</td>\s*<td>', '　|　', body)
    body = re.sub(r'</tr>', '\n', body)
    body = re.sub(r'<[^>]+>', '', body)
    output, code = [], False
    for line in body.splitlines():
        value = line.strip()
        if value.startswith('```'):
            output.append('</pre>' if code else '<pre>'); code = not code; continue
        escaped = html.escape(value)
        if code:
            output.append(escaped+'\n'); continue
        heading = re.match(r'^(#{1,6})\s+(.*)', value)
        if heading:
            level = min(6, len(heading[1])+1)
            output.append(f'<h{level}>'+html.escape(heading[2])+f'</h{level}>')
        elif value:
            output.append('<p>'+escaped+'</p>')
    if code:
        output.append('</pre>')
    result = ''.join(output)
    for i, value in enumerate(links):
        result = result.replace(f'PREVIEWLINK{i}END', value)
    return result


def prepare(workspace, target_file, home_file, directory, output_dir, *, source_manifest=None):
    store = Workspace(workspace, read_only=True)
    target = refresh_reader_target(load(target_file), Path(directory)/'outbox')
    plan = make_plan(store, target=target)
    if plan.get('publication_mode') != 'materials':
        raise DeliveryError('PREPARE_REQUIRES_MATERIAL_MODE')
    if not plan['approvals']:
        raise DeliveryError('NO_APPROVED_MATERIALS')
    scope = check_scope(plan, directory)
    render_target = copy.deepcopy(target)
    unbound = [e['key'] for e in plan['entities'] if e['key'] not in render_target['reader']['pages']]
    for key in unbound:
        render_target['reader']['pages'][key] = placeholder(key)
    pages = render_front_pages(plan, store, render_target, load(home_file))
    home = load(home_file)
    names = {p['id'].replace('-', ''): p['properties']['title'] for p in home['navigation_pages']}
    names.update({pid.replace('-', ''): name for name, pid in target['reader']['indexes'].items()})
    names[target['parent_page']['id'].replace('-', '')] = target['parent_page']['name']
    state_file = Path(directory)/'front/state.json'
    state = load(state_file) if state_file.is_file() else {}
    changed = [p['page_id'] for p in pages if normalized_body(p['body']) !=
               normalized_body(state.get(p['page_id'].replace('-', ''), {}).get('expected_body', ''))]
    package = {'version': 1, 'transport': 'connected-notion-mcp',
               'workspace': str(Path(workspace).resolve()), 'target_file': str(Path(target_file).resolve()),
               'home_file': str(Path(home_file).resolve()), 'directory': str(Path(directory).resolve()),
               'guard': guards(store, target_file, home_file), 'target': target,
               'plan': plan, 'scope': scope, 'front_pages': pages, 'unbound_material_keys': unbound,
               'changed_front_ids': changed}
    if source_manifest is not None:
        package['source_manifest'] = source_manifest
    package['digest'] = digest(package)
    output = new_run(output_dir)
    write_json(output/'package.json', package)
    text = preview(plan)+'\n\n# 학습 화면\n\n'
    for page in pages:
        label = '변경' if page['page_id'] in changed else '유지'
        text += f"## {label} · {page['page_id']}\n\n{page['body']}\n\n"
    (output/'preview.md').write_text(text, encoding='utf-8')
    title = 'Notion 게시 미리보기'
    document = ('<!doctype html><html lang="ko"><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>'+title+'</title><style>body{max-width:1100px;margin:32px auto;padding:0 24px;'
                'font:16px/1.65 system-ui;color:#243247}pre{white-space:pre-wrap;overflow-wrap:anywhere}'
                'details{padding:12px;border-bottom:1px solid #ddd}summary{cursor:pointer}</style>'
                '<h1>'+title+'</h1><p>승인 자료 '+str(len(plan['approvals']))+'건 · 화면 변경 '
                +str(len(changed))+'개 · 실제 전송 전 로컬 확인</p>'
                '<p>신규 자료의 링크는 게시가 완료된 뒤 연결됩니다. '
                '전송에는 현재 채팅의 Notion 연결 도구 중계가 필요합니다.</p>')
    for entity in plan['entities']:
        document += '<details><summary>자료 · '+html.escape(entity['properties']['name'])+'</summary>'+readable_html(entity['body'])+'</details>'
    for page in pages:
        label = names.get(page['page_id'].replace('-', ''), page['page_id'])
        document += '<details><summary>'+('변경' if page['page_id'] in changed else '유지')+' · '+html.escape(label)+'</summary>'+readable_html(page['body'])+'</details>'
    (output/'preview.html').write_text(document+'</html>', encoding='utf-8')
    return {'package': str(output/'package.json'), 'preview': str(output/'preview.html'),
            'materials': len(plan['approvals']), 'changed_fronts': len(changed), 'notion_sent': False}


def validate(package):
    value = dict(package)
    saved = value.pop('digest', None)
    if saved != digest(value) or package.get('version') != 1:
        raise DeliveryError('PREPARED_PACKAGE_CHANGED')
    store = Workspace(package['workspace'], read_only=True)
    if guards(store, package['target_file'], package['home_file']) != package['guard']:
        raise DeliveryError('PUBLISH_STALE')
    if 'source_manifest' in package:
        from .notion_intake import source_manifest
        if source_manifest(package['source_manifest']['root']) != package['source_manifest']:
            raise DeliveryError('PUBLISH_SOURCE_CHANGED')
    current = refresh_reader_target(load(package['target_file']), Path(package['directory'])/'outbox')
    expected = copy.deepcopy(package['target'])
    for key, pid in expected['reader']['pages'].items():
        if current['reader']['pages'].get(key) != pid:
            raise DeliveryError('PUBLISH_STALE')
    expected['reader']['pages'] = current['reader']['pages']
    if expected != current:
        raise DeliveryError('PUBLISH_STALE')
    # Recompute content as well as checking the package's digest. A digest is
    # an integrity check, not authorization for arbitrary edited remote writes.
    plan = make_plan(store, target=package['target'])
    if plan != package['plan'] or check_scope(plan, package['directory']) != package['scope']:
        raise DeliveryError('PUBLISH_STALE')
    target = copy.deepcopy(package['target'])
    for key in package['unbound_material_keys']:
        target['reader']['pages'][key] = placeholder(key)
    if render_front_pages(plan, store, target, load(package['home_file'])) != package['front_pages']:
        raise DeliveryError('PUBLISH_STALE')
    return store


def bind_pages(package, target):
    pages = copy.deepcopy(package['front_pages'])
    for key in package['unbound_material_keys']:
        pid = target['reader']['pages'].get(key)
        if not pid:
            raise DeliveryError('PREPARED_BINDING_MISSING')
        for page in pages:
            page['body'] = page['body'].replace(placeholder(key), pid)
    return pages


def publish(package_file, *, call, call_many, retry=False, recover_interrupted=False):
    from .notion_publisher import NotionPublisher, publish_staged
    package = load(package_file)
    store = validate(package)  # No remote calls on stale packages.
    root = Path(package['directory'])
    output = new_run(root/'runs')
    before = store.path.read_bytes()
    def guarded_call(tool, args):
        validate(package)
        return call(tool, args)
    def guarded_many(requests):
        validate(package)
        return call_many(requests)
    target, plan = copy.deepcopy(package['target']), copy.deepcopy(package['plan'])
    remote = NotionPublisher(target, root/'outbox', call=guarded_call, call_many=guarded_many)
    remote.retry_requested = retry
    report = {'mode': 'prepared-connected-notion-mcp', 'package_digest': package['digest'],
              'errors': [], 'notion_sent': False, 'front_completion': 'incomplete'}
    write_json(output/'status.json', {'state': 'running', 'package': str(Path(package_file).resolve())})
    try:
        plan, target, remote, result = publish_staged(plan, store, remote, root/'outbox', target=target,
            material_ids=list(package['plan']['approvals']), retry=retry, recover_interrupted=recover_interrupted)
        report.update(result)
        report['entity_writes'] = result.get('writes', 0)
        if not report['errors']:
            validate(package)
            report['front_pages'] = refresh_front(plan, store, target, root, remote,
                home_file=package['home_file'], prepared_pages=bind_pages(package, target))
            report['errors'].extend(report['front_pages']['errors'])
            report['notion_sent'] = bool(report['notion_sent'] or report['front_pages']['writes'])
            report['front_completion'] = 'complete' if not report['errors'] else 'incomplete'
        if not report['errors']:
            write_json(root/'published_scope.json', package['scope'])
    except (AnalysisError, DeliveryError) as error:
        report['errors'].append({'code': error.code})
        if not report['notion_sent'] and remote.metrics['tool_calls'].get('notion_update_page'):
            report['notion_sent'] = None
    except KeyboardInterrupt:
        report['errors'].append({'code': 'PUBLICATION_INTERRUPTED'})
        report['notion_sent'] = None
    report['approval_db_unchanged'] = before == store.path.read_bytes()
    report['transport_metrics'] = remote.metrics
    report['result_path'] = str(output/'report.json')
    write_json(output/'report.json', report)
    write_json(output/'status.json', {'state': 'failed' if report['errors'] else 'complete',
                                     'result_path': report['result_path']})
    return report
