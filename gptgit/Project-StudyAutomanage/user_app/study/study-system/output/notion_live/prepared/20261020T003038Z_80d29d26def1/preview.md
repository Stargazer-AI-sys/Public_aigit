# Notion 전송 미리보기

로컬 계획 · 실제 전송 없음 · DB 속성/관계 바인딩 확인

충돌 시 중지 · 승인된 원본 변경은 기존 페이지 갱신

승인 자료 8건 · 게시 객체 8개

대상 페이지: Network 학습 자료
학습자료 DB: Network_Study_DB
제목 속성: 이름
연결 상태: bound · 실제 전송은 별도 명시 실행

## material · 15일차 Dynamic routing_IGP.txt

<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료 목록</mention-page>

## 핵심 정리
IGP의 라우팅 방식과 RIP의 동작, RIPv1·RIPv2의 차이를 설명하며 일부 항목은 질문이나 메모 형태로 미완성입니다.

## 분류
NETWORK / 3. IP 라우팅 / 라우팅 테이블과 경로 선택
NETWORK / 3. IP 라우팅 / 라우팅 방식과 RIP
NETWORK / 1. 네트워크 기초 / 통신과 IP 주소
NETWORK / 4. IP 서비스 / 주소·이름·시간·운영 서비스

## 주제별 내용
<details>
<summary>동적 라우팅과 IGP·EGP 분류</summary>
	### 동적 라우팅
	자료에서 IGP와 EGP를 구분하고, IGP의 라우팅 방식과 RIP를 설명하는 주제입니다.
	### IGP
	자료에서 내부 게이트웨이 프로토콜로 제시하며, Distance vector·Link state·Hybrid 유형을 설명합니다.
	### EGP
	자료에서 외부 게이트웨이 프로토콜로 제시하며, 추가 설명은 없습니다.
	### Distance vector
	자료에서 RIP와 IGRP를 예로 들고, 주기적으로 라우팅 테이블 정보를 교환하는 방식으로 설명합니다.
	### Hybrid
	자료에서 EIGRP를 예로 들며 IGRP 기반 비용 계산과 Link state 방식의 상태 모니터링·변화 업데이트를 결합한 것으로 설명합니다.
	### IGP → Distance vector
	유형으로 제시됨
	자료에서 IGP 아래에 Distance vector를 제시합니다.
	### IGP → Hybrid
	유형으로 제시됨
	자료에서 IGP 아래에 Hybrid를 제시합니다.
	### Distance vector → RIP
	예시로 포함
	자료에서 Distance vector의 예로 RIP를 제시합니다.
	### IGP
	자료에서 IGP를 내부 게이트웨이 프로토콜로 풀이합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		IGP 내부게이트웨이 프로토콜
		```
	</details>
	### EGP
	자료에서 EGP를 외부 게이트웨이 프로토콜로 풀이합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		EGP 외부 게이트웨이 프로토콜
		```
	</details>
	### Distance vector
	자료에서는 RIP와 IGRP를 Distance vector의 예로 들고, 라우팅 테이블 정보를 주기적으로 교환하는 레거시 기술로 설명합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		distance vector : RIP[Metric(계산방식?):홉수기준 MAX 15]IGRP
			=> 주기적 정보(라우팅테이블) 교환 레거시 기술
		```
	</details>
	### Hybrid
	자료에서는 EIGRP의 비용 계산이 IGRP를 기반으로 하며, 상태 모니터링과 네트워크 변화 시 업데이트는 Link state 방식을 사용한다고 설명합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		hybrid: EIGRP 
			=> 비용계산은 IGRP를 기반으로하고 상태 모니터링 및 네트워크 변화시 업데이트는 link state 방식을 사용
		```
	</details>
	<callout icon="💡">
		정정 설명
		EIGRP는 링크상태 프로토콜이 아니라 거리 벡터 기반의 DUAL을 사용하는 프로토콜이다.
	</callout>
	참고: [RFC 7868 — EIGRP architecture](https://www.rfc-editor.org/rfc/rfc7868.html)
</details>

<details>
<summary>링크상태 방식과 이웃 확인</summary>
	### Link state
	자료에서 OSPF와 IS-IS를 예로 들며, 상태 변화 시 정보를 교환하고 평상시 이웃 라우터를 모니터링하는 방식으로 설명합니다.
	### Hello packet
	자료에서 Link state 방식이 평상시 이웃 라우터를 모니터링할 때 사용하는 것으로 설명합니다.
	### IGP → Link state
	유형으로 제시됨
	자료에서 IGP 아래에 Link state를 제시합니다.
	### Link state
	자료에서는 상태 변화 시 정보를 교환하고 평상시에는 Hello packet으로 이웃 라우터를 모니터링하며, 40초 동안 응답이 없으면 테이블에서 삭제한다고 설명합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		link state OSPF[대역폭], IS-IS Metric 구성요소는 무엇인가?
			=> 상태 변화시 정보 교환, 평상시 주기적으로 이웃 라우터를 모니터링(Hello packet을 이용 40초동안 응답이 없으면 테이블 삭제)
		```
	</details>
	<callout icon="💡">
		정정 설명
		원문의 40초는 링크상태 프로토콜 공통값이 아니며, OSPF의 이웃 Down 판정은 인터페이스 Dead Interval 설정에 따른다.
	</callout>
	참고: [Cisco IOS OSPF Command Reference — ip ospf dead-interval](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/iproute_ospf/command/iro-cr-book/m_ospf-a1.html)
</details>

<details>
<summary>RIP 동작과 RIPv1·RIPv2 비교</summary>
	### RIP
	자료에서 UDP 520을 사용하고 30초 주기로 라우팅 테이블 정보를 교환하는 프로토콜로 설명합니다.
	### RIPv1
	자료에서 classful 방식으로 서브넷 범위를 보지 않고 VLSM을 지원하지 않는 RIP 버전으로 설명합니다.
	### RIPv2
	원문에 classless와 VLSM 지원이 표기되어 있으나, 서브넷 범위에 대한 문장은 미완성이다.
	### VLSM
	자료에서 가변길이 서브넷 마스크라고 풀이하며 RIPv1은 지원하지 않고 RIPv2는 지원한다고 설명합니다.
	### 라우팅 테이블 정보 교환
	자료에서 Distance vector의 주기적 정보 교환과 RIP의 30초 주기 정보 교환을 설명합니다.
	### RIP → RIPv1
	버전으로 구분됨
	### RIP → RIPv2
	버전으로 구분됨
	### RIPv1 → VLSM
	지원하지 않음
	자료에서 RIPv1은 VLSM을 지원하지 않는다고 설명합니다.
	### RIPv2 → VLSM
	지원함
	자료에서 RIPv2는 VLSM을 지원한다고 설명합니다.
	### RIP
	자료에서는 RIP가 UDP 520을 사용해 30초 주기로 라우팅 테이블 정보를 교환한다고 설명합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		RIP 
		UDP520
		30초 주기로 정보교환(라우팅 테이블 정보)
		```
	</details>
	### RIPv1 브로드캐스트
	자료에서는 RIPv1으로 설정된 라우터끼리 주기적으로 보내는 신호의 목적지 IP가 255.255.255.255인 브로드캐스트라고 관찰 내용을 서술합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		실제로 와이어샤크에서 ripv1으로 설정된 라우터끼리 신호를 주고 받을때 udp 520포트로 주기적으로 날리는 신호의 데스티네이션 ip 값은 255.255.255.255 브로드케스트 신호이다.
		```
	</details>
	### RIPv1 / RIPv2
	- 주소 지정 방식(classful/classless 표기)
	- VLSM 지원
	<details>
	<summary>원문 근거</summary>
		```text
		RIPv1
			classful => 서브넷 범위를 보지않음 서브넷 범위를 지정한 네트워크이면 쓸대없이 데이터가 가는 현상이 생길수 있다. *보통 A B C D.. 클래스만 구분함
			172.16.1.0/24 -> 172.16.0.0/16 형태로 가버리는게 v1에 대표적인 현상인데 이렇게 되면 받은 쪽에서는 테이블 길이가 길어짐
			테이블 길이가 길어지면 룩업시간이 길어짐
			VLSM 가변길이 서브넷 마스크 지원안함	
			라우트는 브로드케스트 신호를 드랍하지만 예외적으로 ripv1은 허용함 실제로 와이어샤크에서 ripv1으로 설정된 라우터끼리 신호를 주고 받을때 udp 520포트로 주기적으로 날리는 신호의 데스티네이션 ip 값은 255.255.255.255 브로드케스트 신호이다.
		RIPv2
			classless => 서브넷 범위를 
			VLSM 가변길이 서브넷 마스크 지원
		```
	</details>
</details>

<details>
<summary>별도로 적힌 명령 메모</summary>
	### no ip domain lookup
	자료에 단독으로 적힌 명령어이며 용도나 수행 절차는 설명되지 않습니다.
</details>

## 관련 실습
이 자료에 기록된 실습 예시는 없습니다.

<details>
<summary>원본 정보</summary>
	파일명　15일차 Dynamic routing_IGP.txt
	C:\\Users\\ICT\\Desktop\\Aigit\\gptgit\\Project-StudyAutomanage\\study\\sourcefile\\15일차 Dynamic routing_IGP.txt
</details>

연결: {}

## material · 18일차.txt

<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료 목록</mention-page>

## 핵심 정리
VLAN과 스위치 포트, 라우터 서브인터페이스, native VLAN, VTP, 스패닝 트리 및 EtherChannel 설정 명령을 모은 실습 메모입니다.

## 분류
NETWORK / 2. 네트워크 접속 / VLAN과 VLAN 간 연결
NETWORK / 2. 네트워크 접속 / 트렁크·802.1Q·네이티브 VLAN
NETWORK / 2. 네트워크 접속 / VTP와 PAgP
NETWORK / 2. 네트워크 접속 / 스패닝 트리와 루프 방지
NETWORK / 2. 네트워크 접속 / EtherChannel과 LACP

## 주제별 내용
<details>
<summary>VLAN 및 스위치 포트 설정</summary>
	### VLAN
	메모에서는 VLAN 10, 20, 30을 생성하고 스위치 액세스 포트를 VLAN 10 또는 20에 할당하는 명령을 제시합니다.
	### 액세스 포트
	`switchport mode access`와 `switchport access vlan` 축약 명령으로 포트를 액세스 모드로 지정하고 VLAN 10 또는 20에 할당하는 설정 예시가 있습니다.
	### 트렁크 포트
	인터페이스에 `switchport mode trunk` 축약 명령을 적용하는 설정 예시가 있습니다. 일부 포트에는 native VLAN을 10으로 지정합니다.
	### 액세스 포트 → VLAN
	VLAN에 할당하는 설정이 제시됨
	인터페이스에 액세스 모드를 지정한 뒤 VLAN 10 또는 20을 할당하는 명령이 이어집니다.
	### VLAN 및 스위치 포트 설정 예시
	VLAN 10, 20, 30을 생성하고 Fa0/24·Fa0/23 또는 Fa0/24를 트렁크 모드로 지정하는 명령이 있습니다. Fa0/1과 Fa0/2에는 액세스 모드 및 VLAN 10과 20을 지정합니다. 여러 장비 설정으로 보이는 명령이 포함되지만 수행 결과는 확인되지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
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
	</details>
</details>

<details>
<summary>라우터 서브인터페이스와 Native VLAN</summary>
	### 라우터 서브인터페이스와 802.1Q
	라우터 Fa0/0의 서브인터페이스 Fa0/0.10, .20, .30에 VLAN 번호를 지정하는 `encapsulation dot1q` 설정과 각각의 IPv4 주소가 제시됩니다. 앞선 예시에는 불완전하거나 다른 형태로 적힌 `encap dot` 명령도 있습니다.
	### Native VLAN
	스위치 트렁크 인터페이스에 native VLAN 10을 지정하는 예시와 라우터 서브인터페이스에서 `encapsulation dot1q 10 native`를 사용하는 예시가 있습니다.
	### VLAN별 라우터 서브인터페이스 설정 예시
	Fa0/0을 활성화하고 Fa0/0.10, .20, .30 서브인터페이스에 각각 `encapsulation dot1q` VLAN 번호 10, 20, 30과 192.168.10.254/24, 192.168.20.254/24, 192.168.30.254/24 주소를 지정하는 명령이 있습니다. 이는 설정 예시이며 실행 결과는 기록되어 있지 않습니다.
	<details>
	<summary>원문 근거</summary>
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
	</details>
	### Native VLAN 설정 예시
	스위치 Fa0/24와 Fa0/23, 또는 Fa0/24에 native VLAN 10을 지정하는 명령과 라우터 Fa0/0.10에 `encapsulation dot1q 10 native`를 지정하는 예시가 있습니다. 설정 수행 및 동작 결과는 기록되어 있지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
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
	</details>
</details>

<details>
<summary>VTP 메모</summary>
	### VTP
	VTP domain과 password를 지정하는 명령이 제시되며, 메모는 VTP를 VLAN DB 동기화로 설명합니다. ‘최대’ 뒤의 내용은 미완성입니다.
	### VTP에 관한 메모
	자료에서는 VTP를 VLAN DB 동기화라고 설명하고, domain과 password를 지정해 그 정보로 동기화한다고 적습니다. ‘최대’ 뒤의 메모는 완성되지 않았습니다.
	<details>
	<summary>원문 근거</summary>
		```text
		conf t
		vtp domain cisco
		vtp password [인증값 숨김]
		
		vtp는 vlan DB 동기화
		domain, password 를 지정하고 그 정보로 동기화
		최대 
		```
	</details>
</details>

<details>
<summary>스패닝 트리 설정</summary>
	### 스패닝 트리 설정
	SW1\~3 공통 설정 메모에 `spanning-tree portfast default`와 `spanning-tree mode rapid-pvst` 명령이 있습니다.
	### 스패닝 트리 및 액세스 포트 설정 예시
	SW1\~3 공통 설정으로 PortFast 기본 설정과 Rapid PVST 모드를 지정하고, Fa0/1과 Fa0/2를 각각 VLAN 10과 20의 액세스 포트로 설정하는 명령이 있습니다. 실행 결과는 기록되어 있지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
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
	</details>
</details>

<details>
<summary>EtherChannel 설정</summary>
	### EtherChannel
	인터페이스 범위에 `channel-group`을 적용하는 예시가 있습니다. mode 값으로 auto, desirable의 축약형, active, passive, on이 기록되어 있고, 별도 메모에 LACP의 active/passive와 PAgP가 언급됩니다.
	### EtherChannel 설정 예시
	SW1\~3의 인터페이스 범위에 channel-group을 적용하며, 그룹별로 auto, desirable 축약형, active, passive 또는 on 모드를 지정하는 명령이 있습니다. 일부 포트 범위에는 트렁크 모드 명령도 포함됩니다. 장비 간 연결 성립이나 설정 성공 여부는 기록되어 있지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
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
	</details>
</details>

## 관련 실습
- VLAN 및 스위치 포트 설정 예시
- Native VLAN 설정 예시
- 스패닝 트리 및 액세스 포트 설정 예시
- EtherChannel 설정 예시

<details>
<summary>원본 정보</summary>
	파일명　18일차.txt
	C:\\Users\\ICT\\Desktop\\Aigit\\gptgit\\Project-StudyAutomanage\\study\\sourcefile\\18일차.txt
</details>

연결: {}

## material · 2일차_원격접속.txt

<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료 목록</mention-page>

## 핵심 정리
Telnet 원격 접속에 관한 R2·R3 설정 명령과 방화벽·계층 관련 메모를 담고 있으며, 실행 결과는 확인되지 않습니다.

## 분류
NETWORK / 2. 네트워크 접속 / 무선 접속과 장비 관리
NETWORK / 5. 네트워크 보안 기초 / 보안 원칙과 장비·VPN 접근

## 주제별 내용
<details>
<summary>Telnet 원격 접속 설정 예시</summary>
	### Telnet
	자료는 Telnet이 TCP 23번을 사용한다고 적고, R2와 R3에서 VTY 회선 범위 및 암호 관련 명령을 입력하는 설정 예시를 제시합니다. 명령의 실행이나 원격 접속 성공 여부는 확인되지 않습니다.
	### 가상회선(VTY)
	R2에는 `line vty 0 2`, R3에는 `line vty 0 1` 설정 예시가 있습니다. 자료는 가상회선 범위와 접속 암호를 구성 항목으로 나열하지만, 설정 결과나 접속 여부는 제시하지 않습니다.
	### R2·R3 Telnet 원격 접속 설정 예시
	R2에서는 설정 모드 진입 후 특권 암호 설정 명령과 VTY 0–2 범위 및 암호 입력 예시를, R3에서는 설정 모드 진입 후 특권 암호 명령과 VTY 0–1 범위 및 암호 입력 예시를 제시합니다. 실행 여부나 원격 접속 확인 결과는 기록되어 있지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
		```text
		 R2
		conf t
		enable secret [인증값 숨김]
		line vty 0 2
		pass [인증값 숨김]
		
		R3
		conf t
		enable pass [인증값 숨김]
		line vty 0 1
		```
	</details>
</details>

<details>
<summary>방화벽 및 계층 관련 용어 메모</summary>
	### 2계층 방화벽 메모
	자료에는 '방화벽 장비'와 '2계층 방화벽'이라는 메모가 있으나, 기능이나 구성에 관한 설명은 없습니다.
	### Message·Segment·Packet·Frame 메모
	자료에 네 용어가 나열되어 있지만, 서로의 관계나 계층별 대응을 설명하지 않습니다.
</details>

## 관련 실습
- R2·R3 Telnet 원격 접속 설정 예시

<details>
<summary>원본 정보</summary>
	파일명　2일차_원격접속.txt
	C:\\Users\\ICT\\Desktop\\Aigit\\gptgit\\Project-StudyAutomanage\\study\\sourcefile\\2일차_원격접속.txt
</details>

연결: {}

## material · 20일차 경로재분배,루프백가상장비설정.txt

<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료 목록</mention-page>

## 핵심 정리
SVI를 통한 VLAN 라우팅, 루프백을 이용한 핑 테스트, RIP 정적 경로 재분배의 설정과 확인을 다룹니다.

## 분류
NETWORK / 2. 네트워크 접속 / VLAN과 VLAN 간 연결
NETWORK / 3. IP 라우팅 / 라우팅 테이블과 경로 선택
NETWORK / 1. 네트워크 기초 / 통신과 IP 주소
NETWORK / 3. IP 라우팅 / 정적·기본·플로팅 경로
NETWORK / 3. IP 라우팅 / 라우팅 방식과 RIP
NETWORK / 3. IP 라우팅 / 경로 재분배 실습
NETWORK / 2. 네트워크 접속 / 트렁크·802.1Q·네이티브 VLAN

## 주제별 내용
<details>
<summary>SVI와 트렁크 구성</summary>
	### SVI
	VLAN에 IP 주소를 설정해 L3 스위치에서 VLAN 간 라우팅에 사용하는 인터페이스입니다.
	### Inter-VLAN 라우팅
	서로 다른 VLAN 사이에서 이루어지는 라우팅이며, 자료는 SVI를 이용하는 구성을 다룹니다.
	### 트렁크 포트
	스위치 포트를 트렁크 모드로 설정하고 상태를 확인하도록 안내하는 예시다. 상태 확인 출력은 기록되어 있지 않다.
	### SVI → Inter-VLAN 라우팅
	사용하여 구성
	자료는 SVI를 이용한 Inter-VLAN 구성을 다룹니다.
	### L3 스위치의 SVI 및 트렁크 구성 확인
	스위치 포트를 VLAN에 할당하고 트렁크를 설정한 뒤, trunk 상태와 VLAN 인터페이스의 IP 및 활성화 여부를 확인하도록 안내합니다. 결과 출력은 기재되지 않았습니다.
	<details>
	<summary>원문 설정 예시</summary>
		```text
		aSw1
		conf t
		int fa1/1
		sw mode acc
		sw acc vlan 10
		int fa1/2
		sw mo acc
		sw acc vlan 20
		int fa1/15
		sw mo tr
		
		sh vlan-switch
		
		 ASW2
		conf t
		int fa1/1
		sw mode acc
		sw acc vlan 10
		int fa1/2
		sw mo acc
		sw acc vlan 20
		int range fa1/14 - 15
		sw mo tr
		
		conf t
		ip routing
		vlan 10
		int vlan 10
		ip addr 192.168.10.254 255.255.255.0
		vlan 20
		int vlan 20
		ip addr 192.168.20.254 255.255.255.0
		in fa1/14
		sw mo tr
		
		설정 후 2가지 확인
		1. sh int trunk : fa0/14포트가 trunk로 지정되어 있는지, 캡슐화 프로토콜은 무엇인지 확인
		2. sh ip int b : vlan 10, vlan 20에 할당된 IP 및 SVI 활성화 여부 확인
		```
	</details>
</details>

<details>
<summary>루프백 주소를 소스로 지정한 핑</summary>
	### 루프백 인터페이스
	자료에서 가상의 장비를 추가하는 용도로 언급하며, 핑 테스트의 소스 IP로 사용합니다.
	### 루프백 주소를 소스로 지정한 핑
	자료에서는 루프백 인터페이스를 가상 장비로 추가한 경우 확장 핑에 소스 IP를 기입해야 한다고 설명합니다. 예시 명령만 제시되어 있어 핑 성공 여부는 확인되지 않습니다.
	<details>
	<summary>원문 근거</summary>
		```text
		루프백 인터페이스로 가상의 장비를 추가했을때 핑테스트는
		R1#ping 192.168.10.1 source 192.168.30.1
		확장핑으로 소스 아이피를 기입해야된다.
		```
	</details>
	### 루프백 인터페이스를 소스로 지정한 핑 테스트
	루프백 주소를 소스 IP로 지정해 핑을 실행하는 명령 예가 있습니다. 핑 결과는 원문에 제시되지 않아 성공 여부를 확인할 수 없습니다.
	<details>
	<summary>원문 설정 예시</summary>
		```text
		R1#ping 192.168.10.1 source 192.168.30.1
		```
	</details>
	<callout icon="💡">
		정정 설명
		특정 루프백에서 출발하는 통신을 시험할 때 소스 주소를 지정하는 것이며, 루프백이 있다는 이유만으로 모든 핑에 소스 지정이 필수인 것은 아니다.
	</callout>
	참고: [Cisco — Understand the Extended Ping and Extended Traceroute Commands](https://www.cisco.com/c/en/us/support/docs/ip/routing-information-protocol-rip/13730-ext-ping-trace.html)
</details>

<details>
<summary>정적 경로의 RIP 재분배</summary>
	### 경로 재분배
	서로 다른 라우팅 프로토콜을 사용하는 네트워크 간에 경로 정보를 번역하고 공유하는 기능입니다.
	### RIP
	자료에서 경로 재분배 대상 프로토콜로 사용되며, 정적 경로를 재분배하는 설정 예가 제시됩니다.
	### 정적 경로
	자료에서는 기본 경로와 특정 네트워크 경로를 설정한 뒤 RIP로 재분배하는 대상으로 다룹니다.
	### 정적 경로 → RIP
	RIP로 재분배
	R1에서 정적 경로를 RIP로 재분배하는 설정이 제시됩니다.
	### 경로 재분배
	서로 다른 라우팅 프로토콜을 사용하는 네트워크 간에 경로 정보를 번역하고 공유하여 한쪽 프로토콜이 학습한 네트워크 정보를 다른 쪽 프로토콜로 전달하는 기능이라고 설명합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		[경로 재분배]:서로 다른 라우팅 프로토콜(예: OSPF, EIGRP, RIP, BGP 등)을 사용하는 네트워크 간에 경로 정보를 번역하고 공유하여, 한쪽 프로토콜이 학습한 네트워크 정보를 다른 쪽 프로토콜로 전달하는 기능입니다.
		```
	</details>
	### RIP 정적 경로 재분배
	자료에서는 RIP에 정적 경로를 재분배할 때 메트릭을 10으로 지정하는 설정 예를 제시합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		redistribute static metric 10 #RIP의 메트릭값을 10으로 재분배
		```
	</details>
	### 경로 재분배의 적용 구간
	자료에서는 경로 재분배를 동적 라우팅 프로토콜로 연결된 구간에서 사용하며, 정적으로 연결된 라우터 간에는 사용하지 않는다고 설명합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		***경로 재분배는 동적 라우팅 프로토콜로 연결된 구간에서 사용가능.
		-정적으로 연결된 라우터간에는 사용안함
		```
	</details>
	### RIP 정적 경로 재분배 설정 및 라우팅 테이블 확인
	R1에서 정적 경로를 RIP로 재분배하는 명령을 제시합니다. 이어서 학습되지 않은 ESW3의 라우팅 테이블에 192.168.40.0/24 경로가 표시된 관찰 기록이 있으며, 이 기록의 설정과 장비 간 연결 원인은 별도로 확정하지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
		```text
		R1
		router rip
		redistribute static metric 10 #RIP의 메트릭값을 10으로 재분배
		#redistribute connected  #직접 연결된 네트워크 재분배
		
		 설정 하면  
		
		학습이 되지 않은 ESW3
		
		R    192.168.40.0/24 [120/10] via 172.16.12.2, 00:00:21, FastEthernet1/1
		     172.16.0.0/30 is subnetted, 1 subnets
		
		라우팅 테이블에 위와 같이 나온다.
		```
	</details>
	<callout icon="💡">
		정정 설명
		정적 경로도 redistribute static으로 동적 라우팅 프로토콜에 주입할 수 있으므로 정적 경로는 재분배하지 않는다고 일반화하면 안 된다.
	</callout>
	참고: [Cisco — Configure Routing Protocol Redistribution](https://www.cisco.com/c/en/us/support/docs/ip/enhanced-interior-gateway-routing-protocol-eigrp/8606-redist.html)
</details>

## 관련 실습
- L3 스위치의 SVI 및 트렁크 구성 확인
- 루프백 인터페이스를 소스로 지정한 핑 테스트
- RIP 정적 경로 재분배 설정 및 라우팅 테이블 확인

<details>
<summary>원본 정보</summary>
	파일명　20일차 경로재분배,루프백가상장비설정.txt
	C:\\Users\\ICT\\Desktop\\Aigit\\gptgit\\Project-StudyAutomanage\\study\\sourcefile\\20일차 경로재분배,루프백가상장비설정.txt
</details>

연결: {}

## material · 12일차.docx

<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료 목록</mention-page>

## 핵심 정리
라우팅의 기본 기능과 경로 선택 기준을 복습하고, 정적·동적 라우팅 및 디폴트·플로팅 라우트 설정을 다룹니다.

## 분류
NETWORK / 1. 네트워크 기초 / 장비·구조·물리 연결
NETWORK / 3. IP 라우팅 / 라우팅 테이블과 경로 선택
NETWORK / 3. IP 라우팅 / 라우팅 방식과 RIP
NETWORK / 3. IP 라우팅 / 정적·기본·플로팅 경로
NETWORK / 1. 네트워크 기초 / 스위칭·무선·가상화 기초

## 주제별 내용
<details>
<summary>라우팅 기본 기능과 네트워크 분리</summary>
	### 라우팅
	라우팅 테이블을 기준으로 패킷을 특정 인터페이스로 출력하는 과정으로 설명됩니다.
	### 라우팅 테이블
	경로 매핑과 경로 선택에 사용되는 테이블입니다.
	### 라우터 기능
	패킷 스위칭과 경로 선택을 핵심 기능으로 제시합니다.
	### 패킷 스위칭
	자료에서는 패킷을 보낼지 말지를 결정하는 기능으로 설명합니다.
	### 경로 선택
	목적지로 향하는 경로를 선택하는 기능입니다.
	### Routed protocol 구성
	인터페이스에 IP를 설정하여 직접 연결된 네트워크를 구성하는 단계입니다.
	### Routing protocol 구성
	원격지 네트워크를 학습하기 위한 라우팅 프로토콜 구성입니다.
	### 라우팅 → 라우팅 테이블
	기준으로 삼는다
	라우팅은 라우팅 테이블을 기준으로 패킷을 특정 인터페이스로 출력하는 것으로 설명됩니다.
	### 라우터 기능 → 패킷 스위칭
	포함한다
	### 라우터 기능 → 경로 선택
	포함한다
	### 라우팅
	라우팅 테이블을 기준으로 패킷을 특정 인터페이스로 출력하는 과정으로 설명됩니다.
	<details>
	<summary>원문 근거</summary>
		```text
		라우팅이 됐다는 얘기는 라우팅 테이블 매핑을 거쳐 패킷을 특정 인터페이스로 출력
		```
	</details>
	### 물리적 분리 / 논리적 분리
	- 분리 기준
	<details>
	<summary>원문 근거</summary>
		```text
		1. 물리적 분리 : 라우터 or l3 스위치 물리적 포트를 기준으로 나뉜 네트워크
		2. 논리적 분리 : vlan으로 나뉜 네트워크
		```
	</details>
</details>

<details>
<summary>IGP·EGP와 경로 계산 방식</summary>
	### IGP
	하나의 AS 안에서 사용하는 라우팅 프로토콜 분류입니다.
	### EGP
	서로 다른 AS 사이에서 사용하는 라우팅 프로토콜 분류입니다.
	### Distance vector
	자료에서는 주기적으로 정보를 교환하는 경로 계산 방식으로 설명하며 RIP을 예로 듭니다.
	### Link state
	자료에서는 네트워크 상태가 변했을 때 정보를 교환하는 방식으로 설명하며 OSPF를 예로 듭니다.
	### Hybrid
	자료에서는 distance vector와 link state의 혼합 방식으로 설명하며 EIGRP를 예로 듭니다.
	### IGP → Distance vector
	분류로 제시한다
	자료는 IGP의 경로 계산 방식으로 distance vector를 제시합니다.
	### IGP → Link state
	분류로 제시한다
	자료는 IGP의 경로 계산 방식으로 link state를 제시합니다.
	### IGP → Hybrid
	분류로 제시한다
	### IGP / EGP
	- 적용 범위
	- 라우팅 영역
	<details>
	<summary>원문 근거</summary>
		```text
		IGP 하나의 AS에서..
		경로 계산 방식
		distance vector 주기적
		link state 네트워크 상태가 변했을때
		adveanced distance vecrtor 위에 두가지 믹싱해서 나온기술
		EGP 서로 다른 AS에서...
		```
	</details>
	### Distance vector / Link state
	- 정보 교환 시점
	<details>
	<summary>원문 근거</summary>
		```text
		distance vector 주기적
		link state 네트워크 상태가 변했을때
		```
	</details>
	<callout icon="💡">
		정정 설명
		EIGRP는 링크상태 프로토콜이 아니라 거리 벡터 기반의 DUAL을 사용하는 프로토콜이다.
	</callout>
	참고: [RFC 7868 — EIGRP architecture](https://www.rfc-editor.org/rfc/rfc7868.html)
</details>

<details>
<summary>정적 라우팅 설정</summary>
	### 정적 라우팅
	관리자가 원격지 네트워크 정보와 다음 홉 IP 또는 출력 인터페이스를 지정하는 방식입니다.
	### 정적 라우팅 설정
	ip route 명령으로 목적지 네트워크와 출력 인터페이스를 지정하는 명령 예시가 있습니다. 실행 성공 여부는 제시되지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
		```text
		ip route 192.168.2.0 255.255.255.0 s2/0
		```
	</details>
</details>

<details>
<summary>디폴트 라우트와 Stub network</summary>
	### 디폴트 라우트
	자료에서는 불특정 다수와 통신하는 경우 등에 사용하는 기본 경로 방식으로 제시합니다.
	### Stub network
	자료에서는 외부와 통하는 인터페이스가 단 1개인 네트워크로 정의합니다.
	### 정적 라우팅 → 디폴트 라우트
	사용할 수 있다
	자료는 정적 구성 방식 중 기본 방식으로 디폴트 라우트를 설명합니다.
	### Stub network → 디폴트 라우트
	디폴트 라우트와 함께 언급된다
	자료에서는 stub network에서 디폴트 라우트를 사용하는 경우를 설명합니다.
	### Stub network
	자료에서는 외부와 통하는 인터페이스가 단 1개인 네트워크라고 정의합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		stub network : 외부와 통하는 인터페이스가 단 1개인 네트워크
		```
	</details>
	### Stub network와 디폴트 라우트
	자료에서는 stub network가 모든 IP에 대해 패킷을 수신·송신한다고 설명하며 보안성이 없다고 서술합니다. 또한 인터페이스가 1개를 초과할 때 디폴트 라우트를 설정하면 패킷이 일부 소실될 수 있다고 설명합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		-> 인터페이스 1개 초과일때 위와 같이 디폴트 라우트 설정(stub network에서 설정하듯이) 해버리면 패킷이 반절 소실되는 상황이 발생할 수 있다.
		1타임아웃 2핑성공 3타임아웃 4핑성공
		stub network 는 모든 아이피에 대해 패킷을 수신 송신하므로 보안성이 없다.
		```
	</details>
	### 디폴트 라우트 설정 및 삭제
	디폴트 경로 설정과 기존 정적 경로 삭제 명령 예시가 포함되어 있습니다. 실행 결과는 제시되지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
		```text
		no ip route 192.168.2.0 255.255.255.0 Serial2/0
		no ip route 192.168.3.0 255.255.255.0 Serial2/0
		no ip route 192.168.4.0 255.255.255.128 Serial2/0
		no ip route 192.168.4.128 255.255.255.128 Serial2/0
		ip route 0.0.0.0 0.0.0.0 Serial2/0
		```
	</details>
</details>

<details>
<summary>최장 프리픽스·AD·메트릭</summary>
	### Longest prefix
	여러 경로가 적용될 때 프리픽스 길이가 긴 경로를 우선하는 기준으로 제시합니다.
	### AD
	자료에서는 같은 네트워크 정보를 둘 이상의 경로로 학습했을 때 우선 경로를 판단하는 관리 거리로 설명합니다.
	### Cost
	자료에서는 경로 선택 시 낮은 비용을 우선하는 기준으로 제시합니다.
	### AD
	자료에서는 관리 거리이며, 특정 네트워크 정보를 2개 이상 경로로 학습한 경우 우선 경로를 판단하는 기준이라고 설명합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		AD란 관리 거리를 의미하며 특정 네트워크 정보를 2개 이상 경로로 학습한 경우 우선하는 경로를 판단하는 기준으로 사용
		```
	</details>
	### 라우팅 경로 선택 순서
	자료에서는 테이블 룩업에서 프리픽스 길이를 비교하고, 이어서 AD가 낮은 경로와 cost가 낮은 경로를 우선하는 순서를 제시합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		1. 테이블 룩업(다른 서브넷 회선이 2개 이상 적용되는 IP가 둘다 통과 가능한 아이피 대역인경우 프리픽스 길이가 긴쪽을 우선함) _longest prefix
		2. AD값이 적은게 우선시함  192.168.4.0[(1)/0] via ....
		3. cost 낮은 비용을 우선시함
		```
	</details>
	<callout icon="💡">
		정정 설명
		동일 프리픽스의 경로 등록에는 AD·프로토콜별 메트릭을 고려하고, 패킷 전달 시에는 등록된 경로 중 최장 프리픽스를 선택한다.
	</callout>
	참고: [Cisco — Configure Route Selection for Routers](https://www.cisco.com/c/en/us/support/docs/ip/enhanced-interior-gateway-routing-protocol-eigrp/8651-21.html)
</details>

<details>
<summary>RIP 설정과 플로팅 라우트</summary>
	### 동적 라우팅
	라우팅 프로토콜을 사용하여 원격지 네트워크를 학습하는 방식입니다.
	### RIP
	자료에서 distance vector 방식의 라우팅 프로토콜 예로 제시되며 설정 명령도 포함됩니다.
	### Floating route
	주 경로에 장애가 발생했을 때 보조 경로가 동작하도록 AD 등을 이용해 구성하는 경로입니다.
	### 동적 라우팅 → RIP
	예시로 설정한다
	### Floating route → 정적 라우팅
	보조 경로로 사용한다
	자료의 플로팅 라우트 구성 예시는 정적 경로 명령을 사용합니다.
	### Floating route
	목적지로 갈 수 있는 잉여 회선이 있는 경우 주 경로와 보조 경로를 지정하여 주 경로 장애 시 보조 경로가 동작하도록 하는 방식으로 설명합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		플로팅 라우트는 목적지로 갈수 있는 잉여 회선이 있는 경우 주경로와 보조 경로를 지정하여 주 경로 장애 발생 시 보조경로가 동작하도록 하여 장애 내성
		```
	</details>
	### RIP 동적 라우팅 설정
	R1과 R2에서 RIP을 활성화하고 네트워크를 지정하는 명령 예시가 있습니다. 원격지 학습 결과는 제시되지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
		```text
		R1
		conf t
		router rip
		net 192.168.1.0
		net 192.168.12.0
		ip route 192.168.2.0 255.255.255.0 s2/0
		ip route 192.168.2.0 255.255.255.0 192.168.12.2
		router rip
		R2
		conf t
		router rip
		net 192.168.2.0
		net 192.168.12.0
		```
	</details>
	### 플로팅 라우트 구성
	원문에서 보조 경로로 표시한 AD 10의 정적 경로 명령 예시다. 실제로 백업이 되는지는 주 경로와의 AD 비교가 필요하며 장애 전환 결과는 기록되어 있지 않다.
	<details>
	<summary>원문 설정 예시</summary>
		```text
		ip route 192.168.2.0 255.255.255.0 s2/0 10
		```
	</details>
	<callout icon="💡">
		정정 설명
		동일 프리픽스의 기본 RIP 경로를 주 경로로 삼으려면 백업 정적 경로 AD는 120보다 커야 하므로 AD 10은 그 조건에서 백업이 아니다.
	</callout>
	참고: [Cisco — Configure Route Selection for Routers](https://www.cisco.com/c/en/us/support/docs/ip/enhanced-interior-gateway-routing-protocol-eigrp/8651-21.html)
</details>

## 관련 실습
- 정적 라우팅 설정
- 디폴트 라우트 설정 및 삭제
- RIP 동적 라우팅 설정
- 플로팅 라우트 구성

<details>
<summary>원본 정보</summary>
	파일명　12일차.docx
	C:\\Users\\ICT\\Desktop\\Aigit\\gptgit\\Project-StudyAutomanage\\study\\sourcefile\\12일차.docx
</details>

연결: {}

## material · 3일차 7계층 OSI.txt

<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료 목록</mention-page>

## 핵심 정리
OSI 7계층의 역할과 장점, 이더넷 프레임 및 IPv4 헤더 항목을 설명하며 일부 확인 방법과 별도 메모를 포함한다.

## 분류
NETWORK / 1. 네트워크 기초 / 통신과 IP 주소
NETWORK / 1. 네트워크 기초 / 스위칭·무선·가상화 기초

## 주제별 내용
<details>
<summary>OSI 7계층과 역할</summary>
	### OSI 7계층
	자료는 계층을 application, presentation, session, transport, network, datalink, physical 순서로 제시하고, 각 계층의 역할을 프로그램 실행, 표현·압축·암호화, 세션 관리, 전송 프로토콜·포트, IP 주소·경로, LAN/WAN 구분, 신호 변환 등으로 설명한다.
	### OSI 7계층과 계층별 역할
	자료는 application에서 physical까지의 7계층을 나열한다. 프로그램 실행과 표현, 세션 유지·종료, 전송 프로토콜과 포트 지정, IP 주소·경로, LAN/WAN 구분, 신호 변환을 계층별 기능으로 설명하고, 계층적 이해가 프로토콜 이해·장비 호환·장애 대응에 도움이 된다고 제시한다. 게임 실행 사례도 같은 계층 구분에 대응시킨다.
	<details>
	<summary>원문 근거</summary>
		```text
		7계층 application
		6계층 presentation
		5계층 session
		사용자 확인가능
		4계층 transport
		3계층 network
		2계층 datalink
		1계층 physical
		별도 프로그램 사용해서 확인
		
		장점 
		
		1. 개발자 및 엔지니어가 프로토콜에 대한 이해를 쉽게 할 수 있다.
		=> 개발자는 자신이 개발하는 프로그램의 계층을 미리 지정함으로써 사용될 프로토콜 종류를 개발과정에서 추가할 수 있다.
		=>엔지니어는 자신이 관리하는 장비의 계층을 확인하면 사용되는 프로토콜의 종류를 짐작할 수 있다.
		2. 사용자의 편의성 확장
		=> 제조자가 다른 장비의 호환성을 통해 장비를 더 쉽게 사용할 수 있게 됨
		3. 캡슐화 과정에 대한 이해를 쉽게 함으로써 네트워크 장애시 빠른 대처가 가능하다.
		
		7계층에 대한 이해
		1. 통신 프로그램 실행(*.exe)
		=> 프로그램 실행하는 자체가 7계층의 구현
		=> 이때 이미 사용될 TCP/UDP  의 종류와 포트번호는 결정됨
		
		2. 실행된 프로그램의 화면을 표현하기 위한 프로토콜들이 동작
		=>압축 및 암호화 기능도 함께 동작(6계층)
		
		3. 통신의 연결 유지 종료 및 통신 방향을 결정 프로세스를 관리(PID)하는 계층 (5계층)
		*tcp 3-웨이 핸드쉐이크 3-way handshake? ark  
		PID 관리 시 보안이 강화 될 수 있음 서로 다른 pid
		cmd - netstat -ao 프로세스 아이디 확인시 왜 ? 백도어 확인할때 씀(내가 모르는 프로세스를 확인할때 씀)★★
		
		ex 속도 협상 예를들어 10Mbps 100Mbps 가 pc에서 10mbps 설정되어 있고 스위치 컨피크 인터페이스에 100mbps로 고정 설정이 되어 있는 경우 통신이 되지 않는 상황도 있었다.
		요즘은 이정도는 auto로 자동협상
		
		4. 7계층에서 실행된 프로그램의 형태(신뢰TCP)/비신뢰(UDP) 포트번호 지정 (4계층)
		5. 트래픽의 출발지/목적지 주소 지정(IP). 네트워크 경로 지정(RIP ospf 등 프로토콜), IP관련 테이블 매핑(ARP) (3계층) ★★
		6. 목적지의 내 외부 구분 (와이어샤크 확인)(LAN WAN )(2계층)
		시리얼 인터페이스 경우 encap 을 통한 프로토콜 변경 지원 
		7. 모든 트래픽의 신호 변환 (1계층)
		ex 게임실행 
		1. 사용자가 실행아이콘을 더블클릭 => application
		2. 게임 실행화면에 표현되는 여러가지 포맷(파일형식) => presentation
		3. 서버와의 세션 수립,  유지, 종료 및 통신 방향 결정 (로그인?) =>  session
		4. 게임 진행에 필요한 각종 서비스 관련 포트 =>transport
		5. 게임서버와 사용자 시스템간 상호 식별 및 사용자 정보가 네트워크로 넘어갈 때 경로를 지정 =>network
		6. 게임서버가 lan에 있는지 아니면 wan에 존재하는 구분 => datalink
		7. 모든 트래픽의 출력과 신호 종류 구분(연결된 NIC의 종류 기반) => physical
		```
	</details>
</details>

<details>
<summary>이더넷 프레임 구조</summary>
	### 이더넷 프레임
	자료는 프레임의 항목으로 preamble, SFD, 목적지 MAC, 출발지 MAC, 선택적 802.1Q 태그, EtherType/type-or-length, 데이터, FCS를 열거하고 각 항목의 크기나 용도를 설명한다. 일부 설명은 원문에 제시된 내용이며 별도 검증은 제공되지 않았다.
	### 이더넷 프레임 항목
	자료는 preamble 7바이트, SFD 1바이트, 목적지 및 출발지 MAC 각 6바이트, 802.1Q 태그 4바이트, EtherType 2바이트, FCS 4바이트를 기재하고 데이터 영역을 페이로드라고 부른다. preamble과 SFD는 NIC 버퍼에 저장 후 시작되면 버린다고 서술하며, MAC 주소와 EtherType의 역할도 설명한다.
	<details>
	<summary>원문 근거</summary>
		```text
		이더넷 프레임(2계층) 구조
		preable 7바이트 101010101010...
		sfd 1바이트 10101011 시작 
		nic 버퍼에 저장 후 시작되면 버림
		
		destination MAC 6바이트 
		ex FFFF로 올경우 ARP 테이블에 없을경우 브로드케스트를 돌림
		->목적지 주소임
		
		Source MAC 6바이트 : 출발지 MAC 주소로 스위치는 이 주소를 MAC-address-table에 등록 이런 이유로 브로드 캐스트 MAC주소는 MAC table 에 학습될 수 없음
		->출발지 주소임
		
		802.1Q tag 4바이트 (vlan 태크 옵션)
		
		ethertype 2바이트 (위에 상위 계층은 어떤거다 알려주는 역활 ex ipv4 arp ipv6 )
		-type or length(2byte) : 3계층 헤더의 종류를 표시하는 영역으로 IP, ARP, ICMP, IPv6를 미리 알려주는 역활
		data => 페이로드
		
		FCS 4바이트 crc 오류 검출 => 0000을 4바이트 처리 데이터의 끝을 알림
		```
	</details>
</details>

<details>
<summary>IPv4 패킷 헤더와 MTU</summary>
	### IPv4 패킷 헤더
	자료는 IPv4 패킷의 total length, identification, fragment offset, protocol 필드를 언급한다. total length는 패킷 전체 길이로 설명하고, identification과 fragment offset은 데이터 그룹 및 조각의 순서와 관련된다고 설명한다.
	### MTU
	자료는 MTU를 장비가 보낼 수 있는 최대 길이로 설명하고, 일반적인 이더넷 통신에서 1500바이트를 사용한다고 적는다. 이 설명은 원문의 서술이며 조건이나 추가 검증은 제시되지 않았다.
	### IPv4 패킷 헤더 및 MTU 관련 필드
	자료는 total length를 패킷 전체 길이로 설명하고 이론상 최대 길이를 65536바이트로 기재한다. MTU는 장비가 보낼 수 있는 최대 길이로 설명하며, 일반적인 이더넷 통신에서 1500바이트를 사용한다고 적는다. identification, fragment offset, protocol 필드도 언급하지만, 일부 필드 설명은 원문 표현 그대로이며 추가 검증은 제공되지 않았다.
	<details>
	<summary>원문 근거</summary>
		```text
		ipv4 packet 4계층
		-header 길이 : 4bit 처리하며 IPv4 ipv6등을 구분
		-total length : 패킷의 전체 길이 표시 최대길이는 이론적으로 65536바이트의 길이가 최대 길이이나 MTU로 처리하기 때문에 일반적인 이더넷 통신은 1500바이트를 사용
		MTU 장비가 최대한 보낼수 있는 길이 커낵터 형식에 따라 다름 FDDI 
		
		indentification 16비트 데이터 그룹을 표시하기 위한거 똑같은 그룹번호를 부여하면 이게 어떤관련된 데이터인지 알수 있게 하는것
		fragment offset 13비트  MTU에서나 패킷이 한번에 보낼수 있는 용량이 한도가 있기때문에 쪼개고 거기에 붙히는 데이터인데 데이터 수신 받는 입장에서 따로따로 받게 됬을때 프레그먼트 옵셋 값을 통해서 순서를 정렬하게 된다.
		
		
		protocol 8비트
		C:\Windows\System32\drivers\etc protocol 파일에서 해당 프로토콜비트에 관한 숫자를 확인할수 있음
		```
	</details>
</details>

## 관련 실습
이 자료에 기록된 실습 예시는 없습니다.

<details>
<summary>원본 정보</summary>
	파일명　3일차 7계층 OSI.txt
	C:\\Users\\ICT\\Desktop\\Aigit\\gptgit\\Project-StudyAutomanage\\study\\sourcefile\\3일차 7계층 OSI.txt
</details>

연결: {}

## material · 2일차_라우팅테이블구성.txt

<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료 목록</mention-page>

## 핵심 정리
라우팅 테이블과 정적·동적 라우팅을 설명하고, 세 라우터의 인터페이스 및 경로 설정 예시를 제시합니다.

## 분류
NETWORK / 3. IP 라우팅 / 라우팅 테이블과 경로 선택
NETWORK / 3. IP 라우팅 / 라우팅 방식과 RIP
NETWORK / 3. IP 라우팅 / 정적·기본·플로팅 경로

## 주제별 내용
<details>
<summary>라우팅 개념과 테이블</summary>
	### 라우팅 테이블
	자료에서는 라우팅 테이블이 최적의 경로 정보만 저장하며, 가능한 나머지 정보는 Topology Database에 저장된다고 설명합니다.
	### Topology Database
	자료에서 라우팅 테이블에 저장되지 않는 가능한 나머지 경로 정보가 저장되는 곳으로 제시됩니다.
	### Packet Switching
	자료에서 라우터가 패킷을 보낼지 말지를 결정하는 기능으로 설명합니다.
	### Path Selection
	자료에서 패킷을 보내기로 했을 때 어떤 인터페이스로 보낼지 결정하는 기능으로 설명합니다.
	### 정적 라우팅
	자료에서는 관리자가 원격지 네트워크를 직접 지정하는 라우팅 방식으로 설명하고, ip route 명령으로 원격 네트워크와 마스크 및 출력 인터페이스를 지정하는 예시를 제시합니다.
	### 동적 라우팅
	자료에서는 라우터 간 정보 교환을 통해 경로를 학습하는 방식으로 설명합니다.
	### RIP
	자료에는 router rip 설정 모드에서 net 명령으로 R1, R2, R3의 네트워크를 지정하는 구성 예시가 있습니다. 실행 결과는 제시되지 않습니다.
	### 정적 라우팅 → 라우팅 테이블
	관리자가 직접 지정하는 방식이다
	자료는 정적 라우팅을 원격지 네트워크를 관리자가 직접 지정하는 방식으로 설명하고, 라우팅 테이블 확인 명령도 제시합니다.
	### 동적 라우팅 → 라우팅 테이블
	라우터 간 정보 교환을 통해 경로를 학습한다
	자료는 동적 라우팅의 경로 학습을 설명하고 라우팅 테이블을 경로 정보가 저장되는 대상으로 제시합니다.
	### RIP → 동적 라우팅
	자료에서 동적 라우팅 구성 예시로 사용된다
	R1, R2, R3에서 router rip 및 net 명령을 사용하는 예시가 제시됩니다.
	### 라우팅 테이블
	자료에서는 라우팅 테이블에 최적의 경로 정보만 저장되고, 가능한 나머지 정보는 Topology Database에 저장된다고 설명합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		■라우팅 테이블 
		- 최적의 경로 정보만을 저장
		 =>인간이 이용하는 네비게이션과 같은 개념
		-가능한 나머지 정보는 Topology Database에 저장
		```
	</details>
	### 정적 라우팅과 동적 라우팅
	자료에서는 정적 라우팅을 관리자가 원격지 네트워크를 직접 지정하는 방식으로, 동적 라우팅을 라우터 간 정보 교환으로 학습하는 방식으로 구분합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		■라우팅 프로토콜 종류
		1. Static : 원격지 네트워크를 관리자가 직접 지정
		2. Dynamic : 라우터간 정보 교환을 통해 학습
		```
	</details>
	### 라우터 핵심 기능
	자료는 Packet Switching을 패킷 전송 여부 결정으로, Path Selection을 전송 인터페이스 결정으로 설명합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		■라우터의 핵심 기능
		1. Packet Switching : 패킷을 보낼지 말지를 결정
		2. Path Selection : 보낸다면 어떤 인터페이스로 보낼지 결정
		```
	</details>
	### 정적 라우팅 / 동적 라우팅
	- 경로 지정 주체 또는 방법: 관리자가 직접 지정 / 라우터 간 정보 교환으로 학습
	<details>
	<summary>원문 근거</summary>
		```text
		■라우팅 프로토콜 종류
		1. Static : 원격지 네트워크를 관리자가 직접 지정
		2. Dynamic : 라우터간 정보 교환을 통해 학습
		```
	</details>
</details>

<details>
<summary>라우터 인터페이스 구성</summary>
	### 라우터 인터페이스 IP 설정
	R1, R2, R3의 FastEthernet 및 Serial 인터페이스에 IP 주소와 서브넷 마스크를 지정하고 no shut 또는 no sh를 입력하는 설정 예시가 있습니다.
	### 라우터 인터페이스 IP 설정
	R1에는 Fa0/0에 192.168.1.254/24, S1/0에 192.168.12.1/24를 설정합니다. R2에는 S1/1에 192.168.12.2/24, S1/2에 192.168.23.1/24, Fa0/0에 192.168.2.254/24를 설정합니다. R3에는 S1/3에 192.168.23.2/24, Fa0/0에 192.168.3.254/24를 설정합니다. 각 인터페이스에 no shut 또는 no sh를 입력하는 예시이며, 수행 결과는 확인되지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
		```text
		conf t
		int fa0/0
		ip addr 192.168.1.254 255.255.255.0
		no shut
		int s1/0
		ip addr 192.168.12.1 255.255.255.0
		no sh
		
		R2
		conf t
		int s1/1
		ip addr 192.168.12.2 255.255.255.0
		no sh
		int s1/2
		ip addr 192.168.23.1 255.255.255.0
		no sh
		int fa0/0
		ip addr 192.168.2.254 255.255.255.0
		no sh
		
		R3
		conf t
		int s1/3
		ip addr 192.168.23.2 255.255.255.0
		no sh
		int fa0/0
		ip addr 192.168.3.254 255.255.255.0
		no sh
		```
	</details>
</details>

<details>
<summary>RIP 및 정적 경로 구성</summary>
	### RIP 네트워크 지정 예시
	R1은 192.168.1.0과 192.168.12.0, R2는 192.168.2.0·192.168.12.0·192.168.23.0, R3는 192.168.23.0과 192.168.3.0을 router rip 설정에서 지정합니다. 이는 설정 예시이며 동작 결과는 제시되지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
		```text
		■Routing Protocol구성 #라우팅 프로토콜 지정
		R1
		conf t
		router rip		
		net 192.168.1.0
		net 192.168.12.0
		
		R2
		conf t
		router rip
		net 192.168.2.0
		net 192.168.12.0
		net 192.168.23.0
		
		R3
		conf t
		router rip
		net 192.168.23.0
		net 192.168.3.0
		```
	</details>
	### 정적 경로 지정 예시
	R1은 192.168.2.0/24와 192.168.3.0/24 경로를 S1/0으로, R2는 192.168.1.0/24를 S1/1로 및 192.168.3.0/24를 S1/2로, R3는 192.168.1.0/24와 192.168.2.0/24를 S1/3으로 지정하는 ip route 명령 예시를 제시합니다. R1 설정 뒤에는 라우팅 테이블 확인 명령이 있으나 출력 결과는 없습니다.
	<details>
	<summary>원문 설정 예시</summary>
		```text
		■Static Routing구성
		R1
		conf t
		ip route 192.168.2.0 255.255.255.0 s1/0
		ip route 192.168.3.0 255.255.255.0 s1/0
		do sh ip route
		
		R2
		conf t
		ip route 192.168.1.0 255.255.255.0 s1/1
		ip route 192.168.3.0 255.255.255.0 s1/2
		
		R3
		conf t
		ip route 192.168.1.0 255.255.255.0 s1/3
		ip route 192.168.2.0 255.255.255.0 s1/3
		```
	</details>
</details>

<details>
<summary>라우팅 확인 및 PC 설정</summary>
	### 라우팅 상태 확인 명령
	자료는 do sh ip int b를 전체 인터페이스 상태 확인 명령으로, do sh ip route를 라우팅 테이블 확인 명령으로 제시합니다.
	### PC IP 및 게이트웨이 설정
	PC1에 IP 주소 192.168.1.1, 마스크 255.255.255.0, 게이트웨이 192.168.1.254를 지정하는 예시가 있습니다.
	### 인터페이스·라우팅 테이블 확인 명령
	자료는 do sh ip int b로 전체 인터페이스 상태를 확인하고 do sh ip route로 라우팅 테이블을 확인하도록 안내합니다. 실제 명령 실행 결과는 제시되지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
		```text
		확인 명령어
		-do sh ip int b : 전체 인터페이스 상태 확인
		-do sh ip route : 라우팅 테이블 확인
		
		Router#show ip route
		Router(config)#
		Router(config-if)#
		```
	</details>
	### PC1 IP 및 게이트웨이 설정 예시
	PC1에 IP 주소 192.168.1.1, 서브넷 마스크 255.255.255.0, 게이트웨이 192.168.1.254를 설정하는 예시입니다. 설정 수행 결과는 제시되지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
		```text
		pc1 게이트웨이 및 ip 설정
		ip 192.168.1.1 255.255.255.0 192.168.1.254
		```
	</details>
</details>

## 관련 실습
- 라우터 인터페이스 IP 설정
- RIP 네트워크 지정 예시
- 정적 경로 지정 예시
- 인터페이스·라우팅 테이블 확인 명령
- PC1 IP 및 게이트웨이 설정 예시

<details>
<summary>원본 정보</summary>
	파일명　2일차_라우팅테이블구성.txt
	C:\\Users\\ICT\\Desktop\\Aigit\\gptgit\\Project-StudyAutomanage\\study\\sourcefile\\2일차_라우팅테이블구성.txt
</details>

연결: {}

## material · 1일차_LAN구성.txt

<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료 목록</mention-page>

## 핵심 정리
LAN 통신 원리를 소개하고 스위치 VLAN·트렁크, Router-on-a-stick, ACL 설정 예시를 제시합니다.

## 분류
NETWORK / 2. 네트워크 접속 / VLAN과 VLAN 간 연결
NETWORK / 2. 네트워크 접속 / 트렁크·802.1Q·네이티브 VLAN
NETWORK / 3. IP 라우팅 / 라우팅 테이블과 경로 선택
NETWORK / 5. 네트워크 보안 기초 / 접근 제어와 접속 보안
NETWORK / 1. 네트워크 기초 / 스위칭·무선·가상화 기초

## 주제별 내용
<details>
<summary>LAN 통신 원리와 테이블</summary>
	### ARP Table
	자료는 ARP Table을 IP와 MAC 주소의 변환용 테이블로 설명하며, PC·라우터 등에서 목적지 IP에 대응하는 MAC 주소를 확인하는 데 사용한다고 적습니다. arp 또는 show arp 명령으로 확인할 수 있다고 안내합니다.
	### MAC Table
	자료는 MAC Table을 MAC 주소와 포트를 확인하는 테이블로 소개합니다. 목적지 MAC 주소에 대응하는 포트를 스위치가 찾는 LAN 통신 순서도 함께 설명합니다.
	### Routing Table
	자료는 Routing Table을 IP와 포트를 확인하는 테이블로 소개합니다. 이 항목에 대한 추가 동작 설명이나 설정 예시는 제시하지 않습니다.
	### LAN 통신 순서
	자료에서는 송신 시스템이 목적지 IP에 대응하는 MAC 주소를 ARP Table에서 찾고, 없으면 브로드캐스트 주소를 목적지 MAC으로 사용한다고 설명합니다. 스위치는 MAC Table에서 목적지 포트를 찾으며, 없으면 모든 포트로 프레임을 전송합니다. 수신 시스템은 목적지 IP를 자신의 IP와 비교하고, 자료에 적힌 순서에서는 응답 프레임을 받은 스위치가 출발지 MAC을 MAC Table에 기록한 뒤 유니캐스트하며, 송신 시스템은 회신 프레임을 기준으로 ARP Table을 저장한다고 설명합니다.
	### ARP Table, MAC Table, Routing Table
	자료는 ARP Table을 IP와 MAC 주소 변환용, MAC Table을 MAC 주소와 포트 확인용, Routing Table을 IP와 포트 확인용 테이블로 나열합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		PC, 서버, 스위치, 라우터의 통신 원리에서 가장 많이 사용된느 기능은 Table이다.
		1. ARP Table : IP<=>MAC주소 변환용 테이블
		 =>PC, Router등에서 사용
		 =>목적지 IP에 상응하는 MAC주소 확인용
		 =>arp 또는 show arp명려으로 확인 가능
		2. MAC Table : MAC<=>Port 확인용 테이블
		3. Routing Table : IP<=>Port 확인용 테이블
		```
	</details>
	### 자료에 제시된 LAN 통신 순서
	자료에서는 송신 시스템이 목적지 IP에 대응하는 MAC 주소를 ARP Table에서 찾고, 없으면 브로드캐스트 주소를 목적지 MAC으로 사용한다고 설명합니다. 스위치는 목적지 MAC에 대응하는 포트를 찾고, 찾지 못하면 모든 포트로 전송합니다. 수신 시스템은 자신의 IP와 목적지 IP를 비교하며, 이후 응답 프레임을 받은 스위치가 출발지 MAC을 학습하고 유니캐스트한 뒤 송신 시스템이 회신 프레임을 기준으로 ARP Table을 저장한다고 서술합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		LAN통신 순서
		1. 송신 시스템은 ARP Table에서 목적지 IP에 상응하는 MAC주소 확인. 없으면 브로드 캐스트(FFFFFFFFFFFF)주소를 목적지 MAC주소로 입력. 있으면 해당 MAC주소를 목적지 주소로 선택
		2. 스위치는 자신의 MAC Table에서 목적지 MAC주소에 상응하는 포트 확인. 없으면 모든 포트에 프레임 전송(브로드 캐스팅)
		3. 수신 시스템은 자신의 IP와 목적지 IP를 비교. 맞으면 응답. 틀리면 무시
		4. 반송신호를 받은 스위치는 출발지 MAC주소를 MAC Table에 기록 후 유니 캐스팅
		5. 송신 시스템은 회신 프레임을 기준으로 자신의 ARP Table에 목적지 MAC주소를 저장. 이후 동일한 목적지로 프레임 전송 시 유니 캐스팅.
		```
	</details>
</details>

<details>
<summary>스위치 VLAN 및 트렁크 설정</summary>
	### VLAN 액세스 포트
	스위치의 지정 인터페이스 범위에 VLAN을 할당하고 access 모드로 설정하는 명령 예시가 있습니다. SW3의 Fa0/1–3은 VLAN 30, SW2의 Fa0/1–2는 VLAN 20, SW1의 Fa0/1–3은 VLAN 10으로 설정하도록 제시합니다.
	### 트렁크 포트
	자료는 트렁크 포트가 프레임에 VLAN tagging을 붙이는 기능을 갖는다고 설명합니다. SW3의 Fa0/24와 SW1·SW2의 Fa0/23–24를 trunk 모드로 설정하는 예시를 제시하고, 각 스위치의 VLAN DB에 VLAN 10, 20, 30 정보가 있어야 한다고 적습니다.
	### 트렁크 포트 → VLAN 액세스 포트
	프레임에 VLAN 태그를 붙이는 기능을 수행한다
	자료는 트렁크 포트의 태깅 기능과 별도로 각 스위치 액세스 포트의 VLAN 할당 예시를 설명합니다.
	### 트렁크 포트
	자료는 트렁크 포트가 프레임에 VLAN tagging을 붙이는 기능을 갖는다고 설명합니다.
	<details>
	<summary>원문 근거</summary>
		```text
		Step 2. 스위치에 트렁크 포트 생성
		- 트렁크 포트는 프레임에 Vlan tagging(꼬리표)를 붙이는 기능을 갖는다.
		```
	</details>
	### 스위치별 VLAN 정보
	자료는 트렁크 기능을 위해 각 스위치의 VLAN DB에 VLAN 10, 20, 30 정보가 있어야 한다고 설명하고, SW1·SW2·SW3에 누락된 VLAN을 추가하는 명령 예시를 제시합니다.
	<details>
	<summary>원문 근거</summary>
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
	</details>
	### 스위치 액세스 포트의 VLAN 설정
	SW3 Fa0/1–3에 VLAN 30, SW2 Fa0/1–2에 VLAN 20, SW1 Fa0/1–3에 VLAN 10을 할당하고 access 모드로 설정하는 명령 예시입니다. 실행 여부나 결과는 기록되어 있지 않습니다.
	<details>
	<summary>원문 설정 예시</summary>
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
	</details>
	### 스위치 트렁크 및 VLAN DB 설정
	SW3 Fa0/24와 SW1·SW2 Fa0/23–24를 trunk 모드로 설정하고, 각 스위치에 VLAN 10, 20, 30 정보를 추가하는 명령 예시입니다. SW3에는 VLAN 표시 확인 명령도 제시되어 있으나 확인 결과는 없습니다.
	<details>
	<summary>원문 설정 예시</summary>
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
	</details>
	### VLAN
	자료는 스위치 액세스 포트를 VLAN 10·20·30에 할당하고, 각 스위치의 VLAN DB에 해당 VLAN 정보를 구성한 뒤 라우터 하위 인터페이스에 dot1q VLAN ID를 지정하는 예시를 제시합니다.
</details>

<details>
<summary>Router-on-a-stick</summary>
	### Router-on-a-stick
	R1의 G0/0을 활성화하고 G0/0.10, G0/0.20, G0/0.30 하위 인터페이스에 각각 dot1q VLAN ID 10, 20, 30과 192.168.10.254/24, 192.168.20.254/24, 192.168.30.254/24 주소를 설정하는 예시가 있습니다. 자료는 이 구성을 마친 뒤 서로 다른 VLAN 간 통신이 가능한 상태라고 설명하지만, 실행 결과는 제시하지 않습니다.
	### Router-on-a-stick → VLAN
	하위 인터페이스에 VLAN ID를 지정한다
	R1의 하위 인터페이스별 dot1q 설정에 VLAN ID 10, 20, 30이 제시되어 있습니다.
	### Router-on-a-stick 하위 인터페이스 설정
	R1의 G0/0을 활성화하고 하위 인터페이스별 dot1q VLAN ID와 IP 주소를 설정하는 명령 예시입니다. 자료는 서로 다른 VLAN 간 통신이 가능한 상태라고 서술하지만, 별도의 확인 명령이나 실행 결과는 없습니다.
	<details>
	<summary>원문 설정 예시</summary>
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
	</details>
	### VLAN
	자료는 스위치 액세스 포트를 VLAN 10·20·30에 할당하고, 각 스위치의 VLAN DB에 해당 VLAN 정보를 구성한 뒤 라우터 하위 인터페이스에 dot1q VLAN ID를 지정하는 예시를 제시합니다.
</details>

<details>
<summary>ACL 접근 제어</summary>
	### ACL
	자료는 ACL을 접근통제목록으로 소개하고 일반적으로 L3 또는 라우터에 구현하며 표준과 확장 유형으로 분류한다고 설명합니다. 확장은 특정 프로토콜을 제어할 수 있다고 적고, VLAN 10의 웹 접근·VLAN 30의 FTP 접근·메일 서비스 허용 조건에 대응하는 ACL 명령 예시를 제시합니다.
	### ACL
	자료는 ACL을 접근통제목록으로 소개하고, 일반적으로 L3 또는 라우터에 구현하며 표준과 확장의 두 유형으로 나눈다고 설명합니다. 확장은 특정 프로토콜에 대한 제어가 가능하다고 적습니다.
	<details>
	<summary>원문 근거</summary>
		```text
		ACL(Access Control List)-접근통제목록
		=>일반적으로  L3또는 라우터에 구현
		=>표준, 확장의 2가지 유형으로 분류
		=>확장은 특정 프로토콜에 대한 제어 가능
		```
	</details>
	### ACL 설정 및 인터페이스 적용
	ACL 100에 VLAN 10의 TCP 80·UDP 53 허용, TCP 80 거부, VLAN 30의 TCP 21 허용, TCP 21 거부, 나머지 IP 허용 명령을 제시하고 R1 G0/0.20에 outbound 방향으로 적용합니다. 명령 예시만 있으며 정책 동작의 확인 결과는 없습니다.
	<details>
	<summary>원문 설정 예시</summary>
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
	</details>
</details>

## 관련 실습
- 스위치 액세스 포트의 VLAN 설정
- 스위치 트렁크 및 VLAN DB 설정
- Router-on-a-stick 하위 인터페이스 설정
- ACL 설정 및 인터페이스 적용

<details>
<summary>원본 정보</summary>
	파일명　1일차_LAN구성.txt
	C:\\Users\\ICT\\Desktop\\Aigit\\gptgit\\Project-StudyAutomanage\\study\\sourcefile\\1일차_LAN구성.txt
</details>

연결: {}


# 학습 화면

## 유지 · 3fe062cd-7cd1-81bb-9c61-cdb9454abf18

자료별 핵심 정리와 주제별 설명을 읽어보세요.

## <mention-page url="https://app.notion.com/p/3fe062cd7cd1816da520f8909ffc646b">12일차.docx</mention-page>
라우팅의 기본 기능과 경로 선택 기준을 복습하고, 정적·동적 라우팅 및 디폴트·플로팅 라우트 설정을 다룹니다.
NETWORK / 1. 네트워크 기초 / 장비·구조·물리 연결
NETWORK / 3. IP 라우팅 / 라우팅 테이블과 경로 선택
NETWORK / 3. IP 라우팅 / 라우팅 방식과 RIP
NETWORK / 3. IP 라우팅 / 정적·기본·플로팅 경로
NETWORK / 1. 네트워크 기초 / 스위칭·무선·가상화 기초

## <mention-page url="https://app.notion.com/p/3fe062cd7cd181a6b38ee6d1a668909f">15일차 Dynamic routing_IGP.txt</mention-page>
IGP의 라우팅 방식과 RIP의 동작, RIPv1·RIPv2의 차이를 설명하며 일부 항목은 질문이나 메모 형태로 미완성입니다.
NETWORK / 3. IP 라우팅 / 라우팅 테이블과 경로 선택
NETWORK / 3. IP 라우팅 / 라우팅 방식과 RIP
NETWORK / 1. 네트워크 기초 / 통신과 IP 주소
NETWORK / 4. IP 서비스 / 주소·이름·시간·운영 서비스

## <mention-page url="https://app.notion.com/p/3fb062cd7cd181dc975dfeae2f1329ed">18일차.txt</mention-page>
VLAN과 스위치 포트, 라우터 서브인터페이스, native VLAN, VTP, 스패닝 트리 및 EtherChannel 설정 명령을 모은 실습 메모입니다.
NETWORK / 2. 네트워크 접속 / VLAN과 VLAN 간 연결
NETWORK / 2. 네트워크 접속 / 트렁크·802.1Q·네이티브 VLAN
NETWORK / 2. 네트워크 접속 / VTP와 PAgP
NETWORK / 2. 네트워크 접속 / 스패닝 트리와 루프 방지
NETWORK / 2. 네트워크 접속 / EtherChannel과 LACP

## <mention-page url="https://app.notion.com/p/3fe062cd7cd181b7b4d6c5741481bb32">1일차_LAN구성.txt</mention-page>
LAN 통신 원리를 소개하고 스위치 VLAN·트렁크, Router-on-a-stick, ACL 설정 예시를 제시합니다.
NETWORK / 2. 네트워크 접속 / VLAN과 VLAN 간 연결
NETWORK / 2. 네트워크 접속 / 트렁크·802.1Q·네이티브 VLAN
NETWORK / 3. IP 라우팅 / 라우팅 테이블과 경로 선택
NETWORK / 5. 네트워크 보안 기초 / 접근 제어와 접속 보안
NETWORK / 1. 네트워크 기초 / 스위칭·무선·가상화 기초

## <mention-page url="https://app.notion.com/p/3fe062cd7cd18167a9a3c20998aadab6">20일차 경로재분배,루프백가상장비설정.txt</mention-page>
SVI를 통한 VLAN 라우팅, 루프백을 이용한 핑 테스트, RIP 정적 경로 재분배의 설정과 확인을 다룹니다.
NETWORK / 2. 네트워크 접속 / VLAN과 VLAN 간 연결
NETWORK / 3. IP 라우팅 / 라우팅 테이블과 경로 선택
NETWORK / 1. 네트워크 기초 / 통신과 IP 주소
NETWORK / 3. IP 라우팅 / 정적·기본·플로팅 경로
NETWORK / 3. IP 라우팅 / 라우팅 방식과 RIP
NETWORK / 3. IP 라우팅 / 경로 재분배 실습
NETWORK / 2. 네트워크 접속 / 트렁크·802.1Q·네이티브 VLAN

## <mention-page url="https://app.notion.com/p/3fe062cd7cd18164bf3ccdc83d35128e">2일차_라우팅테이블구성.txt</mention-page>
라우팅 테이블과 정적·동적 라우팅을 설명하고, 세 라우터의 인터페이스 및 경로 설정 예시를 제시합니다.
NETWORK / 3. IP 라우팅 / 라우팅 테이블과 경로 선택
NETWORK / 3. IP 라우팅 / 라우팅 방식과 RIP
NETWORK / 3. IP 라우팅 / 정적·기본·플로팅 경로

## <mention-page url="https://app.notion.com/p/3fe062cd7cd18160adfec58bee312eb0">2일차_원격접속.txt</mention-page>
Telnet 원격 접속에 관한 R2·R3 설정 명령과 방화벽·계층 관련 메모를 담고 있으며, 실행 결과는 확인되지 않습니다.
NETWORK / 2. 네트워크 접속 / 무선 접속과 장비 관리
NETWORK / 5. 네트워크 보안 기초 / 보안 원칙과 장비·VPN 접근

## <mention-page url="https://app.notion.com/p/3fe062cd7cd181e194d8f2703c0637af">3일차 7계층 OSI.txt</mention-page>
OSI 7계층의 역할과 장점, 이더넷 프레임 및 IPv4 헤더 항목을 설명하며 일부 확인 방법과 별도 메모를 포함한다.
NETWORK / 1. 네트워크 기초 / 통신과 IP 주소
NETWORK / 1. 네트워크 기초 / 스위칭·무선·가상화 기초


## 유지 · 3fb062cd-7cd1-80c6-ab73-d56d5fadc0a5

분야에서 시작해 개념을 이해하고, 원문과 실습까지 이어서 찾아보세요.
<mention-page url="https://app.notion.com/p/3fb062cd-7cd1-80c6-ab73-d56d5fadc0a5">학습 홈</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8115-be2c-cf26275aea30">개념 찾아보기</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8147-8ea1-f99fb7ae9ef8">실습 찾아보기</mention-page>

## 학습 분야
<columns>
	<column ratio="50">
		<callout color="gray_bg">
			<page url="https://app.notion.com/p/3fe062cd7cd18139aeb6f6aecf72977b">1. 네트워크 기초</page>
			통신 원리 · 장비와 이더넷 · IP 주소와 서브넷
		</callout>
	</column>
	<column ratio="50">
		<callout color="gray_bg">
			<page url="https://app.notion.com/p/3fe062cd7cd18159af76d840845dedee">2. 네트워크 접속</page>
			VLAN · STP · EtherChannel · 무선 LAN
		</callout>
	</column>
</columns>
<columns>
	<column ratio="50">
		<callout color="gray_bg">
			<page url="https://app.notion.com/p/3fe062cd7cd181388041eb53e303c9cc">3. IP 라우팅</page>
			라우팅 기초 · 정적 라우팅 · OSPF
		</callout>
	</column>
	<column ratio="50">
		<callout color="gray_bg">
			<page url="https://app.notion.com/p/3fe062cd7cd181f694d0dfd47ea91c7d">4. IP 서비스</page>
			주소와 이름 서비스 · 장비 접속과 관리 · 운영과 모니터링
		</callout>
	</column>
</columns>
<columns>
	<column ratio="50">
		<callout color="gray_bg">
			<page url="https://app.notion.com/p/3fe062cd7cd181068d8de8a96028a03d">5. 네트워크 보안 기초</page>
			보안과 인증 · 접근 제어
		</callout>
	</column>
	<column ratio="50">
		<callout color="gray_bg">
			<page url="https://app.notion.com/p/3fe062cd7cd18195a3b6f3fe48189ad7">6. 자동화와 프로그래밍</page>
			네트워크 자동화 기초 · API와 데이터 · 자료 준비 중
		</callout>
	</column>
</columns>

## 학습자료
<table header-row="true" fit-page-width="true">
	<tr><td>자료</td><td>관련 개념</td><td>실습</td></tr>
	<tr><td><mention-page url="https://app.notion.com/p/3fe062cd7cd1816da520f8909ffc646b">12일차.docx</mention-page></td><td><mention-page url="https://app.notion.com/p/3fe062cd7cd181638620c4ce427d8691">Longest prefix</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd18147986bce9e26fa0727">동적 라우팅</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd1816a9169ddcf2a0b3a31">Routing protocol 구성</mention-page></td><td><mention-page url="https://app.notion.com/p/3fe062cd7cd1816f8441d0b15aed4e29">정적 라우팅 설정</mention-page></td></tr>
	<tr><td><mention-page url="https://app.notion.com/p/3fe062cd7cd181a6b38ee6d1a668909f">15일차 Dynamic routing_IGP.txt</mention-page></td><td><mention-page url="https://app.notion.com/p/3fe062cd7cd18147986bce9e26fa0727">동적 라우팅</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd1815e9d02ee2c03953782">RIPv1</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd18111aa83f01bd26523b7">Hybrid</mention-page></td><td>—</td></tr>
	<tr><td><mention-page url="https://app.notion.com/p/3fb062cd7cd181dc975dfeae2f1329ed">18일차.txt</mention-page></td><td><mention-page url="https://app.notion.com/p/3fb062cd7cd18105b6a8d3e0098f1b39">EtherChannel</mention-page> · <mention-page url="https://app.notion.com/p/3fb062cd7cd18110bc8ccf0eca372007">라우터 서브인터페이스와 802.1Q</mention-page> · <mention-page url="https://app.notion.com/p/3fb062cd7cd181fab722d29dad2a268a">트렁크 포트</mention-page></td><td><mention-page url="https://app.notion.com/p/3fb062cd7cd181f59646d49eec9fba28">VLAN 및 스위치 포트 설정 예시</mention-page></td></tr>
	<tr><td><mention-page url="https://app.notion.com/p/3fe062cd7cd181b7b4d6c5741481bb32">1일차_LAN구성.txt</mention-page></td><td><mention-page url="https://app.notion.com/p/3fe062cd7cd18161866fdfb5bbe87306">Router-on-a-stick</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd18179be63da3ac1aaa973">VLAN 액세스 포트</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd1818aa424e721c329fa48">ACL</mention-page></td><td><mention-page url="https://app.notion.com/p/3fe062cd7cd1815fb42de26771f3b25f">스위치 액세스 포트의 VLAN 설정</mention-page></td></tr>
	<tr><td><mention-page url="https://app.notion.com/p/3fe062cd7cd18167a9a3c20998aadab6">20일차 경로재분배,루프백가상장비설정.txt</mention-page></td><td><mention-page url="https://app.notion.com/p/3fe062cd7cd181cc9dd3d80f97142671">SVI</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd1813d88fbd9622e282c70">루프백 인터페이스</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd18123986bf67ae0990e2d">경로 재분배</mention-page></td><td><mention-page url="https://app.notion.com/p/3fe062cd7cd181ffbce4dfc4c9efcbd6">L3 스위치의 SVI 및 트렁크 구성 확인</mention-page></td></tr>
	<tr><td><mention-page url="https://app.notion.com/p/3fe062cd7cd18164bf3ccdc83d35128e">2일차_라우팅테이블구성.txt</mention-page></td><td><mention-page url="https://app.notion.com/p/3fe062cd7cd18147986bce9e26fa0727">동적 라우팅</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181cb8900f354c24967d4">Path Selection</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181c699a1f27f9936cd5e">라우터 인터페이스 IP 설정</mention-page></td><td><mention-page url="https://app.notion.com/p/3fe062cd7cd181658560eddda1e11031">라우터 인터페이스 IP 설정</mention-page></td></tr>
	<tr><td><mention-page url="https://app.notion.com/p/3fe062cd7cd18160adfec58bee312eb0">2일차_원격접속.txt</mention-page></td><td><mention-page url="https://app.notion.com/p/3fe062cd7cd18162accaf41b17ed1f28">Telnet</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd1813989d9f432b8c3c672">Message·Segment·Packet·Frame 메모</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd1812d852bf4f1668a2b56">가상회선(VTY)</mention-page></td><td><mention-page url="https://app.notion.com/p/3fe062cd7cd18157b98accd97ae2880c">R2·R3 Telnet 원격 접속 설정 예시</mention-page></td></tr>
	<tr><td><mention-page url="https://app.notion.com/p/3fe062cd7cd181e194d8f2703c0637af">3일차 7계층 OSI.txt</mention-page></td><td>IPv4 패킷 헤더 · MTU · OSI 7계층</td><td>—</td></tr>
</table>

## 개념으로 바로 찾기
<mention-page url="https://app.notion.com/p/3fb062cd7cd1810f8ffbcf0b2c5ec10a">스패닝 트리</mention-page> · <mention-page url="https://app.notion.com/p/3fb062cd7cd1815a91daeb303bd1bc73">VLAN</mention-page> · <mention-page url="https://app.notion.com/p/3fb062cd7cd181fab722d29dad2a268a">트렁크 포트</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd1810eb6e1eea9758689d9">정적 라우팅</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd18123986bf67ae0990e2d">경로 재분배</mention-page>

<details>
<summary>전체 자료 찾아보기</summary>
	<page url="https://app.notion.com/p/3fe062cd-7cd1-8115-be2c-cf26275aea30">개념 찾아보기</page>
	<page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료</page>
	<page url="https://app.notion.com/p/3fe062cd-7cd1-8147-8ea1-f99fb7ae9ef8">실습 찾아보기</page>
</details>

## 유지 · 3fe062cd-7cd1-8139-aeb6-f6aecf72977b

<mention-page url="https://app.notion.com/p/3fb062cd-7cd1-80c6-ab73-d56d5fadc0a5">학습 홈</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8115-be2c-cf26275aea30">개념 찾아보기</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8147-8ea1-f99fb7ae9ef8">실습 찾아보기</mention-page>

CCNA 기초 학습 항목

## 통신 원리
관련 내용　OSI·TCP/IP·캡슐화·TCP·UDP

관련 개념　OSI 7계층
### 학습자료
- <mention-page url="https://app.notion.com/p/3fe062cd7cd181e194d8f2703c0637af">3일차 7계층 OSI.txt</mention-page>
<details>
<summary>기존 분류의 연결 자료</summary>
	<mention-page url="https://app.notion.com/p/3fe062cd7cd18199a39dd18956f4202e">통신과 IP 주소</mention-page>
</details>

## 장비와 이더넷
관련 내용　라우터·스위치·케이블·MAC·ARP·이더넷·스위칭·토폴로지

관련 개념　<mention-page url="https://app.notion.com/p/3fe062cd7cd18114ba81c49625401cb5">ARP Table</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd1815e8368e0e425cf985c">MAC Table</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181678885da1ec34780ec">라우터 기능</mention-page> · 이더넷 프레임 · <mention-page url="https://app.notion.com/p/3fe062cd7cd18150b02cccfec8190607">패킷 스위칭</mention-page>
### 학습자료
- <mention-page url="https://app.notion.com/p/3fe062cd7cd1816da520f8909ffc646b">12일차.docx</mention-page>
- <mention-page url="https://app.notion.com/p/3fe062cd7cd181b7b4d6c5741481bb32">1일차_LAN구성.txt</mention-page>
- <mention-page url="https://app.notion.com/p/3fe062cd7cd181e194d8f2703c0637af">3일차 7계층 OSI.txt</mention-page>
관련 실습　<mention-page url="https://app.notion.com/p/3fe062cd7cd1815fb42de26771f3b25f">스위치 액세스 포트의 VLAN 설정</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181e2923ff4c82ec436f5">스위치 트렁크 및 VLAN DB 설정</mention-page>
<details>
<summary>기존 분류의 연결 자료</summary>
	<mention-page url="https://app.notion.com/p/3fe062cd7cd1812f81b0fd2036569238">장비·구조·물리 연결</mention-page>
	<mention-page url="https://app.notion.com/p/3fe062cd7cd18198be06c70646f34c02">스위칭·무선·가상화 기초</mention-page>
</details>

## IP 주소와 서브넷
관련 내용　IPv4·IPv6·IP 주소·서브넷·VLSM·루프백

관련 개념　IPv4 패킷 헤더 · <mention-page url="https://app.notion.com/p/3fe062cd7cd181ab86c5f18eb9c563b1">VLSM</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd1813d88fbd9622e282c70">루프백 인터페이스</mention-page>
### 학습자료
- <mention-page url="https://app.notion.com/p/3fe062cd7cd181a6b38ee6d1a668909f">15일차 Dynamic routing_IGP.txt</mention-page>
- <mention-page url="https://app.notion.com/p/3fe062cd7cd18167a9a3c20998aadab6">20일차 경로재분배,루프백가상장비설정.txt</mention-page>
- <mention-page url="https://app.notion.com/p/3fe062cd7cd181e194d8f2703c0637af">3일차 7계층 OSI.txt</mention-page>
관련 실습　<mention-page url="https://app.notion.com/p/3fe062cd7cd18185b1b5e1a209f134cb">루프백 인터페이스를 소스로 지정한 핑 테스트</mention-page>
<details>
<summary>기존 분류의 연결 자료</summary>
	<mention-page url="https://app.notion.com/p/3fe062cd7cd18199a39dd18956f4202e">통신과 IP 주소</mention-page>
</details>


## 유지 · 3fe062cd-7cd1-8159-af76-d840845dedee

<mention-page url="https://app.notion.com/p/3fb062cd-7cd1-80c6-ab73-d56d5fadc0a5">학습 홈</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8115-be2c-cf26275aea30">개념 찾아보기</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8147-8ea1-f99fb7ae9ef8">실습 찾아보기</mention-page>

CCNA 기초 학습 항목

## VLAN
관련 내용　VLAN·트렁크·802.1Q·네이티브 VLAN·SVI

관련 개념　<mention-page url="https://app.notion.com/p/3fe062cd7cd18144a2d1cab8448bac1d">Inter-VLAN 라우팅</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181cc9dd3d80f97142671">SVI</mention-page> · <mention-page url="https://app.notion.com/p/3fb062cd7cd1815a91daeb303bd1bc73">VLAN</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd18179be63da3ac1aaa973">VLAN 액세스 포트</mention-page> · <mention-page url="https://app.notion.com/p/3fb062cd7cd181b6bb07f469156bcc06">네이티브 VLAN</mention-page> · <mention-page url="https://app.notion.com/p/3fb062cd7cd18110bc8ccf0eca372007">라우터 서브인터페이스와 802.1Q</mention-page> · <mention-page url="https://app.notion.com/p/3fb062cd7cd181fab722d29dad2a268a">트렁크 포트</mention-page>
### 학습자료
- <mention-page url="https://app.notion.com/p/3fb062cd7cd181dc975dfeae2f1329ed">18일차.txt</mention-page>
- <mention-page url="https://app.notion.com/p/3fe062cd7cd181b7b4d6c5741481bb32">1일차_LAN구성.txt</mention-page>
- <mention-page url="https://app.notion.com/p/3fe062cd7cd18167a9a3c20998aadab6">20일차 경로재분배,루프백가상장비설정.txt</mention-page>
관련 실습　<mention-page url="https://app.notion.com/p/3fb062cd7cd181f59646d49eec9fba28">VLAN 및 스위치 포트 설정 예시</mention-page> · <mention-page url="https://app.notion.com/p/3fb062cd7cd181368bc4d9b49473bbe0">Native VLAN 설정 예시</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd1815fb42de26771f3b25f">스위치 액세스 포트의 VLAN 설정</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181e2923ff4c82ec436f5">스위치 트렁크 및 VLAN DB 설정</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181c79541c97b7b2d084d">Router-on-a-stick 하위 인터페이스 설정</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181ffbce4dfc4c9efcbd6">L3 스위치의 SVI 및 트렁크 구성 확인</mention-page>
<details>
<summary>기존 분류의 연결 자료</summary>
	<mention-page url="https://app.notion.com/p/3fb062cd7cd181a4bae1facd451c29df">트렁크·802.1Q·네이티브 VLAN</mention-page>
	<mention-page url="https://app.notion.com/p/3fb062cd7cd1813893aec7728bc089d2">VTP와 PAgP</mention-page>
	<mention-page url="https://app.notion.com/p/3fb062cd7cd18190b506daf025b73904">VLAN과 VLAN 간 연결</mention-page>
</details>

## STP
관련 내용　STP·스패닝 트리·루트 브리지·PortFast·BPDU

관련 개념　<mention-page url="https://app.notion.com/p/3fb062cd7cd1810f8ffbcf0b2c5ec10a">스패닝 트리</mention-page>
### 학습자료
- <mention-page url="https://app.notion.com/p/3fb062cd7cd181dc975dfeae2f1329ed">18일차.txt</mention-page>
관련 실습　<mention-page url="https://app.notion.com/p/3fb062cd7cd1813f9a1de50f82548485">스패닝 트리 및 액세스 포트 설정 예시</mention-page>
<details>
<summary>기존 분류의 연결 자료</summary>
	<mention-page url="https://app.notion.com/p/3fb062cd7cd18158a03dc841a0e84772">스패닝 트리와 루프 방지</mention-page>
</details>

## EtherChannel
관련 내용　EtherChannel·LACP·링크 묶음

관련 개념　<mention-page url="https://app.notion.com/p/3fb062cd7cd18105b6a8d3e0098f1b39">EtherChannel</mention-page>
### 학습자료
- <mention-page url="https://app.notion.com/p/3fb062cd7cd181dc975dfeae2f1329ed">18일차.txt</mention-page>
관련 실습　<mention-page url="https://app.notion.com/p/3fb062cd7cd1814ba7bdfad721b3f614">EtherChannel 설정 예시</mention-page>
<details>
<summary>기존 분류의 연결 자료</summary>
	<mention-page url="https://app.notion.com/p/3fb062cd7cd1813f8ed1ffa08313b07f">EtherChannel과 LACP</mention-page>
	<mention-page url="https://app.notion.com/p/3fb062cd7cd1813893aec7728bc089d2">VTP와 PAgP</mention-page>
</details>

## 무선 LAN
관련 내용　AP·WLC·WLAN·SSID·무선·WPA

학습자료 준비 중


## 유지 · 3fe062cd-7cd1-8138-8041-eb53e303c9cc

<mention-page url="https://app.notion.com/p/3fb062cd-7cd1-80c6-ab73-d56d5fadc0a5">학습 홈</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8115-be2c-cf26275aea30">개념 찾아보기</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8147-8ea1-f99fb7ae9ef8">실습 찾아보기</mention-page>

CCNA 기초 학습 항목

## 라우팅 기초
관련 내용　라우팅 테이블·경로 선택·AD·메트릭·FHRP

관련 개념　<mention-page url="https://app.notion.com/p/3fe062cd7cd1811aa0f6fde791d5b90f">AD</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd1813695bcd93d10b60db4">경로 선택</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181de920bc1284d7196c3">라우팅 테이블</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd18125918df963d2803d68">라우팅 테이블 정보 교환</mention-page>
### 학습자료
- <mention-page url="https://app.notion.com/p/3fe062cd7cd1816da520f8909ffc646b">12일차.docx</mention-page>
- <mention-page url="https://app.notion.com/p/3fe062cd7cd181a6b38ee6d1a668909f">15일차 Dynamic routing_IGP.txt</mention-page>
- <mention-page url="https://app.notion.com/p/3fe062cd7cd181b7b4d6c5741481bb32">1일차_LAN구성.txt</mention-page>
- <mention-page url="https://app.notion.com/p/3fe062cd7cd18167a9a3c20998aadab6">20일차 경로재분배,루프백가상장비설정.txt</mention-page>
- <mention-page url="https://app.notion.com/p/3fe062cd7cd18164bf3ccdc83d35128e">2일차_라우팅테이블구성.txt</mention-page>
관련 실습　<mention-page url="https://app.notion.com/p/3fe062cd7cd181b8b94bd5b2f66e7f96">RIP 정적 경로 재분배 설정 및 라우팅 테이블 확인</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181a3bff5e22d2b6c03bf">인터페이스·라우팅 테이블 확인 명령</mention-page>
<details>
<summary>기존 분류의 연결 자료</summary>
	<mention-page url="https://app.notion.com/p/3fe062cd7cd18198beeade5b5dbdcca5">라우팅 테이블과 경로 선택</mention-page>
	<mention-page url="https://app.notion.com/p/3fe062cd7cd1819a91efdc7bdd1700f9">라우팅 방식과 RIP</mention-page>
	<mention-page url="https://app.notion.com/p/3fe062cd7cd181819463d129d31de168">경로 재분배 실습</mention-page>
</details>

## 정적 라우팅
관련 내용　정적 라우팅·정적 경로·기본 경로·플로팅·디폴트

관련 개념　<mention-page url="https://app.notion.com/p/3fe062cd7cd181d0b328debad2f03b1d">디폴트 라우트</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181c4a815f86ceaeeb062">정적 경로</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd1810eb6e1eea9758689d9">정적 라우팅</mention-page>
### 학습자료
- <mention-page url="https://app.notion.com/p/3fe062cd7cd1816da520f8909ffc646b">12일차.docx</mention-page>
- <mention-page url="https://app.notion.com/p/3fe062cd7cd18167a9a3c20998aadab6">20일차 경로재분배,루프백가상장비설정.txt</mention-page>
- <mention-page url="https://app.notion.com/p/3fe062cd7cd18164bf3ccdc83d35128e">2일차_라우팅테이블구성.txt</mention-page>
관련 실습　<mention-page url="https://app.notion.com/p/3fe062cd7cd1816f8441d0b15aed4e29">정적 라우팅 설정</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd1819bb418f44a96340906">디폴트 라우트 설정 및 삭제</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181ab82c5e037b184955f">플로팅 라우트 구성</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181b8b94bd5b2f66e7f96">RIP 정적 경로 재분배 설정 및 라우팅 테이블 확인</mention-page> · <mention-page url="https://app.notion.com/p/3fe062cd7cd181a0b8a9dffeb8a3407f">정적 경로 지정 예시</mention-page>
<details>
<summary>기존 분류의 연결 자료</summary>
	<mention-page url="https://app.notion.com/p/3fe062cd7cd181c8ae05c1976a9dd7d6">정적·기본·플로팅 경로</mention-page>
</details>

## OSPF
관련 내용　OSPF·Router ID·이웃 관계·DR·BDR

학습자료 준비 중


## 유지 · 3fe062cd-7cd1-81f6-94d0-dfd47ea91c7d

<mention-page url="https://app.notion.com/p/3fb062cd-7cd1-80c6-ab73-d56d5fadc0a5">학습 홈</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8115-be2c-cf26275aea30">개념 찾아보기</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8147-8ea1-f99fb7ae9ef8">실습 찾아보기</mention-page>

CCNA 기초 학습 항목

## 주소와 이름 서비스
관련 내용　DHCP·DNS·NAT·PAT

학습자료 준비 중

## 장비 접속과 관리
관련 내용　CLI·콘솔·SSH·CDP·LLDP

### 학습자료
- <mention-page url="https://app.notion.com/p/3fe062cd7cd18160adfec58bee312eb0">2일차_원격접속.txt</mention-page>
관련 실습　<mention-page url="https://app.notion.com/p/3fe062cd7cd18157b98accd97ae2880c">R2·R3 Telnet 원격 접속 설정 예시</mention-page>
<details>
<summary>기존 분류의 연결 자료</summary>
	<mention-page url="https://app.notion.com/p/3fe062cd7cd18166820fe77561b8a7bc">무선 접속과 장비 관리</mention-page>
</details>

## 운영과 모니터링
관련 내용　NTP·Syslog·SNMP·TFTP·FTP·QoS

### 학습자료
- <mention-page url="https://app.notion.com/p/3fe062cd7cd181a6b38ee6d1a668909f">15일차 Dynamic routing_IGP.txt</mention-page>
<details>
<summary>기존 분류의 연결 자료</summary>
	<mention-page url="https://app.notion.com/p/3fe062cd7cd181cf8093c6f36d43a6d6">주소·이름·시간·운영 서비스</mention-page>
</details>


## 유지 · 3fe062cd-7cd1-8106-8d8d-e8a96028a03d

<mention-page url="https://app.notion.com/p/3fb062cd-7cd1-80c6-ab73-d56d5fadc0a5">학습 홈</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8115-be2c-cf26275aea30">개념 찾아보기</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8147-8ea1-f99fb7ae9ef8">실습 찾아보기</mention-page>

CCNA 기초 학습 항목

## 보안과 인증
관련 내용　보안·위협·비밀번호·AAA·VPN·IPsec

### 학습자료
- <mention-page url="https://app.notion.com/p/3fe062cd7cd18160adfec58bee312eb0">2일차_원격접속.txt</mention-page>
<details>
<summary>기존 분류의 연결 자료</summary>
	<mention-page url="https://app.notion.com/p/3fe062cd7cd1813d9048f81f7dd614d2">보안 원칙과 장비·VPN 접근</mention-page>
</details>

## 접근 제어
관련 내용　ACL·Port Security·DHCP Snooping·ARP inspection

관련 개념　<mention-page url="https://app.notion.com/p/3fe062cd7cd1818aa424e721c329fa48">ACL</mention-page>
### 학습자료
- <mention-page url="https://app.notion.com/p/3fe062cd7cd181b7b4d6c5741481bb32">1일차_LAN구성.txt</mention-page>
관련 실습　<mention-page url="https://app.notion.com/p/3fe062cd7cd181eeadd5d9b53ee73330">ACL 설정 및 인터페이스 적용</mention-page>
<details>
<summary>기존 분류의 연결 자료</summary>
	<mention-page url="https://app.notion.com/p/3fe062cd7cd181bfa36cf08dad43d6bc">접근 제어와 접속 보안</mention-page>
</details>


## 유지 · 3fe062cd-7cd1-8195-a3b6-f3fe48189ad7

<mention-page url="https://app.notion.com/p/3fb062cd-7cd1-80c6-ab73-d56d5fadc0a5">학습 홈</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8115-be2c-cf26275aea30">개념 찾아보기</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-81bb-9c61-cdb9454abf18">학습자료</mention-page>　·　<mention-page url="https://app.notion.com/p/3fe062cd-7cd1-8147-8ea1-f99fb7ae9ef8">실습 찾아보기</mention-page>

CCNA 기초 학습 항목

## 네트워크 자동화 기초
관련 내용　자동화·SDN·컨트롤러·AI

학습자료 준비 중

## API와 데이터
관련 내용　REST·HTTP·JSON·Ansible·Terraform

학습자료 준비 중


