"""Conservative reference spelling repair and source-grounded review, without AI calls."""
import re


VERSION = 'concept-refs-v1'


def spelling_key(name):
    # No compatibility folding, punctuation removal, aliases or fuzzy matching.
    return re.sub(r'\s+', '', name).lower()


def source_mentions(name, text):
    from .render import redact
    compact = re.sub(r'\s+', '', name)
    if not compact:
        return []
    pattern = re.compile(r'(?<!\w)' + r'\s*'.join(re.escape(c) for c in compact) + r'(?!\w)', re.IGNORECASE)
    mentions = []
    for match in pattern.finditer(text):
        start = text.rfind('\n', 0, match.start()) + 1
        end = text.find('\n', match.end())
        if end < 0:
            end = len(text)
        # Bound excerpts while keeping their source location reproducible.
        start = max(start, match.start() - 160)
        end = min(end, match.start() + 400)
        excerpt = text[start:end]
        safe = redact(excerpt)
        span = {'start_offset': start, 'end_offset': end,
                'start_line': text.count('\n', 0, start) + 1,
                'end_line': text.count('\n', 0, end) + 1,
                'quote': safe, 'redacted': safe != excerpt}
        if not mentions or (span['start_line'], span['end_line']) != (mentions[-1]['start_line'], mentions[-1]['end_line']):
            mentions.append(span)
        if len(mentions) == 3:
            break
    return mentions


def normalize_references(analysis, text):
    """Only rewrite references to a unique existing name. Never add concepts."""
    names = [concept['name'] for concept in analysis.get('concepts', [])]
    available = set(names)
    index = {}
    for name in names:
        index.setdefault(spelling_key(name), []).append(name)
    report = {'policy_version': VERSION, 'status': 'passed',
              'automatic_api_retry': False, 'concepts_added': 0,
              'normalizations': [], 'items': [],
              'evidence_scope': '원문 용어 언급이며 개념 추가나 관계의 사실성을 입증하지 않습니다.'}

    def check(container, key, path, owner):
        name = container[key]
        if name in available:
            return
        candidates = index.get(spelling_key(name), [])
        if len(candidates) == 1:
            container[key] = candidates[0]
            report['normalizations'].append({'path': path, 'before': name,
                                            'after': candidates[0], 'method': 'unique_whitespace_case_match'})
            return
        mentions = source_mentions(name, text)
        report['items'].append({'path': path, 'name': name,
                                'reason': 'ambiguous_spelling' if candidates else 'missing_concept',
                                'candidates': candidates,
                                'section_ids': [section['id'] for section in analysis.get('sections', [])
                                                if owner in section.get('content_refs', [])],
                                'source_evidence_status': 'mention_found' if mentions else 'not_found',
                                'source_mentions': mentions,
                                'action': '원문과 기존 개념을 검토하여 수동 수정 후 저장 응답을 무료 재검증하세요.'})

    for i, relation in enumerate(analysis.get('relationships', [])):
        for key in ('from', 'to'):
            check(relation, key, f'/relationships/{i}/{key}', f'/relationships/{i}')

    def visit(value, path):
        if isinstance(value, dict):
            for i in range(len(value.get('related_concepts', []))):
                check(value['related_concepts'], i, f'{path}/related_concepts/{i}', path)
            for key, child in value.items():
                visit(child, path + '/' + key.replace('~', '~0').replace('/', '~1'))
        elif isinstance(value, list):
            for i, child in enumerate(value):
                visit(child, f'{path}/{i}')
    visit(analysis, '')
    if report['items']:
        report['status'] = 'needs_review'
    return report
