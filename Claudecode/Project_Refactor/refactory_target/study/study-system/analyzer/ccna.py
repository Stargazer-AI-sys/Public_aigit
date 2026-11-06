"""CCNA 학습 분류표. Cisco CCNA v1.1 공식 범위를 묶어 만든 프로젝트용 분류다."""

BLUEPRINT = 'https://learningcontent.cisco.com/documents/marketing/exam-topics/200-301-CCNA-v1.1.pdf'

# (분야, [(시험 항목 번호, 단원, 판단에 도움이 되는 용어)]). '보충'은 공식 시험 항목 밖의 확장 단원이다.
DOMAINS = [
    ('1. 네트워크 기초', [
        ('1.1–1.4', '장비·구조·물리 연결', '라우터 기능, 네트워크 분리, 토폴로지, 케이블, 클라우드·가상 네트워크'),
        ('1.5–1.10', '통신과 IP 주소', 'OSI, TCP, UDP, IPv4, IPv6, 서브넷, VLSM, 루프백'),
        ('1.11–1.13', '스위칭·무선·가상화 기초', 'MAC, 스위칭, 무선 원리, 가상화, VRF'),
    ]),
    ('2. 네트워크 접속', [
        ('2.1', 'VLAN과 VLAN 간 연결', 'VLAN, Inter-VLAN, SVI, 액세스 포트, 서브인터페이스'),
        ('2.2', '트렁크·802.1Q·네이티브 VLAN', '트렁크, 802.1Q, 네이티브 VLAN'),
        ('2.3', '인접 장비 탐색', 'CDP, LLDP'),
        ('2.4', 'EtherChannel과 LACP', 'EtherChannel, LACP'),
        ('2.5', '스패닝 트리와 루프 방지', 'STP, PVST, PortFast, BPDU'),
        ('2.6–2.9', '무선 접속과 장비 관리', 'WLAN, WLC, AP 모드, Telnet·SSH·콘솔 관리 접속'),
        ('보충', 'VTP와 PAgP', 'VTP, PAgP'),
    ]),
    ('3. IP 라우팅', [
        ('3.1–3.2', '라우팅 테이블과 경로 선택', '라우팅 테이블, Longest prefix, AD, 메트릭'),
        ('3.3', '정적·기본·플로팅 경로', '정적 경로, 디폴트 경로, 플로팅 경로, Stub network'),
        ('3.4', '단일 영역 OSPFv2', 'OSPF, DR, BDR'),
        ('3.5', '게이트웨이 이중화', 'FHRP, HSRP, VRRP'),
        ('보충', '라우팅 방식과 RIP', 'IGP, EGP, Distance vector, Link state, RIP'),
        ('보충', '경로 재분배 실습', 'redistribution'),
    ]),
    ('4. IP 서비스', [
        ('4.1–4.6', '주소·이름·시간·운영 서비스', 'NAT, NTP, DHCP, DNS, SNMP, syslog'),
        ('4.7–4.9', '트래픽 처리와 관리 전송', 'QoS, SSH, TFTP, FTP'),
    ]),
    ('5. 네트워크 보안 기초', [
        ('5.1–5.5', '보안 원칙과 장비·VPN 접근', '보안 정책, 방화벽, AAA, IPsec, VPN'),
        ('5.6–5.10', '접근 제어와 접속 보안', 'ACL, port security, DHCP snooping, ARP inspection, WPA'),
    ]),
    ('6. 자동화와 프로그래밍', [
        ('6.1–6.4', '네트워크 자동화와 제어 구조', 'SDN, 컨트롤러, 네트워크 자동화'),
        ('6.5–6.7', 'API·구성 관리·데이터 표현', 'REST, Ansible, Terraform, JSON, NETCONF, RESTCONF'),
    ]),
]


def unit_names():
    """AI가 고를 수 있는 분류 이름 목록. 예: '3. IP 라우팅 / 정적·기본·플로팅 경로'."""
    return [f'{domain} / {title}' for domain, units in DOMAINS for _, title, _ in units]


def prompt_table():
    lines = []
    for domain, units in DOMAINS:
        for code, title, terms in units:
            lines.append(f'- {domain} / {title} (CCNA {code}): {terms}')
    return '\n'.join(lines)
