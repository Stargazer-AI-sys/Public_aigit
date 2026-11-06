"""Notion에 올릴 페이지 내용, 미리보기, 채팅 게시 요청문을 만든다. Notion에 직접 접속하지 않는다."""
import html
import re
import shutil
from pathlib import Path

from .ccna import DOMAINS
from .records import all_results, now, published, write_json
from .sources import file_hash, list_sources

INDEX_PAGES = ('학습자료', '개념 찾아보기', '실습 찾아보기')
DOMAIN_TITLES = [domain for domain, _ in DOMAINS]


def redact(value):
    # 장비 설정 예시의 비밀번호·키 값을 가린다. 분석 결과 파일의 원문은 그대로 둔다.
    value = re.sub(
        r'(?im)^(\s*(?:vtp\s+password|(?:en(?:able)?\s+)?(?:password|passwd|pass|pw|secret|sec)|'
        r'username\s+\S+(?:\s+privilege\s+\d+)?\s+(?:password|pass|secret))\s+)[^\r\n]+',
        r'\1[인증값 숨김]', str(value))
    return re.sub(
        r'''(?im)(\b(?:password|passwd|secret|token|[a-z0-9_]*api[_-]?key)\s*[:=]\s*)(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s,;]+)''',
        r'\1[인증값 숨김]', value)


def text(value):
    # Notion 마크다운 문법 문자를 일반 글자로 표시한다. `코드`는 그대로 둔다.
    parts = re.split(r'(`[^`\n]+`)', redact(value))
    value = ''.join(p if p.startswith('`') and p.endswith('`') else
                    re.sub(r'([\\*~`$\[\]<>{}|^])', r'\\\1', p) for p in parts)
    # "2. 네트워크 접속"처럼 숫자와 점으로 시작하면 Notion이 번호 목록으로 바꾼다(2026-10-29 게시에서 확인).
    return re.sub(r'(?m)^(\s*\d+)([.)])(?=\s)', r'\1\\\2', value)


def code(value):
    value = redact(value)
    fence = '`' * max(3, max((len(m) for m in re.findall(r'`+', value)), default=0) + 1)
    return f'{fence}text\n{value}\n{fence}'


# 페이지는 블록(문단·제목·목록·코드·접기) 문자열의 목록으로 만들고 빈 줄로 잇는다.
# Notion 마크다운 규칙(notion://docs/notion-flavored-markdown-spec, 2026-10-28 확인):
# 블록 태그는 여는 태그 바로 다음 줄이 제목이고 빈 줄 뒤가 내용이다. 태그 안쪽 앞뒤에는 빈 줄을 두지 않는다.
def join(blocks):
    return '\n\n'.join(blocks)


def block(name, title, children, attributes=''):
    return f'<{name}{attributes}>\n{title}\n\n{join(children)}\n</{name}>'


def toggle(title, children):
    return block('toggle', text(title), children)


def callout(icon, title, children):
    return block('callout', title, children, f' icon="{icon}"')


def bullets(items):
    return '\n'.join('- ' + item for item in items)


def link(title, urls):
    """이미 게시된 페이지는 바로 링크하고, 아직 없는 페이지는 게시할 때 채팅 AI가 링크로 바꾼다."""
    if urls.get(title):
        # 멘션 라벨은 Notion이 글자 그대로 표시하므로 이스케이프하지 않는다.
        return f'<mention url="{urls[title]}">{title}</mention>'
    return '{{page:' + title + '}}'


def navigation(home_title, urls):
    return '　·　'.join(link(t, urls) for t in (home_title, *INDEX_PAGES))


def material_page(record, nav):
    a = record['analysis']
    blocks = [nav, '## 핵심 정리', text(a['summary']),
              '## CCNA 분류', bullets(text(c) for c in a['categories']), '## 주제별 내용']
    for section in a['sections']:
        children = []
        for point in section['points']:
            children += ['### ' + text(point['subject']), text(point['content']),
                         toggle('원문 근거', [code(point['evidence'])])]
        for item in section['practice']:
            children += ['### 실습 · ' + text(item['title']), text(item['description']),
                         toggle('원문 설정 예시', [code(item['evidence'])])]
        if section['comment']:
            children.append(callout('💡', f"AI 검토 의견 · {section['comment']['kind']}",
                                    [text(section['comment']['text'])]))
        blocks.append(toggle(section['title'], children))
    if a['ccna_gaps']:
        blocks += ['## CCNA 기준 보완할 점',
                   callout('🧭', 'AI가 CCNA 학습 범위와 비교해 짚은 내용입니다. 공식 자료로 확인하세요.',
                           [bullets(f"**{text(g['category'])}**: {text(g['text'])}" for g in a['ccna_gaps'])])]
    blocks.append(toggle('원본 정보', [
        '파일명　' + text(record['filename']), '내용 해시　' + record['sha256'],
        '분석　' + record['analyzed_at'] + ' · ' + record['model']]))
    return join(blocks)


def materials_in(records, domain):
    return [r for r in records if any(c.startswith(domain + ' / ') for c in r['analysis']['categories'])]


def home_page(records, nav, urls):
    recent = sorted(records, key=lambda r: r['analyzed_at'], reverse=True)[:10]
    return join([nav, 'CCNA 분야에서 시작해 자료별 정리와 실습을 찾아보세요.', '## 학습 분야',
                 bullets(f'{link(d, urls)} · 자료 {len(materials_in(records, d))}개' for d in DOMAIN_TITLES),
                 '## 최근 학습자료',
                 bullets(f"{link(r['filename'], urls)} · {text(r['analysis']['summary'])}" for r in recent)])


def domain_page(domain, units, records, nav, urls):
    blocks = [nav, f'CCNA 분류 · {text(domain)}']
    for _, title, terms in units:
        name = f'{domain} / {title}'
        found = [r for r in records if name in r['analysis']['categories']]
        blocks += ['## ' + text(title), '관련 용어　' + text(terms)]
        if not found:
            blocks.append('아직 연결된 학습자료가 없습니다.')
            continue
        blocks.append(bullets(link(r['filename'], urls) for r in found))
        gaps = [g['text'] for r in found for g in r['analysis']['ccna_gaps'] if g['category'] == name]
        if gaps:
            blocks.append(callout('🧭', 'AI가 짚은 보완할 점', [bullets(text(g) for g in gaps)]))
    return join(blocks)


def materials_page(records, nav, urls):
    blocks = [nav, '자료별 핵심 정리와 CCNA 분류입니다.']
    for r in records:
        blocks += ['## ' + link(r['filename'], urls), text(r['analysis']['summary']),
                   bullets(text(c) for c in r['analysis']['categories'])]
    return join(blocks)


def concepts_page(records, nav, urls):
    # 개념은 분류가 아니라 자료 전체에 붙어 있으므로 분류별로 나누면 같은 목록이 반복된다.
    index = {}
    for r in records:
        for concept in r['analysis']['concepts']:
            index.setdefault(concept.strip(), []).append(r['filename'])
    return join([nav, '개념을 고르면 그 개념이 나오는 학습자료로 이동할 수 있습니다.', bullets(
        f'**{text(c)}**　' + ' · '.join(link(f, urls) for f in dict.fromkeys(index[c]))
        for c in sorted(index, key=str.casefold))])


def practice_page(records, nav, urls):
    blocks = [nav, '학습자료에 기록된 장비 설정 예시입니다.']
    for r in records:
        items = [p['title'] for s in r['analysis']['sections'] for p in s['practice']]
        if items:
            blocks += ['## ' + link(r['filename'], urls), bullets(text(t) for t in items)]
    return join(blocks)


GUIDE = """# Notion 게시 안내 (채팅 AI용)

이 폴더의 페이지를 현재 연결된 Notion 도구로 게시한다. 다른 페이지는 고치거나 지우지 않는다.

1. 홈 페이지: `manifest.json`의 `home_url` 페이지 본문을 `pages/home.md` 내용으로 바꾼다.
2. 목록·분야 페이지: `manifest.json`의 `index_pages`마다 홈 페이지 바로 아래에서 제목이 정확히 같은 페이지를 찾는다. 있으면 본문을 바꾸고, 없으면 새로 만든다.
3. 자료 페이지: `materials`마다 '학습자료' 페이지 바로 아래에서 제목(=파일명)이 정확히 같은 페이지를 찾는다. 있으면 본문을 바꾸고, 없으면 새로 만든다. 같은 제목의 페이지를 두 개 만들지 않는다.
4. 링크: 모든 본문에서 `{{page:제목}}`을 해당 제목 페이지의 멘션 `<mention url="페이지URL">제목</mention>`로 바꾼다. 제목은 홈 페이지, 목록·분야 페이지, 자료 페이지 중 하나다.
   - 페이지 파일은 Notion 마크다운이다. 내용을 고치거나 요약하지 말고 그대로 넣는다.
   - 홈과 '학습자료' 페이지에는 하위 페이지가 있다. 본문을 바꿀 때 하위 페이지(`<page>` 태그)를 지우지 말고 본문 끝에 그대로 남긴다.
5. 끝나면 이 폴더에 `result.json`을 만든다. 형식:
   `{"published_at": "ISO 시각", "pages": {"파일명": "자료 페이지 URL"}, "errors": ["실패한 항목과 이유"]}`
6. 실패한 페이지가 있어도 나머지는 계속 진행하고, 마지막에 결과를 짧게 알려 준다.
"""


def build(source, data, config):
    """현재 분석 결과로 게시 패키지를 새로 만든다. 원본이 바뀐 자료는 제외한다."""
    current = {p.name: file_hash(p) for p in list_sources(source)}
    records = [r for r in all_results(data) if current.get(r['filename']) == r['sha256']]
    if not records:
        raise ValueError('게시할 분석 결과가 없습니다. 먼저 자료를 분석하세요.')
    done = published(data)
    pending = [r for r in records if done.get(r['filename'], {}).get('sha256') != r['sha256']]
    urls = {config['home_title']: config['home_url']}
    urls.update({r['filename']: done[r['filename']]['url'] for r in records if r['filename'] in done})
    nav = navigation(config['home_title'], urls)

    folder = Path(data) / 'publish'
    if folder.exists():
        shutil.rmtree(folder)
    pages = {'home.md': home_page(records, nav, urls),
             '학습자료.md': materials_page(records, nav, urls),
             '개념 찾아보기.md': concepts_page(records, nav, urls),
             '실습 찾아보기.md': practice_page(records, nav, urls)}
    for number, (domain, units) in enumerate(DOMAINS, 1):
        pages[f'domain_{number}.md'] = domain_page(domain, units, records, nav, urls)
    materials = []
    for number, record in enumerate(pending, 1):
        name = f'material_{number:02d}.md'
        pages[name] = material_page(record, nav)
        materials.append({'filename': record['filename'], 'sha256': record['sha256'],
                          'file': 'pages/' + name})
    for name, body in pages.items():
        path = folder / 'pages' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body + '\n', encoding='utf-8')
    index_pages = [{'title': t, 'file': f'pages/{t}.md'} for t in INDEX_PAGES]
    index_pages += [{'title': d, 'file': f'pages/domain_{i}.md'} for i, d in enumerate(DOMAIN_TITLES, 1)]
    manifest = {'created_at': now(), 'home_title': config['home_title'], 'home_url': config['home_url'],
                'home_file': 'pages/home.md', 'index_pages': index_pages, 'materials': materials}
    write_json(folder / 'manifest.json', manifest)
    (folder / 'GUIDE.md').write_text(GUIDE, encoding='utf-8')
    (folder / 'preview.html').write_text(preview_html(manifest, folder), encoding='utf-8')
    prompt = ('아래 폴더의 Notion 게시 패키지를 현재 연결된 Notion 도구로 게시해줘. '
              '순서와 규칙은 폴더의 GUIDE.md를 그대로 따라줘.\n'
              f'게시 폴더: {folder.resolve()}')
    (folder / 'prompt.txt').write_text(prompt, encoding='utf-8')
    return {'folder': str(folder.resolve()), 'prompt': prompt, 'materials': [m['filename'] for m in materials],
            'unchanged': len(records) - len(materials)}


def inline_html(value):
    value = re.sub(r'<mention url="[^"]*">(.*?)</mention>', r'⟦\1⟧', value)
    value = re.sub(r'\{\{page:(.*?)\}\}', r'⟦\1⟧', value)
    value = re.sub(r'\\(.)', r'\1', value)
    value = html.escape(value)
    value = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', value)
    return re.sub(r'⟦(.*?)⟧', r'<span class="link">\1</span>', value)


def markdown_html(body):
    """이 모듈이 만드는 마크다운만 화면용 HTML로 바꾼다(미리보기 전용)."""
    out, fence, title = [], None, None
    for line in body.splitlines():
        if fence is not None:
            if line == fence:
                out.append('</pre>')
                fence = None
            else:
                out.append(html.escape(line))
            continue
        if title:
            out.append(f'<{title}>' + inline_html(line) + f'</{title}>')
            title = None
        elif line.startswith('```'):
            fence = line.split('text')[0]
            out.append('<pre>')
        elif line == '<toggle>':
            out.append('<details>')
            title = 'summary'
        elif line.startswith('<callout'):
            out.append('<div class="callout">')
            title = 'b'
        elif line in ('</toggle>', '</callout>'):
            out.append('</details>' if line == '</toggle>' else '</div>')
        elif line.startswith('### '):
            out.append('<h4>' + inline_html(line[4:]) + '</h4>')
        elif line.startswith('## '):
            out.append('<h3>' + inline_html(line[3:]) + '</h3>')
        elif line.startswith('- '):
            out.append('<div class="item">• ' + inline_html(line[2:]) + '</div>')
        elif line:
            out.append('<p>' + inline_html(line) + '</p>')
    return '\n'.join(out)


def preview_html(manifest, folder):
    def read(file):
        return (folder / file).read_text(encoding='utf-8')
    sections = [('홈 · ' + manifest['home_title'], read(manifest['home_file']))]
    sections += [('자료 · ' + m['filename'], read(m['file'])) for m in manifest['materials']]
    sections += [('목록 · ' + p['title'], read(p['file'])) for p in manifest['index_pages']]
    body = '\n'.join(f'<section><h2>{html.escape(title)}</h2>{markdown_html(page)}</section>'
                     for title, page in sections)
    return f"""<!doctype html><html lang="ko"><meta charset="utf-8"><title>게시 미리보기</title>
<style>body{{font-family:sans-serif;max-width:900px;margin:auto;padding:16px;line-height:1.6}}
section{{border:1px solid #ccc;border-radius:8px;padding:12px 20px;margin:16px 0}}
pre{{background:#f4f4f4;padding:8px;white-space:pre-wrap}} details{{margin:6px 0 6px 12px}}
summary{{cursor:pointer;font-weight:bold}} .callout{{background:#fff7e0;padding:8px;border-radius:6px}}
.link{{color:#0b6bcb;text-decoration:underline}}</style>
<p>새로 게시할 자료 {len(manifest['materials'])}개 · 파란 글씨는 Notion에서 페이지 링크가 됩니다.</p>
{body}</html>"""
