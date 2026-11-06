# 18일차\.txt

Schema 0.2 · 원문 기반 분석 · 내용 검토 필요

VLAN과 트렁크, 라우터 서브인터페이스, VTP, 스패닝 트리 및 EtherChannel의 설정 명령 예시를 모은 자료입니다\.

형식·연결 검사와 기술적 사실성·실습 성공 검증은 별개입니다.

## VLAN 및 트렁크 설정

### VLAN

자료에는 VLAN 10, 20, 30 생성과 액세스 포트에 VLAN을 지정하는 명령 예시가 있다\.

### 액세스 포트

자료에는 인터페이스를 액세스 모드로 설정하고 VLAN 10 또는 VLAN 20을 지정하는 명령 예시가 있다\.

### 트렁크 포트

자료에는 스위치 인터페이스를 트렁크 모드로 설정하는 명령 예시가 있다\.

### 네이티브 VLAN

자료에는 스위치 트렁크의 네이티브 VLAN을 VLAN 10으로 지정하고, 라우터 서브인터페이스에서 VLAN 10을 native로 지정하는 명령 예시가 있다\.

### VLAN, 액세스 포트 및 트렁크 설정 예시

스위치에서 VLAN 10, 20, 30을 생성하고 일부 인터페이스를 트렁크로, Fa0/1과 Fa0/2를 각각 VLAN 10과 VLAN 20의 액세스 포트로 설정하는 명령 예시다\. 설정 결과는 기록되어 있지 않다\.

원문 인용 · 표시본의 인증값은 숨김

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

## 라우터 서브인터페이스와 802\.1Q

### 라우터 서브인터페이스

자료에는 Fa0/0의 서브인터페이스를 만들고 각 서브인터페이스에 캡슐화와 IP 주소를 지정하는 명령 예시가 있다\.

### 802\.1Q

자료에는 라우터 서브인터페이스에서 VLAN 번호를 지정하는 dot1q 캡슐화 명령 예시가 있다\.

### 라우터 서브인터페이스 및 네이티브 VLAN 설정 예시

Fa0/0을 활성화하고 VLAN 10, 20, 30에 대응하는 서브인터페이스에 dot1q 캡슐화와 IP 주소를 지정하는 예시가 있다\. 별도 구간에는 스위치 트렁크의 네이티브 VLAN을 10으로 지정하고 라우터 서브인터페이스에 native를 지정하는 명령이 있다\. 설정 결과는 기록되어 있지 않다\.

원문 인용 · 표시본의 인증값은 숨김

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

-------------------------------------------
int fa0/24
switchport trunk native vlan 10
int fa0/23
switchport trunk native vlan 10

int fa0/24
switchport trunk native vlan 10

-------------------------------------

conf t
vtp domain cisco
vtp password [인증값 숨김]

vtp는 vlan DB 동기화
domain, password [인증값 숨김]
최대 

sw1
int range fa0/23 - 24
sw tr nati vlan 10

sw
int fa0/23
sw tr nati vlan 10

r1
conf t
int fa0/0.10
encap dot1q 10 native
```

### 라우터 서브인터페이스 → 802\.1Q

VLAN 번호를 지정하는 캡슐화를 설정한다

서브인터페이스 설정 예시에 dot1q와 VLAN 번호가 함께 나타난다\.

## VTP

### VTP

자료는 VTP를 VLAN DB 동기화로 설명하고 도메인과 비밀번호를 지정하는 명령 예시를 제시한다\.

### VTP → VLAN

자료에서 VLAN DB를 동기화한다고 설명한다

자료는 도메인과 비밀번호를 지정하고 그 정보로 동기화한다고 적고 있다\.

### VTP

자료에서는 VTP를 VLAN DB 동기화로 설명하며, 도메인과 비밀번호를 지정하고 그 정보로 동기화한다고 적는다\. 이어지는 '최대' 메모는 값이나 설명이 완성되어 있지 않다\.

원문 인용 · 표시본의 인증값은 숨김

```text
conf t
vtp domain cisco
vtp password [인증값 숨김]

vtp는 vlan DB 동기화
domain, password [인증값 숨김]
최대 
```

### VTP 도메인 및 비밀번호 설정 예시

VTP 도메인을 cisco로 지정하고 비밀번호를 설정하는 명령 예시가 있다\. 동기화 결과는 기록되어 있지 않으며, '최대'라는 메모는 미완성이다\.

원문 인용 · 표시본의 인증값은 숨김

```text
conf t
vtp domain cisco
vtp password [인증값 숨김]

vtp는 vlan DB 동기화
domain, password [인증값 숨김]
최대 
```

## 스패닝 트리 설정

### 스패닝 트리

자료에는 spanning\-tree 설정 명령과 Rapid PVST 모드 지정 예시가 있다\.

### PortFast

자료에는 spanning\-tree portfast default 명령 예시가 있다\.

### Rapid PVST\+

자료에는 spanning\-tree mode rapid\-pvst 명령 예시가 있다\.

### 스패닝 트리 및 액세스 포트 설정 예시

SW1\~3 공통 설정으로 PortFast 기본 설정과 Rapid PVST 모드 지정 명령을 제시하고, 이어 액세스 포트의 VLAN을 지정하는 예시가 있다\. 실행 결과는 기록되어 있지 않다\.

원문 인용 · 표시본의 인증값은 숨김

```text
SW1~3 공통설정

en 
conf t
spanning-tree portfast default
spanning-tree mode rapid-pvst

int fa0/1
sw mo acc
sw acc vlan 10
int fa0/2
sw mo acc
sw acc vlan 20
```

## EtherChannel 설정

### EtherChannel

자료에는 여러 인터페이스에 channel\-group 명령을 적용하는 설정 예시가 있다\.

### LACP

자료에는 LACP의 active와 passive 모드가 언급되고, 인터페이스 채널 그룹에 active 또는 passive를 지정하는 예시가 있다\.

### PAgP

자료에는 PAgP라는 명칭과 channel\-group 설정 예시의 auto 및 desirable 모드가 나타난다\.

### 정적 EtherChannel

자료에는 channel\-group 설정에 mode on을 사용하는 명령 예시가 있다\.

### EtherChannel 모드 설정 예시

인터페이스 범위에 channel\-group 명령을 적용하는 예시와 SW1\~3의 채널 그룹 설정이 있다\. mode auto, active, passive, desirable, on이 기재되어 있으며, 채널 형성 여부나 결과는 기록되어 있지 않다\.

원문 인용 · 표시본의 인증값은 숨김

```text
conf t
int range fa0/1 - 4
channel-group ?

lacp active passive
PAGP 


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
```

---

코멘트 0개 · 검토 대기 후보 미확인 · 보조 항목 제외 사유 미확인

원본 JSON은 별도로 보존합니다. 표시본의 인증값 숨김은 원문 인용 수정이 아닙니다.
