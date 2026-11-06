"""Resumable multi-material processing; no paid generation without explicit opt-in."""
import json
import os
from pathlib import Path
from uuid import uuid4

from .cache import context_for, digest, run_with_cache, saved_conditions_match
from .core import AnalysisError, FileResponseProvider, from_collector, load_schema, strict_json
from .schemas import DEFAULT_SCHEMA
from .workspace import Workspace


def run_batch(inventory, directory, *, responses=None, provider='mock-file', allow_api=False,
              max_new_calls=1, retry_failed=False, reanalyze=False, recover_interrupted=False,
              ask_api_key=False, model='gpt-6-luna', provider_factory=None):
    from .main import new_run, read_rows, write_json, write_readable
    if provider == 'openai' and allow_api and (not isinstance(max_new_calls, int) or not 1 <= max_new_calls <= 100):
        raise AnalysisError('BATCH_CONFIG_ERROR', '이번 실행의 새 API 요청 한도는 1~100회입니다.')
    store = Workspace(directory)
    schema = load_schema(DEFAULT_SCHEMA)
    owner, lock = uuid4().hex, store.root/'batch.lock'
    if recover_interrupted and lock.exists():
        lock.unlink()  # Explicit recovery after the user confirms the old worker is stopped.
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise AnalysisError('BATCH_LOCKED', '같은 지식베이스의 일괄 작업이 실행 중입니다. 종료된 작업이면 --recover-interrupted로 복구하세요.') from None
    os.write(fd, owner.encode()); os.close(fd)
    report = {'items': [], 'new_api_attempts': 0, 'new_successes': 0, 'reused': 0, 'failed': 0, 'blocked': 0}
    try:
        report['recovered_cache_locks'] = 0
        if recover_interrupted:
            for stale_lock in (store.root/'cache').glob('*.lock'):
                stale_lock.unlink()
                report['recovered_cache_locks'] += 1
        store.recover_jobs()
        response_map = strict_json(Path(responses).read_text(encoding='utf-8-sig')) if responses else {}
        if not isinstance(response_map, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in response_map.items()):
            raise AnalysisError('BATCH_CONFIG_ERROR', '모의 응답 매핑은 파일명:JSON경로 객체여야 합니다.')
        for index, row in enumerate(read_rows(inventory), start=1):
            item = {'row': index, 'filename': row['filename']}
            try:
                data = from_collector(row)
                mid = digest({key: data[key] for key in ('material_id', 'filename', 'extension')})
                existing = store.reusable(data)
                # No provider/response requested: reuse the validated imported result.
                saved_only = provider == 'mock-file' and not responses and not provider_factory
                if existing and not reanalyze and saved_only:
                    if existing.get('analysis_context') and not saved_conditions_match(existing['analysis_context'], data, schema):
                        item.update(status='blocked', material_id=mid, stage='analysis', reason='저장 분석 조건 변경; --reanalyze 및 응답/제공자 지정 필요')
                        report['blocked'] += 1; report['items'].append(item); continue
                    store.observe(row.get('path') or ('filename-'+row['filename']), mid)
                    item.update(status='reused', material_id=mid, reason='검증된 저장 결과 재사용 (분석 조건 지정 없음)')
                    report['reused'] += 1; report['items'].append(item); continue
                if provider_factory:
                    engine = provider_factory(data)
                elif provider == 'openai':
                    from .openai_provider import OpenAIProvider
                    engine = OpenAIProvider(schema, ask_api_key=ask_api_key, model=model)
                else:
                    response = response_map.get(row['filename'])
                    if response is None:
                        raise AnalysisError('RESPONSE_REQUIRED', '저장 결과 또는 --responses 매핑이 필요합니다.')
                    response_path = Path(response)
                    if not response_path.is_absolute():
                        response_path = Path(responses).resolve().parent / response_path
                    engine = FileResponseProvider(response_path)
                # Paid attempts are capped per invocation as well as by the shared ledger.
                reuse_only = provider == 'openai' and (not allow_api or report['new_api_attempts'] >= max_new_calls)
                context, _ = context_for(data, engine, schema)
                if existing and not reanalyze:
                    previous_context = existing.get('analysis_context')
                    if previous_context == context:
                        store.observe(row.get('path') or ('filename-'+row['filename']), mid)
                        item.update(status='reused', material_id=mid, reason='원본·분석 조건 일치; 승인·본문 보존')
                        report['reused'] += 1; report['items'].append(item); continue
                    item.update(status='blocked', material_id=mid,
                                reason='분석 조건 변경 또는 기존 조건 미확인; --reanalyze 명시 필요',
                                stage='analysis', conditions_known=previous_context is not None)
                    report['blocked'] += 1; report['items'].append(item); continue
                key = digest(context)
                claimed, previous = store.claim_job(key, item, retry=retry_failed, reanalyze=reanalyze)
                if not claimed:
                    item.update(status='blocked', reason='이전 상태: '+previous['state']+'; 명시적 재처리 필요')
                    report['blocked'] += 1; report['items'].append(item); continue
                output = new_run(store.root/'runs')
                try:
                    result, audit = run_with_cache(data, engine, schema, store.root/'cache', store.root/'runs', reuse_only=reuse_only, force=reanalyze and not reuse_only)
                    report['new_api_attempts'] += int(audit['trace'].get('api_request_attempted', False))
                    write_json(output/'analyzer_input.json', data)
                    for name, value in audit.items():
                        write_json(output/(name+'.json'), value)
                    write_json(output/'result.json', result)
                    if result['status'] == 'SUCCESS':
                        write_json(output/'analysis.json', result['analysis'])
                        write_readable(output, result['analysis'], audit, schema)
                        record = store.ingest(result['analysis'], data, origin=str(output), location=row.get('path'), analysis_context=context)
                        item.update(status='success', material_id=record['id'], run=str(output),
                                    warnings=audit.get('trace', {}).get('warnings', []))
                        report['new_successes'] += 1
                        store.finish_job(key, 'success', item)
                    else:
                        item.update(status='failed', error=result['error'], run=str(output))
                        if audit.get('concept_reference_review', {}).get('status') == 'needs_review':
                            item.update(review_required=True, review_report=str(output/'concept_reference_review.json'))
                        report['failed'] += 1; store.finish_job(key, 'failed', item)
                except Exception:
                    store.finish_job(key, 'failed', dict(item, error={'code': 'BATCH_STORAGE_OR_PROCESSING_ERROR'}))
                    raise
            except (AnalysisError, OSError, ValueError) as error:
                item.update(status='failed', error={'code': getattr(error, 'code', 'BATCH_INPUT_ERROR'), 'message': str(error)})
                report['failed'] += 1
            report['items'].append(item)
        report['status'] = 'PASS' if not report['failed'] and not report['blocked'] else 'PARTIAL'
        destination = new_run(store.root/'batch_reports')
        write_json(destination/'report.json', report)
        report['report_path'] = str(destination/'report.json')
        return report
    finally:
        if lock.exists() and lock.read_text(encoding='utf-8') == owner:
            lock.unlink()
