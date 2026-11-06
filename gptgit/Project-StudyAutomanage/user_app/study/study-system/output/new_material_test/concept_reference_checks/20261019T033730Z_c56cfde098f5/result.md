# 1일차\_LAN구성\.txt

Schema 0.2 · 원문 기반 분석 · 내용 검토 필요

LAN 통신 원리를 소개하고 스위치 VLAN·트렁크, Router\-on\-a\-stick, ACL 설정 예시를 제시합니다\.

형식·연결 검사와 기술적 사실성·실습 성공 검증은 별개입니다.

## LAN 통신 원리와 테이블

### ARP Table

자료는 ARP Table을 IP와 MAC 주소의 변환용 테이블로 설명하며, PC·라우터 등에서 목적지 IP에 대응하는 MAC 주소를 확인하는 데 사용한다고 적습니다\. arp 또는 show arp 명령으로 확인할 수 있다고 안내합니다\.

### MAC Table

자료는 MAC Table을 MAC 주소와 포트를 확인하는 테이블로 소개합니다\. 목적지 MAC 주소에 대응하는 포트를 스위치가 찾는 LAN 통신 순서도 함께 설명합니다\.

### Routing Table

자료는 Routing Table을 IP와 포트를 확인하는 테이블로 소개합니다\. 이 항목에 대한 추가 동작 설명이나 설정 예시는 제시하지 않습니다\.

### LAN 통신 순서

자료에서는 송신 시스템이 목적지 IP에 대응하는 MAC 주소를 ARP Table에서 찾고, 없으면 브로드캐스트 주소를 목적지 MAC으로 사용한다고 설명합니다\. 스위치는 MAC Table에서 목적지 포트를 찾으며, 없으면 모든 포트로 프레임을 전송합니다\. 수신 시스템은 목적지 IP를 자신의 IP와 비교하고, 자료에 적힌 순서에서는 응답 프레임을 받은 스위치가 출발지 MAC을 MAC Table에 기록한 뒤 유니캐스트하며, 송신 시스템은 회신 프레임을 기준으로 ARP Table을 저장한다고 설명합니다\.

### ARP Table, MAC Table, Routing Table

자료는 ARP Table을 IP와 MAC 주소 변환용, MAC Table을 MAC 주소와 포트 확인용, Routing Table을 IP와 포트 확인용 테이블로 나열합니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
PC, 서버, 스위치, 라우터의 통신 원리에서 가장 많이 사용된느 기능은 Table이다.
1. ARP Table : IP<=>MAC주소 변환용 테이블
 =>PC, Router등에서 사용
 =>목적지 IP에 상응하는 MAC주소 확인용
 =>arp 또는 show arp명려으로 확인 가능
2. MAC Table : MAC<=>Port 확인용 테이블
3. Routing Table : IP<=>Port 확인용 테이블
```

### 자료에 제시된 LAN 통신 순서

자료에서는 송신 시스템이 목적지 IP에 대응하는 MAC 주소를 ARP Table에서 찾고, 없으면 브로드캐스트 주소를 목적지 MAC으로 사용한다고 설명합니다\. 스위치는 목적지 MAC에 대응하는 포트를 찾고, 찾지 못하면 모든 포트로 전송합니다\. 수신 시스템은 자신의 IP와 목적지 IP를 비교하며, 이후 응답 프레임을 받은 스위치가 출발지 MAC을 학습하고 유니캐스트한 뒤 송신 시스템이 회신 프레임을 기준으로 ARP Table을 저장한다고 서술합니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
LAN통신 순서
1. 송신 시스템은 ARP Table에서 목적지 IP에 상응하는 MAC주소 확인. 없으면 브로드 캐스트(FFFFFFFFFFFF)주소를 목적지 MAC주소로 입력. 있으면 해당 MAC주소를 목적지 주소로 선택
2. 스위치는 자신의 MAC Table에서 목적지 MAC주소에 상응하는 포트 확인. 없으면 모든 포트에 프레임 전송(브로드 캐스팅)
3. 수신 시스템은 자신의 IP와 목적지 IP를 비교. 맞으면 응답. 틀리면 무시
4. 반송신호를 받은 스위치는 출발지 MAC주소를 MAC Table에 기록 후 유니 캐스팅
5. 송신 시스템은 회신 프레임을 기준으로 자신의 ARP Table에 목적지 MAC주소를 저장. 이후 동일한 목적지로 프레임 전송 시 유니 캐스팅.
```

## 스위치 VLAN 및 트렁크 설정

### VLAN 액세스 포트

스위치의 지정 인터페이스 범위에 VLAN을 할당하고 access 모드로 설정하는 명령 예시가 있습니다\. SW3의 Fa0/1–3은 VLAN 30, SW2의 Fa0/1–2는 VLAN 20, SW1의 Fa0/1–3은 VLAN 10으로 설정하도록 제시합니다\.

### 트렁크 포트

자료는 트렁크 포트가 프레임에 VLAN tagging을 붙이는 기능을 갖는다고 설명합니다\. SW3의 Fa0/24와 SW1·SW2의 Fa0/23–24를 trunk 모드로 설정하는 예시를 제시하고, 각 스위치의 VLAN DB에 VLAN 10, 20, 30 정보가 있어야 한다고 적습니다\.

### 트렁크 포트 → VLAN 액세스 포트

프레임에 VLAN 태그를 붙이는 기능을 수행한다

자료는 트렁크 포트의 태깅 기능과 별도로 각 스위치 액세스 포트의 VLAN 할당 예시를 설명합니다\.

### 트렁크 포트

자료는 트렁크 포트가 프레임에 VLAN tagging을 붙이는 기능을 갖는다고 설명합니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
Step 2. 스위치에 트렁크 포트 생성
- 트렁크 포트는 프레임에 Vlan tagging(꼬리표)를 붙이는 기능을 갖는다.
```

### 스위치별 VLAN 정보

자료는 트렁크 기능을 위해 각 스위치의 VLAN DB에 VLAN 10, 20, 30 정보가 있어야 한다고 설명하고, SW1·SW2·SW3에 누락된 VLAN을 추가하는 명령 예시를 제시합니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
Trunk기능은 각 스위치의 VLAN DB에 해당 vlan정보가 있어야 가능하다. 따라서, 각 스위치에 vlan10, 20, 30이 모두 학습되어야 함.
SW1
conf t
vlan 20
vlan 30

SW2
conf t
vlan 10
vlan 30

SW3
conf t
vlan 10
vlan 20
```

### 스위치 액세스 포트의 VLAN 설정

SW3 Fa0/1–3에 VLAN 30, SW2 Fa0/1–2에 VLAN 20, SW1 Fa0/1–3에 VLAN 10을 할당하고 access 모드로 설정하는 명령 예시입니다\. 실행 여부나 결과는 기록되어 있지 않습니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
Step 1. 각 스위치별 Vlan설정
SW3
en
conf t
int range fa0/1 - 3
sw acc vlan 30
sw mode access

SW2
en
conf t
int range fa0/1 - 2
sw acc vlan 20
sw mode access

SW1
en
conf t
int range fa0/1 - 3
sw acc vlan 10
sw mode access
```

### 스위치 트렁크 및 VLAN DB 설정

SW3 Fa0/24와 SW1·SW2 Fa0/23–24를 trunk 모드로 설정하고, 각 스위치에 VLAN 10, 20, 30 정보를 추가하는 명령 예시입니다\. SW3에는 VLAN 표시 확인 명령도 제시되어 있으나 확인 결과는 없습니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
Step 2. 스위치에 트렁크 포트 생성
- 트렁크 포트는 프레임에 Vlan tagging(꼬리표)를 붙이는 기능을 갖는다.
SW3
conf t
int fa0/24
sw mode trunk
do sh vlan

SW2, SW1
conf t
int range fa0/23 - 24
sw mode trunk

Trunk기능은 각 스위치의 VLAN DB에 해당 vlan정보가 있어야 가능하다. 따라서, 각 스위치에 vlan10, 20, 30이 모두 학습되어야 함.
SW1
conf t
vlan 20
vlan 30

SW2
conf t
vlan 10
vlan 30

SW3
conf t
vlan 10
vlan 20
```

### VLAN

자료는 스위치 액세스 포트를 VLAN 10·20·30에 할당하고, 각 스위치의 VLAN DB에 해당 VLAN 정보를 구성한 뒤 라우터 하위 인터페이스에 dot1q VLAN ID를 지정하는 예시를 제시합니다\.

## Router\-on\-a\-stick

### Router\-on\-a\-stick

R1의 G0/0을 활성화하고 G0/0\.10, G0/0\.20, G0/0\.30 하위 인터페이스에 각각 dot1q VLAN ID 10, 20, 30과 192\.168\.10\.254/24, 192\.168\.20\.254/24, 192\.168\.30\.254/24 주소를 설정하는 예시가 있습니다\. 자료는 이 구성을 마친 뒤 서로 다른 VLAN 간 통신이 가능한 상태라고 설명하지만, 실행 결과는 제시하지 않습니다\.

### Router\-on\-a\-stick → VLAN

하위 인터페이스에 VLAN ID를 지정한다

R1의 하위 인터페이스별 dot1q 설정에 VLAN ID 10, 20, 30이 제시되어 있습니다\.

### Router\-on\-a\-stick 하위 인터페이스 설정

R1의 G0/0을 활성화하고 하위 인터페이스별 dot1q VLAN ID와 IP 주소를 설정하는 명령 예시입니다\. 자료는 서로 다른 VLAN 간 통신이 가능한 상태라고 서술하지만, 별도의 확인 명령이나 실행 결과는 없습니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
Step 3. Router-on-a-stick구성
R1
en
conf t
int g0/0
no sh
int g0/0.10
encap dot1q 10
ip addr 192.168.10.254 255.255.255.0
int g0/0.20
encap dot1q 20
ip addr 192.168.20.254 255.255.255.0
int g0/0.30
encap dot1q 30
ip addr 192.168.30.254 255.255.255.0

※이제 서로 다른  vlan간 통신 가능 상태
```

### VLAN

자료는 스위치 액세스 포트를 VLAN 10·20·30에 할당하고, 각 스위치의 VLAN DB에 해당 VLAN 정보를 구성한 뒤 라우터 하위 인터페이스에 dot1q VLAN ID를 지정하는 예시를 제시합니다\.

## ACL 접근 제어

### ACL

자료는 ACL을 접근통제목록으로 소개하고 일반적으로 L3 또는 라우터에 구현하며 표준과 확장 유형으로 분류한다고 설명합니다\. 확장은 특정 프로토콜을 제어할 수 있다고 적고, VLAN 10의 웹 접근·VLAN 30의 FTP 접근·메일 서비스 허용 조건에 대응하는 ACL 명령 예시를 제시합니다\.

### ACL

자료는 ACL을 접근통제목록으로 소개하고, 일반적으로 L3 또는 라우터에 구현하며 표준과 확장의 두 유형으로 나눈다고 설명합니다\. 확장은 특정 프로토콜에 대한 제어가 가능하다고 적습니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
ACL(Access Control List)-접근통제목록
=>일반적으로  L3또는 라우터에 구현
=>표준, 확장의 2가지 유형으로 분류
=>확장은 특정 프로토콜에 대한 제어 가능
```

### ACL 설정 및 인터페이스 적용

ACL 100에 VLAN 10의 TCP 80·UDP 53 허용, TCP 80 거부, VLAN 30의 TCP 21 허용, TCP 21 거부, 나머지 IP 허용 명령을 제시하고 R1 G0/0\.20에 outbound 방향으로 적용합니다\. 명령 예시만 있으며 정책 동작의 확인 결과는 없습니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
ACL조건
- Vlan 10은 Web접근 가능
- Vlan 30은 FTP접근 가능
- Mail서비스는 모두 가능

R1
conf t
acc 100 permit tcp 192.168.10.0 0.0.0.255 any eq 80
acc 100 permit udp 192.168.10.0 0.0.0.255 any eq 53
acc 100 deny tcp any any eq 80
acc 100 permit tcp 192.168.30.0 0.0.0.255 any eq 21
acc 100 deny tcp any any eq 21
acc 100 permit ip any any
int g0/0.20
ip access-group 100 out
```

---

코멘트 0개 · 검토 대기 후보 0개 · 보조 항목 제외 사유 0개

원본 JSON은 별도로 보존합니다. 표시본의 인증값 숨김은 원문 인용 수정이 아닙니다.
