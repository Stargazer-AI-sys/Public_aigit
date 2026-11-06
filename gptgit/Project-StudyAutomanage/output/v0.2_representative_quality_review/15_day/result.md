# 15일차 — 새 흐름 적용 검토 결과

IGP의 라우팅 방식과 RIP의 동작, RIPv1·RIPv2의 차이를 설명하며 일부 항목은 질문이나 메모 형태로 미완성입니다.

> 저장 결과를 원문 대조 후 재구성한 검토용 결과입니다. 새 API 분석은 수행하지 않았습니다.

## 동적 라우팅과 IGP·EGP 분류

자료에서 IGP를 내부 게이트웨이 프로토콜로 풀이합니다.

자료에서 EGP를 외부 게이트웨이 프로토콜로 풀이합니다.

자료에서는 RIP와 IGRP를 Distance vector의 예로 들고, 라우팅 테이블 정보를 주기적으로 교환하는 레거시 기술로 설명합니다.

자료에서는 EIGRP의 비용 계산이 IGRP를 기반으로 하며, 상태 모니터링과 네트워크 변화 시 업데이트는 Link state 방식을 사용한다고 설명합니다.

❗ **정정** EIGRP는 링크상태 프로토콜이 아니라 거리 벡터 기반의 DUAL을 사용하는 프로토콜이다. [RFC 7868 — EIGRP architecture](https://www.rfc-editor.org/rfc/rfc7868.html)

## 링크상태 방식과 이웃 확인

자료에서는 상태 변화 시 정보를 교환하고 평상시에는 Hello packet으로 이웃 라우터를 모니터링하며, 40초 동안 응답이 없으면 테이블에서 삭제한다고 설명합니다.

❗ **정정** 원문의 40초는 링크상태 프로토콜 공통값이 아니며, OSPF의 이웃 Down 판정은 인터페이스 Dead Interval 설정에 따른다. [Cisco IOS OSPF Command Reference — ip ospf dead-interval](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/iproute_ospf/command/iro-cr-book/m_ospf-a1.html)

## RIP 동작과 RIPv1·RIPv2 비교

자료에서는 RIP가 UDP 520을 사용해 30초 주기로 라우팅 테이블 정보를 교환한다고 설명합니다.

자료에서는 RIPv1으로 설정된 라우터끼리 주기적으로 보내는 신호의 목적지 IP가 255.255.255.255인 브로드캐스트라고 관찰 내용을 서술합니다.

RIPv1 / RIPv2: 주소 지정 방식(classful/classless 표기), VLSM 지원

## 별도로 적힌 명령 메모

자료에 단독으로 적힌 명령어이며 용도나 수행 절차는 설명되지 않습니다.

## 남은 확인 사항

- RIPv2 서브넷 범위·IS-IS 메트릭·AS 질문은 원문에서 미완성인 상태로 유지했다.
- RIPv1 브로드캐스트 관찰은 원문 기록으로만 유지했으며 원본 패킷 캡처를 검증하지 않았다.
