<mention url="https://app.notion.com/p/3fb062cd7cd180c6ab73d56d5fadc0a5">Network 학습 자료</mention>　·　{{page:학습자료}}　·　{{page:개념 찾아보기}}　·　{{page:실습 찾아보기}}

CCNA 분류 · 2\. 네트워크 접속

## VLAN과 VLAN 간 연결

관련 용어　VLAN, Inter-VLAN, SVI, 액세스 포트, 서브인터페이스

- {{page:18일차.txt}}
- {{page:1일차_LAN구성.txt}}

<callout icon="🧭">
AI가 짚은 보완할 점

- VLAN 30은 생성되고 라우터 서브인터페이스도 설정되어 있지만, VLAN 30에 연결할 액세스 포트 설정은 보이지 않는다.
- VLAN 생성 명령, 액세스 포트와 VLAN 배정의 검증, VLAN 간 라우팅의 동작 확인은 다루지 않습니다.
</callout>

## 트렁크·802.1Q·네이티브 VLAN

관련 용어　트렁크, 802.1Q, 네이티브 VLAN

- {{page:18일차.txt}}
- {{page:1일차_LAN구성.txt}}

<callout icon="🧭">
AI가 짚은 보완할 점

- 트렁크 양 끝의 설정 일치 확인과 802.1Q 태그 처리 설명은 다루지 않는다.
- 802.1Q 태깅 방식과 네이티브 VLAN의 동작 및 설정은 다루지 않습니다. 트렁크 인터페이스에서 허용 VLAN을 지정하거나 확인하는 내용도 없습니다.
</callout>

## 인접 장비 탐색

관련 용어　CDP, LLDP

아직 연결된 학습자료가 없습니다.

## EtherChannel과 LACP

관련 용어　EtherChannel, LACP

- {{page:18일차.txt}}

<callout icon="🧭">
AI가 짚은 보완할 점

- LACP와 PAgP의 협상 방식 및 호환 가능한 모드 조합에 대한 설명이 부족하다. auto/desirable은 PAgP 모드이고 active/passive는 LACP 모드이다.
</callout>

## 스패닝 트리와 루프 방지

관련 용어　STP, PVST, PortFast, BPDU

- {{page:18일차.txt}}

<callout icon="🧭">
AI가 짚은 보완할 점

- 루트 브리지 선출, 포트 역할·상태, BPDU 등 루프 방지 동작에 관한 내용은 없다.
</callout>

## 무선 접속과 장비 관리

관련 용어　WLAN, WLC, AP 모드, Telnet·SSH·콘솔 관리 접속

- <mention url="https://app.notion.com/p/408062cd7cd1812b931ac580a333172d">2일차_원격접속.txt</mention>

<callout icon="🧭">
AI가 짚은 보완할 점

- Telnet 설정 예시만 있어 SSH와 콘솔 접속을 포함한 관리 접속 방법, 접속 설정 확인 및 관련 보안 관리 내용이 다뤄지지 않았다.
</callout>

## VTP와 PAgP

관련 용어　VTP, PAgP

- {{page:18일차.txt}}

<callout icon="🧭">
AI가 짚은 보완할 점

- VTP의 server/client/transparent 모드, revision number 및 동기화 조건에 관한 설명은 없다. PAgP는 이름만 언급되며 설정 모드의 의미는 설명하지 않는다.
</callout>
