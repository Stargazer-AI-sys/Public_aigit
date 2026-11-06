"""Reading pages derived from approved content; no enrichment or approval edits."""
import re
import copy
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from .classification import concept_name, normalized
from .curriculum import CURRICULUM, learning_view
from .render import redact, resolve


def refresh_reader_target(target, directory):
    """Resolve display links from this destination's existing delivery receipts."""
    path = Path(directory)/'delivery.sqlite3'
    if not target.get('reader') or not path.is_file():
        return target
    from .cache import digest
    from .core import AnalysisError
    identity = 'notion-mcp:'+digest({k: v['data_source_id'] for k,v in target['collections'].items()})
    result = copy.deepcopy(target)
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True)) as db:
        if db.execute('SELECT id FROM destination').fetchone()[0] != identity:
            raise AnalysisError('PUBLISH_DESTINATION_MISMATCH', '다른 대상의 페이지 ID를 연결할 수 없습니다.')
        rows = db.execute('SELECT entity_key,record FROM receipts').fetchall()
    result['reader']['pages'].update({eid: json.loads(raw)['id'] for eid,raw in rows})
    return result


def text(value):
    # Preserve approved inline code, escape ordinary Notion inline syntax.
    parts = re.split(r'(`[^`\n]+`)', redact(str(value)))
    return ''.join(p if p.startswith('`') and p.endswith('`') else
                   re.sub(r'([\\*~`$\[\]<>{}|^])', r'\\\1', p) for p in parts)


def mention(pid, label):
    return f'<mention-page url="https://app.notion.com/p/{pid}">{text(label)}</mention-page>'


def quote(value):
    value = redact(value)
    longest = max((len(m[0]) for m in re.finditer(r'`+', value)), default=0)
    fence = '`' * max(3, longest+1)
    return fence+'text\n'+value+'\n'+fence


def navigation(target):
    reader = target.get('reader', {})
    links = [('학습 홈', target['parent_page']['id'])]
    links += [(name, pid) for name, pid in reader.get('indexes', {}).items()]
    return '　·　'.join(mention(pid, name) for name, pid in links)


def material_navigation(target):
    indexes = target.get('reader', {}).get('indexes', {})
    pid = indexes.get('학습자료')
    return mention(pid, '학습자료 목록') if pid else '학습자료'


def material_body(record, nav, *, concept_link=None, practice_link=None,
                  practice_summary=None, classification=True):
    """Render approved content inline; optional links belong to full publication."""
    analysis = record['analysis']
    concept_link = concept_link or (lambda item: text(item['name']))
    practice_link = practice_link or (lambda index, title: text(title))
    if practice_summary is None:
        practice_summary = '\n'.join('- '+text(p['title']) for p in analysis.get('practice', [])) or '이 자료에 기록된 실습 예시는 없습니다.'
    lines = [nav, '', '## 핵심 정리', text(analysis['summary'])]
    if classification:
        lines += ['', '## 분류'] + [' / '.join(text(v) for v in path) for path in record['classification']['paths']]
    lines += ['', '## 주제별 내용']
    refs = {r['id']: r for r in analysis.get('references', [])}
    sections = analysis.get('sections', [])
    if not sections:
        pointers = [f'/concepts/{i}' for i in range(len(analysis['concepts']))]
        if classification:
            pointers += [f'/relationships/{i}' for i in range(len(analysis.get('relationships', [])))]
            pointers += [f'/theory/{group}/{i}' for group, items in analysis.get('theory', {}).items()
                         for i in range(len(items))]
            pointers += [f'/practice/{i}' for i in range(len(analysis.get('practice', [])))]
        sections = [{'title': '학습 내용', 'content_refs': pointers}]
    for section in sections:
        children = []
        for pointer in section['content_refs']:
            item = resolve(analysis, pointer)
            title = item.get('name') or item.get('title') or item.get('subject')
            if pointer.startswith('/concepts/'):
                children += ['### '+concept_link(item), text(item['description'])]
            elif pointer.startswith('/practice/'):
                children += ['### '+practice_link(int(pointer.split('/')[-1]), title), text(item['description']),
                             '<details>', '<summary>원문 설정 예시</summary>',
                             *['\t'+line for line in quote(item['evidence']).splitlines()], '</details>']
            else:
                if 'from' in item:
                    title = item['from']+' → '+item['to']
                if 'subject_a' in item:
                    title = item['subject_a']+' / '+item['subject_b']
                if title:
                    children += ['### '+text(title)]
                for field in ('relation', 'description', 'content'):
                    if item.get(field): children += [text(item[field])]
                children += ['- '+text(v) for v in item.get('criteria', [])]
                if item.get('evidence'):
                    children += ['<details>', '<summary>원문 근거</summary>',
                                 *['\t'+line for line in quote(item['evidence']).splitlines()], '</details>']
        if section.get('comment'):
            c = section['comment']
            children += ['<callout icon="💡">', '\t'+('보충 설명' if c['kind']=='supplement' else '정정 설명'), '\t'+text(c['text']), '</callout>']
            for rid in c['reference_ids']:
                ref = refs[rid]
                children += [f'참고: [{text(ref["title"])}]({ref["url"]})']
        lines += ['<details>', '<summary>'+text(section['title'])+'</summary>',
                  *['\t'+line for line in children], '</details>', '']
    lines += ['## 관련 실습', practice_summary, '',
              '<details>', '<summary>원본 정보</summary>', '\t파일명　'+text(analysis['source']['filename'])]
    lines += ['\t'+text(p) for p in record.get('locations', [])]
    lines += ['</details>']
    return '\n'.join(lines)


def build_reader(entities, approved, policy, target, material_keys):
    """Return bodies and UI models without changing stored classifications/relations.

    Topic membership reuses the existing learning_view alias/keyword map. Practice
    links use explicit section content_refs, never every concept in a source.
    """
    pages = target['reader'].get('pages', {})
    materials = {r['id']: r for r in approved['materials']}
    concepts = {'concept:'+c['id']: c for c in approved['concepts']}
    by_name = {normalized(c['name']): eid for eid, c in concepts.items()}
    category_children = {}
    for key, entity in entities.items():
        if entity['kind'] == 'category':
            for parent in entity['relations']['parent']:
                category_children.setdefault(parent, []).append(key)
    practice_items, practice_concepts, concept_practices = {}, {}, {eid: [] for eid in concepts}
    for mid, record in materials.items():
        analysis = record['analysis']
        practice_entities = entities[material_keys[mid]]['relations']['practice']
        for index, item in enumerate(analysis.get('practice', [])):
            eid = practice_entities[index]
            pointers = {p for s in analysis.get('sections', [])
                        if f'/practice/{index}' in s['content_refs'] for p in s['content_refs']
                        if p.startswith('/concepts/')}
            connected = sorted({by_name[normalized(concept_name(resolve(analysis, p)['name'], policy))]
                                for p in pointers})
            practice_items[eid] = (mid, item)
            practice_concepts[eid] = connected
            for cid in connected:
                concept_practices[cid].append(eid)
    curriculum = learning_view(approved['materials'], approved['concepts'], policy.get('curriculum', CURRICULUM))
    paths, concept_paths = {}, {eid: [] for eid in concepts}
    for domain in curriculum['domains']:
        for unit in domain['units']:
            path = 'NETWORK / '+domain['title']+' / '+unit['title']
            paths[path] = unit
            for c in unit['concepts']:
                concept_paths['concept:'+c['id']].append(path)

    def link(eid, label=None):
        label = label or entities[eid]['properties']['name']
        return mention(pages[eid], label) if eid in pages else text(label)

    def links(keys):
        return ' · '.join(link(k) for k in dict.fromkeys(keys))

    def practice_list(keys):
        return '\n'.join('- '+link(k) for k in dict.fromkeys(keys)) or '현재 연결된 원문 실습이 없습니다.'

    bodies = {}
    nav = navigation(target)
    category_by_path = {e['properties']['path']: eid for eid, e in entities.items() if e['kind'] == 'category'}
    for eid, concept in concepts.items():
        aliases = list(concept.get('aliases', []))
        aliases += [k for k, v in policy['concept_aliases'].items()
                    if normalized(concept_name(v, policy)) == normalized(concept['name'])]
        aliases = list(dict.fromkeys(a for a in aliases if normalized(a) != normalized(concept['name'])))
        lines = [nav, '']
        if aliases:
            lines += ['다른 이름　'+text(' · '.join(aliases)), '']
        cats = [category_by_path[p] for p in concept_paths[eid] if p in category_by_path]
        if cats:
            lines += ['학습 항목　'+links(cats), '']
        lines += ['## 자료별 설명', '']
        for source in concept['sources']:
            lines += ['### '+link(material_keys[source['material_id']], source['filename']),
                      text(source['description']), '']
        lines += ['## 관련 실습', practice_list(concept_practices[eid])]
        bodies[eid] = '\n'.join(lines)
    for eid, (mid, item) in practice_items.items():
        lines = [nav, '', '학습자료　'+link(material_keys[mid]), '']
        if practice_concepts[eid]:
            lines += ['관련 개념　'+links(practice_concepts[eid]), '']
        lines += ['## 실습 내용', text(item['description']), '',
                  '## 원문 설정 예시', '원문에 기록된 예시입니다. 장비 실행 결과와 구분해 확인하세요.',
                  quote(item['evidence'])]
        bodies[eid] = '\n'.join(lines)
    for mid, record in materials.items():
        eid = material_keys[mid]
        bodies[eid] = material_body(record, nav,
            concept_link=lambda item: link(by_name[normalized(concept_name(item['name'], policy))], item['name']),
            practice_link=lambda index, title: link(entities[eid]['relations']['practice'][index], title),
            practice_summary=practice_list(entities[eid]['relations']['practice']), classification=False)
    for eid, entity in entities.items():
        if entity['kind'] != 'category': continue
        path = entity['properties']['path']; unit = paths.get(path)
        lines = [nav, '']
        children = category_children.get(eid, [])
        if children:
            lines += ['## 세부 학습 항목']+['- '+link(k) for k in children]
        cids = ['concept:'+c['id'] for c in unit['concepts']] if unit else []
        if unit:
            lines += ['공식 범위 연결' if unit['scope']=='core' else '보충 학습 항목', '', '## 관련 개념']
            lines += ['- '+link(k) for k in cids] or ['현재 연결된 개념이 없습니다.']
            mids = unit['material_ids']
        else:
            mids = [m for m, r in materials.items() if any(' / '.join(p).startswith(path+' / ') or ' / '.join(p)==path for p in r['classification']['paths'])]
        lines += ['', '## 학습자료']+['- '+link(material_keys[m]) for m in mids]
        selected_practice = [p for p in practice_items if any(c in cids for c in practice_concepts[p])]
        if unit:
            lines += ['', '## 관련 실습', practice_list(selected_practice)]
            lines += ['', '<details>', '<summary>학습 범위와 참고자료</summary>']
            lines += ['\t['+text(r['title'])+']('+r['url']+')' for r in unit['references']]
            lines += ['</details>']
        bodies[eid] = '\n'.join(lines)
    return {'bodies': bodies, 'concept_paths': concept_paths,
            'concept_practices': concept_practices, 'practice_concepts': practice_concepts,
            'curriculum': curriculum}


def apply_reader(entities, approved, policy, target, material_keys):
    model = build_reader(entities, approved, policy, target, material_keys)
    for eid, body in model['bodies'].items():
        entities[eid]['body'] = body
    return model


def build_front_pages(plan, approved, policy, target, home, *, navigation_plan=None):
    """Native Notion learning navigation. Database controls stay in management."""
    from .notion_sync import material_key, key
    entities = {e['key']: e for e in plan['entities']}
    mids = {r['id']: material_key(r) for r in approved['materials']}
    if plan.get('publication_mode') == 'materials':
        lines = ['자료별 핵심 정리와 주제별 설명을 읽어보세요.', '']
        pages = target['reader']['pages']
        for record in sorted(approved['materials'], key=lambda r: r['analysis']['source']['filename']):
            eid = mids[record['id']]
            if eid not in pages:
                raise ValueError('자료 페이지 ID가 없습니다.')
            lines += ['## '+mention(pages[eid], entities[eid]['properties']['name']),
                      text(record['analysis']['summary'])]
            lines += [' / '.join(text(v) for v in path) for path in record['classification']['paths']]
            lines += ['']
        changes = [{'page_id': target['reader']['indexes']['학습자료'], 'body': '\n'.join(lines)}]
        if home.get('navigation_pages'):
            if navigation_plan is None or navigation_plan.get('publication_mode') == 'materials':
                raise ValueError('학습 홈·분야의 로컬 화면 계획이 없습니다.')
            # Render only: these logical entities are never submitted for DB publication.
            fronts = build_front_pages(navigation_plan, approved, policy, target, home)
            if home.get('category_layout') == 'ccna-basic-17':
                from .learning_categories import domain_pages
                domain_ids = {p['id'].replace('-', '') for p in home['navigation_pages']}
                fronts = [p for p in fronts if p['page_id'].replace('-', '') not in domain_ids]
                fronts += domain_pages(approved, target, home, {e['key']: e for e in navigation_plan['entities']})
            ids = {p['id'].replace('-', '') for p in home['navigation_pages']}
            ids.add(target['parent_page']['id'].replace('-', ''))
            changes += [p for p in fronts if p['page_id'].replace('-', '') in ids]
        return changes
    model = build_reader(entities, approved, policy, target, mids)
    pages = target['reader']['pages']
    def link(eid):
        label = entities[eid]['properties']['name']
        return mention(pages[eid], label) if eid in pages else text(label)
    def joined(keys):
        return ' · '.join(link(k) for k in dict.fromkeys(keys))
    nav = navigation(target)
    nav_pages = home['navigation_pages']
    changes = []
    by_name = {normalized(c['name']): 'concept:'+c['id'] for c in approved['concepts']}
    short = {0:'장비 · 연결 · 기본 동작',1:'VLAN · 트렁크 · STP',2:'경로 선택 · 라우팅 프로토콜',
             3:'주소 할당 · 네트워크 서비스',4:'접근 제어 · 장비 보안',5:'네트워크 자동화 · 데이터 표현'}
    for i, domain in enumerate(model['curriculum']['domains']):
        lines = [nav, '', short[i], '']
        for scope, title in [('core','세부 학습 항목'),('extension','보충 학습')]:
            units = [u for u in domain['units'] if u['scope']==scope and u['material_ids']]
            if not units: continue
            lines += ['## '+title, '']
            for u in units:
                cid = key('category', ['NETWORK',domain['title'],u['title']])
                lines += ['### '+link(cid)]
                if u['concepts']:
                    lines += [joined(['concept:'+c['id'] for c in u['concepts'][:4]])]
                lines += ['개념 설명 → 학습자료 → 관련 실습', '']
        if not domain['material_ids']:
            lines += ['<callout icon="📚">','\t아직 연결된 학습자료가 없습니다.','\t자료가 준비되면 이곳에서 찾아볼 수 있습니다.','</callout>']
        else:
            lines += ['## 분야의 학습자료']+['- '+link(mids[m]) for m in domain['material_ids']]
        changes.append({'page_id': nav_pages[i]['id'], 'body':'\n'.join(lines)})
    indexes = target['reader']['indexes']
    concept_lines = [nav,'','학습할 개념을 선택하면 자료별 설명과 관련 실습을 함께 볼 수 있습니다.','']
    seen = set()
    for domain in model['curriculum']['domains']:
        cids = list(dict.fromkeys('concept:'+c['id'] for u in domain['units'] for c in u['concepts']))
        cids = [cid for cid in cids if cid not in seen]
        if cids:
            concept_lines += ['## '+domain['title']]+['- '+link(cid) for cid in cids]+['']
            seen.update(cids)
    remaining = [eid for eid,e in entities.items() if e['kind']=='concept' and eid not in seen]
    if remaining:
        concept_lines += ['## 함께 살펴볼 개념']+['- '+link(cid) for cid in remaining]
    changes.append({'page_id': indexes['개념 찾아보기'], 'body':'\n'.join(concept_lines)})
    material_lines = [nav,'','자료별로 핵심 정리와 주제별 설명을 읽어보세요.','']
    practice_lines = [nav,'','학습자료에 기록된 설정 예시입니다. 자료를 골라 관련 실습을 살펴보세요.','']
    table = ['<table header-row="true" fit-page-width="true">',
             '\t<tr><td>자료</td><td>관련 개념</td><td>실습</td></tr>']
    for record in sorted(approved['materials'],key=lambda r:r['analysis']['source']['filename']):
        eid = mids[record['id']]; e=entities[eid]
        material_lines += ['## '+link(eid), text(record['analysis']['summary']), '']
        practices = e['relations']['practice']
        practice_lines += ['## '+link(eid)]+(['- '+link(p) for p in practices] or ['이 자료에 기록된 실습 예시는 없습니다.'])+['']
        table += ['\t<tr><td>'+link(eid)+'</td><td>'+joined(e['relations']['concepts'][:3])+'</td><td>'+
                  (link(practices[0]) if practices else '—')+'</td></tr>']
    table += ['</table>']
    changes += [{'page_id':indexes['학습자료'],'body':'\n'.join(material_lines)},
                {'page_id':indexes['실습 찾아보기'],'body':'\n'.join(practice_lines)}]
    root_lines = ['분야에서 시작해 개념을 이해하고, 원문과 실습까지 이어서 찾아보세요.',nav,'','## 학습 분야']
    for row in range(3):
        root_lines += ['<columns>']
        for col in range(2):
            i=row*2+col;p=nav_pages[i]
            title=p['properties']['title'];url=p['url'].split('?')[0]
            description = short[i]
            if home.get('category_layout') == 'ccna-basic-17':
                from .learning_categories import GROUPS
                description = ' · '.join(g[0] for g in GROUPS[i])
            root_lines += ['\t<column ratio="50">','\t\t<callout color="gray_bg">',
                           f'\t\t\t<page url="{url}">{text(title)}</page>',
                           '\t\t\t'+description+(' · 자료 준비 중' if not model['curriculum']['domains'][i]['material_ids'] else ''), '\t\t</callout>','\t</column>']
        root_lines += ['</columns>']
    root_lines += ['','## 학습자료',*table,'','## 개념으로 바로 찾기']
    shortcuts = [by_name[normalized(n)] for n in ['스패닝 트리','VLAN','트렁크 포트','정적 라우팅','경로 재분배'] if normalized(n) in by_name]
    root_lines += [joined(shortcuts),'']
    root_lines += ['<details>','<summary>전체 자료 찾아보기</summary>']
    for name,pid in indexes.items():
        root_lines += [f'\t<page url="https://app.notion.com/p/{pid}">{text(name)}</page>']
    root_lines += ['</details>']
    changes.append({'page_id':target['parent_page']['id'],'body':'\n'.join(root_lines)})
    return changes
