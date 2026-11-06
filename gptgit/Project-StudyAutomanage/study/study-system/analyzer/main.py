import argparse
import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from jsonschema.exceptions import SchemaError

from .cache import run_with_cache
from .core import AnalysisError, FileResponseProvider, analyze, from_collector, load_schema, schema_errors
from .schemas import DEFAULT_SCHEMA, schema_for, schema_for_run
from .render import render_markdown


ROOT = Path(__file__).resolve().parent.parent


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def new_run(output):
    path = Path(output) / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:12])
    path.mkdir(parents=True, exist_ok=False)
    return path


def write_readable(path, analysis, audit=None, schema=None):
    audit = audit or {}
    pending = len(audit.get('review_request', {}).get('candidates', []))
    excluded = len(audit.get('auxiliary_review', {}).get('issues', []))
    (path / 'result.md').write_text(render_markdown(analysis, schema=schema, pending=pending, excluded=excluded), encoding='utf-8')


def read_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"sha256", "filename", "extension", "text", "status"}
        if not required <= set(reader.fieldnames or []):
            raise ValueError("CSV에 필수 열이 없습니다: " + ", ".join(sorted(required)))
        return list(reader)


def convert(rows):
    inputs, rejected = [], []
    for index, row in enumerate(rows, start=1):
        try:
            inputs.append(from_collector(row))
        except AnalysisError as error:
            rejected.append({"row": index, "filename": row.get("filename"),
                             "error": {"code": error.code, "message": str(error)}})
    return inputs, rejected


def main():
    from .notion_sync import DeliveryError
    parser = argparse.ArgumentParser(description="NETWORK Analyzer — v0.2 기본 / v0.1·v0.2 초안 호환")
    sub = parser.add_subparsers(dest="command", required=True)
    from .organizer import register
    register(sub)
    from .notion_cli import register as register_notion
    register_notion(sub)
    cv = sub.add_parser("convert", help="Collector CSV를 입력 JSON으로 변환")
    cv.add_argument("--inventory", type=Path, default=ROOT / "output/material_inventory.csv")
    cv.add_argument("--output-dir", type=Path, default=ROOT / "output/input_runs")
    va = sub.add_parser("validate", help="단일 결과 또는 materials 묶음의 구조 검사")
    va.add_argument("--file", type=Path, required=True)
    va.add_argument("--schema", type=Path, help="미지정 시 결과별 버전 자동 선택")
    va.add_argument("--output-dir", type=Path, default=ROOT / "output/validation_runs")
    rc = sub.add_parser("recheck", help="저장 응답 무료 재검증; 명백한 참조 표기 보정·누락 검토·유일한 원문 인용 복원")
    rc.add_argument("--run-dir", type=Path, required=True)
    rc.add_argument("--schema", type=Path, help="미지정 시 저장 응답 버전 자동 선택")
    rc.add_argument("--output-dir", type=Path, default=ROOT / "output/recheck_runs")
    rc.add_argument("--reference-context", type=Path, help="v0.2용 검토된 한 줄 설명·출처 JSON")
    review = sub.add_parser('apply-review', help='보충 후보의 출처 검토 결정을 무료 반영; 원래 결과 보존')
    review.add_argument('--analysis', type=Path, required=True)
    review.add_argument('--request', type=Path, required=True)
    review.add_argument('--decisions', type=Path, required=True)
    review.add_argument('--source-file', type=Path, required=True)
    review.add_argument('--schema', type=Path, help='미지정 시 기존 결과 버전 자동 선택')
    review.add_argument('--output-dir', type=Path, default=ROOT / 'output/comment_review_runs')
    sub.add_parser("budget", help="현재 검증 단계의 누적 호출·예산 확인")
    view = sub.add_parser('render', help='기존 결과를 읽기용 Markdown으로 출력; API 호출 없음')
    view.add_argument('--file', type=Path, required=True)
    view.add_argument('--schema', type=Path)
    view.add_argument('--output-dir', type=Path, default=ROOT / 'output/readable_runs')
    run = sub.add_parser("run", help="대표 자료 1개 분석 또는 성공 결과 재사용")
    run.add_argument("--inventory", type=Path, default=ROOT / "output/material_inventory.csv")
    run.add_argument("--filename", required=True)
    run.add_argument("--response-file", type=Path)
    run.add_argument("--provider", choices=["mock-file", "openai"], default="mock-file")
    run.add_argument("--ask-api-key", action="store_true")
    run.add_argument("--model", choices=["gpt-6-luna", "gpt-6.1-sol"], default="gpt-6-luna")
    run.add_argument("--timeout", type=float, default=90)
    run.add_argument("--max-output-tokens", type=int, default=6000)
    run.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    run.add_argument("--reference-context", type=Path, help="v0.2용 검토된 한 줄 설명·출처 JSON; 미지정 시 코멘트 없음")
    run.add_argument("--output-dir", type=Path, default=ROOT / "output/analyzer_runs")
    run.add_argument("--cache-dir", type=Path, default=ROOT / "output/analyzer_cache")
    run.add_argument("--force", action="store_true", help="기존 성공 결과가 있어도 재분석")
    run.add_argument("--reuse-only", action="store_true", help="결과 재사용만 허용; API 호출 차단")
    args = parser.parse_args()
    if args.command == "run" and args.force and args.reuse_only:
        parser.error("--force와 --reuse-only는 함께 사용할 수 없습니다.")
    try:
        if args.command == 'notion':
            from .notion_cli import execute as execute_notion
            return execute_notion(args)
        if args.command in ('batch', 'library', 'review'):
            from .organizer import execute
            return execute(args)
        if args.command == "budget":
            from .budget import Budget
            print(json.dumps(Budget().status(), ensure_ascii=False, indent=2))
            return 0
        if args.command == "convert":
            inputs, rejected = convert(read_rows(args.inventory))
            path = new_run(args.output_dir)
            write_json(path / "analyzer_inputs.json", inputs)
            write_json(path / "conversion_report.json", {"accepted": len(inputs), "rejected": rejected})
            print(f"accepted={len(inputs)}, rejected={len(rejected)}\n{path}")
            return 1 if rejected or not inputs else 0
        from .core import strict_json
        if args.command == 'render':
            original = strict_json(args.file.read_text(encoding='utf-8-sig'))
            rendered = render_markdown(original, schema=schema_for(original, args.schema))
            path = new_run(args.output_dir)
            (path / 'result.md').write_text(rendered, encoding='utf-8')
            write_json(path / 'render_report.json', {'input': str(args.file.resolve()), 'actual_ai_call': False,
                       'original_modified': False, 'content_review_required': True})
            print(f'PASS (readable-result / actual_ai_call=false)\n{path}')
            return 0
        if args.command == 'validate':
            data = strict_json(args.file.read_text(encoding='utf-8-sig'))
            items = data.get('materials') if isinstance(data, dict) and 'materials' in data else [data]
            if not isinstance(items, list) or not items:
                raise ValueError('materials는 비어 있지 않은 배열이어야 합니다.')
            from .knowledge import knowledge_errors
            checks = []
            for index, item in enumerate(items, start=1):
                selected = schema_for(item, args.schema)
                errors = schema_errors(item, selected)
                if not errors:
                    errors.extend(knowledge_errors(item))
                checks.append({'index': index, 'errors': errors})
            passed = all(not check['errors'] for check in checks)
            path = new_run(args.output_dir)
            write_json(path / 'validation_report.json', {'status': 'PASS' if passed else 'FAIL', 'checks': checks})
            print(f"{'PASS' if passed else 'FAIL'}: {len(checks)} materials\n{path}")
            return 0 if passed else 1
        if args.command == 'recheck':
            schema = schema_for_run(args.run_dir, args.schema)
        elif args.command == 'apply-review':
            schema = schema_for(strict_json(args.analysis.read_text(encoding='utf-8-sig')), args.schema)
        else:
            schema = load_schema(args.schema)
        from .knowledge import load_context, knowledge_errors, is_v02
        context_warning = False
        try:
            reference_context = load_context(getattr(args, 'reference_context', None), schema)
        except (AnalysisError, OSError, ValueError):
            if not is_v02(schema) or args.command not in ('run', 'recheck'):
                raise
            reference_context, context_warning = [], True
        if args.command == 'apply-review':
            from .comment_review import apply_review
            from .core import strict_json
            from collector.main import process_file
            def read(path):return strict_json(path.read_text(encoding='utf-8-sig'))
            original, request, decisions = read(args.analysis), read(args.request), read(args.decisions)
            material = from_collector(process_file(args.source_file))
            result, report = apply_review(original, request, decisions, schema, material)
            path = new_run(args.output_dir)
            write_json(path / 'analysis.json', result)
            write_json(path / 'review_report.json', report)
            write_json(path / 'review_request.json', request)
            write_json(path / 'review_decisions.json', decisions)
            write_readable(path, result, {'review_request': {'candidates': [d for d in report['decisions'] if d['status'] in ('pending', 'unresolved', 'conflict')]}}, schema)
            print(f"PASS (reviewed-comments / actual_ai_call=false)\n{path}")
            print('추가 API 호출 0회 / 예산 변경 없음 / 원래 결과 보존')
            applied = sum(item['status'] == 'applied' for item in report['decisions'])
            remaining = sum(item['status'] in ('pending', 'unresolved', 'conflict') for item in report['decisions'])
            print(f'코멘트 반영 {applied}개 / 추가 검토 필요 {remaining}개')
            return 0
        if args.command == "recheck":
            from .recheck import recheck_run
            data,result,audit = recheck_run(args.run_dir,schema,reference_context,context_warning)
            path = new_run(args.output_dir)
            write_json(path / "analyzer_input.json",data)
            for name,value in audit.items():write_json(path / (name + ".json"),value)
            destination = path / ("success" if result["status"] == "SUCCESS" else "failed")
            destination.mkdir()
            write_json(destination / "result.json",result)
            if result["status"] == "SUCCESS":
                write_json(destination / "analysis.json",result["analysis"])
                write_readable(path, result['analysis'], audit, schema)
            recovered = sum(item['method']=='unique_exact_anchor_span_recovery' for item in audit.get('evidence_resolution',[]))
            print(f"{result['status']} (saved-response / actual_ai_call=false)\n{path}\n추가 API 호출 0회 / 예산 집계 변경 없음 / 원문 인용 복원 {recovered}곳")
            if result["status"] == "FAILED":print(result["error"]["code"] + ": " + result["error"]["message"])
            else:print("형식·연결·인용 검사는 통과했습니다. 줄 범위의 적절성과 내용 정확성은 사용자 검토가 필요합니다.")
            if audit.get('concept_reference_review', {}).get('status') == 'needs_review':
                print(f"개념 참조 검토 필요 (원문 줄 번호·구절 포함): {path / 'concept_reference_review.json'}\n자동 유료 재호출·개념 추가 없음")
            if audit['trace'].get('review_candidates_pending'):
                print(f"출처 검토 대기 후보 {audit['trace']['review_candidates_pending']}개: review_request.json (최종 코멘트 미반영)")
            if audit.get('auxiliary_review', {}).get('issues'):
                print('검증되지 않은 보조 항목은 제외했습니다: auxiliary_review.json (핵심 분석 결과 보존)')
            return 0 if result["status"] == "SUCCESS" else 1
        rows = [row for row in read_rows(args.inventory) if row["filename"] == args.filename]
        if len(rows) != 1:
            raise ValueError(f"파일명에 해당하는 행이 정확히 하나여야 합니다: 현재 {len(rows)}개")
        row = rows[0]
        if args.provider == "mock-file":
            if not args.response_file:
                raise ValueError("mock-file 실행에는 --response-file이 필요합니다.")
            provider = FileResponseProvider(args.response_file)
        else:
            if args.response_file:
                raise ValueError("openai 실행에는 --response-file을 사용하지 않습니다.")
            from .openai_provider import OpenAIProvider
            provider = OpenAIProvider(schema, ask_api_key=args.ask_api_key, timeout=args.timeout,
                                      max_output_tokens=args.max_output_tokens, model=args.model)
        provider.reference_context = reference_context
        provider.reference_context_warning = context_warning
        try:
            data = from_collector(row)
            result, audit = run_with_cache(data, provider, schema, args.cache_dir, args.output_dir,
                                           force=args.force, reuse_only=args.reuse_only)
        except AnalysisError as error:
            data = None
            result = {"status": "FAILED", "material_id": row.get("sha256"),
                      "error": {"code": error.code, "message": str(error)}}
            audit = {"trace": {"provider": provider.name, "actual_ai_call": False, "completed_stages": [], "warnings": []}}
        path = new_run(args.output_dir)
        if data:
            write_json(path / "analyzer_input.json", data)
        for name, value in audit.items():
            write_json(path / (name + ".json"), value)
        destination = path / ("success" if result["status"] == "SUCCESS" else "failed")
        destination.mkdir()
        write_json(destination / "result.json", result)
        if result["status"] == "SUCCESS":
            write_json(destination / "analysis.json", result["analysis"])
            write_readable(path, result['analysis'], audit, schema)
        print(f"{result['status']} ({provider.name} / actual_ai_call={str(audit['trace']['actual_ai_call']).lower()})\n{path}")
        if result["status"] == "FAILED":
            print(result["error"]["code"] + ": " + result["error"]["message"])
            if audit.get('concept_reference_review', {}).get('status') == 'needs_review':
                print(f"개념 참조 검토 필요 (원문 줄 번호·구절 포함): {path / 'concept_reference_review.json'}\n자동 유료 재호출·개념 추가 없음")
        elif audit["trace"].get("result_reused"):
            print("기존 결과 재사용: API 호출 0회 / 이번 호출 사용량 0토큰")
        elif args.provider == "openai":
            print("사용량: " + json.dumps(audit["trace"].get("usage"), ensure_ascii=False))
        if audit["trace"].get("budget"):
            budget = audit["trace"]["budget"]
            print(f"검증 단계 호출: {budget['calls_used']}/{budget['call_limit']}회 / 추정·예약 누적: ${budget['estimated_or_reserved_usd']:.6f} / 한도: ${budget['budget_usd']:.2f}")
        if result["status"] == "SUCCESS":
            print("형식·연결·인용 검사는 통과했습니다. 내용 정확성과 실습 결과 해석은 사용자 검토가 필요합니다.")
            if audit['trace'].get('review_candidates_pending'):
                print(f"출처 검토 대기 후보 {audit['trace']['review_candidates_pending']}개: review_request.json (최종 코멘트 미반영)")
            if audit.get('auxiliary_review', {}).get('issues'):
                print('검증되지 않은 보조 항목은 제외했습니다: auxiliary_review.json (핵심 분석 결과 보존)')
        return 0 if result["status"] == "SUCCESS" else 1
    except KeyboardInterrupt:
        if args.command == 'notion' and args.notion_action in ('prepare', 'review'):
            print('게시 준비를 중단했습니다. 저장된 승인은 유지됩니다. prepare로 다시 준비하세요.')
        else:
            print('실행을 중단했습니다. 저장 결과와 실행 상태를 확인한 뒤 재개하세요.')
        return 130
    except (AnalysisError, DeliveryError) as error:
        print(error.code + ": " + str(error))
        return 1
    except (OSError, ValueError, SchemaError, sqlite3.Error) as error:
        print(f"실행 설정 오류: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
