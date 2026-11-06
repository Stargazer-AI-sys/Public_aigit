# 18일차 — 지식베이스 결과 예시 (v0.2 초안)

VLAN과 트렁크, 라우터 서브인터페이스, VTP, 스패닝 트리 및 EtherChannel 설정 명령 예시를 모은 자료입니다.

> 기존 저장 결과를 재구성한 검토용 예시이며, 새 AI 분석 결과가 아닙니다.

## VLAN 및 스위치 포트 설정

VLAN 10, 20, 30을 생성하고, 포트를 트렁크 또는 액세스 모드로 설정해 VLAN 10 및 20에 할당하는 명령 예시입니다. 명령이 제시되어 있지만 실행 여부와 성공 여부는 확인되지 않습니다.

## 라우터 서브인터페이스와 네이티브 VLAN

R1의 fa0/0을 활성화하고 서브인터페이스에 VLAN 캡슐화와 IP 주소를 설정하는 명령 예시입니다. 한 구간은 VLAN 10과 20을, 다른 구간은 VLAN 10, 20, 30을 다루며 설정 결과는 제시되지 않습니다.

스위치 트렁크 인터페이스에 네이티브 VLAN 10을 지정하고 라우터 서브인터페이스에 VLAN 10을 native로 표시하는 명령 예시입니다. 설정 확인이나 결과는 기록되어 있지 않습니다.

## VTP 설정과 VLAN DB 동기화

자료에서는 VTP를 VLAN DB 동기화로 설명하며, domain과 password를 지정해 그 정보로 동기화한다고 적습니다. 뒤의 '최대' 메모는 내용이 완성되지 않았습니다.

VTP domain을 cisco로, password를 1234로 지정하는 명령 예시와 VLAN DB 동기화에 관한 메모가 있습니다. 설정 수행이나 동기화 결과는 확인되지 않습니다.

## 스패닝 트리 및 액세스 포트 설정

스위치의 기본 PortFast 설정과 Rapid-PVST 모드 설정, 그리고 fa0/1과 fa0/2를 액세스 포트로 설정해 VLAN 10 및 20에 할당하는 명령 예시입니다. 실행이나 확인 결과는 제시되지 않습니다.

## EtherChannel 구성과 모드

SW1·SW2·SW3의 인터페이스 범위에 트렁크와 channel-group을 설정하는 예시다. SW1의 그룹 1은 auto, SW2의 그룹 1은 desi이며, 그룹 2는 SW1 active·SW3 passive, 그룹 3은 SW2·SW3 모두 on이다. 배선과 상태 출력은 기록되어 있지 않아 구성 성공 여부는 확인되지 않는다.

❗ **정정** 기존 분석의 미완성 메모라는 해석과 달리, channel-group ?는 입력 가능한 인수·옵션을 조회하는 도움말 구문이다. [Cisco IOS XE 17.x — Using the Cisco IOS Command-Line Interface](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/syst-mgmt/b-system-management/m_cf-cli-basics.html)

---

원본: `test_file/18일차.txt` · 원문 식별값과 인용 7곳 보존. 실행·구성 성공 여부는 미확인.

이 예시는 단락 구성과 선택적 코멘트의 표시를 확인하기 위한 것입니다. 기술적 사실성 전체를 자동 검증한 결과는 아닙니다.
