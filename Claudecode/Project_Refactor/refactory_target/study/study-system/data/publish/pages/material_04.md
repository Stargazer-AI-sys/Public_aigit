<mention url="https://app.notion.com/p/3fb062cd7cd180c6ab73d56d5fadc0a5">Network 학습 자료</mention>　·　{{page:학습자료}}　·　{{page:개념 찾아보기}}　·　{{page:실습 찾아보기}}

## 핵심 정리

LAN 통신에서 ARP·MAC·라우팅 테이블의 역할을 설명하고, VLAN·트렁크·Router-on-a-stick 구성과 확장 ACL 설정을 다룬다.

## CCNA 분류

- 1\. 네트워크 기초 / 통신과 IP 주소
- 2\. 네트워크 접속 / VLAN과 VLAN 간 연결
- 2\. 네트워크 접속 / 트렁크·802.1Q·네이티브 VLAN
- 5\. 네트워크 보안 기초 / 접근 제어와 접속 보안

## 주제별 내용

<toggle>
LAN 통신 원리와 테이블

### 테이블의 역할

ARP Table은 IP 주소와 MAC 주소의 변환 및 목적지 IP에 대응하는 MAC 주소 확인에 사용된다. MAC Table은 MAC 주소와 포트를 확인하며, Routing Table은 IP 주소와 포트를 확인하는 용도로 설명되어 있다.

<toggle>
원문 근거

```text
PC, 서버, 스위치, 라우터의 통신 원리에서 가장 많이 사용된느 기능은 Table이다.
1. ARP Table : IP<=>MAC주소 변환용 테이블
 =>PC, Router등에서 사용
 =>목적지 IP에 상응하는 MAC주소 확인용
 =>arp 또는 show arp명려으로 확인 가능
2. MAC Table : MAC<=>Port 확인용 테이블
3. Routing Table : IP<=>Port 확인용 테이블
```
</toggle>

### LAN 통신 순서

송신 시스템은 ARP Table에서 목적지 IP에 대응하는 MAC 주소를 확인하고, 없으면 브로드캐스트 MAC 주소를 목적지로 사용한다. 스위치는 MAC Table에 목적지 MAC 주소가 없으면 모든 포트로 프레임을 전송한다. 수신 시스템은 자신의 IP와 목적지 IP를 비교하며, 응답 과정에서 스위치는 출발지 MAC 주소를 학습하고 송신 시스템은 목적지 MAC 주소를 ARP Table에 저장한다.

<toggle>
원문 근거

```text
LAN통신 순서
1. 송신 시스템은 ARP Table에서 목적지 IP에 상응하는 MAC주소 확인. 없으면 브로드 캐스트(FFFFFFFFFFFF)주소를 목적지 MAC주소로 입력. 있으면 해당 MAC주소를 목적지 주소로 선택
2. 스위치는 자신의 MAC Table에서 목적지 MAC주소에 상응하는 포트 확인. 없으면 모든 포트에 프레임 전송(브로드 캐스팅)
3. 수신 시스템은 자신의 IP와 목적지 IP를 비교. 맞으면 응답. 틀리면 무시
4. 반송신호를 받은 스위치는 출발지 MAC주소를 MAC Table에 기록 후 유니 캐스팅
5. 송신 시스템은 회신 프레임을 기준으로 자신의 ARP Table에 목적지 MAC주소를 저장. 이후 동일한 목적지로 프레임 전송 시 유니 캐스팅.
```
</toggle>

<callout icon="💡">
AI 검토 의견 · 정정

라우팅 테이블은 일반적으로 목적지 네트워크와 다음 홉 또는 출구 인터페이스를 기준으로 경로를 선택합니다. IP와 포트를 직접 대응시키는 테이블이라는 표현은 부정확합니다.
</callout>
</toggle>

<toggle>
VLAN, 트렁크와 VLAN 간 라우팅 구성

### 액세스 포트와 트렁크

스위치별로 포트를 VLAN 10, 20, 30의 액세스 포트로 설정하고, 스위치 간 포트를 트렁크 모드로 설정한다. 자료에서는 트렁크가 프레임에 VLAN 태그를 붙이며, 트렁크가 동작하려면 각 스위치의 VLAN DB에 해당 VLAN 정보가 있어야 한다고 설명한다.

<toggle>
원문 근거

```text
■Inter Vlan구성
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
</toggle>

### Router-on-a-stick

라우터의 물리 인터페이스를 활성화하고 VLAN별 서브인터페이스를 생성한다. 각 서브인터페이스에 dot1q 캡슐화 VLAN 번호와 해당 VLAN의 IP 주소를 설정해 서로 다른 VLAN 간 통신이 가능하도록 한다.

<toggle>
원문 근거

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
</toggle>

### 실습 · 스위치 VLAN 및 트렁크 설정

SW1, SW2, SW3에 액세스 VLAN을 설정하고 스위치 간 인터페이스를 트렁크 모드로 설정한다. 각 스위치의 VLAN DB에 VLAN 10, 20, 30을 생성한다.

<toggle>
원문 설정 예시

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
</toggle>

### 실습 · Router-on-a-stick 설정

R1의 G0/0을 활성화하고 VLAN 10, 20, 30용 서브인터페이스에 dot1q VLAN 캡슐화와 IP 주소를 설정한다.

<toggle>
원문 설정 예시

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
```
</toggle>
</toggle>

<toggle>
확장 ACL 접근 제어

### ACL 개요와 조건

ACL은 일반적으로 L3 장비 또는 라우터에 구현되며 표준과 확장 유형으로 분류된다. 자료에서는 확장 ACL이 특정 프로토콜을 제어할 수 있다고 설명하고, VLAN 10의 웹 접근, VLAN 30의 FTP 접근, 전체의 메일 서비스 접근을 조건으로 제시한다.

<toggle>
원문 근거

```text
ACL(Access Control List)-접근통제목록
=>일반적으로  L3또는 라우터에 구현
=>표준, 확장의 2가지 유형으로 분류
=>확장은 특정 프로토콜에 대한 제어 가능

ACL조건
- Vlan 10은 Web접근 가능
- Vlan 30은 FTP접근 가능
- Mail서비스는 모두 가능
```
</toggle>

### ACL 설정과 적용

확장 ACL 100에 TCP/80, UDP/53, TCP/21 및 IP 허용·차단 규칙을 추가하고, R1의 G0/0.20 서브인터페이스에 outbound 방향으로 적용한다.

<toggle>
원문 근거

```text
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
</toggle>

### 실습 · 확장 ACL 설정

R1에서 ACL 100 규칙을 입력한 뒤 G0/0.20의 outbound 방향에 ACL을 적용한다.

<toggle>
원문 설정 예시

```text
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
</toggle>

<callout icon="💡">
AI 검토 의견 · 정정

제시된 ACL은 VLAN 10의 DNS 허용만 UDP/53으로 처리하고 TCP/53은 허용하지 않습니다. 또한 ACL은 위에서부터 순서대로 평가되므로, VLAN 30의 FTP 허용 규칙은 앞선 `deny tcp any any eq 21`에 의해 차단됩니다.
</callout>
</toggle>

## CCNA 기준 보완할 점

<callout icon="🧭">
AI가 CCNA 학습 범위와 비교해 짚은 내용입니다. 공식 자료로 확인하세요.

- **1\. 네트워크 기초 / 통신과 IP 주소**: ARP 요청은 브로드캐스트이지만, 자료의 `FFFFFFFFFFFF` 표기는 MAC 주소 구분자인 콜론이나 하이픈이 빠져 있습니다. 라우팅 테이블의 경로 선택과 목적지 네트워크·다음 홉·출구 인터페이스에 관한 설명도 다뤄지지 않습니다.
- **2\. 네트워크 접속 / VLAN과 VLAN 간 연결**: VLAN 생성 명령, 액세스 포트와 VLAN 배정의 검증, VLAN 간 라우팅의 동작 확인은 다루지 않습니다.
- **2\. 네트워크 접속 / 트렁크·802.1Q·네이티브 VLAN**: 802.1Q 태깅 방식과 네이티브 VLAN의 동작 및 설정은 다루지 않습니다. 트렁크 인터페이스에서 허용 VLAN을 지정하거나 확인하는 내용도 없습니다.
- **5\. 네트워크 보안 기초 / 접근 제어와 접속 보안**: ACL의 와일드카드 마스크, 암시적 deny, ACL 순서·방향·적용 위치의 영향과 설정 검증이 충분히 다뤄지지 않습니다. 제시된 예시는 FTP 규칙이 앞선 deny에 가려지고 DNS가 UDP만 허용되는 등 조건과 설정이 일치하지 않습니다.
</callout>

<toggle>
원본 정보

파일명　1일차_LAN구성.txt

내용 해시　6a3b013e1a8df696d37209438367329973945018c2e31f4541caefc258254acc

분석　2026-11-06T00:28:45+00:00 · gpt-6-luna
</toggle>
