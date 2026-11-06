# 네트워크 엔지니어 취업 프로젝트

> 문서 연결 기준일: 2026-10-18. 위치와 읽는 순서를 안내한다. 실제 상태·주소·이력은 담당 원본에 둔다.

사내망·Linux·웹서비스·AWS/Hybrid의 구조와 통신 흐름을 실습한다. 목적·범위는 [프로젝트 범위](docs/01_requirements/프로젝트%20범위.md), AI 역할·실행 제약은 [AGENTS](AGENTS.md)가 기준이다.

## 작업 시작·종료

- **“작업기록 보고 다음 작업 진행해줘”**: 적용 규칙 확인 → [최신 인계](docs/04_records/작업%20기록.md#latest-handoff) → [현재 상태·다음 작업](docs/02_design/network%20project%20진행상황.md#next-work) → 인계에 연결된 관련 상세 절만 확인 → 범위 내 작업.
- **“작업기록 남겨줘”**: 확정 결과를 분야별 원본과 진행상황에 반영 → 기존 작업기록에 변경 이유·근거·다음 행동 기록 → 최신 인계 연결과 수정 문서 검사.
- 새 작업은 범위·설계를, 문서 정리만 하는 작업은 지정 문서·관련 규칙부터 확인한다. 공통 재개·권한은 [상위 공통 작업 흐름](../docs/common_workflow.md), 이 프로젝트의 구체적인 연결·재질문 절차는 [문서 운영 및 재개](docs/00_rules/문서%20운영%20및%20재개.md)가 기준이다.

## 문서 트리·읽는 조건

| 위치 | 원본이 맡는 내용 | 읽는 경우 |
| --- | --- | --- |
| [AGENTS.md](AGENTS.md) | AI 행동·권한·규칙 진입점 | 작업 시작 |
| [docs/00_rules/network project 규칙.md](docs/00_rules/network%20project%20규칙.md) | 기술 판단·사실 구분·실습 원칙 | 적용 규칙 확인 |
| [docs/00_rules/문서 운영 및 재개.md](docs/00_rules/문서%20운영%20및%20재개.md) | 문서 책임·종료/재개·재확인·카테고리 | 기록·재개·문서 정리 |
| [docs/01_requirements/프로젝트 범위.md](docs/01_requirements/프로젝트%20범위.md) | 목표·대상·제약 | 범위 판단 |
| [docs/02_design/전체 설계 및 구축 단계.md](docs/02_design/전체%20설계%20및%20구축%20단계.md) | 목표 구조·통신 기준·Phase 범위 | 설계·다음 단계 검토 |
| [docs/02_design/실습 환경 및 주소.md](docs/02_design/실습%20환경%20및%20주소.md) | 장비·포트·IP·경로·DHCP·Image | 설정값·연결 관계 필요 시 |
| [docs/02_design/network project 진행상황.md](docs/02_design/network%20project%20진행상황.md) | 현재 단계·완료 요약·미확정·다음 작업 | 현재 상태·우선순위 확인 |
| [docs/03_verification/Phase1 검증.md](docs/03_verification/Phase1%20검증.md) | 시점별 출력·사용자 확인·검증 한계 | 근거 대조·재검증 판단 |
| [docs/04_records/작업 기록.md](docs/04_records/작업%20기록.md) | 날짜별 이력·최신 인계 | 작업 재개·종료·결정 이유 확인 |
| [docs/04_records/2026-10-02 백업](docs/04_records/network%20project%20진행상황_261002_backup.md) | 과거 스냅샷 | 과거 비교만; 현재 기준 아님 |
| [guide_docs/](guide_docs/) | 사용자 직접 실행·재현 절차 | 해당 단계 실습 |
| [Codex 활용 메모](Codex_활용_메모.md) | 요청 예시 | 사용자 요청 작성 |

진행상황은 현재 상태의 통합 진입점으로 유지한다. 별도 파일로 옮긴 상세 내용은 해당 문서에서만 관리하며 매 작업마다 트리 전체를 읽지 않는다. 날짜별 기록의 옛 “다음 작업”은 그 시점의 이력이다.

## 사용자 가이드

- [Linux–PNETLab 통신](guide_docs/Linux_PNETLab_통신검증_가이드.html)
- [CORE–EDGE 연결](guide_docs/CORE_EDGE_연결_검증_가이드.html)
- [EDGE 인터넷·NAT](guide_docs/EDGE_인터넷_NAT_검증_가이드.html)
- [Phase 1 DNS·잔여 검증](guide_docs/Phase1_DNS_및_잔여검증_가이드.html)

가이드의 작성 시점별 결과는 검증 근거로 활용하되 최신 주소·현재 상태를 대신하지 않는다. 장비 적용은 사용자가 수행한다.

## 변경 이력

| 날짜 | 내용 |
| --- | --- |
| 2026-10-16 | 네트워크 고유 실습 흐름과 상위 공통 절차의 책임 구분 |
| 2026-10-18 | DNS 가이드 연결 추가 후 MD 역할별 분리·중복 통합, 최신 인계에서 다음 작업으로 이어지는 연결 추가 |
