# 18일차\.txt

Schema 0.2 · 원문 기반 분석 · 내용 검토 필요

VLAN과 스위치 포트, 라우터 서브인터페이스, native VLAN, VTP, 스패닝 트리 및 EtherChannel 설정 명령을 모은 실습 메모입니다\.

형식·연결 검사와 기술적 사실성·실습 성공 검증은 별개입니다.

## VLAN 및 스위치 포트 설정

### VLAN

메모에서는 VLAN 10, 20, 30을 생성하고 스위치 액세스 포트를 VLAN 10 또는 20에 할당하는 명령을 제시합니다\.

### 액세스 포트

\`switchport mode access\`와 \`switchport access vlan\` 축약 명령으로 포트를 액세스 모드로 지정하고 VLAN 10 또는 20에 할당하는 설정 예시가 있습니다\.

### 트렁크 포트

인터페이스에 \`switchport mode trunk\` 축약 명령을 적용하는 설정 예시가 있습니다\. 일부 포트에는 native VLAN을 10으로 지정합니다\.

### 액세스 포트 → VLAN

VLAN에 할당하는 설정이 제시됨

인터페이스에 액세스 모드를 지정한 뒤 VLAN 10 또는 20을 할당하는 명령이 이어집니다\.

### VLAN 및 스위치 포트 설정 예시

VLAN 10, 20, 30을 생성하고 Fa0/24·Fa0/23 또는 Fa0/24를 트렁크 모드로 지정하는 명령이 있습니다\. Fa0/1과 Fa0/2에는 액세스 모드 및 VLAN 10과 20을 지정합니다\. 여러 장비 설정으로 보이는 명령이 포함되지만 수행 결과는 확인되지 않습니다\.

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

## 라우터 서브인터페이스와 Native VLAN

### 라우터 서브인터페이스와 802\.1Q

라우터 Fa0/0의 서브인터페이스 Fa0/0\.10, \.20, \.30에 VLAN 번호를 지정하는 \`encapsulation dot1q\` 설정과 각각의 IPv4 주소가 제시됩니다\. 앞선 예시에는 불완전하거나 다른 형태로 적힌 \`encap dot\` 명령도 있습니다\.

### Native VLAN

스위치 트렁크 인터페이스에 native VLAN 10을 지정하는 예시와 라우터 서브인터페이스에서 \`encapsulation dot1q 10 native\`를 사용하는 예시가 있습니다\.

### VLAN별 라우터 서브인터페이스 설정 예시

Fa0/0을 활성화하고 Fa0/0\.10, \.20, \.30 서브인터페이스에 각각 \`encapsulation dot1q\` VLAN 번호 10, 20, 30과 192\.168\.10\.254/24, 192\.168\.20\.254/24, 192\.168\.30\.254/24 주소를 지정하는 명령이 있습니다\. 이는 설정 예시이며 실행 결과는 기록되어 있지 않습니다\.

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
```

### Native VLAN 설정 예시

스위치 Fa0/24와 Fa0/23, 또는 Fa0/24에 native VLAN 10을 지정하는 명령과 라우터 Fa0/0\.10에 \`encapsulation dot1q 10 native\`를 지정하는 예시가 있습니다\. 설정 수행 및 동작 결과는 기록되어 있지 않습니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
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

## VTP 메모

### VTP

VTP domain과 password를 지정하는 명령이 제시되며, 메모는 VTP를 VLAN DB 동기화로 설명합니다\. ‘최대’ 뒤의 내용은 미완성입니다\.

### VTP에 관한 메모

자료에서는 VTP를 VLAN DB 동기화라고 설명하고, domain과 password를 지정해 그 정보로 동기화한다고 적습니다\. ‘최대’ 뒤의 메모는 완성되지 않았습니다\.

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

### 스패닝 트리 설정

SW1\~3 공통 설정 메모에 \`spanning\-tree portfast default\`와 \`spanning\-tree mode rapid\-pvst\` 명령이 있습니다\.

### 스패닝 트리 및 액세스 포트 설정 예시

SW1\~3 공통 설정으로 PortFast 기본 설정과 Rapid PVST 모드를 지정하고, Fa0/1과 Fa0/2를 각각 VLAN 10과 20의 액세스 포트로 설정하는 명령이 있습니다\. 실행 결과는 기록되어 있지 않습니다\.

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

인터페이스 범위에 \`channel\-group\`을 적용하는 예시가 있습니다\. mode 값으로 auto, desirable의 축약형, active, passive, on이 기록되어 있고, 별도 메모에 LACP의 active/passive와 PAgP가 언급됩니다\.

### EtherChannel 설정 예시

SW1\~3의 인터페이스 범위에 channel\-group을 적용하며, 그룹별로 auto, desirable 축약형, active, passive 또는 on 모드를 지정하는 명령이 있습니다\. 일부 포트 범위에는 트렁크 모드 명령도 포함됩니다\. 장비 간 연결 성립이나 설정 성공 여부는 기록되어 있지 않습니다\.

원문 인용 · 표시본의 인증값은 숨김

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

---

코멘트 0개 · 검토 대기 후보 0개 · 보조 항목 제외 사유 0개

원본 JSON은 별도로 보존합니다. 표시본의 인증값 숨김은 원문 인용 수정이 아닙니다.
