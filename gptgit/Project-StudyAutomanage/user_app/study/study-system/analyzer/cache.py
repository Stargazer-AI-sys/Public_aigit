"""Local validated result reuse. No credentials or network operations."""
import copy
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from .core import AnalysisError, SOURCE_KEYS, analyze, build_prompt, schema_errors, strict_json, validate_input


LEGACY_V02_PROCESSING_SHA256 = 'be2bb318ee352594c3aaf4570dce36000e3b156be5da367b97a8e2e0bd2b72b2'


class CacheError(Exception):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def processing_digest(provider_name):
    root = Path(__file__).resolve().parent
    files = ['core.py', 'quality.py', 'concept_refs.py', 'knowledge.py', 'schemas.py', 'comment_review.py', 'auxiliary.py'] + (['openai_provider.py', 'evidence.py'] if provider_name == 'openai' else [])
    return hashlib.sha256(b''.join((root / f).read_bytes() for f in files)).hexdigest()


def saved_conditions_match(context, data, schema):
    """Validate recorded conditions without a response file, credentials or calls."""
    from types import SimpleNamespace
    if not isinstance(context, dict):
        return False
    config = context.get('config', {})
    name = config.get('provider')
    if (context.get('input_sha256') != digest(data) or context.get('schema_sha256') != digest(schema)
            or config.get('processing_sha256') != processing_digest(name)):
        return False
    provider = SimpleNamespace(name=name)
    if name == 'openai':
        from .openai_provider import OpenAIProvider
        try:
            provider = OpenAIProvider(schema, model=config['model'], max_output_tokens=config['max_output_tokens'])
        except (KeyError, ValueError):
            return False
    messages = build_prompt(data, schema)
    if hasattr(provider, 'prepare_messages'):
        messages = provider.prepare_messages(messages)
    return context.get('prompt_sha256') == digest(messages)


def context_for(data, provider, schema):
    messages = build_prompt(data, schema, getattr(provider, 'reference_context', None))
    if hasattr(provider, 'prepare_messages'):
        messages = provider.prepare_messages(messages)
    config = {'provider': provider.name}
    from .knowledge import is_v02
    if is_v02(schema):
        from .auxiliary import safe_context
        _, context_issues = safe_context(getattr(provider, 'reference_context', None), schema)
        config['auxiliary_context_omitted'] = bool(context_issues or getattr(provider, 'reference_context_warning', False))
    if provider.name == 'openai':
        config.update(model=provider.trace['model'], reasoning_effort=provider.trace['reasoning_effort'],
                      max_output_tokens=provider.trace['max_output_tokens'], service_tier='default')
    elif provider.name == 'mock-file':
        config['response_sha256'] = hashlib.sha256(provider.path.read_bytes()).hexdigest()
    config['processing_sha256'] = processing_digest(provider.name)
    context = {'cache_format': 1, 'input_sha256': digest(data), 'prompt_sha256': digest(messages),
               'schema_sha256': digest(schema), 'config': config}
    return context, messages


def check_analysis(analysis, data, schema):
    if not isinstance(analysis, dict) or schema_errors(analysis, schema):
        raise CacheError('저장 결과가 현재 Schema 검증을 통과하지 못합니다.')
    from .quality import quality_errors
    if quality_errors(analysis, data['extracted_text']):
        raise CacheError('저장 결과가 확정된 분석 품질 검사를 통과하지 못합니다.')
    expected = {key: data[key] for key in SOURCE_KEYS}
    if analysis.get('source') != expected:
        raise CacheError('저장 결과의 원본 정보가 입력과 다릅니다.')


def read_json(path):
    try:
        return strict_json(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError, TypeError, RecursionError) as error:
        raise CacheError('캐시 파일을 읽을 수 없습니다. 자동 재호출을 차단합니다.') from error


def load_cache(path, context, data, schema):
    if not path.exists():
        return None
    entry = read_json(path)
    if not isinstance(entry, dict) or entry.get('context') != context:
        raise CacheError('캐시 식별 조건이 다르거나 손상되었습니다. 자동 재호출을 차단합니다.')
    if digest(entry.get('analysis')) != entry.get('analysis_sha256'):
        raise CacheError('저장 결과의 무결성 확인에 실패했습니다. 자동 재호출을 차단합니다.')
    check_analysis(entry['analysis'], data, schema)
    if 'review_request' in entry:
        from .comment_review import validate_request
        try:
            validate_request(entry['analysis'], entry['review_request'])
        except AnalysisError as error:
            raise CacheError('저장된 보충 검토 요청이 손상되었습니다.') from error
    return entry


def store_cache(path, context, analysis, origin, review_request=None, auxiliary_review=None):
    entry = {'context': context, 'analysis': analysis, 'analysis_sha256': digest(analysis), 'origin': origin}
    if review_request is not None:
        entry['review_request'] = copy.deepcopy(review_request)
    if auxiliary_review is not None:
        entry['auxiliary_review'] = copy.deepcopy(auxiliary_review)
    temporary = path.with_name(path.name + '.' + uuid4().hex + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8') as file:
            json.dump(entry, file, ensure_ascii=False, indent=2, allow_nan=False)
            file.write('\n')
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return entry


def find_previous_run(history, data, messages, provider, schema):
    """Adopt v0.2 successful runs only when recorded inputs/prompts/config match."""
    current, _ = context_for(data, provider, schema)
    if (provider.name != 'openai' or not Path(history).is_dir()
            or current['config']['processing_sha256'] != LEGACY_V02_PROCESSING_SHA256):
        return None
    for path in sorted(Path(history).iterdir(), key=lambda p: p.name, reverse=True):
        if not path.is_dir():
            continue
        try:
            result = read_json(path / 'success/result.json')
            analysis = read_json(path / 'success/analysis.json')
            trace = read_json(path / 'trace.json')
            if (result.get('status') != 'SUCCESS' or result.get('material_id') != data['material_id'] or result.get('analysis') != analysis
                    or read_json(path / 'analyzer_input.json') != data
                    or read_json(path / 'prompt.json') != messages):
                continue
            if (trace.get('provider') != 'openai' or trace.get('actual_ai_call') is not True
                    or trace.get('response_received') is not True or trace.get('response_status') != 'completed'
                    or 'schema_validation' not in trace.get('completed_stages', [])):
                continue
            if any(trace.get(key) != provider.trace[key]
                   for key in ('model', 'reasoning_effort', 'max_output_tokens')):
                continue
            # The supported v0.2 adapter always used Standard and the same processing code.
            if trace.get('response_model') != provider.trace['model']:
                continue
            check_analysis(analysis, data, schema)
            return analysis, {'kind': 'previous_openai_run', 'path': str(path.resolve())}
        except (CacheError, AttributeError, TypeError):
            continue
    return None


def reused_result(entry, data, messages, key):
    trace = {'provider': entry['context']['config']['provider'], 'actual_ai_call': False,
             'api_request_attempted': False, 'response_received': False, 'result_reused': True,
             'cache_key': key, 'cached_origin': entry.get('origin'),
             'completed_stages': ['input_validation', 'cache_validation', 'schema_validation'],
             'content_review_required': True, 'warnings': [], 'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}}
    trace.update({k: v for k, v in entry['context']['config'].items()
                  if k in ('model', 'reasoning_effort', 'max_output_tokens')})
    audit = {'trace': trace, 'prompt': messages}
    if 'review_request' in entry:
        audit['review_request'] = copy.deepcopy(entry['review_request'])
        trace['review_candidates_pending'] = len(entry['review_request']['candidates'])
    if 'auxiliary_review' in entry:
        audit['auxiliary_review'] = copy.deepcopy(entry['auxiliary_review'])
        if entry['auxiliary_review'].get('issues'):
            trace['warnings'].append('보조 항목 제외 이력이 있는 핵심 분석 결과를 재사용했습니다.')
    return {'status': 'SUCCESS', 'material_id': data['material_id'], 'analysis': copy.deepcopy(entry['analysis'])}, audit


def run_with_cache(data, provider, schema, cache_dir, history, *, force=False, reuse_only=False):
    def failed(code, message):
        return {'status': 'FAILED', 'material_id': data.get('material_id') if isinstance(data, dict) else None,
                'error': {'code': code, 'message': message}}, {'trace': {'provider': provider.name,
                'actual_ai_call': False, 'api_request_attempted': False, 'result_reused': False,
                'completed_stages': [], 'warnings': []}}
    if force and reuse_only:
        return failed('CACHE_ERROR', '--force와 --reuse-only는 함께 사용할 수 없습니다.')
    try:
        data = validate_input(data)
        context, messages = context_for(data, provider, schema)
        key = digest(context)
        directory = Path(cache_dir)
        directory.mkdir(parents=True, exist_ok=True)
        path, lock = directory / (key + '.json'), directory / (key + '.lock')
        # Hold the same per-input lock during lookup and generation to prevent double calls.
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            return failed('CACHE_LOCKED', '같은 분석이 실행 중이거나 이전 잠금이 남아 있습니다. API 호출을 차단했습니다.')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as file:
                file.write(str(os.getpid()))
            if not force:
                entry = load_cache(path, context, data, schema)
                if entry is None:
                    previous = find_previous_run(history, data, messages, provider, schema)
                    if previous:
                        analysis, origin = previous
                        entry = store_cache(path, context, analysis, origin)
                if entry is not None:
                    return reused_result(entry, data, messages, key)
            if reuse_only:
                return failed('CACHE_MISS', '재사용 가능한 결과가 없습니다. --reuse-only이므로 API를 호출하지 않았습니다.')
            result, audit = analyze(data, provider, schema)
            audit['trace'].update(result_reused=False, cache_key=key, force_reanalysis=force)
            if result['status'] == 'SUCCESS':
                try:
                    store_cache(path, context, result['analysis'], {'kind': 'generated_result'},
                                audit.get('review_request'), audit.get('auxiliary_review'))
                except OSError:
                    audit['trace']['warnings'].append('분석은 성공했지만 캐시 저장에 실패했습니다. 재실행 전 저장 결과를 확인하세요.')
            return result, audit
        finally:
            try:
                lock.unlink(missing_ok=True)
            except OSError:
                pass  # Keep a stale lock; never trigger an untracked second paid request.
    except AnalysisError as error:
        return failed(error.code, str(error))
    except CacheError as error:
        return failed('CACHE_ERROR', str(error))
    except OSError:
        return failed('CACHE_ERROR', '캐시 읽기·쓰기 준비에 실패했습니다. API를 호출하지 않았습니다.')
