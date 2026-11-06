"""Project learning map based on a pinned Cisco scope; RFCs are references, not a syllabus."""
import copy

BLUEPRINT = 'https://learningcontent.cisco.com/documents/marketing/exam-topics/200-301-CCNA-v1.1.pdf'
RIP = 'https://www.rfc-editor.org/info/rfc2453/'
OSPF = 'https://www.rfc-editor.org/info/rfc2328/'
VTP = 'https://www.cisco.com/c/en/us/support/docs/lan-switching/vtp/98154-conf-vlan.html'
REDISTRIBUTION = 'https://www.cisco.com/c/en/us/support/docs/ip/enhanced-interior-gateway-routing-protocol-eigrp/8606-redist.html'
ETHER = 'https://www.cisco.com/c/en/us/td/docs/switches/lan/c9000/lyr2-fwd/etherchannel/etherchannel-configuration-guide/m_ethernetchannel.html'


def unit(code, title, terms, *, scope='core', references=None):
    return {'code': code, 'title': title, 'terms': terms, 'scope': scope,
            'references': references or [{'title': 'Cisco CCNA v1.1 학습 범위', 'url': BLUEPRINT}]}


CURRICULUM = {
    'id': 'cisco-ccna-200-301-v1.1-project-map', 'checked_on': '2026-10-16',
    'title': 'Cisco CCNA v1.1 기반 학습 분류', 'source_url': BLUEPRINT,
    'notice': '공식 범위를 묶어 구성한 프로젝트 학습 지도입니다. 보충 항목은 공식 시험 항목과 구분하며, RFC는 기술 참고자료입니다. 시험 전체 범위는 공식 원문을 확인하세요.',
    'domains': [
        {'title': '1. 네트워크 기초', 'units': [
            unit('1.1–1.4', '장비·구조·물리 연결', ['라우터 기능', '네트워크 분리', '토폴로지', '케이블', '클라우드 네트워크', '가상 네트워크', 'VPC', 'VNET', '하이브리드 연결']),
            unit('1.5–1.10', '통신과 IP 주소', ['TCP', 'UDP', 'IPv4', 'IPv6', '서브넷', 'VLSM', 'IP 주소', '루프백']),
            unit('1.11–1.13', '스위칭·무선·가상화 기초', ['MAC', '스위칭', '무선 원리', '가상화', 'VRF']),
        ]},
        {'title': '2. 네트워크 접속', 'units': [
            unit('2.1', 'VLAN과 VLAN 간 연결', ['VLAN', 'Inter-VLAN', 'SVI', '액세스 포트', '서브인터페이스']),
            unit('2.2', '트렁크·802.1Q·네이티브 VLAN', ['트렁크', '802.1Q', 'native VLAN', '네이티브 VLAN']),
            unit('2.3', '인접 장비 탐색', ['CDP', 'LLDP']),
            unit('2.4', 'EtherChannel과 LACP', ['EtherChannel', 'LACP'], references=[{'title': 'Cisco CCNA v1.1 · 2.4', 'url': BLUEPRINT}, {'title': 'Cisco EtherChannel 구성', 'url': ETHER}]),
            unit('2.5', '스패닝 트리와 루프 방지', ['스패닝 트리', 'STP', 'PVST', 'PortFast', 'BPDU']),
            unit('2.6–2.9', '무선 접속과 장비 관리', ['WLAN', 'WLC', 'AP 모드', '장비 관리 접속']),
            unit('보충', 'VTP와 PAgP', ['VTP', 'PAgP'], scope='extension', references=[{'title': 'Cisco VTP 구성', 'url': VTP}, {'title': 'Cisco EtherChannel 구성', 'url': ETHER}]),
        ]},
        {'title': '3. IP 라우팅', 'units': [
            unit('3.1–3.2', '라우팅 테이블과 경로 선택', ['라우팅', '라우팅 테이블', '경로 선택', 'Longest prefix', 'AD', 'Cost']),
            unit('3.3', '정적·기본·플로팅 경로', ['정적 라우팅', '정적 경로', '디폴트', '기본 경로', '플로팅', 'Floating', 'Stub network']),
            unit('3.4', '단일 영역 OSPFv2', ['OSPF', 'DR', 'BDR'], references=[{'title': 'Cisco CCNA v1.1 · 3.4', 'url': BLUEPRINT}, {'title': 'RFC 2328 · OSPFv2', 'url': OSPF}]),
            unit('3.5', '게이트웨이 이중화', ['FHRP', 'HSRP', 'VRRP']),
            unit('보충', '라우팅 방식과 RIP', ['IGP', 'EGP', 'Distance vector', 'Link state', 'Hybrid', '동적 라우팅', '라우팅 프로토콜', '경로 계산', 'Routing protocol', 'Routed protocol', 'Hello packet', 'RIP', 'RIPv1', 'RIPv2'], scope='extension', references=[{'title': 'RFC 2453 · RIP v2', 'url': RIP}]),
            unit('보충', '경로 재분배 실습', ['재분배', 'redistribution'], scope='extension', references=[{'title': 'Cisco 라우팅 재분배 구성', 'url': REDISTRIBUTION}]),
        ]},
        {'title': '4. IP 서비스', 'units': [
            unit('4.1–4.6', '주소·이름·시간·운영 서비스', ['NAT', 'NTP', 'DHCP', 'DNS', 'domain lookup', 'SNMP', 'syslog']),
            unit('4.7–4.9', '트래픽 처리와 관리 전송', ['QoS', 'SSH', 'TFTP', 'FTP']),
        ]},
        {'title': '5. 네트워크 보안 기초', 'units': [
            unit('5.1–5.5', '보안 원칙과 장비·VPN 접근', ['보안 정책', '방화벽', '장비 인증', 'AAA', 'IPsec', 'VPN']),
            unit('5.6–5.10', '접근 제어와 접속 보안', ['ACL', '접근 제어', '망 분리', 'DHCP snooping', 'ARP inspection', 'port security', 'WPA']),
        ]},
        {'title': '6. 자동화와 프로그래밍', 'units': [
            unit('6.1–6.4', '네트워크 자동화와 제어 구조', ['네트워크 자동화', 'network automation', 'SDN', '컨트롤러', '네트워크 AI']),
            unit('6.5–6.7', 'API·구성 관리·데이터 표현', ['REST', 'Ansible', 'Terraform', 'JSON', 'NETCONF', 'RESTCONF']),
        ]},
    ],
}


def validate_curriculum(value):
    from .core import AnalysisError
    if (not isinstance(value, dict) or not {'id', 'checked_on', 'title', 'source_url', 'notice', 'domains'} <= set(value)
            or not isinstance(value['domains'], list) or not 1 <= len(value['domains']) <= 20):
        raise AnalysisError('CLASSIFICATION_ERROR', '학습 범위와 출처 메타데이터를 확인하세요.')
    for key in ('id', 'checked_on', 'title', 'source_url', 'notice'):
        if not isinstance(value[key], str) or not value[key].strip():
            raise AnalysisError('CLASSIFICATION_ERROR', '학습 범위 설명이 필요합니다.')
    if not value['source_url'].startswith('https://'):
        raise AnalysisError('CLASSIFICATION_ERROR', '학습 범위는 HTTPS 출처가 필요합니다.')
    for domain in value['domains']:
        if not isinstance(domain, dict) or not isinstance(domain.get('title'), str) or not isinstance(domain.get('units'), list) or not domain['units']:
            raise AnalysisError('CLASSIFICATION_ERROR', '학습 영역·항목 목록을 확인하세요.')
        for item in domain['units']:
            if (not isinstance(item, dict) or not {'code', 'title', 'terms', 'scope', 'references'} <= set(item)
                    or not all(isinstance(item[k], str) and item[k].strip() for k in ('code', 'title', 'scope'))
                    or item['scope'] not in ('core', 'extension') or not isinstance(item['terms'], list) or not item['terms']
                    or any(not isinstance(t, str) or not t.strip() for t in item['terms'])
                    or not isinstance(item['references'], list) or not item['references']):
                raise AnalysisError('CLASSIFICATION_ERROR', '학습 항목 대응 규칙을 확인하세요.')
            for ref in item['references']:
                if (not isinstance(ref, dict) or not isinstance(ref.get('title'), str)
                        or not isinstance(ref.get('url'), str) or not ref['url'].startswith('https://')):
                    raise AnalysisError('CLASSIFICATION_ERROR', '학습 참고 링크를 확인하세요.')
    return value


def suggest_curriculum(analysis, curriculum):
    from .classification import topic_paths, matches
    paths, reasons, unknown = [], [], []
    context = ' '.join(' / '.join(p) for p in topic_paths(analysis['topics'])) + ' ' + ' '.join(c['name'] for c in analysis.get('concepts', []))
    network_context = any(matches(context, t) for t in ['NETWORK', '네트워크', '라우팅', '라우터', '스위치', 'VLAN', 'VPC', 'VNET', 'OSPF', 'RIP', 'NETCONF', 'RESTCONF'])
    sources = [(p, 'analysis.topics', True) for p in topic_paths(analysis['topics'])]
    sources += [([c['name']], 'analysis.concepts.name', False) for c in analysis.get('concepts', [])]
    for source_path, source_kind, required in sources:
        text = ' / '.join(source_path)
        found = False
        for domain in curriculum['domains']:
            if domain['title'].startswith('6.') and not network_context:
                continue
            for item in domain['units']:
                if any(matches(text, term) for term in item['terms']):
                    found = True
                    path = ['NETWORK', domain['title'], item['title']]
                    if path not in paths:
                        paths.append(path)
                        reasons.append({'path': path, 'source': source_kind+' -> pinned curriculum map',
                                        'matched_topic': text, 'curriculum_code': item['code'], 'scope': item['scope']})
        if not found and required:
            unknown.append(source_path)
    if unknown or not paths:
        paths.append(['NETWORK', '관련성 미확인'])
    return {'paths': paths, 'reasons': reasons, 'unclassified_topics': unknown,
            'scope_confirmed': bool(reasons) and not unknown, 'curriculum_id': curriculum['id']}


def learning_view(materials, concepts, curriculum):
    from .classification import matches
    result = copy.deepcopy(curriculum)
    for domain in result['domains']:
        for item in domain['units']:
            path = ['NETWORK', domain['title'], item['title']]
            ids = {m['id'] for m in materials if path in m['classification']['paths']}
            item['material_ids'] = sorted(ids)
            item['concepts'] = []
            for concept in concepts:
                if not any(matches(alias, term) for alias in [concept['name'], *concept['aliases']] for term in item['terms']):
                    continue
                sources = [s for s in concept['sources'] if s['material_id'] in ids]
                if sources:
                    item['concepts'].append(dict(concept, sources=sources))
        domain['material_ids'] = sorted({mid for item in domain['units'] for mid in item['material_ids']})
    return result
