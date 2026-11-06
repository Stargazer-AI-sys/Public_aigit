<mention url="https://app.notion.com/p/3fb062cd7cd180c6ab73d56d5fadc0a5">Network 학습 자료</mention>　·　{{page:학습자료}}　·　{{page:개념 찾아보기}}　·　{{page:실습 찾아보기}}

## 핵심 정리

VLAN 및 트렁크와 라우터 서브인터페이스를 설정하고, VTP·STP 및 EtherChannel 모드 설정을 연습한다.

## CCNA 분류

- 2\. 네트워크 접속 / VLAN과 VLAN 간 연결
- 2\. 네트워크 접속 / 트렁크·802.1Q·네이티브 VLAN
- 2\. 네트워크 접속 / 스패닝 트리와 루프 방지
- 2\. 네트워크 접속 / EtherChannel과 LACP
- 2\. 네트워크 접속 / VTP와 PAgP

## 주제별 내용

<toggle>
VLAN·액세스 포트와 트렁크 설정

### VLAN 생성 및 포트 할당

VLAN 10, 20, 30을 생성하고 액세스 포트를 VLAN 10과 VLAN 20에 할당한다.

<toggle>
원문 근거

```text
conf t
vlan 10
exit
vlan 20
exit
vlan 30
exit


int fa0/24
sw mo tr
int fa0/23
sw mo tr
int fa0/1
sw mo acc
sw acc vlan 10
int fa0/2
sw mo acc
sw acc vlan 20
```
</toggle>

### 트렁크 포트

Fa0/23과 Fa0/24를 트렁크 모드로 설정한다.

<toggle>
원문 근거

```text
int fa0/24
sw mo tr
int fa0/23
sw mo tr
```
</toggle>

### 네이티브 VLAN

트렁크 포트의 네이티브 VLAN을 10으로 지정하는 명령이 기록되어 있다.

<toggle>
원문 근거

```text
-------------------------------------------
int fa0/24
switchport trunk native vlan 10
int fa0/23
switchport trunk native vlan 10

int fa0/24
switchport trunk native vlan 10
```
</toggle>

### 실습 · 스위치 VLAN 및 포트 설정

VLAN을 생성하고 스위치 포트를 트렁크 또는 액세스 모드로 설정한 뒤, 액세스 포트를 VLAN 10과 20에 할당한다.

<toggle>
원문 설정 예시

```text
conf t
vlan 10
exit
vlan 20
exit
vlan 30
exit


int fa0/24
sw mo tr
int fa0/23
sw mo tr
int fa0/1
sw mo acc
sw acc vlan 10
int fa0/2
sw mo acc
sw acc vlan 20



conf t
int fa0/24
sw mo tr
int fa0/1
sw mo acc
sw acc vlan 10
int fa0/2
sw mo acc
sw acc vlan 20
```
</toggle>

### 실습 · 트렁크 네이티브 VLAN 설정

스위치의 트렁크 포트에서 네이티브 VLAN을 10으로 지정한다.

<toggle>
원문 설정 예시

```text
-------------------------------------------
int fa0/24
switchport trunk native vlan 10
int fa0/23
switchport trunk native vlan 10

int fa0/24
switchport trunk native vlan 10
```
</toggle>
</toggle>

<toggle>
라우터 서브인터페이스를 이용한 VLAN 간 라우팅

### 서브인터페이스와 802.1Q

Fa0/0을 활성화하고 Fa0/0.10, Fa0/0.20, Fa0/0.30 서브인터페이스에 802.1Q 캡슐화와 IP 주소를 설정한다. Fa0/0.10을 VLAN 10의 네이티브 서브인터페이스로 지정하는 명령도 기록되어 있다.

<toggle>
원문 근거

```text
en
conf t
int fa0/0
no sh
int fa0/0.10
encap dot1q 10
ip addr 192.168.10.254 255.255.255.0
int fa0/0.20
encap dot1q 20
ip addr 192.168.20.254 255.255.255.0
int fa0/0.30
encap dot1q 30
ip addr 192.168.30.254 255.255.255.0
```
</toggle>

### 서브인터페이스 주소

VLAN 10, 20, 30에 각각 192.168.10.254/24, 192.168.20.254/24, 192.168.30.254/24 주소를 설정한다.

<toggle>
원문 근거

```text
int fa0/0.10
encap dot1q 10
ip addr 192.168.10.254 255.255.255.0
int fa0/0.20
encap dot1q 20
ip addr 192.168.20.254 255.255.255.0
int fa0/0.30
encap dot1q 30
ip addr 192.168.30.254 255.255.255.0
```
</toggle>

### 실습 · 라우터 서브인터페이스 설정

물리 인터페이스를 활성화하고 VLAN별 서브인터페이스에 802.1Q 캡슐화 및 IP 주소를 설정한다.

<toggle>
원문 설정 예시

```text
en
conf t
int fa0/0
no sh
int fa0/0.10
encap dot1q 10
ip addr 192.168.10.254 255.255.255.0
int fa0/0.20
encap dot1q 20
ip addr 192.168.20.254 255.255.255.0
int fa0/0.30
encap dot1q 30
ip addr 192.168.30.254 255.255.255.0
```
</toggle>

<callout icon="💡">
AI 검토 의견 · 보충

Inter-VLAN 라우팅을 위해 스위치 쪽 트렁크와 라우터 서브인터페이스의 VLAN 태그 및 네이티브 VLAN 설정이 서로 일치해야 합니다.
</callout>
</toggle>

<toggle>
VTP 및 스패닝 트리

### VTP 설정 메모

VTP domain을 cisco로, password를 1234로 지정하는 설정과 VTP가 VLAN DB를 동기화한다는 메모가 있다.

<toggle>
원문 근거

```text
conf t
vtp domain cisco
vtp password [인증값 숨김]

vtp는 vlan DB 동기화
domain, password 를 지정하고 그 정보로 동기화
```
</toggle>

### Rapid PVST+와 PortFast

스위치에서 PortFast 기본 설정과 rapid-pvst 스패닝 트리 모드를 지정한다.

<toggle>
원문 근거

```text
SW1~3 공통설정

en 
conf t
spanning-tree portfast default
spanning-tree mode rapid-pvst
```
</toggle>

### 실습 · VTP 도메인·암호 설정

VTP domain과 password를 설정한다.

<toggle>
원문 설정 예시

```text
conf t
vtp domain cisco
vtp password [인증값 숨김]
```
</toggle>

### 실습 · 스패닝 트리 설정

PortFast 기본 설정과 rapid-pvst 모드를 적용한다.

<toggle>
원문 설정 예시

```text
SW1~3 공통설정

en 
conf t
spanning-tree portfast default
spanning-tree mode rapid-pvst
```
</toggle>
</toggle>

<toggle>
EtherChannel 설정 메모

### 협상 모드 기록

메모에는 LACP의 active·passive와 PAgP가 언급되어 있으며, 스위치별 EtherChannel 설정에 auto, desirable, active, passive, on 모드가 기록되어 있다.

<toggle>
원문 근거

```text
conf t
int range fa0/1 - 4
channel-group ?

lacp active passive
PAGP 
```
</toggle>

### 채널 그룹 구성

스위치 간 인터페이스 범위에 channel-group을 설정하고 트렁크 모드를 지정하는 명령이 기록되어 있다.

<toggle>
원문 근거

```text
sw1
en
conf t
int fa0/1
sw mo acc
sw acc vlan 10
int fa0/2
sw mo acc
sw acc vlan 20
int range fa0/23-24
sw mo tr
channel-group 1 mode auto
int range fa0/21-22
channel-group 2 mode active
sw mo tr



sw2
en
conf t
int fa0/1
sw mo acc
sw acc vlan 10
int fa0/2
sw mo acc
sw acc vlan 20
int range fa0/23-24
sw mo tr
channel-group 1 mode desi
int range fa0/19-20
channel-group 3 mode on
sw mo tr

sw3
en
conf t
int fa0/1
sw mo acc
sw acc vlan 10
int fa0/2
sw mo acc
sw acc vlan 20
int range fa0/21-22
sw mo tr
channel-group 2 mode passive
int range fa0/19-20
channel-group 3 mode on
sw mo tr
```
</toggle>

### 실습 · EtherChannel 채널 그룹 설정

각 스위치의 지정된 인터페이스 범위에 channel-group 모드를 설정하고 트렁크 모드를 지정한다.

<toggle>
원문 설정 예시

```text
sw1
en
conf t
int fa0/1
sw mo acc
sw acc vlan 10
int fa0/2
sw mo acc
sw acc vlan 20
int range fa0/23-24
sw mo tr
channel-group 1 mode auto
int range fa0/21-22
channel-group 2 mode active
sw mo tr



sw2
en
conf t
int fa0/1
sw mo acc
sw acc vlan 10
int fa0/2
sw mo acc
sw acc vlan 20
int range fa0/23-24
sw mo tr
channel-group 1 mode desi
int range fa0/19-20
channel-group 3 mode on
sw mo tr

sw3
en
conf t
int fa0/1
sw mo acc
sw acc vlan 10
int fa0/2
sw mo acc
sw acc vlan 20
int range fa0/21-22
sw mo tr
channel-group 2 mode passive
int range fa0/19-20
channel-group 3 mode on
sw mo tr
```
</toggle>

<callout icon="💡">
AI 검토 의견 · 정정

LACP에서 사용하는 모드는 active/passive이고, PAgP에서 사용하는 모드는 desirable/auto입니다. 따라서 서로 다른 프로토콜의 모드를 짝지어 구성할 수 없습니다.
</callout>
</toggle>

## CCNA 기준 보완할 점

<callout icon="🧭">
AI가 CCNA 학습 범위와 비교해 짚은 내용입니다. 공식 자료로 확인하세요.

- **2\. 네트워크 접속 / VLAN과 VLAN 간 연결**: VLAN 30은 생성되고 라우터 서브인터페이스도 설정되어 있지만, VLAN 30에 연결할 액세스 포트 설정은 보이지 않는다.
- **2\. 네트워크 접속 / 트렁크·802.1Q·네이티브 VLAN**: 트렁크 양 끝의 설정 일치 확인과 802.1Q 태그 처리 설명은 다루지 않는다.
- **2\. 네트워크 접속 / 스패닝 트리와 루프 방지**: 루트 브리지 선출, 포트 역할·상태, BPDU 등 루프 방지 동작에 관한 내용은 없다.
- **2\. 네트워크 접속 / EtherChannel과 LACP**: LACP와 PAgP의 협상 방식 및 호환 가능한 모드 조합에 대한 설명이 부족하다. auto/desirable은 PAgP 모드이고 active/passive는 LACP 모드이다.
- **2\. 네트워크 접속 / VTP와 PAgP**: VTP의 server/client/transparent 모드, revision number 및 동기화 조건에 관한 설명은 없다. PAgP는 이름만 언급되며 설정 모드의 의미는 설명하지 않는다.
</callout>

<toggle>
원본 정보

파일명　18일차.txt

내용 해시　475bb0dedd096ba1ba136d8a480894d332729b2fddfaca504a4eb7edae2fd18a

분석　2026-11-06T00:28:31+00:00 · gpt-6-luna
</toggle>
