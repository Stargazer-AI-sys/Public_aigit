"""Source intake for the publication launcher. Never approves or pays implicitly."""
import json
from collections import Counter
from pathlib import Path

from collector.main import process_file, save_inventory
from collector.scanner import scan_all_files, SUPPORTED_EXTENSIONS
from collector.hasher import calculate_sha256
from .cache import digest
from .core import AnalysisError, from_collector, SOURCE_KEYS
from .main import new_run, write_json
from .workspace import Workspace

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT.parent/'sourcefile'
LABELS = {'approved': '승인 완료', 'new': '신규·분석 필요', 'changed': '원본 변경·분석 필요',
          'pending': '내용·분류 승인 대기', 'held': '보류', 'blocked': '승인 유효성 확인 필요',
          'error': '수집·검증 오류', 'unsupported': '지원하지 않는 파일', 'missing': '원본 누락'}


def _manifest(root, all_files, stable_hashes=None):
    stable_hashes = stable_hashes or {}
    return {'root': str(root), 'files': [{'path': str(p.relative_to(root)),
            'sha256': stable_hashes[str(p)] if str(p) in stable_hashes else calculate_sha256(p)}
            for p in all_files], 'supported': sum(p.suffix.lower() in SUPPORTED_EXTENSIONS for p in all_files)}


def source_manifest(source):
    """Fresh content hashes for every file; never trust the UI metadata hint."""
    root = Path(source).resolve()
    return _manifest(root, scan_all_files(root))


def inspect(source, workspace):
    root = Path(source).resolve()
    all_files = scan_all_files(root)
    paths = [p for p in all_files if p.suffix.lower() in SUPPORTED_EXTENSIONS]
    store = Workspace(workspace, read_only=True) if (Path(workspace)/'library.sqlite3').is_file() else None
    records = store.list(current=False) if store else []
    approved = {r['id'] for r in store.approved()['materials']} if store else set()
    counts = Counter(p.name.casefold() for p in paths)
    items, rows = [], []
    for path in paths:
        row = process_file(path)
        rows.append(row)
        item = {'filename': path.name, 'path': str(path), 'status': 'error'}
        if counts[path.name.casefold()] > 1:
            item['reason'] = '서로 다른 폴더의 동일 파일명은 구분이 필요합니다.'
        else:
            try:
                data = from_collector(row)
                mid = digest({key: data[key] for key in SOURCE_KEYS})
                record = store.reusable(data) if store else None
                item['material_id'] = mid
                if record:
                    item['status'] = 'approved' if mid in approved else record['status']
                    if item['status'] not in ('approved', 'pending', 'held'):
                        item['status'] = 'blocked'
                    if item['status'] == 'approved' and mid not in approved:
                        item['status'] = 'blocked'
                    item['snapshot'] = record['snapshot']
                    item['holds'] = record['holds']
                    item['paths'] = record['classification']['paths']
                else:
                    item['status'] = 'changed' if any(r['analysis']['source']['filename'] == path.name for r in records) else 'new'
            except (AnalysisError, ValueError) as error:
                item['reason'] = getattr(error, 'code', 'COLLECTION_ERROR')
        items.append(item)
    for path in all_files:
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            items.append({'filename': path.name, 'path': str(path), 'status': 'unsupported',
                          'reason': 'TXT/DOCX만 지원합니다.'})
    names = {p.name for p in paths}
    for record in records:
        if record['id'] in approved and record['analysis']['source']['filename'] not in names:
            items.append({'filename': record['analysis']['source']['filename'], 'status': 'missing',
                          'reason': '기존 승인 자료의 원본이 현재 원본 폴더에 없습니다.'})
    # Include unsupported files too: a partial plan may skip them, but source
    # changes after preview must still invalidate the prepared package.
    # process_file already hashes before/after extraction. Reuse that stable
    # hash only in this collection snapshot; later guards still rehash files.
    manifest = _manifest(root, all_files, {row['path']: row['sha256'] for row in rows
                                          if row['status'] == 'success'})
    summary = dict(Counter(i['status'] for i in items))
    return {'source_dir': str(root), 'files': items, 'counts': summary,
            'source_manifest': manifest,
            'ready': bool(paths) and all(i['status'] == 'approved' for i in items),
            'notion_sent': False}, rows


def collect(source, workspace, directory):
    if Path(directory).resolve().is_relative_to(Path(source).resolve()) or Path(workspace).resolve().is_relative_to(Path(source).resolve()):
        raise AnalysisError('SOURCE_PATH_ERROR', '수집 결과와 저장소는 원본 폴더 밖에 지정하세요.')
    report, rows = inspect(source, workspace)
    output = new_run(Path(directory)/'intake')
    save_inventory(rows, output/'inventory.csv')
    report['inventory'] = str(output/'inventory.csv')
    report['report_path'] = str(output/'report.json')
    write_json(output/'report.json', report)
    return report, rows


def analyze(source, workspace, directory, *, filenames=None, allow_api=False,
            max_new_calls=None, ask_api_key=False, model='gpt-6-luna', responses=None,
            retry_failed=False, recover_interrupted=False, api_key=None, _collected=None):
    """Use the existing batch processor only for new/changed, selected inputs."""
    from .batch import run_batch
    from .cache import run_with_cache
    from .openai_provider import OpenAIProvider
    from .core import load_schema
    from .schemas import DEFAULT_SCHEMA
    if allow_api and (not isinstance(max_new_calls, int) or isinstance(max_new_calls, bool)
                      or not 1 <= max_new_calls <= 100):
        raise AnalysisError('API_SCOPE_REQUIRED', '--allow-api에는 --max-new-calls 1~100을 명시하세요.')
    if allow_api and responses:
        raise AnalysisError('API_SCOPE_REQUIRED', '저장 응답 시험과 새 유료 분석을 함께 지정할 수 없습니다.')
    report, rows = _collected if _collected is not None else collect(source, workspace, directory)
    selected = set(filenames or [])
    if selected - {i['filename'] for i in report['files']}:
        raise AnalysisError('SOURCE_SELECTION_ERROR', '--file에 원본 폴더의 정확한 파일명을 지정하세요.')
    wanted = {i['path'] for i in report['files'] if i['status'] in ('new', 'changed')
              and (not selected or i['filename'] in selected)}
    candidates = [row for row in rows if row['path'] in wanted]
    ready, misses = [], []
    if not allow_api and not responses:
        schema = load_schema(DEFAULT_SCHEMA)
        for row in candidates:
            engine = OpenAIProvider(schema, model=model)
            result, _ = run_with_cache(from_collector(row), engine, schema,
                Path(workspace)/'cache', Path(workspace)/'runs', reuse_only=True)
            if result['status'] == 'SUCCESS':
                ready.append(row)
            else:
                misses.append({'filename': row['filename'], 'code': result['error']['code']})
    else:
        # Do not create failed jobs for files outside this invocation's allowance.
        ready = candidates[:max_new_calls] if allow_api else candidates
        misses = [{'filename': row['filename'], 'code': 'CALL_SCOPE_LIMIT'} for row in candidates[len(ready):]]
    batch = None
    if ready:
        if source_manifest(source) != report['source_manifest']:
            raise AnalysisError('SOURCE_CHANGED', '수집 후 원본 폴더가 변경됐습니다. 다시 수집하세요.')
        inventory = Path(report['inventory']).with_name('analysis_inventory.csv')
        save_inventory(ready, inventory)
        batch = run_batch(inventory, workspace, provider='mock-file' if responses else 'openai',
            responses=responses, allow_api=allow_api, max_new_calls=max_new_calls or 1,
            ask_api_key=ask_api_key, model=model, retry_failed=retry_failed,
            recover_interrupted=recover_interrupted,
            provider_factory=(lambda data: OpenAIProvider(load_schema(DEFAULT_SCHEMA), api_key=api_key, model=model))
                if api_key is not None and not responses else None)
    after, _ = inspect(source, workspace)
    after.update(analysis=batch, analysis_not_run=misses, report_path=report['report_path'],
                 new_api_attempts=batch['new_api_attempts'] if batch else 0)
    write_json(Path(report['report_path']), after)
    return after


def prepare_sources(workspace, target, home, directory, output, source=DEFAULT_SOURCE, *, allow_partial=False):
    from .notion_prepared import prepare
    report, rows = collect(source, workspace, directory)
    if any(i['status'] in ('new', 'changed') for i in report['files']):
        # Reuse valid caches, but a cache miss is an actionable state, never a
        # paid request or a failed batch job that requires an accidental retry.
        report = analyze(source, workspace, directory, _collected=(report, rows))
    report['package'] = None
    report['all_sources_ready'] = report['ready']
    if allow_partial and not report['ready']:
        # Never waive validation or approval. Only omit inputs without a valid
        # approval; published scope preservation remains enforced by prepare().
        approved = Workspace(workspace, read_only=True).approved()['materials']
        approved_names = {r['analysis']['source']['filename'] for r in approved}
        skipped = [i for i in report['files'] if i['status'] != 'approved']
        unsafe = [i for i in skipped if i['filename'] in approved_names
                  and i['status'] not in ('missing', 'unsupported')]
        if unsafe:
            raise AnalysisError('PARTIAL_SOURCE_CONFLICT', '변경·중복 원본과 기존 승인본이 충돌합니다. 해당 자료를 먼저 확인하세요.')
        report['retained'] = [i for i in skipped if i['status'] == 'missing' and i['filename'] in approved_names]
        report['skipped'] = [i for i in skipped if i not in report['retained']]
        report['ready'] = bool(approved)
    if report['ready']:
        manifest = report['source_manifest']
        if source_manifest(source) != manifest or Path(output).resolve().is_relative_to(Path(source).resolve()):
            raise AnalysisError('SOURCE_CHANGED', '원본 변경 여부와 결과 폴더 위치를 확인하고 다시 준비하세요.')
        result = prepare(workspace, target, home, directory, output, source_manifest=manifest)
        if source_manifest(source) != manifest:
            raise AnalysisError('SOURCE_CHANGED', '준비 중 원본 폴더가 변경됐습니다. 다시 준비하세요.')
        report.update(result)
    return report


def print_report(report):
    print('원본 처리: '+' · '.join(f'{LABELS.get(k,k)} {v}건' for k, v in report['counts'].items()), flush=True)
    for item in report['files']:
        if item['status'] != 'approved':
            print(f"- {item['filename']}: {LABELS.get(item['status'],item['status'])}", flush=True)
    if not report['ready']:
        print('게시 준비 보류: 미처리 원본이 있습니다. analyze로 분석한 뒤 review에서 승인하세요. 자동 승인·Notion 전송 없음.', flush=True)
    print('이번 새 API 요청: '+str(report.get('new_api_attempts', 0))+'회', flush=True)
    summary = {k: report[k] for k in ('ready', 'counts', 'package', 'preview', 'changed_fronts',
                                     'materials', 'report_path', 'new_api_attempts', 'notion_sent') if k in report}
    summary['unprocessed'] = [{'filename': i['filename'], 'status': i['status'],
                              **({'reason': i['reason']} if 'reason' in i else {})}
                             for i in report['files'] if i['status'] != 'approved']
    if report.get('analysis'):
        summary['analysis_report'] = report['analysis'].get('report_path')
    print(json.dumps(summary, ensure_ascii=False), flush=True)
