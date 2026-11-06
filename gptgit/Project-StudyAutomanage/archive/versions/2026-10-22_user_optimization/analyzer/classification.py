"""Local classification suggestions and traceable cross-material links."""
import copy
import re
import unicodedata

from .cache import digest
from .core import AnalysisError
from .curriculum import CURRICULUM

DEFAULT_POLICY = {
    'version': 1,
    'curriculum': CURRICULUM,
    'categories': [
        {'name': '하이브리드 네트워크', 'terms': ['하이브리드 연결', '온프레미스와 클라우드', 'VPN 연결', 'direct connect', 'expressroute']},
        {'name': '클라우드 네트워크', 'terms': ['클라우드 네트워크', 'VPC', 'VNET', '가상 네트워크', '서브넷']},
        {'name': '네트워크 자동화', 'terms': ['네트워크 자동화', 'network automation', 'netmiko', 'napalm', 'netconf', 'restconf']},
        {'name': '네트워크 보안', 'terms': ['방화벽', 'ACL', '접근 제어', '망 분리', '네트워크 보안']},
        {'name': '온프레미스 네트워크', 'terms': ['VLAN', '라우팅', '라우터', '스위치', '트렁크', 'OSPF', 'BGP', 'RIP', 'IGP', 'EGP', '스패닝 트리', 'STP', 'EtherChannel', 'VTP', '루프백', 'TCP', 'DNS', 'DHCP']},
    ],
    'concept_aliases': {'STP': '스패닝 트리', '스패닝 트리 설정': '스패닝 트리', 'Native VLAN': '네이티브 VLAN'},
    'publication_holds': {'12일차.docx': '기존 인계의 Stub network 보안·패킷 손실 단락 게시 보류. 해당 내용 검토 후 명시적으로 해제 필요.'},
}


def normalized(value):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', value)).casefold()


def validate_paths(paths):
    if not isinstance(paths, list) or not paths or len(paths) > 100:
        raise AnalysisError('CLASSIFICATION_ERROR', '하나 이상의 분류 경로가 필요합니다.')
    result = []
    for path in paths:
        if (not isinstance(path, list) or not 2 <= len(path) <= 12
                or path[0] != 'NETWORK' or any(not isinstance(v, str) or not v.strip() or len(v) > 200 for v in path)):
            raise AnalysisError('CLASSIFICATION_ERROR', '분류 경로는 NETWORK로 시작하는 2~12개 이름이어야 합니다.')
        cleaned = [v.strip() for v in path]
        if cleaned not in result:
            result.append(cleaned)
    return result


def validate_policy(policy):
    if not isinstance(policy, dict) or not {'version', 'categories', 'concept_aliases', 'publication_holds'} <= set(policy) or set(policy) - {'version', 'categories', 'concept_aliases', 'publication_holds', 'curriculum'} or policy['version'] != 1:
        raise AnalysisError('CLASSIFICATION_ERROR', '분류 정책 형식을 확인하세요.')
    if not isinstance(policy['categories'], list) or not policy['categories']:
        raise AnalysisError('CLASSIFICATION_ERROR', '분야 분류 규칙이 필요합니다.')
    for rule in policy['categories']:
        if (not isinstance(rule, dict) or set(rule) != {'name', 'terms'} or not isinstance(rule['name'], str)
                or not rule['name'].strip() or not isinstance(rule['terms'], list) or not rule['terms']
                or any(not isinstance(t, str) or not t.strip() for t in rule['terms'])):
            raise AnalysisError('CLASSIFICATION_ERROR', '분야 이름과 검색어 목록을 확인하세요.')
    aliases = policy['concept_aliases']
    if not isinstance(aliases, dict) or any(not isinstance(k, str) or not isinstance(v, str) or not k.strip() or not v.strip() for k, v in aliases.items()):
        raise AnalysisError('CLASSIFICATION_ERROR', '개념 별칭 형식을 확인하세요.')
    targets = {normalized(k): normalized(v) for k, v in aliases.items()}
    for key in targets:
        seen, current = set(), key
        while current in targets and targets[current] != current:
            if current in seen:
                raise AnalysisError('CLASSIFICATION_ERROR', '개념 별칭이 순환합니다.')
            seen.add(current); current = targets[current]
    holds = policy['publication_holds']
    if not isinstance(holds, dict) or any(not isinstance(k, str) or not isinstance(v, str) or not k.strip() or not v.strip() for k, v in holds.items()):
        raise AnalysisError('CLASSIFICATION_ERROR', '게시 보류 이름·사유를 확인하세요.')
    if 'curriculum' in policy:
        from .curriculum import validate_curriculum
        validate_curriculum(policy['curriculum'])
    return copy.deepcopy(policy)


def topic_paths(topics, prefix=()):
    for topic in topics:
        path = prefix + (topic['name'],)
        if topic.get('children'):
            yield from topic_paths(topic['children'], path)
        else:
            yield list(path)


def matches(text, term):
    if re.fullmatch(r'[A-Za-z0-9]+', term):
        return re.search(r'(?<![A-Za-z0-9])' + re.escape(term) + r'(?![A-Za-z0-9])', text, re.I) is not None
    return normalized(term) in normalized(text)


def suggest(analysis, policy):
    if policy.get('curriculum'):
        from .curriculum import suggest_curriculum
        return suggest_curriculum(analysis, policy['curriculum'])
    paths, reasons, unclassified = [], [], []
    for path in topic_paths(analysis['topics']):
        path = [p for p in path if normalized(p) != 'network']
        text = ' / '.join(path)
        if not path:
            continue
        rule = next((r for r in policy['categories'] if any(matches(text, t) for t in r['terms'])), None)
        if rule:
            candidate = ['NETWORK', rule['name']] + (path[1:] if normalized(path[0]) == normalized(rule['name']) else path)
            if candidate not in paths:
                paths.append(candidate[:12])
                reasons.append({'path': candidate[:12], 'source': 'analysis.topics', 'matched_topic': text})
        else:
            unclassified.append(path)
    if unclassified or not paths:
        paths.append(['NETWORK', '관련성 미확인'])
    return {'paths': paths, 'reasons': reasons, 'unclassified_topics': unclassified,
            'scope_confirmed': bool(paths) and not unclassified and paths != [['NETWORK', '관련성 미확인']]}


def concept_name(name, policy):
    names = {normalized(k): v for k, v in policy['concept_aliases'].items()}
    seen = set()
    while normalized(name) in names and normalized(name) not in seen:
        seen.add(normalized(name)); name = names[normalized(name)]
    return name


def knowledge_index(materials, policy):
    concepts, by_material, categories = {}, {}, {}
    for material in materials:
        mid, analysis = material['id'], material['analysis']
        by_material[mid] = set()
        for path in material['classification']['paths']:
            for depth in range(2, len(path)+1):
                key = ' / '.join(path[:depth])
                categories.setdefault(key, []).append(mid)
        for index, concept in enumerate(analysis['concepts']):
            name = concept_name(concept['name'], policy)
            key = digest(normalized(name))
            entry = concepts.setdefault(key, {'id': key, 'name': name, 'aliases': [], 'sources': []})
            if concept['name'] not in entry['aliases']:
                entry['aliases'].append(concept['name'])
            entry['sources'].append({'material_id': mid, 'filename': analysis['source']['filename'],
                                     'pointer': f'/concepts/{index}', 'description': concept['description'],
                                     'approval_status': material['status']})
            by_material[mid].add(key)
    related = {m['id']: [] for m in materials}
    for i, left in enumerate(materials):
        for right in materials[i+1:]:
            shared = by_material[left['id']] & by_material[right['id']]
            same = left['analysis']['source']['material_id'] == right['analysis']['source']['material_id']
            if not shared and not same:
                continue
            reason = {'shared_concepts': sorted(concepts[k]['name'] for k in shared), 'same_source_hash': same,
                      'kind': 'duplicate_bytes' if same else 'shared_concepts', 'semantic_duplicate_confirmed': False}
            related[left['id']].append(dict(reason, material_id=right['id'], filename=right['analysis']['source']['filename']))
            related[right['id']].append(dict(reason, material_id=left['id'], filename=left['analysis']['source']['filename']))
    for entry in concepts.values():
        entry['different_descriptions'] = len({s['description'] for s in entry['sources']}) > 1
        entry['interpretation'] = '원문별 설명 보존; 서로 다르다고 오류·모순으로 자동 판정하지 않음'
    return {'categories': [{'path': path, 'material_ids': sorted(set(ids))} for path, ids in sorted(categories.items())],
            'concepts': sorted(concepts.values(), key=lambda x: x['name']), 'related': related}
