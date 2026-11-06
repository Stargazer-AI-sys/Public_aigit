# Notion 전송 미리보기

로컬 계획 · 실제 전송 없음 · DB 속성/관계 바인딩 확인

충돌 시 중지 · 승인된 원본 변경은 기존 페이지 갱신

승인 자료 1건 · 게시 객체 19개

대상 페이지: Network 학습 자료
학습자료 DB: Network_Study_DB
제목 속성: 이름
연결 상태: bound · 실제 전송은 별도 명시 실행

## category · 2. 네트워크 접속



연결: {"parent": []}

## category · 트렁크·802.1Q·네이티브 VLAN



연결: {"parent": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a"]}

## category · 스패닝 트리와 루프 방지



연결: {"parent": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a"]}

## category · EtherChannel과 LACP



연결: {"parent": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a"]}

## category · VTP와 PAgP



연결: {"parent": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a"]}

## category · VLAN과 VLAN 간 연결



연결: {"parent": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a"]}

## concept · EtherChannel

18일차.txt
인터페이스 범위에 `channel-group`을 적용하는 예시가 있습니다. mode 값으로 auto, desirable의 축약형, active, passive, on이 기록되어 있고, 별도 메모에 LACP의 active/passive와 PAgP가 언급됩니다.

연결: {"materials": ["material:237276f429fc40b9f0574406f178e477a1112c7b36a256089a29c8fec9e05709"], "categories": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a", "category:70c9ff4e2bd298310e77c4f47eaed599b2324fc4a5ab503126bc1a3a3ddeac5e", "category:8b07f229bdbfbe07efeaea021de7f3aa6002c41bbf551465c1d0cede9f601f49", "category:b0df47a74e35948b183b5d02a99772a38fccf6caf9fd42ab3924fe940125b4d8", "category:ba9037c8e8322abf74eb5509e86a11acda07e2206650fc42c8fbde2660c02542", "category:be5af9f909fec8360c7949588fa38acc24a9b7e384283eb5c4e7f8d9e86390b6"]}

## concept · 라우터 서브인터페이스와 802.1Q

18일차.txt
라우터 Fa0/0의 서브인터페이스 Fa0/0.10, .20, .30에 VLAN 번호를 지정하는 `encapsulation dot1q` 설정과 각각의 IPv4 주소가 제시됩니다. 앞선 예시에는 불완전하거나 다른 형태로 적힌 `encap dot` 명령도 있습니다.

연결: {"materials": ["material:237276f429fc40b9f0574406f178e477a1112c7b36a256089a29c8fec9e05709"], "categories": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a", "category:70c9ff4e2bd298310e77c4f47eaed599b2324fc4a5ab503126bc1a3a3ddeac5e", "category:8b07f229bdbfbe07efeaea021de7f3aa6002c41bbf551465c1d0cede9f601f49", "category:b0df47a74e35948b183b5d02a99772a38fccf6caf9fd42ab3924fe940125b4d8", "category:ba9037c8e8322abf74eb5509e86a11acda07e2206650fc42c8fbde2660c02542", "category:be5af9f909fec8360c7949588fa38acc24a9b7e384283eb5c4e7f8d9e86390b6"]}

## concept · 트렁크 포트

18일차.txt
인터페이스에 `switchport mode trunk` 축약 명령을 적용하는 설정 예시가 있습니다. 일부 포트에는 native VLAN을 10으로 지정합니다.

연결: {"materials": ["material:237276f429fc40b9f0574406f178e477a1112c7b36a256089a29c8fec9e05709"], "categories": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a", "category:70c9ff4e2bd298310e77c4f47eaed599b2324fc4a5ab503126bc1a3a3ddeac5e", "category:8b07f229bdbfbe07efeaea021de7f3aa6002c41bbf551465c1d0cede9f601f49", "category:b0df47a74e35948b183b5d02a99772a38fccf6caf9fd42ab3924fe940125b4d8", "category:ba9037c8e8322abf74eb5509e86a11acda07e2206650fc42c8fbde2660c02542", "category:be5af9f909fec8360c7949588fa38acc24a9b7e384283eb5c4e7f8d9e86390b6"]}

## concept · 액세스 포트

18일차.txt
`switchport mode access`와 `switchport access vlan` 축약 명령으로 포트를 액세스 모드로 지정하고 VLAN 10 또는 20에 할당하는 설정 예시가 있습니다.

연결: {"materials": ["material:237276f429fc40b9f0574406f178e477a1112c7b36a256089a29c8fec9e05709"], "categories": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a", "category:70c9ff4e2bd298310e77c4f47eaed599b2324fc4a5ab503126bc1a3a3ddeac5e", "category:8b07f229bdbfbe07efeaea021de7f3aa6002c41bbf551465c1d0cede9f601f49", "category:b0df47a74e35948b183b5d02a99772a38fccf6caf9fd42ab3924fe940125b4d8", "category:ba9037c8e8322abf74eb5509e86a11acda07e2206650fc42c8fbde2660c02542", "category:be5af9f909fec8360c7949588fa38acc24a9b7e384283eb5c4e7f8d9e86390b6"]}

## concept · VTP

18일차.txt
VTP domain과 password를 지정하는 명령이 제시되며, 메모는 VTP를 VLAN DB 동기화로 설명합니다. ‘최대’ 뒤의 내용은 미완성입니다.

연결: {"materials": ["material:237276f429fc40b9f0574406f178e477a1112c7b36a256089a29c8fec9e05709"], "categories": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a", "category:70c9ff4e2bd298310e77c4f47eaed599b2324fc4a5ab503126bc1a3a3ddeac5e", "category:8b07f229bdbfbe07efeaea021de7f3aa6002c41bbf551465c1d0cede9f601f49", "category:b0df47a74e35948b183b5d02a99772a38fccf6caf9fd42ab3924fe940125b4d8", "category:ba9037c8e8322abf74eb5509e86a11acda07e2206650fc42c8fbde2660c02542", "category:be5af9f909fec8360c7949588fa38acc24a9b7e384283eb5c4e7f8d9e86390b6"]}

## concept · 스패닝 트리

18일차.txt
SW1~3 공통 설정 메모에 `spanning-tree portfast default`와 `spanning-tree mode rapid-pvst` 명령이 있습니다.

연결: {"materials": ["material:237276f429fc40b9f0574406f178e477a1112c7b36a256089a29c8fec9e05709"], "categories": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a", "category:70c9ff4e2bd298310e77c4f47eaed599b2324fc4a5ab503126bc1a3a3ddeac5e", "category:8b07f229bdbfbe07efeaea021de7f3aa6002c41bbf551465c1d0cede9f601f49", "category:b0df47a74e35948b183b5d02a99772a38fccf6caf9fd42ab3924fe940125b4d8", "category:ba9037c8e8322abf74eb5509e86a11acda07e2206650fc42c8fbde2660c02542", "category:be5af9f909fec8360c7949588fa38acc24a9b7e384283eb5c4e7f8d9e86390b6"]}

## concept · 네이티브 VLAN

18일차.txt
스위치 트렁크 인터페이스에 native VLAN 10을 지정하는 예시와 라우터 서브인터페이스에서 `encapsulation dot1q 10 native`를 사용하는 예시가 있습니다.

연결: {"materials": ["material:237276f429fc40b9f0574406f178e477a1112c7b36a256089a29c8fec9e05709"], "categories": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a", "category:70c9ff4e2bd298310e77c4f47eaed599b2324fc4a5ab503126bc1a3a3ddeac5e", "category:8b07f229bdbfbe07efeaea021de7f3aa6002c41bbf551465c1d0cede9f601f49", "category:b0df47a74e35948b183b5d02a99772a38fccf6caf9fd42ab3924fe940125b4d8", "category:ba9037c8e8322abf74eb5509e86a11acda07e2206650fc42c8fbde2660c02542", "category:be5af9f909fec8360c7949588fa38acc24a9b7e384283eb5c4e7f8d9e86390b6"]}

## concept · VLAN

18일차.txt
메모에서는 VLAN 10, 20, 30을 생성하고 스위치 액세스 포트를 VLAN 10 또는 20에 할당하는 명령을 제시합니다.

연결: {"materials": ["material:237276f429fc40b9f0574406f178e477a1112c7b36a256089a29c8fec9e05709"], "categories": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a", "category:70c9ff4e2bd298310e77c4f47eaed599b2324fc4a5ab503126bc1a3a3ddeac5e", "category:8b07f229bdbfbe07efeaea021de7f3aa6002c41bbf551465c1d0cede9f601f49", "category:b0df47a74e35948b183b5d02a99772a38fccf6caf9fd42ab3924fe940125b4d8", "category:ba9037c8e8322abf74eb5509e86a11acda07e2206650fc42c8fbde2660c02542", "category:be5af9f909fec8360c7949588fa38acc24a9b7e384283eb5c4e7f8d9e86390b6"]}

## material · 18일차.txt

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
domain, password 를 지정하고 그 정보로 동기화
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
domain, password 를 지정하고 그 정보로 동기화
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

코멘트 0개 · 검토 대기 후보 미확인 · 보조 항목 제외 사유 미확인

원본 JSON은 별도로 보존합니다. 표시본의 인증값 숨김은 원문 인용 수정이 아닙니다.


연결: {"categories": ["category:56060c1c6b6e24d1e16cd68e6fca1e0a1a4fd8ffd662ec22dc4ad331db568d1a", "category:70c9ff4e2bd298310e77c4f47eaed599b2324fc4a5ab503126bc1a3a3ddeac5e", "category:8b07f229bdbfbe07efeaea021de7f3aa6002c41bbf551465c1d0cede9f601f49", "category:b0df47a74e35948b183b5d02a99772a38fccf6caf9fd42ab3924fe940125b4d8", "category:ba9037c8e8322abf74eb5509e86a11acda07e2206650fc42c8fbde2660c02542", "category:be5af9f909fec8360c7949588fa38acc24a9b7e384283eb5c4e7f8d9e86390b6"], "concepts": ["concept:4dd5b8546ee6f1137e012f6a1ed2fd3a9e65382636d1298ea2e0c1e1fad91a23", "concept:98a0f0acedbcd73fccc92b2f549db005c010a95ac9d806abd080cd543241e931", "concept:a16551bcd5719207b36ed84613a9056d09ebdf6a405e82237ecd71777d6756c1", "concept:a57ee0d5b8f37ff2a2ebf9c598ed0a7ffc1e6858c1f1bbacc668ec7fcfc84988", "concept:c79f24b68e87b2627917fdab34c647530ca3d27011d42d1af0a0fcdaf95ba6d6", "concept:c9c4bfafa58580dba499fef14c83801babbf441de05681226ce71fb6dc6dc972", "concept:d9f9cd0c4c7ccd8106a3c1bfa7d1ba56f261ed6875789e0f3c8646f25c31a0bf", "concept:f34f1410cc6e4b5f105010c224c6f6e0d58eabd6b6531217c00ba85f5ed7be41"], "related": [], "practice": ["practice:c10b65892053b937864408601a7a2ccde354667ed8bf02f4821974fda9e282d0", "practice:7ec3137ba6eb21958f98a5bb258ac199dbeeadaf87d1f1c9e53f2f59e1a9d9dd", "practice:686709031b1f9cc3d7b91c4d836948aab24b53d25be1f8c4cb0aa64867b6681e", "practice:84e242d96f9dcb377fc6e4fcea9236b56635b9dca9f26d94444d832faddff2e9"]}

## practice · 스패닝 트리 및 액세스 포트 설정 예시

SW1~3 공통 설정으로 PortFast 기본 설정과 Rapid PVST 모드를 지정하고, Fa0/1과 Fa0/2를 각각 VLAN 10과 20의 액세스 포트로 설정하는 명령이 있습니다. 실행 결과는 기록되어 있지 않습니다.

원문 근거
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

연결: {"material": ["material:237276f429fc40b9f0574406f178e477a1112c7b36a256089a29c8fec9e05709"], "concepts": ["concept:4dd5b8546ee6f1137e012f6a1ed2fd3a9e65382636d1298ea2e0c1e1fad91a23", "concept:98a0f0acedbcd73fccc92b2f549db005c010a95ac9d806abd080cd543241e931", "concept:a16551bcd5719207b36ed84613a9056d09ebdf6a405e82237ecd71777d6756c1", "concept:a57ee0d5b8f37ff2a2ebf9c598ed0a7ffc1e6858c1f1bbacc668ec7fcfc84988", "concept:c79f24b68e87b2627917fdab34c647530ca3d27011d42d1af0a0fcdaf95ba6d6", "concept:c9c4bfafa58580dba499fef14c83801babbf441de05681226ce71fb6dc6dc972", "concept:d9f9cd0c4c7ccd8106a3c1bfa7d1ba56f261ed6875789e0f3c8646f25c31a0bf", "concept:f34f1410cc6e4b5f105010c224c6f6e0d58eabd6b6531217c00ba85f5ed7be41"]}

## practice · Native VLAN 설정 예시

스위치 Fa0/24와 Fa0/23, 또는 Fa0/24에 native VLAN 10을 지정하는 명령과 라우터 Fa0/0.10에 `encapsulation dot1q 10 native`를 지정하는 예시가 있습니다. 설정 수행 및 동작 결과는 기록되어 있지 않습니다.

원문 근거
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
domain, password 를 지정하고 그 정보로 동기화
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

연결: {"material": ["material:237276f429fc40b9f0574406f178e477a1112c7b36a256089a29c8fec9e05709"], "concepts": ["concept:4dd5b8546ee6f1137e012f6a1ed2fd3a9e65382636d1298ea2e0c1e1fad91a23", "concept:98a0f0acedbcd73fccc92b2f549db005c010a95ac9d806abd080cd543241e931", "concept:a16551bcd5719207b36ed84613a9056d09ebdf6a405e82237ecd71777d6756c1", "concept:a57ee0d5b8f37ff2a2ebf9c598ed0a7ffc1e6858c1f1bbacc668ec7fcfc84988", "concept:c79f24b68e87b2627917fdab34c647530ca3d27011d42d1af0a0fcdaf95ba6d6", "concept:c9c4bfafa58580dba499fef14c83801babbf441de05681226ce71fb6dc6dc972", "concept:d9f9cd0c4c7ccd8106a3c1bfa7d1ba56f261ed6875789e0f3c8646f25c31a0bf", "concept:f34f1410cc6e4b5f105010c224c6f6e0d58eabd6b6531217c00ba85f5ed7be41"]}

## practice · EtherChannel 설정 예시

SW1~3의 인터페이스 범위에 channel-group을 적용하며, 그룹별로 auto, desirable 축약형, active, passive 또는 on 모드를 지정하는 명령이 있습니다. 일부 포트 범위에는 트렁크 모드 명령도 포함됩니다. 장비 간 연결 성립이나 설정 성공 여부는 기록되어 있지 않습니다.

원문 근거
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

연결: {"material": ["material:237276f429fc40b9f0574406f178e477a1112c7b36a256089a29c8fec9e05709"], "concepts": ["concept:4dd5b8546ee6f1137e012f6a1ed2fd3a9e65382636d1298ea2e0c1e1fad91a23", "concept:98a0f0acedbcd73fccc92b2f549db005c010a95ac9d806abd080cd543241e931", "concept:a16551bcd5719207b36ed84613a9056d09ebdf6a405e82237ecd71777d6756c1", "concept:a57ee0d5b8f37ff2a2ebf9c598ed0a7ffc1e6858c1f1bbacc668ec7fcfc84988", "concept:c79f24b68e87b2627917fdab34c647530ca3d27011d42d1af0a0fcdaf95ba6d6", "concept:c9c4bfafa58580dba499fef14c83801babbf441de05681226ce71fb6dc6dc972", "concept:d9f9cd0c4c7ccd8106a3c1bfa7d1ba56f261ed6875789e0f3c8646f25c31a0bf", "concept:f34f1410cc6e4b5f105010c224c6f6e0d58eabd6b6531217c00ba85f5ed7be41"]}

## practice · VLAN 및 스위치 포트 설정 예시

VLAN 10, 20, 30을 생성하고 Fa0/24·Fa0/23 또는 Fa0/24를 트렁크 모드로 지정하는 명령이 있습니다. Fa0/1과 Fa0/2에는 액세스 모드 및 VLAN 10과 20을 지정합니다. 여러 장비 설정으로 보이는 명령이 포함되지만 수행 결과는 확인되지 않습니다.

원문 근거
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

연결: {"material": ["material:237276f429fc40b9f0574406f178e477a1112c7b36a256089a29c8fec9e05709"], "concepts": ["concept:4dd5b8546ee6f1137e012f6a1ed2fd3a9e65382636d1298ea2e0c1e1fad91a23", "concept:98a0f0acedbcd73fccc92b2f549db005c010a95ac9d806abd080cd543241e931", "concept:a16551bcd5719207b36ed84613a9056d09ebdf6a405e82237ecd71777d6756c1", "concept:a57ee0d5b8f37ff2a2ebf9c598ed0a7ffc1e6858c1f1bbacc668ec7fcfc84988", "concept:c79f24b68e87b2627917fdab34c647530ca3d27011d42d1af0a0fcdaf95ba6d6", "concept:c9c4bfafa58580dba499fef14c83801babbf441de05681226ce71fb6dc6dc972", "concept:d9f9cd0c4c7ccd8106a3c1bfa7d1ba56f261ed6875789e0f3c8646f25c31a0bf", "concept:f34f1410cc6e4b5f105010c224c6f6e0d58eabd6b6531217c00ba85f5ed7be41"]}
