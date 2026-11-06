<mention url="https://app.notion.com/p/3fb062cd7cd180c6ab73d56d5fadc0a5">Network 학습 자료</mention>　·　{{page:학습자료}}　·　{{page:개념 찾아보기}}　·　{{page:실습 찾아보기}}

## 핵심 정리

IGP의 라우팅 방식과 RIP의 동작 및 RIPv1·RIPv2 차이를 정리하고 관련 설정 명령을 기록한 자료입니다.

## CCNA 분류

- 3\. IP 라우팅 / 라우팅 방식과 RIP

## 주제별 내용

<toggle>
동적 라우팅과 라우팅 방식

### IGP와 라우팅 방식

IGP를 내부 게이트웨이 프로토콜로 설명하고, Distance vector의 예로 RIP와 IGRP, Link state의 예로 OSPF와 IS-IS를 기록했다. RIP의 메트릭은 홉 수 기준이며 최대 15라고 적었다.

<toggle>
원문 근거

```text
IGP 내부게이트웨이 프로토콜
	distance vector : RIP[Metric(계산방식?):홉수기준 MAX 15]IGRP
	=> 주기적 정보(라우팅테이블) 교환 레거시 기술
	link state OSPF[대역폭], IS-IS Metric 구성요소는 무엇인가?
```
</toggle>

### 라우팅 정보 교환과 모니터링

Distance vector는 라우팅 테이블 정보를 주기적으로 교환하는 레거시 기술로, Link state는 상태 변화 시 정보를 교환하고 평상시 Hello packet으로 이웃 라우터를 모니터링한다고 기록했다. 40초 동안 응답이 없으면 테이블에서 삭제한다고 적었다.

<toggle>
원문 근거

```text
	=> 주기적 정보(라우팅테이블) 교환 레거시 기술
	link state OSPF[대역폭], IS-IS Metric 구성요소는 무엇인가?
	=> 상태 변화시 정보 교환, 평상시 주기적으로 이웃 라우터를 모니터링(Hello packet을 이용 40초동안 응답이 없으면 테이블 삭제)
```
</toggle>

### EIGRP와 EGP

EIGRP를 hybrid로 분류하고, 비용 계산은 IGRP를 기반으로 하며 상태 모니터링과 네트워크 변화 시 업데이트는 Link state 방식을 사용한다고 기록했다. EGP는 외부 게이트웨이 프로토콜로 적었다.

<toggle>
원문 근거

```text
	hybrid: EIGRP 
	=> 비용계산은 IGRP를 기반으로하고 상태 모니터링 및 네트워크 변화시 업데이트는 link state 방식을 사용




EGP 외부 게이트웨이 프로토콜
```
</toggle>

<callout icon="💡">
AI 검토 의견 · 정정

EIGRP는 IGRP에서 발전한 고급 거리 벡터(advanced distance vector) 프로토콜이며, Link state 방식으로 분류하지 않습니다. Hello 패킷 응답이 없어 경로를 무효화하는 시간은 OSPF에서 네트워크 유형 등에 따라 달라지므로, 40초를 모든 경우에 적용되는 값으로 일반화하면 안 됩니다.
</callout>
</toggle>

<toggle>
RIP과 버전별 차이

### RIP 기본 동작

RIP은 UDP 520을 사용하고 라우팅 테이블 정보를 30초 주기로 교환한다고 기록했다.

<toggle>
원문 근거

```text
RIP 
UDP520
30초 주기로 정보교환(라우팅 테이블 정보)
```
</toggle>

### RIPv1

RIPv1은 classful 방식으로 서브넷 범위를 보지 않으며 VLSM을 지원하지 않는다고 기록했다. 예시로 172.16.1.0/24가 172.16.0.0/16 형태로 전달될 수 있고, 브로드캐스트 주소 255.255.255.255를 목적지로 하는 UDP 520 패킷을 주기적으로 보낸다고 적었다.

<toggle>
원문 근거

```text
RIPv1
	classful => 서브넷 범위를 보지않음 서브넷 범위를 지정한 네트워크이면 쓸대없이 데이터가 가는 현상이 생길수 있다. *보통 A B C D.. 클래스만 구분함
	172.16.1.0/24 -> 172.16.0.0/16 형태로 가버리는게 v1에 대표적인 현상인데 이렇게 되면 받은 쪽에서는 테이블 길이가 길어짐
	테이블 길이가 길어지면 룩업시간이 길어짐
	VLSM 가변길이 서브넷 마스크 지원안함	
	라우트는 브로드케스트 신호를 드랍하지만 예외적으로 ripv1은 허용함 실제로 와이어샤크에서 ripv1으로 설정된 라우터끼리 신호를 주고 받을때 udp 520포트로 주기적으로 날리는 신호의 데스티네이션 ip 값은 255.255.255.255 브로드케스트 신호이다.
```
</toggle>

### RIPv2

RIPv2는 classless 방식이며 VLSM을 지원한다고 기록했다.

<toggle>
원문 근거

```text
RIPv2
	classless => 서브넷 범위를 
	VLSM 가변길이 서브넷 마스크 지원
```
</toggle>

<callout icon="💡">
AI 검토 의견 · 보충

RIPv1은 경로 업데이트를 브로드캐스트하고 RIPv2는 멀티캐스트 주소 224.0.0.9를 사용합니다. RIP의 메트릭은 홉 수이며 16은 도달 불가를 뜻하므로, 최대 15홉까지 도달 가능합니다.
</callout>
</toggle>

<toggle>
기록된 설정 명령

### 도메인 이름 조회 비활성화 명령

no ip domain lookup 명령을 기록했다.

<toggle>
원문 근거

```text
no ip domain lookup
```
</toggle>

### 실습 · 도메인 이름 조회 비활성화

기록된 설정 명령은 no ip domain lookup이다.

<toggle>
원문 설정 예시

```text
no ip domain lookup
```
</toggle>
</toggle>

## CCNA 기준 보완할 점

<callout icon="🧭">
AI가 CCNA 학습 범위와 비교해 짚은 내용입니다. 공식 자료로 확인하세요.

- **3\. IP 라우팅 / 라우팅 방식과 RIP**: RIP의 메트릭 및 16홉의 의미, RIPv2의 멀티캐스트 업데이트 주소(224.0.0.9), RIPv1과 RIPv2의 업데이트 전송 차이가 빠져 있습니다. 자료에 언급된 EGP의 구체적인 라우팅 방식이나 예시는 다루지 않습니다.
</callout>

<toggle>
원본 정보

파일명　15일차 Dynamic routing_IGP.txt

내용 해시　5520ea4cfcab84de60fba38f45a7c0f5d68173bf9c58f525630414acfc5f0efc

분석　2026-11-06T00:28:18+00:00 · gpt-6-luna
</toggle>
