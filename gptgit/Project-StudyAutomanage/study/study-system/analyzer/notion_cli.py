"""Local planning and explicitly requested delivery through the connected bridge."""
import json
from pathlib import Path

from .core import AnalysisError, strict_json
from .notion_sync import MockNotion, deliver_mock, make_plan, mapping_for, preview
from .workspace import Workspace


def register(sub):
    from .organizer import DEFAULT_WORKSPACE
    parser = sub.add_parser('notion', help='Notion 게시 준비·미리보기·연결 도구 전송')
    parser.add_argument('--workspace', type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument('--target', type=Path, default=Path(__file__).resolve().parents[1]/'config/notion_target.json',
                        help='대상 페이지·DB 설정 (기본 config/notion_target.json)')
    commands = parser.add_subparsers(dest='notion_action', required=True)
    prepare = commands.add_parser('prepare', help='자료·학습 화면·변경 대상을 로컬 게시 패키지로 준비')
    prepare.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parents[1]/'output/notion_live/prepared')
    prepare.add_argument('--publication-dir', type=Path, default=Path(__file__).resolve().parents[1]/'output/notion_live')
    prepare.add_argument('--home', type=Path, default=Path(__file__).resolve().parents[1]/'config/notion_home.json')
    from .notion_intake import DEFAULT_SOURCE
    prepare.add_argument('--source-dir', type=Path, default=DEFAULT_SOURCE)
    status = commands.add_parser('status', help='원본별 신규·변경·승인 상태 확인; 유료 호출 없음')
    status.add_argument('--source-dir', type=Path, default=DEFAULT_SOURCE)
    analyze = commands.add_parser('analyze', help='신규·변경 원본만 수집·분석·분류; 자동 승인 없음')
    analyze.add_argument('--source-dir', type=Path, default=DEFAULT_SOURCE)
    analyze.add_argument('--publication-dir', type=Path, default=Path(__file__).resolve().parents[1]/'output/notion_live')
    analyze.add_argument('--file', dest='filenames', action='append', help='처리할 정확한 파일명; 여러 번 지정 가능')
    analyze.add_argument('--allow-api', action='store_true', help='명시한 한도 안에서 새 유료 분석 허용')
    analyze.add_argument('--max-new-calls', type=int, help='유료 분석 허용 시 필수 호출 한도')
    analyze.add_argument('--ask-api-key', action='store_true')
    analyze.add_argument('--model', choices=['gpt-6-luna', 'gpt-6.1-sol'], default='gpt-6-luna')
    analyze.add_argument('--responses', type=Path, help='로컬 시험용 저장 응답 매핑')
    analyze.add_argument('--retry-failed', action='store_true')
    analyze.add_argument('--recover-interrupted', action='store_true')
    review = commands.add_parser('review', help='기존 내용·분류 승인 화면; 종료 후 게시 준비 재확인')
    review.add_argument('--source-dir', type=Path, default=DEFAULT_SOURCE)
    review.add_argument('--publication-dir', type=Path, default=Path(__file__).resolve().parents[1]/'output/notion_live')
    review.add_argument('--home', type=Path, default=Path(__file__).resolve().parents[1]/'config/notion_home.json')
    review.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parents[1]/'output/notion_live/prepared')
    review.add_argument('--port', type=int, default=8765)
    send = commands.add_parser('send', help='확인한 패키지 전송; 현재 채팅의 Notion 도구 중계 필요')
    send.add_argument('--package', type=Path, required=True)
    send.add_argument('--allow-notion-write', action='store_true', required=True)
    send.add_argument('--retry', action='store_true', help='조회 후 미완료 부분만 명시적으로 복구')
    send.add_argument('--recover-interrupted', action='store_true')
    commands.add_parser('mapping', help='DB 속성·관계 구조안')
    plan = commands.add_parser('plan', help='현재 승인 결과의 게시 계획·읽기용 미리보기')
    plan.add_argument('--output-dir', type=Path, required=True)
    simulate = commands.add_parser('simulate', help='저장 계획을 검증한 뒤 로컬 모의 대상으로 전송')
    simulate.add_argument('--plan', type=Path, required=True)
    simulate.add_argument('--output-dir', type=Path, required=True)
    simulate.add_argument('--retry', action='store_true', help='실패/응답 유실 작업을 조회 후 명시적으로 재개')
    simulate.add_argument('--recover-interrupted', action='store_true', help='이전 작업 종료 확인 후 잠금 복구')


def execute(args):
    from .main import new_run, write_json
    if args.notion_action == 'prepare':
        from .notion_intake import prepare_sources, print_report
        result = prepare_sources(args.workspace, args.target, args.home, args.publication_dir, args.output_dir, args.source_dir)
        print_report(result); return 0 if result['ready'] else 3
    if args.notion_action == 'status':
        from .notion_intake import inspect, print_report
        result, _ = inspect(args.source_dir, args.workspace)
        print_report(result); return 0 if result['ready'] else 3
    if args.notion_action == 'analyze':
        from .notion_intake import analyze, print_report
        result = analyze(args.source_dir, args.workspace, args.publication_dir,
            filenames=args.filenames, allow_api=args.allow_api, max_new_calls=args.max_new_calls,
            ask_api_key=args.ask_api_key, model=args.model, responses=args.responses,
            retry_failed=args.retry_failed, recover_interrupted=args.recover_interrupted)
        print_report(result); return 0 if result['ready'] else 3
    if args.notion_action == 'review':
        from .notion_intake import prepare_sources, inspect, print_report
        from .review_server import serve
        before, _ = inspect(args.source_dir, args.workspace)
        print_report(before)
        if before['ready']:
            result = prepare_sources(args.workspace, args.target, args.home, args.publication_dir, args.output_dir, args.source_dir)
            print_report(result); return 0 if result['ready'] else 3
        if not any(i['status'] in ('pending', 'held') for i in before['files']):
            print('승인 화면에 올릴 분석 결과가 없습니다. 먼저 analyze로 신규 자료를 처리하세요.', flush=True)
            return 3
        print('표시된 로컬 URL에서 내용·분류를 확인하고 승인한 뒤 Ctrl+C로 종료하세요.', flush=True)
        serve(Workspace(args.workspace), args.port)
        print('승인 화면을 종료했습니다. 승인 상태 확인·게시안 생성 중입니다. 완료 메시지가 나올 때까지 기다려 주세요.', flush=True)
        result = prepare_sources(args.workspace, args.target, args.home, args.publication_dir, args.output_dir, args.source_dir)
        print_report(result); return 0 if result['ready'] else 3
    if args.notion_action == 'send':
        from . import notion_mcp
        from .notion_prepared import load, publish, validate
        package = load(args.package)
        validate(package)
        notion_mcp.BRIDGE_DIRECTORY = Path(package['directory'])/'bridge'
        notion_mcp.BRIDGE_PACKAGE = args.package
        print('Notion 연결 도구의 중계를 기다립니다. 현재 채팅에서 전송 중계를 실행하세요.', flush=True)
        report = publish(args.package, call=notion_mcp.rpc, call_many=notion_mcp.rpc_many,
                         retry=args.retry, recover_interrupted=args.recover_interrupted)
        print('NOTION_DONE '+json.dumps({'done': report}, ensure_ascii=False), flush=True)
        return int(bool(report['errors']))
    if not args.target.is_file():
        raise AnalysisError('PUBLISH_TARGET_ERROR', '지정한 Notion 대상 설정 파일이 없습니다.')
    target = strict_json(args.target.read_text(encoding='utf-8-sig'))
    from .notion_reader import refresh_reader_target
    target = refresh_reader_target(target, args.workspace.parent/'notion_live/outbox')
    mapping = mapping_for(target)
    if args.notion_action == 'mapping':
        print(json.dumps(mapping, ensure_ascii=False, indent=2)); return 0
    store = Workspace(args.workspace, read_only=True)
    if args.notion_action == 'plan':
        plan = make_plan(store, target=target)
        output = new_run(args.output_dir)
        write_json(output/'plan.json', plan)
        (output/'preview.md').write_text(preview(plan), encoding='utf-8')
        write_json(output/'mapping.json', mapping)
        print(json.dumps({'mode': 'offline-plan', 'notion_sent': False,
                          'materials': len(plan['approvals']), 'entities': len(plan['entities']),
                          'plan': str(output/'plan.json'), 'preview': str(output/'preview.md')}, ensure_ascii=False))
        return 0
    plan = strict_json(args.plan.read_text(encoding='utf-8-sig'))
    remote = MockNotion(args.output_dir/'mock_remote.sqlite3')
    report = deliver_mock(plan, store, remote, args.output_dir/'outbox',
                          retry=args.retry, recover_interrupted=args.recover_interrupted, target=target)
    output = new_run(args.output_dir/'reports')
    write_json(output/'report.json', report)
    print(json.dumps(dict(report, report_path=str(output/'report.json')), ensure_ascii=False))
    return 1 if report['errors'] else 0
