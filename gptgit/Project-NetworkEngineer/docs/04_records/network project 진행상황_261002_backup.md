# network project 진행상황

> 과거 백업(2026-10-02): 현재 설계·상태의 기준으로 사용하지 않는다. 본문은 당시 기록을 유지하고 문서 연결만 현재 배치로 수정했다.
> 문서 연결: [프로젝트 안내](../../README.md) · [AI 작업 지침](../../AGENTS.md) · [상세 규칙](../00_rules/network%20project%20%EA%B7%9C%EC%B9%99.md) · [현재 설계·상태](../02_design/network%20project%20%EC%A7%84%ED%96%89%EC%83%81%ED%99%A9.md) · [작업 이력](%EC%9E%91%EC%97%85%20%EA%B8%B0%EB%A1%9D.md)

## $1 프로젝트 개요

### %1 프로젝트 목적 및 범위

Network engineer 취업을 위한 전체 인프라 구조 이해 및 실습 프로젝트.

범위:

- On-Premise Network
- Linux Server
- Web Service
- Database
- AWS Cloud Network
- On-Premise ↔ AWS 연결
- HA / Redundancy
- Security
- Monitoring
- Python Automation

### %2 프로젝트 진행 방향

- 전체 구조를 먼저 설계하고 단계적으로 구현한다.
- 실제 현업의 구현 순서를 그대로 따라가기보다 전체 구조 이해와 학습 효과를 우선한다.
- 구현 중 문제나 변경 필요 사항이 발견되면 설계를 수정한다.
- 설계 변경은 프로젝트 진행 과정의 정상적인 절차로 취급한다.


---

## $2 전체 아키텍처

### %1 Hybrid Cloud

#### ^1 구성 배경

이 프로젝트는 특정 웹서비스 자체를 운영하는 것을 목표로 하지 않는다.

가상의 중견 규모 회사를 전제로 하며, 과거에는 AWS와 같은 클라우드 환경으로 대부분의 인프라를 이전했지만 현재는 기존 On-Premise 환경을 일부 유지하면서 AWS와 함께 사용하는 **Hybrid Cloud 환경**을 구성하는 것을 목표로 한다.

따라서 서비스 자체의 상세한 애플리케이션 개발보다는 다음 네트워크 엔지니어 관점의 영역을 중심으로 학습한다.

- On-Premise ↔ AWS 연결
- 사설 네트워크 간 통신
- Routing / Subnet / Security
- 개발 및 운영 환경의 네트워크 접근
- AWS 네트워크 운영
- 장애 및 연결성 검증

#### ^2 기본 Hybrid 구조

```text
                         Internet
                            │
                            ▼
                     AWS Public Area
                            │
                           ALB
                            │
                            ▼
                    AWS Private Subnet
                       │           │
                     APP-01      APP-02
                       │           │
                       └─────┬─────┘
                             │
                            DB

Developer / Admin / Monitoring
              │
              ▼
        On-Premise Network
              │
         Edge Router
              │
             VPN
              │
              ▼
           AWS VPC

※ 서비스 트래픽과 관리/배포 트래픽은 논리적으로 구분하여 설계한다.
```

#### ^3 개발/운영 환경 관점

개발자가 애플리케이션을 직접 구현하는 것이 아니라, On-Premise에 존재하는 개발/관리 환경에서 AWS Private Subnet의 시스템에 접근할 수 있는 구조를 중심으로 학습한다.

배포 방식 자체는 아직 확정하지 않는다. 향후 필요에 따라 Git / CI-CD / 배포 서버 등의 구성을 검토한다.

기본 방향:

```text
Developer / Admin
        │
        ▼
 On-Premise Network
        │
       VPN
        │
        ▼
    AWS VPC
        │
 ┌──────┴────────┐
 │               │
 ▼               ▼
Public         Private
Subnet         Subnet
 │               │
ALB          APP / DB
```

### %2 On-Premise

#### ^1 내부망 기본 구조

현재 프로젝트의 On-Premise 내부 인프라망은 가상의 개발회사를 기준으로 다음과 같이 구성한다.

- [확정] Edge Router 1대를 외부/클라우드 연결 경계로 사용한다.
- [확정] Core L3 Switch를 사내 내부망의 중심 장비로 사용한다.
- [확정] L2 Switch는 총 3대를 기본 구성으로 한다.
- [확정] L2-SW01은 개발/테스트 영역으로 구성한다.
- [확정] L2-SW02와 L2-SW03은 운영 영역으로 구성한다.
- [확정] 개발/테스트 영역에는 개발 PC, Test Server, Test DB를 배치하는 방향으로 한다.
- [확정] 운영 영역에는 실제 운영 환경을 가정한 시스템 및 사용자/업무 단말 등을 배치한다.
- [확정] AWS는 사내 L2 End Device 영역이 아니라 Edge Router 외부의 Cloud 영역으로 모델링한다.
- [검토] 실제 VLAN 분리, IP/Subnet, L3 Routing 및 ACL 정책은 장비 이미지와 기능 확인 후 설계한다.

기본 논리 구조:

```text
                         AWS VPC
                            │
                     VPN / Internet
                            │
                    Edge Router
                            │
                        Core L3
                            │
              ┌─────────────┼─────────────┐
              │             │             │
           L2-SW01       L2-SW02       L2-SW03
          개발/테스트        운영           운영
              │             │             │
        ┌─────┼─────┐     운영 영역      운영 영역
        │     │     │
     개발 PC Test   Test
            Server  DB
```

※ 위 구조는 회사 내부망의 기본 모델이며, 실제 PNETLab 노드 연결과 VMware 외부 네트워크 연결 방식은 Cisco 이미지/기능 확인 후 확정한다.

#### ^2 내부망 설계 기준

```text
회사 운영 환경 가정
        ↓
On-Premise + AWS Hybrid 구조 정의
        ↓
논리적 노드 / 역할 정의
        ↓
통신 흐름 정의
        ↓
IP / VLAN / Subnet / Routing 설계
        ↓
VMware / 네트워크 실습 환경 구현
        ↓
AWS 연결
        ↓
Monitoring / Automation
```

### %3 AWS

#### ^1 기본 AWS 구조

```text
                         On-Premise
                              │
                         Edge Router
                              │ VPN
                              ▼
                     ┌─────────────────┐
                     │     AWS VPC     │
                     │                 │
                     │ ┌─────────────┐ │
                     │ │Public Subnet│ │
                     │ │     ALB     │ │
                     │ └──────┬──────┘ │
                     │        │         │
                     │ ┌──────▼──────┐  │
                     │ │   Private   │  │
                     │ │   Subnet    │  │
                     │ │    EC2      │  │
                     │ └─────────────┘  │
                     └─────────────────┘
```

#### ^2 AWS 학습 항목

- VPC
- Public / Private Subnet
- Route Table
- Internet Gateway
- Security Group
- NACL
- EC2
- ALB
- VPN

### %4 네트워크 실습 환경

- On-Premise 네트워크 장비는 실제 물리 장비 대신 VMware 위에서 가상 환경으로 구성한다.
- 네트워크 장비 에뮬레이션/실습 플랫폼은 현재 **PNETLab**을 사용한다.
- 네트워크 장비 계열은 사용자의 기존 학습 경험을 고려하여 **Cisco 계열**로 통일한다.
- Virtual Router와 Virtual L3 Switch 모두 Cisco 계열을 우선 사용한다.
- [추론:확인필요] 실제 사용할 Cisco 이미지와 정확한 모델/기능은 Phase 1에서 PNETLab 환경과 이미지 호환성을 확인한 뒤 확정한다.

---

## $3 현재 환경

### %1 VMware 가상화 환경

- VMware 사용
- On-Premise Network Lab 구성에 사용
- PNETLab VM을 VMware 위에서 실행
- Linux 서버 VM도 VMware 환경에서 구성
- [확정] 현재 VMware 환경에는 PNETLab VM, Linux 테스트 Server VM, Linux 테스트 DB Server VM을 구축한 상태
- [확정] 현재 3개 VM은 모두 VMware VMnet8 NAT 네트워크를 사용

현재 VMware 구조:

```text
Windows PC
  │
  └── VMware Workstation
       │
       └── VMnet8 (NAT)
            192.168.111.0/24
            Gateway: 192.168.111.2
            DHCP: Enabled
                 │
        ┌────────┼────────┐
        │        │        │
     PNETLab  Linux     Linux DB
              Server      Server
     VMnet8   .200        .100 / .128
```

### %2 PNETLab

- [현재 사용] PNETLab 테스트 환경 구축 완료
- [검토] 최종 네트워크 실습 플랫폼은 실제 테스트 및 비교 후 확정
- PNETLab은 네트워크 장비 실습 계층으로 사용한다.
- Linux 서버 VM은 필요에 따라 별도의 VMware VM으로 구성하여 VMware 가상 네트워크 → Cisco Router/L3 Switch → VLAN → Linux Server 흐름을 학습한다.

### %3 Linux 테스트 VM

#### ^1 Linux 테스트 Server

- [확정] 192.168.111.200/24
- [확정] Gateway: 192.168.111.2

#### ^2 Linux 테스트 DB Server

- [확정] 192.168.111.100/24
- [확정] 192.168.111.128/24
- [확정] Default Gateway: 192.168.111.2
- [추론:확인필요] 두 IPv4 주소가 의도된 구성인지 확인 필요

### %4 네트워크 장비

- 플랫폼: PNETLab
- Vendor: Cisco 계열
- Router: Cisco Virtual Router
- L3 Switch: Cisco Virtual L3 Switch
- [추론:확인필요] 실제 Cisco 이미지 및 모델은 Phase 1에서 결정

실습실 물리 장비 환경은 프로젝트 네트워크 장비 구성의 참고 기준으로 사용한다.

- Cisco 2800 Router 1대
- Catalyst 3560 24포트 L3 Switch 2대
- Catalyst 2960 48포트 L2 Switch 1대
- Catalyst 2960 24포트 L2 Switch 2대

[검토] PNETLab에서는 위 실습실 장비와 대응되는 Cisco 이미지/모델을 우선 검토하되, 실제 이미지 호환성과 필요한 기능을 확인한 뒤 결정한다.

### %5 AWS 환경

- AWS 기본 리소스 사용
- 비용 최소화가 중요
- 필요한 리소스만 생성하고 실습 후 제거하는 방향

---

## $4 현재 설계

### %1 내부 네트워크 역할

- [확정] 기본 내부망 모델은 1 Router + 1 Core L3 Switch + 3 L2 Switch로 구성
- [확정] L2 Switch 역할은 개발/테스트 1대 + 운영 2대로 구분
- [확정] 초기 구현에서는 기능 검증을 위해 단순화할 수 있으며, 이후 필요 시 HA / Redundancy를 확장
- [검토] 실제 VLAN 분리, IP/Subnet, L3 Routing 및 ACL 정책은 장비 이미지와 기능 확인 후 설계한다.

### %2 관리망 / 실습망

현재는 관리망과 별도 실습망을 아직 확정하지 않았다.

PNETLab 지원 장비/연결 방식을 확인한 뒤 다음 항목을 설계한다.

- VMware 관리망 / 실습망 구조
- PNETLab과 VMware 외부 Linux VM 연결 방식
- PNETLab 외부 연결에 필요한 VMware 네트워크 구성

### %3 서비스 통신 구조

서비스 구조는 네트워크 구성과 통신 흐름을 이해하기 위한 참고 모델로 사용한다.
애플리케이션 개발 자체는 프로젝트의 핵심 범위에서 제외한다.

현재 On-Premise 내부망의 상세 장비 구성은 `$2 전체 아키텍처`의 On-Premise 구조를 기준으로 하며, AWS는 별도의 Cloud 영역으로 모델링한다.


### %4 통신 흐름 기준

| 출발지 | 목적지 | Protocol | Port | 목적 |
|---|---|---|---|---|
| Client | Web Server | HTTPS | 443 | 웹서비스 |
| Web Server | DB | TCP | 3306 | DB 조회/저장 |
| Monitoring | Linux Server | HTTP/TCP | TBD | Metric 수집 |
| Monitoring | Network Device | SNMP | 161 | 장비 모니터링 |
| Python | Network Device | SSH | 22 | 상태조회/자동화 |
| Python | AWS | HTTPS | 443 | AWS API |
| On-Prem | AWS | VPN | TBD | 사설망 연결 |

### %5 관리 / 모니터링 / 자동화

- Monitoring은 네트워크 및 서버 상태를 확인하는 운영 영역으로 구성한다.
- Python은 네트워크/서버/AWS의 관리 및 운영 자동화 영역으로 사용한다.
- 구체적인 도구와 구현 내용은 `$5 구축 단계`의 Phase 6~7에서 관리한다.

---

## $5 구축 단계

### %1 Phase 0 - 전체 설계

상태: 설계 단계

확정/검토 내용:

- 전체 인프라 구조
- On-Premise / AWS 역할 분리
- Hybrid Cloud 방향
- 네트워크 장비 및 가상화 실습 방향
- Monitoring / Automation 방향
- HA / Redundancy 및 보안 학습 방향

핵심 질문:

"누가 누구와 어떤 IP / Port / Protocol로 통신하는가?"


### %2 Phase 1 - VMware / PNETLab Network

상태: 진행 준비

완료:

1. VMware 기본 가상 네트워크 구조 확인
2. PNETLab VM 구축
3. Linux 테스트 Server VM 구축
4. Linux 테스트 DB Server VM 구축
5. 현재 3개 VM의 VMnet8 연결 상태 확인

다음 작업:

1. VMware 관리망 / 실습망 구조 설계
2. PNETLab과 VMware 외부 Linux VM의 연결 방식 설계
3. PNETLab에서 지원하는 Cisco Router / L3 / L2 장비 후보 확인
4. 실제 사용할 장비를 기준으로 Cisco 이미지/모델 및 필요한 기능 검토
5. Router ↔ L3 Switch 연결
6. VLAN / Trunk 구성
7. IP / Subnet 설계
8. Inter-VLAN Routing
9. Linux WEB-01 연결
10. Ping / ARP / MAC / Routing Table 검증

[추론:확인필요] Cisco 이미지의 정확한 모델과 기능은 PNETLab에서 실제 구동 및 필요한 기능을 검증한 뒤 최종 확정한다.

학습 항목:

- Ethernet
- MAC
- ARP
- VLAN
- Access / Trunk
- STP / RSTP
- IP / Subnet
- Gateway
- Static Routing
- DHCP
- DNS

초기 구현은 기능 검증을 우선하며, 이후 필요하면 HA 구성을 확장한다.


### %3 Phase 2 - Linux Server

상태: 예정

구성:

- WEB-01
- WEB-02
- DB-01

예정 기술:

- Linux
- Nginx / Apache
- Python Web Application
- MariaDB

### %4 Phase 3 - Web Service

상태: 예정

예정 기능:

- GET /
- GET /users
- POST /users

통신 구조:

Client → HTTP/HTTPS → Web Server → TCP 3306 → DB

### %5 Phase 4 - Network Redundancy

상태: 예정

학습 항목:

- STP / RSTP
- LACP
- Gateway Redundancy
- Routing Redundancy
- ECMP 개념

초기에는 단일 장비 구조로 전체 동작을 먼저 확인하고 이후 Cisco 기반 HA 구성을 확장한다.

장애 실습:

- Switch 장애
- Link 장애
- VLAN 장애
- Routing 장애

### %6 Phase 5 - AWS / Hybrid Cloud

상태: 예정

학습 방향:

- On-Premise ↔ AWS 연결
- 사설 네트워크 간 통신
- Routing / Subnet / Security
- 개발 및 운영 환경의 네트워크 접근
- AWS 네트워크 운영
- 장애 및 연결성 검증

### %7 Phase 6 - Monitoring

상태: 예정

구성:

- Prometheus
- Grafana
- Node Exporter
- SNMP Exporter

모니터링 대상:

- Linux CPU
- Memory
- Disk
- Network
- Server 상태
- Network Device Interface
- 장애 상태

### %8 Phase 7 - Python Automation

상태: 예정

기본 방향:

```text
Monitoring
→ 장애 감지
→ Python
→ 상태 수집
→ 엔지니어 판단
```

사용 예정:

- Netmiko
- Paramiko
- Boto3
- Requests

초기에는:

1. 상태 조회
2. Health Check
3. 정보 수집
4. 결과 출력 / 기록

순서로 진행한다.

초기 단계에서는 자동 복구를 적용하지 않는다.

Python은 서비스 트래픽 경로가 아니라 관리/운영 자동화 영역으로 사용한다.

### %9 Phase 8 - 장애 / 보안 / 운영

상태: 예정

장애 시나리오:

- WEB-01 Down
- Switch Link Down
- DB Port 차단
- AWS EC2 Down
- VPN Tunnel Down
- Routing 장애
- VLAN 장애

표준 처리:

장애 발생
→ 증상 확인
→ 범위 확인
→ 원인 분석
→ 조치
→ 재검증
→ 문서화

---

## $6 현재 상태

### %1 현재 진행 위치

**Phase 0 전체 아키텍처 설계 → Hybrid Cloud 관점의 전체 구조 재정리 → Phase 1 진입 준비**

### %2 현재 확정된 방향

- [확정] 특정 웹서비스 자체의 운영을 프로젝트 중심으로 두지 않는다.
- [확정] 중견 규모 회사를 가정하고 On-Premise와 AWS를 함께 사용하는 Hybrid Cloud 환경을 기본 배경으로 한다.
- [확정] 서비스 구조는 네트워크 구성의 이해를 위한 참고 모델로 사용하고, 애플리케이션 개발 자체는 프로젝트의 핵심 범위에서 제외한다.
- [확정] On-Premise는 개발/관리/모니터링 등의 내부 환경으로 활용하고 AWS Private Subnet의 시스템과 연결되는 구조를 학습한다.
- [확정] 서비스 트래픽과 관리/배포 트래픽을 논리적으로 구분하여 설계한다.
- [확정] On-Premise Network Lab은 VMware 기반으로 구성한다.
- [현재 사용] PNETLab 테스트 환경 구축 완료
- [확정] 네트워크 장비 계열은 Cisco로 통일한다.
- [확정] 기본 내부망 모델은 1 Router + 1 Core L3 Switch + 3 L2 Switch로 구성한다.
- [확정] L2 Switch 역할은 개발/테스트 1대 + 운영 2대로 구분한다.
- [검토] 최종 네트워크 실습 플랫폼
- [검토] 실제 Cisco 이미지 및 모델
- [검토] VLAN ID / IP Subnet
- [검토] Routing Protocol
- [검토] AWS VPN 방식
- [검토] 실제 배포 방식(Git / CI-CD / 배포 서버 등)


### %3 확인 필요

- [추론:확인필요] DB Server의 두 IPv4 주소가 의도된 구성인지 확인 필요
- [추론:확인필요] 실제 Cisco 이미지 및 모델은 PNETLab에서 구동 및 필요한 기능을 검증한 뒤 확정
- [검토] 관리망과 별도 실습망의 구체적인 VMware 네트워크 구조
- [검토] PNETLab과 VMware 외부 Linux VM 연결 방식


---

## $7 미확정 사항

- Firewall 구성 방법 및 제품
- 실제 Cisco Virtual Router 이미지/모델
- 실제 Cisco Virtual L3 Switch 이미지/모델
- VLAN ID
- IP / Subnet
- Routing Protocol
- AWS Region
- AWS VPN 방식
- DB Replication
- Load Balancer 세부 구성
- Monitoring Server 위치
- 실제 HA 범위
- 세부 Security 정책
- 실제 배포 방식(Git / CI-CD / 배포 서버 등)

미확정 사항은 실제 구현 단계에서 환경과 학습 목적을 확인한 뒤 결정한다.

---

## $8 다음 작업

### %1 Phase 1 우선 작업

1. VMware 관리망 / 실습망 구조 설계
2. PNETLab과 VMware 외부 Linux VM 연결 방식 설계
3. PNETLab에서 지원하는 Cisco Router / L3 / L2 장비 후보 확인
4. 실제 사용할 장비를 기준으로 Cisco 이미지/모델 및 필요한 기능 검토

### %2 이후 작업

Phase 1의 장비/연결 구조가 확정된 후:

1. Router ↔ L3 Switch 연결
2. VLAN / Trunk 구성
3. IP / Subnet 설계
4. Inter-VLAN Routing
5. Linux WEB-01 연결
6. Ping / ARP / MAC / Routing Table 검증

---

## $9 문서 역할

- [network project 규칙.md](../00_rules/network%20project%20%EA%B7%9C%EC%B9%99.md) → 프로젝트 전체 작업 원칙과 답변 기준
- [network project 진행상황.md](../02_design/network%20project%20%EC%A7%84%ED%96%89%EC%83%81%ED%99%A9.md) → 현재 프로젝트의 설계와 현재 상태
- [작업 기록.md](%EC%9E%91%EC%97%85%20%EA%B8%B0%EB%A1%9D.md) → 프로젝트 작업 이력 및 작업 내용 요약

[network project 진행상황.md](../02_design/network%20project%20%EC%A7%84%ED%96%89%EC%83%81%ED%99%A9.md)에는 작업 중간의 임시 판단이나 작업 이력을 수시로 기록하지 않고, 최종적으로 확정된 현재 상태와 설계 변경사항을 반영한다.

문서 내 정보는 가능한 한 한 곳에서 관리한다. 전체 구조는 `$2`, 실제 구축 환경은 `$3`, 현재 설계 원칙은 `$4`, 구현 내용은 `$5`, 현재 진행 상태는 `$6`, 미확정 항목은 `$7`, 바로 다음 작업은 `$8`을 기준으로 하며 동일 정보를 여러 `$` 영역에서 반복하지 않는다.
