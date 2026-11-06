# Phase 1 검증 근거

> 2026-10-18 정리 · 사용자 제공 출력과 성공 보고를 구분한다. AI가 장비에 접속·적용·재실행한 결과가 아니다.
> [현재 상태·다음 작업](../02_design/network%20project%20진행상황.md) · [환경·주소 원본](../02_design/실습%20환경%20및%20주소.md) · [날짜별 이력](../04_records/작업%20기록.md)
> 이 문서는 시점별 증거를 관리한다. 현재 주소·설정을 여기와 환경 문서에 동시에 갱신하지 않는다.

<a id="baseline"></a>
## $1 이전에 완료한 검증 — 2026-10-10~11

| 검증 | 기록된 결과 | 근거 수준 |
| --- | --- | --- |
| IOSvL2 SVI·VLAN 간 라우팅 | VLAN10·20 up/up, 직접 연결 경로, PC10 → PC20 5/5 | 제공 출력·사용자 확인 |
| Trunk·STP | CORE Gi0/2 VLAN10·20 forwarding, 두 VLAN Root FWD | 제공 출력; 이전 none의 정확한 원인은 미확정 |
| 외부 Linux 연결 | eth1/pnet1 직접 브리지, Linux → CORE·PC20 성공, 두 VM 재부팅 후 유지 | 설정 출력·사용자 성공 보고 |
| CORE–EDGE·중복 SVI 조치 | ASW 중복 주소 제거 후 정상화; 재부팅 후 Linux → EDGE 손실 0%, EDGE → PC20 10/10 | 제공 출력·사용자 확인 |
| EDGE 자체 외부 통신 | NAT GW 5/5, 1.1.1.1 10/10 | 제공 결과 |
| 내부 단말 PAT | PC20 외부 IP 성공·ICMP 변환, Linux 실습 경로 손실 0% | 제공 출력·사용자 확인 |
| PNETLab 재부팅 후 외부 통신 | CORE 기본 경로·EDGE 외부 IP 유지, PC20 외부 Ping 성공 | 사용자 확인; 마지막 손실률 전체 출력 미수집 |
| EDGE 외부 고정 주소 후보 검사 | ARP 검사 3 probes / 0 responses | 당시 응답 미감지이며 향후 무충돌 보장은 아님 |

전체 Image 이름·PC20 역방향 Ping·Linux 임시 경로 삭제 결과가 과거에는 미수집이었으나 아래 10월 18일 근거가 이를 보완한다. 과거 미완료 문구를 최신 할 일로 다시 승계하지 않는다.

<a id="dns"></a>
## $2 DNS·저장·PC20 재시작 — 2026-10-18

1. [사용자 확인] `ping 1.1.1.1` 정상. `ping example.com`은 `Cannot resolve example.com`, DNS 주소는 비어 있음.
2. [절차 제시·사용자 적용 결과] PC20에서 `ip dns 1.1.1.1` 안내 후 이름 해석·통신 성공 출력 제공.
3. [제공 출력] `example.com resolved to 104.20.23.154`; ICMP 1~5 모두 응답, TTL 126, 39.092~42.939ms, 손실 0%.
4. [사용자 확인] PC20 `save` 완료. 이후 PC20 재시작 후 DNS 설정 유지와 통신 성공 보고. 재시작 후 원시 출력은 별도 미수집.

도메인의 응답 주소는 당시 값이다. DNS 서버·PNETLab 전체를 재시작한 검증이 아니라 PC20의 저장 유지 검증이다. 재현 명령은 [DNS 가이드 2절](../../guide_docs/Phase1_DNS_및_잔여검증_가이드.html#dns)을 따른다.

<a id="linux"></a>
## $3 임시 경로·DHCP 정정 — 2026-10-18

- [사용자 확인] `ip route show 1.1.1.1/32` 출력 없음. 현재 조회 테이블의 임시 경로는 없으므로 추가 삭제는 하지 않음.
- [제공 출력] ens32 .100/24는 유효기간 forever, .128/24는 secondary dynamic, 남은 유효기간 1710초.
- [제공 출력] 활성 연결 netplan-ens32, DHCP 서버 식별자 .254, 임대시간 1800초, 임대 ip_address .128, routers·DNS .2.
- [제공 출력] 프로필 method auto, 수동 addresses .100/24. Netplan에서도 addresses .100, dhcp4 true, dhcp6 true 확인.
- [사용자 확인] VMware DHCP Settings의 시작 .128 / 끝 .254.
- [판정] 현재 .128은 DHCP 임대이며 수동 .100·EDGE .110과 범위가 겹치지 않음. 설정 변경 없이 확인 종료. 다른 VM 전체의 임대·고정 주소 조사는 하지 않음.
- [충돌 처리] 과거 .100·.128 모두 수동 입력했다는 보고와 현재 출처를 구분. 변경 경위는 미확인으로 유지. 기존의 현재 상태 설명 중 “.128 수동 고정 주소 중복·미조치” 판단을 대체함.

현재 값은 [환경 문서의 관리망 DHCP](../02_design/실습%20환경%20및%20주소.md#dhcp)가 기준이다. 조회 명령·필요한 출력 범위는 [가이드 3절](../../guide_docs/Phase1_DNS_및_잔여검증_가이드.html#linux)에 있다.

<a id="images"></a>
## $4 이미지 이름·역방향 통신 — 2026-10-18

- [사용자 확인] ASW1·CORE-TEST와 EDGE-TEST의 전체 Image 이름 수집 완료. 값은 [환경 문서](../02_design/실습%20환경%20및%20주소.md#images)로 통합했다. 기존 계열·버전·기능 검증을 다시 수행한 것이 아니다.
- [사용자 확인] PC20 → PC10 Ping 성공. 기존 반대 방향 결과와 합쳐 양방향 통신 확인. 이번 역방향 Ping의 전체 손실률 출력은 별도 미수집.
- [제한] Template 선택값 중 CORE·EDGE는 미수집. 현재 기본 통신 진행을 막는 조건으로 두지 않는다.

<a id="tables"></a>
## $5 CORE·ASW·EDGE 출력 대조 — 2026-10-18

### %1 CORE 경로·ARP

제공된 `show ip route`에서 VLAN10·20 /24 및 전송망 /30의 C 경로와 각 인터페이스의 L 경로를 확인했다. 기본 경로는 EDGE 방향이며 기존 설계와 일치한다.

| ARP 대상 | 제공된 MAC | 인터페이스 |
| --- | --- | --- |
| PC10 | 0050.7966.6803 | Vlan10 |
| PC20 | 0050.7966.6805 | Vlan20 |
| CORE VLAN10 / VLAN20 자신 | 5053.3100.800a / 5053.3100.8014 | Vlan10 / Vlan20 |
| EDGE 내부 | 50f0.6e00.0600 | Gi0/3 |

Linux는 해당 ARP 표에 없었다. 이것만으로 장애라고 판단하지 않는다.

### %2 ASW 동적 MAC

`show mac address-table dynamic` 제공 결과: VLAN10 PC10 MAC은 Gi0/0, VLAN20 PC20 MAC은 Gi0/1, CORE의 두 SVI MAC은 각각 VLAN10·20에서 Gi0/2로 학습. 총 4개이며 CORE ARP와 일치한다. 기존 기록에서 미수집이던 단말별 실제 포트가 보완됐다.

### %3 EDGE 경로·NAT

- 제공된 경로에서 내부 VLAN 두 대역의 정적 반환 경로, 전송망·외부망 직접 연결, VMware GW 방향 기본 경로를 확인했다. 현재 경로 값은 [환경 문서](../02_design/실습%20환경%20및%20주소.md#routing) 참조.
- PC20 연속 Ping을 안내한 뒤 제공된 NAT 표에서 inside local PC20 → inside global EDGE 외부 주소, 목적지 1.1.1.1의 ICMP 행을 확인했다. 식별자 31890 등 여러 행이 있으며 식별자는 TCP/UDP 포트가 아니다.
- 이 출력은 NAT 변환 생성 근거다. 해당 연속 Ping의 전체 응답·손실률과 Ctrl+C 중지 결과는 별도 수집하지 않았다. 반복 행만으로 오류라고 판단하지 않는다.

<a id="scope"></a>
## $6 검증 범위와 미검증

이번에 확보된 근거는 현재 실습 VLAN의 연결성·DNS·주소 출처·장비 정보·통신 테이블 대조다. 다음을 완료로 확대하지 않는다.

- HTTP/HTTPS 서비스 전체 동작, Linux WEB-01·WEB-02·DB-01 역할 구축
- 최종 회사망 전체 주소·VLAN·실습 DHCP·보안 ACL 설계
- AWS/VPN, HA 및 이미지의 미검증 추가 기능
- 관리망 전체 무충돌, 모든 정책 라우팅 테이블, 학교 자동 OFF 문제 해결

예전 TCP NAT 행만으로 웹서비스를 검증했다고 간주하지 않는다. 중복 SVI 조치 직후 손실·과거 STP none의 정확한 원인은 확정하지 않는다.

## $7 사용 자료

- 이전 결과: 작업기록의 2026-10-10~11 항목. 원시 로그 파일이 별도로 보관됐다는 근거는 없다.
- 이번 결과: 현재 채팅의 사용자 제공 출력·성공 보고. 독립 재실행 검증은 하지 않았다.
- 재현 안내: [Linux 연결](../../guide_docs/Linux_PNETLab_통신검증_가이드.html), [CORE–EDGE](../../guide_docs/CORE_EDGE_연결_검증_가이드.html), [EDGE 인터넷·NAT](../../guide_docs/EDGE_인터넷_NAT_검증_가이드.html), [DNS·잔여 검증](../../guide_docs/Phase1_DNS_및_잔여검증_가이드.html).
