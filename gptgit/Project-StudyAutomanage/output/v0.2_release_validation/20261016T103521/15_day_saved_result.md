# 15일차 Dynamic routing\_IGP\.txt

Schema 0.2-draft · 원문 기반 분석 · 내용 검토 필요

IGP의 라우팅 방식과 RIP의 동작, RIPv1·RIPv2의 차이를 설명하며 일부 항목은 질문이나 메모 형태로 미완성입니다\.

형식·연결 검사와 기술적 사실성·실습 성공 검증은 별개입니다.

## 동적 라우팅과 IGP·EGP 분류

### 동적 라우팅

자료에서 IGP와 EGP를 구분하고, IGP의 라우팅 방식과 RIP를 설명하는 주제입니다\.

### IGP

자료에서 내부 게이트웨이 프로토콜로 제시하며, Distance vector·Link state·Hybrid 유형을 설명합니다\.

### EGP

자료에서 외부 게이트웨이 프로토콜로 제시하며, 추가 설명은 없습니다\.

### Distance vector

자료에서 RIP와 IGRP를 예로 들고, 주기적으로 라우팅 테이블 정보를 교환하는 방식으로 설명합니다\.

### Hybrid

자료에서 EIGRP를 예로 들며 IGRP 기반 비용 계산과 Link state 방식의 상태 모니터링·변화 업데이트를 결합한 것으로 설명합니다\.

### IGP → Distance vector

유형으로 제시됨

자료에서 IGP 아래에 Distance vector를 제시합니다\.

### IGP → Hybrid

유형으로 제시됨

자료에서 IGP 아래에 Hybrid를 제시합니다\.

### Distance vector → RIP

예시로 포함

자료에서 Distance vector의 예로 RIP를 제시합니다\.

### IGP

자료에서 IGP를 내부 게이트웨이 프로토콜로 풀이합니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
IGP 내부게이트웨이 프로토콜
```

### EGP

자료에서 EGP를 외부 게이트웨이 프로토콜로 풀이합니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
EGP 외부 게이트웨이 프로토콜
```

### Distance vector

자료에서는 RIP와 IGRP를 Distance vector의 예로 들고, 라우팅 테이블 정보를 주기적으로 교환하는 레거시 기술로 설명합니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
distance vector : RIP[Metric(계산방식?):홉수기준 MAX 15]IGRP
	=> 주기적 정보(라우팅테이블) 교환 레거시 기술
```

### Hybrid

자료에서는 EIGRP의 비용 계산이 IGRP를 기반으로 하며, 상태 모니터링과 네트워크 변화 시 업데이트는 Link state 방식을 사용한다고 설명합니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
hybrid: EIGRP 
	=> 비용계산은 IGRP를 기반으로하고 상태 모니터링 및 네트워크 변화시 업데이트는 link state 방식을 사용
```

❗ 정정: EIGRP는 링크상태 프로토콜이 아니라 거리 벡터 기반의 DUAL을 사용하는 프로토콜이다\.

- 출처: [RFC 7868 — EIGRP architecture](<https://www.rfc-editor.org/rfc/rfc7868.html>) · 확인일 2026\-10\-15

## 링크상태 방식과 이웃 확인

### Link state

자료에서 OSPF와 IS\-IS를 예로 들며, 상태 변화 시 정보를 교환하고 평상시 이웃 라우터를 모니터링하는 방식으로 설명합니다\.

### Hello packet

자료에서 Link state 방식이 평상시 이웃 라우터를 모니터링할 때 사용하는 것으로 설명합니다\.

### IGP → Link state

유형으로 제시됨

자료에서 IGP 아래에 Link state를 제시합니다\.

### Link state

자료에서는 상태 변화 시 정보를 교환하고 평상시에는 Hello packet으로 이웃 라우터를 모니터링하며, 40초 동안 응답이 없으면 테이블에서 삭제한다고 설명합니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
link state OSPF[대역폭], IS-IS Metric 구성요소는 무엇인가?
	=> 상태 변화시 정보 교환, 평상시 주기적으로 이웃 라우터를 모니터링(Hello packet을 이용 40초동안 응답이 없으면 테이블 삭제)
```

❗ 정정: 원문의 40초는 링크상태 프로토콜 공통값이 아니며, OSPF의 이웃 Down 판정은 인터페이스 Dead Interval 설정에 따른다\.

- 출처: [Cisco IOS OSPF Command Reference — ip ospf dead\-interval](<https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/iproute_ospf/command/iro-cr-book/m_ospf-a1.html>) · 확인일 2026\-10\-15

## RIP 동작과 RIPv1·RIPv2 비교

### RIP

자료에서 UDP 520을 사용하고 30초 주기로 라우팅 테이블 정보를 교환하는 프로토콜로 설명합니다\.

### RIPv1

자료에서 classful 방식으로 서브넷 범위를 보지 않고 VLSM을 지원하지 않는 RIP 버전으로 설명합니다\.

### RIPv2

원문에 classless와 VLSM 지원이 표기되어 있으나, 서브넷 범위에 대한 문장은 미완성이다\.

### VLSM

자료에서 가변길이 서브넷 마스크라고 풀이하며 RIPv1은 지원하지 않고 RIPv2는 지원한다고 설명합니다\.

### 라우팅 테이블 정보 교환

자료에서 Distance vector의 주기적 정보 교환과 RIP의 30초 주기 정보 교환을 설명합니다\.

### RIP → RIPv1

버전으로 구분됨

### RIP → RIPv2

버전으로 구분됨

### RIPv1 → VLSM

지원하지 않음

자료에서 RIPv1은 VLSM을 지원하지 않는다고 설명합니다\.

### RIPv2 → VLSM

지원함

자료에서 RIPv2는 VLSM을 지원한다고 설명합니다\.

### RIP

자료에서는 RIP가 UDP 520을 사용해 30초 주기로 라우팅 테이블 정보를 교환한다고 설명합니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
RIP 
UDP520
30초 주기로 정보교환(라우팅 테이블 정보)
```

### RIPv1 브로드캐스트

자료에서는 RIPv1으로 설정된 라우터끼리 주기적으로 보내는 신호의 목적지 IP가 255\.255\.255\.255인 브로드캐스트라고 관찰 내용을 서술합니다\.

원문 인용 · 표시본의 인증값은 숨김

```text
실제로 와이어샤크에서 ripv1으로 설정된 라우터끼리 신호를 주고 받을때 udp 520포트로 주기적으로 날리는 신호의 데스티네이션 ip 값은 255.255.255.255 브로드케스트 신호이다.
```

### RIPv1 / RIPv2

- 주소 지정 방식\(classful/classless 표기\)
- VLSM 지원

원문 인용 · 표시본의 인증값은 숨김

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

## 별도로 적힌 명령 메모

### no ip domain lookup

자료에 단독으로 적힌 명령어이며 용도나 수행 절차는 설명되지 않습니다\.

---

코멘트 2개 · 검토 대기 후보 미확인 · 보조 항목 제외 사유 미확인

원본 JSON은 별도로 보존합니다. 표시본의 인증값 숨김은 원문 인용 수정이 아닙니다.
