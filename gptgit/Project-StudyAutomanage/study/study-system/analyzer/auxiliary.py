"""Isolate optional comments before core validation; never repair core content."""
import copy
from .core import AnalysisError, schema_errors
from .knowledge import validate_context, bind_references


def safe_context(context, schema):
    try:
        return validate_context([] if context is None else context, schema), []
    except AnalysisError:
        return [], [{'path': '/reference_context', 'code': 'REFERENCE_CONTEXT_OMITTED'}]


def core_schema(schema):
    result = copy.deepcopy(schema)
    for name in ('review_candidates', 'references'):
        result.get('properties', {}).pop(name, None)
        if name in result.get('required', []):result['required'].remove(name)
    section = result.get('$defs', {}).get('section', {})
    section.get('properties', {}).pop('comment', None)
    if 'comment' in section.get('required', []):section['required'].remove('comment')
    return result


def split(analysis):
    core = copy.deepcopy(analysis)
    extra = {'candidates': core.pop('review_candidates', None),
             'references': core.pop('references', None), 'comments': []}
    if isinstance(core.get('sections'), list):
        for index, section in enumerate(core['sections']):
            if isinstance(section, dict) and 'comment' in section:
                value = section.pop('comment')
                if value is not None:extra['comments'].append((index, value))
    return core, extra


def restore(core, extra, context, schema, text, initial_issues=None):
    """Called only after core schema, evidence, and links have passed."""
    from .quality import quality_errors
    from .comment_review import make_request
    result = copy.deepcopy(core)
    issues = list(initial_issues or [])
    for index, comment in extra['comments']:
        trial = copy.deepcopy(result)
        trial['sections'][index]['comment'] = comment
        trial.pop('references', None)  # Rebuild metadata from trusted context.
        try:
            bind_references(trial, context, schema)
            if schema_errors(trial, schema) or quality_errors(trial, text):
                raise AnalysisError('OPTIONAL_COMMENT_ERROR', '보조 코멘트 검증 실패')
        except AnalysisError:
            issues.append({'path': f'/sections/{index}/comment', 'code': 'COMMENT_OMITTED'})
        else:
            result = trial
    supplied = extra['references']
    if supplied is not None and supplied != result.get('references', []):
        issues.append({'path': '/references', 'code': 'UNTRUSTED_REFERENCE_METADATA_OMITTED'})
    candidates = extra['candidates']
    accepted = []
    if candidates is not None and not isinstance(candidates, list):
        issues.append({'path': '/review_candidates', 'code': 'CANDIDATES_OMITTED'})
        candidates = []
    commented = {s['id'] for s in result['sections'] if 'comment' in s}
    for index, candidate in enumerate(candidates or []):
        try:
            make_request(result, accepted + [candidate])
            if candidate['section_id'] in commented:
                raise AnalysisError('OPTIONAL_DUPLICATE', '기존 코멘트와 후보 중복')
        except AnalysisError:
            issues.append({'path': f'/review_candidates/{index}', 'code': 'CANDIDATE_OMITTED'})
        else:
            accepted.append(candidate)
    request = make_request(result, accepted)
    return result, request, {'status': 'OMITTED_OPTIONAL_ITEMS' if issues else 'OK',
                             'issues': issues, 'core_result_preserved': True}
