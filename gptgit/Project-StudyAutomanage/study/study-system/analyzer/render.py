"""Offline, traceable Markdown view. Never enriches or edits analysis JSON."""
import html
import re

from .core import AnalysisError, schema_errors
from .knowledge import knowledge_errors
from .schemas import schema_for, version_of


def redact(text):
    # Mask credential command arguments in views; evidence in JSON stays intact.
    text = re.sub(
        r'(?im)^(\s*(?:vtp\s+password|(?:en(?:able)?\s+)?(?:password|passwd|pass|pw|secret|sec)|'
        r'username\s+\S+(?:\s+privilege\s+\d+)?\s+(?:password|secret))\s+)[^\r\n]+',
        r'\1[인증값 숨김]', str(text))
    return re.sub(
        r'''(?im)(\b(?:password|passwd|secret|token|[a-z0-9_]*api[_-]?key)\s*[:=]\s*)(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s,;]+)''',
        r'\1[인증값 숨김]', text)


def plain(value):
    text = html.escape(redact(value), quote=False)
    return re.sub(r'([\\`*_{}\[\]()#+!|>~.-])', r'\\\1', text).replace('\n', ' ')


def quote_block(value):
    text = redact(value)
    longest = max((len(m.group()) for m in re.finditer(r'`+', text)), default=0)
    fence = '`' * max(3, longest + 1)
    return ['원문 인용 · 표시본의 인증값은 숨김', '', fence + 'text', text, fence, '']


def item_lines(item):
    title = item.get('name') or item.get('title') or item.get('subject')
    if 'from' in item:
        title = f"{item['from']} → {item['to']}"
    if 'subject_a' in item:
        title = f"{item['subject_a']} / {item['subject_b']}"
    lines = ['### ' + plain(title or '분석 항목'), '']
    if 'relation' in item:
        lines += [plain(item['relation']), '']
    for key in ('description', 'content'):
        if item.get(key):
            lines += [plain(item[key]), '']
    for criterion in item.get('criteria', []):
        lines += ['- ' + plain(criterion)]
    if item.get('criteria'):
        lines.append('')
    if 'evidence' in item:
        lines += quote_block(item['evidence'])
    return lines


def resolve(analysis, pointer):
    value = analysis
    for part in pointer.split('/')[1:]:
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def render_markdown(analysis, *, schema=None, pending=None, excluded=None):
    schema = schema or schema_for(analysis)
    errors = schema_errors(analysis, schema)
    if not errors:
        errors = knowledge_errors(analysis)
    if errors:
        raise AnalysisError('READABLE_RESULT_ERROR', '구조·단락·출처 연결 오류가 있는 결과는 출력하지 않습니다.')
    lines = ['# ' + plain(analysis['source']['filename']), '',
             f"Schema {version_of(analysis)} · 원문 기반 분석 · 내용 검토 필요", '',
             plain(analysis['summary']), '',
             '형식·연결 검사와 기술적 사실성·실습 성공 검증은 별개입니다.', '']
    if 'sections' in analysis:
        references = {r['id']: r for r in analysis.get('references', [])}
        for section in analysis['sections']:
            lines += ['## ' + plain(section['title']), '']
            for pointer in section['content_refs']:
                lines += item_lines(resolve(analysis, pointer))
            comment = section.get('comment')
            if comment:
                kind = '보충' if comment['kind'] == 'supplement' else '정정'
                lines += [f"❗ {kind}: {plain(comment['text'])}", '']
                for ref_id in comment['reference_ids']:
                    ref = references[ref_id]
                    # Angle delimiters prevent Markdown destinations escaping their link.
                    url = ref['url'].replace('<', '%3C').replace('>', '%3E').replace('\n', '').replace('\r', '')
                    lines += [f"- 출처: [{plain(ref['title'])}](<{url}>) · 확인일 {plain(ref.get('checked_on', '미기록'))}"]
                lines.append('')
    else:
        for title, items in [('개념', analysis.get('concepts', [])),
                             ('관계', analysis.get('relationships', [])),
                             ('이론', [v for group in analysis.get('theory', {}).values() for v in group]),
                             ('실습', analysis.get('practice', []))]:
            if items:
                lines += ['## ' + title, '']
                for item in items:
                    lines += item_lines(item)
    comments = sum('comment' in s for s in analysis.get('sections', []))
    pending_label = '미확인' if pending is None else f'{pending}개'
    excluded_label = '미확인' if excluded is None else f'{excluded}개'
    lines += ['---', '', f'코멘트 {comments}개 · 검토 대기 후보 {pending_label} · 보조 항목 제외 사유 {excluded_label}', '',
              '원본 JSON은 별도로 보존합니다. 표시본의 인증값 숨김은 원문 인용 수정이 아닙니다.', '']
    return '\n'.join(lines)
