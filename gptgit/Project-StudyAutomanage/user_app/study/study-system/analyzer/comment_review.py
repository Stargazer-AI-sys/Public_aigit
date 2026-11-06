"""Unverified proposals stay in audit files until a source review is supplied.

No network, API keys, budget changes, or model-generated verification status.
Review decisions are trusted local input; format checks do not prove truth.
"""
import copy
import hashlib
import json
import re
from jsonschema import Draft202012Validator
from .core import AnalysisError, schema_errors
from .knowledge import is_v02, validate_context, knowledge_errors

CANDIDATES = {
    'type': 'array', 'items': {
        'type': 'object', 'additionalProperties': False,
        'required': ['section_id', 'kind', 'text', 'reason', 'search_query'],
        'properties': {
            'section_id': {'type': 'string', 'minLength': 1},
            'kind': {'type': 'string', 'enum': ['supplement', 'correction']},
            'text': {'type': 'string', 'minLength': 1, 'pattern': r'^[^\r\n]+$'},
            'reason': {'type': 'string', 'minLength': 1},
            'search_query': {'type': 'string', 'minLength': 1}}}}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     allow_nan=False).encode('utf-8')).hexdigest()


def fail(message):
    raise AnalysisError('COMMENT_REVIEW_ERROR', message)


def make_request(analysis, candidates):
    if list(Draft202012Validator(CANDIDATES).iter_errors(candidates)):
        fail('보충 후보의 형식이 잘못되었습니다. 확인 상태·출처는 후보가 생성할 수 없습니다.')
    section_ids = {s['id'] for s in analysis['sections']}
    seen, entries = set(), []
    for candidate in candidates:
        sid = candidate['section_id']
        if sid not in section_ids or sid in seen:
            fail('후보는 존재하는 큰 단락마다 최대 1개만 제안할 수 있습니다.')
        if any(not v.strip() for v in candidate.values()):
            fail('보충 후보에 빈 내용이 있습니다.')
        if len(re.findall(r'[.!?。！？]+(?=\s|$)', candidate['text'])) > 1:
            fail('보충 후보는 짧은 한 문장이어야 합니다.')
        seen.add(sid)
        entries.append(dict(candidate, id='candidate-' + digest(candidate)[:16], status='pending'))
    return {'review_version': 1, 'analysis_sha256': digest(analysis),
            'source': copy.deepcopy(analysis['source']), 'candidates': entries}


def validate_request(analysis, request):
    if not isinstance(request, dict) or not isinstance(request.get('candidates'), list):
        fail('검토 요청 형식이 잘못되었습니다.')
    fields = ('section_id', 'kind', 'text', 'reason', 'search_query')
    try:
        candidates = [{key: entry[key] for key in fields} for entry in request['candidates']]
    except (KeyError, TypeError):
        fail('검토 후보 정보가 누락되었습니다.')
    if request != make_request(analysis, candidates):
        fail('분석 결과 또는 검토 요청이 변경되었습니다. 해당 결과로 요청을 다시 생성하세요.')


def apply_review(analysis, request, decisions, schema, material):
    if not is_v02(schema) or schema_errors(analysis, schema):
        fail('v0.2 또는 호환 초안 결과와 Schema가 필요합니다.')
    from .quality import quality_errors
    expected = {k: material[k] for k in ('material_id', 'filename', 'extension')}
    if analysis['source'] != expected or quality_errors(analysis, material['extracted_text']):
        fail('입력 결과의 원본 식별정보·본문 근거·연결 검사가 실패했습니다.')
    validate_request(analysis, request)
    if not isinstance(decisions, list):
        fail('검토 결정은 배열이어야 합니다.')
    candidates = {c['id']: c for c in request['candidates']}
    reviewed, accepted = {}, {}
    for decision in decisions:
        if not isinstance(decision, dict):
            fail('검토 결정 형식이 잘못되었습니다.')
        cid, outcome = decision.get('candidate_id'), decision.get('outcome')
        if not isinstance(cid, str) or cid not in candidates or cid in reviewed:
            fail('검토 결정의 후보 ID가 없거나 중복됩니다.')
        if outcome not in ('supported', 'rejected', 'unresolved'):
            fail('지원·기각·미확인 중 하나의 검토 결과가 필요합니다.')
        reason = decision.get('reason')
        if not isinstance(reason, str) or not reason.strip():
            fail('출처가 주장을 뒷받침하는지 검토한 이유가 필요합니다.')
        allowed = {'candidate_id', 'outcome', 'reason'} | ({'reference'} if outcome == 'supported' else set())
        if set(decision) != allowed:
            fail('검토 결정에 필요한 정보가 없거나 불필요한 필드가 있습니다.')
        if outcome == 'supported':
            reference = decision['reference']
            if not isinstance(reference, dict) or 'comments' in reference:
                fail('검토 출처 형식이 잘못되었습니다.')
            c = candidates[cid]
            validate_context([dict(reference, comments=[{'kind': c['kind'], 'text': c['text']}])], schema)
            accepted[cid] = reference
        reviewed[cid] = decision
    result = copy.deepcopy(analysis)
    sections = {s['id']: s for s in result['sections']}
    references = {r['id']: r for r in result.get('references', [])}
    states = []
    for cid, candidate in candidates.items():
        state = reviewed.get(cid, {}).get('outcome', 'pending')
        if cid in accepted:
            section = sections[candidate['section_id']]
            # Never silently replace an existing different comment. A reviewer
            # must prepare a new base result before changing a published note.
            reference = accepted[cid]
            comment = {'kind': candidate['kind'], 'text': candidate['text'],
                       'reference_ids': [reference['id']]}
            if 'comment' in section and section['comment'] != comment:
                state = 'conflict'
            else:
                existing = references.get(reference['id'])
                if existing is not None and existing != reference:
                    fail('동일 출처 ID의 메타데이터가 충돌합니다.')
                references[reference['id']] = copy.deepcopy(reference)
                section['comment'] = comment
                state = 'applied'
        states.append({'candidate_id': cid, 'section_id': candidate['section_id'],
                       'status': state, 'reason': reviewed.get(cid, {}).get('reason')})
    if references:
        result['references'] = list(references.values())
    errors = schema_errors(result, schema)
    if errors or quality_errors(result, material['extracted_text']):
        fail('검토 반영 후 Schema·품질 검사가 실패했습니다.')
    return result, {'status': 'PASS', 'actual_ai_call': False, 'decisions': states,
                    'technical_review_source': 'trusted local decisions; not URL availability checks',
                    'input_analysis_sha256': digest(analysis), 'output_analysis_sha256': digest(result)}
