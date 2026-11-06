"""Small CCNA reading groups. Approved classifications and content stay intact."""
from .classification import matches, topic_paths


# (title, related concepts, legacy approved headings). Legacy headings only
# resolve presentation membership; they never create new approval decisions.
GROUPS = [
    [('통신 원리', 'OSI·TCP/IP·캡슐화·TCP·UDP', ['통신과 IP 주소']),
     ('장비와 이더넷', '라우터·스위치·케이블·MAC·ARP·이더넷·스위칭·토폴로지', ['장비·구조·물리 연결', '스위칭·무선·가상화 기초']),
     ('IP 주소와 서브넷', 'IPv4·IPv6·IP 주소·서브넷·VLSM·루프백', ['통신과 IP 주소'])],
    [('VLAN', 'VLAN·트렁크·802.1Q·네이티브 VLAN·SVI', ['VLAN과 VLAN 간 연결', '트렁크·802.1Q·네이티브 VLAN', 'VTP와 PAgP']),
     ('STP', 'STP·스패닝 트리·루트 브리지·PortFast·BPDU', ['스패닝 트리와 루프 방지']),
     ('EtherChannel', 'EtherChannel·LACP·링크 묶음', ['EtherChannel과 LACP', 'VTP와 PAgP']),
     ('무선 LAN', 'AP·WLC·WLAN·SSID·무선·WPA', ['무선 접속과 장비 관리', '스위칭·무선·가상화 기초'])],
    [('라우팅 기초', '라우팅 테이블·경로 선택·AD·메트릭·FHRP', ['라우팅 테이블과 경로 선택', '게이트웨이 이중화', '라우팅 방식과 RIP', '경로 재분배 실습']),
     ('정적 라우팅', '정적 라우팅·정적 경로·기본 경로·플로팅·디폴트', ['정적·기본·플로팅 경로']),
     ('OSPF', 'OSPF·Router ID·이웃 관계·DR·BDR', ['단일 영역 OSPFv2'])],
    [('주소와 이름 서비스', 'DHCP·DNS·NAT·PAT', ['주소·이름·시간·운영 서비스']),
     ('장비 접속과 관리', 'CLI·콘솔·SSH·CDP·LLDP', ['인접 장비 탐색', '무선 접속과 장비 관리', '트래픽 처리와 관리 전송']),
     ('운영과 모니터링', 'NTP·Syslog·SNMP·TFTP·FTP·QoS', ['주소·이름·시간·운영 서비스', '트래픽 처리와 관리 전송'])],
    [('보안과 인증', '보안·위협·비밀번호·AAA·VPN·IPsec', ['보안 원칙과 장비·VPN 접근']),
     ('접근 제어', 'ACL·Port Security·DHCP Snooping·ARP inspection', ['접근 제어와 접속 보안'])],
    [('네트워크 자동화 기초', '자동화·SDN·컨트롤러·AI', ['네트워크 자동화와 제어 구조']),
     ('API와 데이터', 'REST·HTTP·JSON·Ansible·Terraform', ['API·구성 관리·데이터 표현'])],
]

MATCH_ALIASES = {'VLAN': ['VTP'], 'EtherChannel': ['PAgP'],
                 '장비 접속과 관리': ['Telnet', 'VTY', '원격 접속', '원격접속']}
LEGACY_DEFAULTS = {'통신과 IP 주소': 'IP 주소와 서브넷',
                   '스위칭·무선·가상화 기초': '장비와 이더넷',
                   'VTP와 PAgP': 'VLAN', '무선 접속과 장비 관리': '장비 접속과 관리',
                   '주소·이름·시간·운영 서비스': '운영과 모니터링',
                   '트래픽 처리와 관리 전송': '장비 접속과 관리'}


def grouped_materials(materials):
    """Honor explicit new paths; translate old paths without reclassifying records."""
    result = [[[] for _ in domain] for domain in GROUPS]
    for record in materials:
        paths = record['classification']['paths']
        analysis = record['analysis']
        context = ' '.join(' / '.join(p) for p in topic_paths(analysis['topics']))
        context += ' '+' '.join(c['name'] for c in analysis['concepts'])
        selected = set()
        for path in paths:
            if len(path) < 3 or path[0] != 'NETWORK':
                continue
            exact = [(di, gi) for di, domain in enumerate(GROUPS)
                     for gi, (title, _, _) in enumerate(domain)
                     if path[1].startswith(str(di+1)+'.') and path[-1] == title]
            if exact:
                selected.update(exact)
                continue
            candidates = [(di, gi) for di, domain in enumerate(GROUPS)
                          for gi, (_, _, aliases) in enumerate(domain) if path[-1] in aliases]
            relevant = [(di, gi) for di, gi in candidates
                        if any(matches(context, term) for term in GROUPS[di][gi][1].split('·')
                               + MATCH_ALIASES.get(GROUPS[di][gi][0], []))]
            # A broad old heading alone is not evidence for every possible group.
            fallback = [(di, gi) for di, gi in candidates
                        if GROUPS[di][gi][0] == LEGACY_DEFAULTS.get(path[-1])]
            selected.update(relevant or fallback or candidates)
        for di, gi in selected:
            result[di][gi].append(record)
    return result


def domain_pages(approved, target, home, entities):
    from .notion_reader import navigation, mention, text
    from .notion_sync import material_key
    grouped = grouped_materials(approved['materials'])
    bindings = target['reader']['pages']
    pages = []
    for di, domain in enumerate(GROUPS):
        lines = [navigation(target), '', 'CCNA 기초 학습 항목', '']
        for gi, (title, terms, aliases) in enumerate(domain):
            records = sorted(grouped[di][gi], key=lambda r: r['analysis']['source']['filename'])
            lines += ['## '+title, '관련 내용　'+text(terms), '']
            if not records:
                lines += ['학습자료 준비 중', '']
                continue
            mids = {r['id'] for r in records}
            concepts = [c for c in approved['concepts'] if any(s['material_id'] in mids for s in c['sources'])
                        and any(matches(' '.join([c['name'], *c.get('aliases', [])]), t) for t in terms.split('·'))]
            if concepts:
                lines += ['관련 개념　'+' · '.join(
                    mention(bindings['concept:'+c['id']], c['name']) if 'concept:'+c['id'] in bindings else text(c['name'])
                    for c in concepts)]
            lines += ['### 학습자료']
            for r in records:
                eid = material_key(r)
                if eid not in bindings:
                    raise ValueError('자료 페이지 ID가 없습니다.')
                lines += ['- '+mention(bindings[eid], r['analysis']['source']['filename'])]
            practice_ids = []
            for r in records:
                for index, pid in enumerate(entities[material_key(r)]['relations'].get('practice', [])):
                    if pid not in bindings:
                        continue
                    pointers = {ref for section in r['analysis']['sections']
                                if f'/practice/{index}' in section['content_refs']
                                for ref in section['content_refs'] if ref.startswith('/concepts/')}
                    context = entities[pid]['properties']['name']
                    context += ' '+' '.join(r['analysis']['concepts'][int(ref.split('/')[-1])]['name'] for ref in pointers)
                    if any(matches(context, term) for term in terms.split('·')+MATCH_ALIASES.get(title, [])):
                        practice_ids.append(pid)
            practice_ids = list(dict.fromkeys(practice_ids))
            if practice_ids:
                lines += ['관련 실습　'+' · '.join(mention(bindings[p], entities[p]['properties']['name']) for p in practice_ids)]
            legacy = [e for e in entities.values() if e['kind'] == 'category'
                      and e['properties']['path'].split(' / ')[-1] in aliases and e['key'] in bindings]
            if legacy:
                lines += ['<details>', '<summary>기존 분류의 연결 자료</summary>']
                lines += ['\t'+mention(bindings[e['key']], e['properties']['name']) for e in legacy]
                lines += ['</details>']
            lines += ['']
        pages.append({'page_id': home['navigation_pages'][di]['id'], 'body': '\n'.join(lines)})
    return pages
