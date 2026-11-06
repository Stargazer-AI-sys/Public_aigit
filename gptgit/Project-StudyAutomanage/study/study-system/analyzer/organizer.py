"""Classification/library CLI; existing single-material Analyzer stays available."""
import json
from pathlib import Path

from .core import AnalysisError, strict_json, from_collector
from .workspace import Workspace

DEFAULT_WORKSPACE = Path(__file__).resolve().parent.parent / 'output/knowledge_base'


def register(sub):
    batch = sub.add_parser('batch', help='여러 자료 분류·분석 및 중단 후 재개')
    batch.add_argument('--inventory', type=Path, required=True)
    batch.add_argument('--workspace', type=Path, default=DEFAULT_WORKSPACE)
    batch.add_argument('--responses', type=Path, help='모의 응답 파일명:경로 JSON')
    batch.add_argument('--provider', choices=['mock-file', 'openai'], default='mock-file')
    batch.add_argument('--allow-api', action='store_true', help='새 유료 분석 허용; 미지정 시 API 재사용만')
    batch.add_argument('--max-new-calls', type=int, default=1)
    batch.add_argument('--ask-api-key', action='store_true')
    batch.add_argument('--model', choices=['gpt-6-luna', 'gpt-6.1-sol'], default='gpt-6-luna')
    batch.add_argument('--retry-failed', action='store_true')
    batch.add_argument('--reanalyze', action='store_true')
    batch.add_argument('--recover-interrupted', action='store_true', help='이전 실행이 종료됐음을 확인한 뒤 잠금·중단 상태 복구')
    library = sub.add_parser('library', help='분류 지식베이스·자료 연결·승인 관리')
    library.add_argument('--workspace', type=Path, default=DEFAULT_WORKSPACE)
    commands = library.add_subparsers(dest='library_action', required=True)
    imp = commands.add_parser('import', help='검증된 기존 분석을 원문과 대조해 가져오기')
    imp.add_argument('--run-dir', type=Path)
    imp.add_argument('--analysis', type=Path)
    imp.add_argument('--source-file', type=Path)
    commands.add_parser('catalog')
    exp = commands.add_parser('export', help='승인된 자료만 로컬 스냅샷으로 저장; Notion 전송 없음')
    exp.add_argument('--output-dir', type=Path)
    decision = commands.add_parser('decide')
    decision.add_argument('--id', required=True)
    decision.add_argument('--snapshot', required=True)
    decision.add_argument('--action', required=True, choices=['approve', 'hold'])
    decision.add_argument('--note', default='')
    policy = commands.add_parser('policy')
    policy.add_argument('--file', type=Path, help='미지정 시 현재 정책 확인')
    hold = commands.add_parser('release-hold')
    hold.add_argument('--id', required=True); hold.add_argument('--snapshot', required=True)
    hold.add_argument('--reason', required=True)
    review = sub.add_parser('review', help='로컬 분류·지식베이스 검토 화면 실행')
    review.add_argument('--workspace', type=Path, default=DEFAULT_WORKSPACE)
    review.add_argument('--port', type=int, default=8765)


def read(path):
    return strict_json(Path(path).read_text(encoding='utf-8-sig'))


def import_material(store, *, run_dir=None, analysis_file=None, source_file=None):
    location = None
    if run_dir:
        run = Path(run_dir)
        target = run/'success/analysis.json' if (run/'success/analysis.json').exists() else run/'analysis.json'
        analysis = read(target)
        data = read(run/'analyzer_input.json')
        origin = str(run.resolve())
    elif analysis_file and source_file:
        from collector.main import process_file
        analysis = read(analysis_file)
        data = from_collector(process_file(Path(source_file)))
        origin = str(Path(analysis_file).resolve()); location = source_file
    else:
        raise AnalysisError('LIBRARY_INPUT_ERROR', '--run-dir 또는 --analysis와 --source-file이 필요합니다.')
    return store.ingest(analysis, data, origin=origin, location=location)


def export_approved(store, output=None):
    from .main import new_run, write_json
    snapshot = store.approved()
    path = new_run(output or store.root/'approved_exports')
    write_json(path/'approved_snapshot.json', snapshot)
    return path/'approved_snapshot.json', len(snapshot['materials'])


def execute(args):
    if args.command == 'batch':
        from .batch import run_batch
        result = run_batch(args.inventory, args.workspace, responses=args.responses, provider=args.provider,
                           allow_api=args.allow_api, max_new_calls=args.max_new_calls, retry_failed=args.retry_failed,
                           reanalyze=args.reanalyze, recover_interrupted=args.recover_interrupted,
                           ask_api_key=args.ask_api_key, model=args.model)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['status'] == 'PASS' else 1
    store = Workspace(args.workspace)
    if args.command == 'review':
        from .review_server import serve
        serve(store, args.port)
        return 0
    action = args.library_action
    if action == 'import':
        result = import_material(store, run_dir=args.run_dir, analysis_file=args.analysis, source_file=args.source_file)
        print(json.dumps({'id': result['id'], 'classification': result['classification'], 'status': result['status']}, ensure_ascii=False, indent=2))
    elif action == 'catalog':
        catalog = store.catalog()
        print(json.dumps({'materials': [{'id': r['id'], 'filename': r['analysis']['source']['filename'],
                      'paths': r['classification']['paths'], 'status': r['status'], 'snapshot': r['snapshot'], 'holds': r['holds']} for r in catalog['materials']],
                         'categories': catalog['categories'], 'concepts_count': len(catalog['concepts'])}, ensure_ascii=False, indent=2))
    elif action == 'export':
        path, count = export_approved(store, args.output_dir)
        print(f'승인 자료 {count}건 저장: {path}\nNotion 전송 없음')
    elif action == 'decide':
        result = store.decide(args.id, args.snapshot, args.action, note=args.note)
        print(json.dumps({'status': result['status'], 'snapshot': result['snapshot']}, ensure_ascii=False))
    elif action == 'release-hold':
        result = store.release_hold(args.id, args.snapshot, args.reason)
        print(json.dumps({'status': result['status'], 'snapshot': result['snapshot']}, ensure_ascii=False))
    elif action == 'policy':
        if args.file:
            store.set_policy(read(args.file))
        print(json.dumps(store.policy(), ensure_ascii=False, indent=2))
    return 0
