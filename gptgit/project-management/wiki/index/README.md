# wiki 전체 문서 색인

> 색인 갱신: 2026-11-05 | [wiki 첫 화면](../index.md)

위키는 기능, 구성 관계, 선택 이유, 운영 조건과 날짜별 사건을 나누어 설명한다. [내용 분류표](content_classification.md)는 원문 12개의 40개 내용 단위와 설명 페이지를 연결한다. 원문은 [raw](../../raw/)에 보존하며 현재 실행 상태는 [관리 작업기록](../../docs/04_records/management_log.md)을 기준으로 한다.

과거 자동화 설계와 당시 시험 결과는 현행 기능이나 현재 환경의 동작 보장이 아니다. 문서의 상태와 확인 범위를 본문에서 함께 읽는다. 현행 요구사항 이후 담당 위임은 [프로젝트 규칙](../../AGENTS.md)에 따른 herdr pane 제어이며 과거 자동화 전체를 재개한 것은 아니다.

## 기능 — 무엇을 제공하는가

- [요구사항 작성 양식](../features/신규_개발_프로젝트_요구사항_작성양식.md): 사용자가 목적·범위·조건을 입력하는 양식. 예시는 확정 요구가 아니다.
- [프로젝트 진입점](../features/project_entry.md): 개설·기존 프로젝트 선택·관리 환경 요청의 제공 범위와 연결 한계.
- [문서 점검](../features/document_checks.md): 검사로 확인할 수 있는 것과 내용·화면 검토의 차이.
- [과거 워크플로 도구](../features/historical_workflow_tools.md): 로컬 상태 도구와 제한형 기록 worker의 당시 기능 및 한계.
- [features 담당 기준](../features/AGENTS.md)

## 구조 — 어떻게 연결되는가

다음 다섯 문서는 과거 설계·구현 관계를 도식과 본문으로 설명한다. 도식에 연결이 있다는 이유로 실제 연결·독립 QA·전체 완주가 확인되는 것은 아니다.

- [역할과 인계](../architecture/roles.md): 마스터·기획·제작·검토·QA·문서화 책임.
- [자동화 워크플로](../architecture/automation_workflow.md): 단계·상태·증거·기록 관계.
- [프로젝트 진입점 구조](../architecture/project_entry.md): 개설 화면·기본 틀·요청·세션 관계.
- [세션 수명주기](../architecture/agent_session_lifecycle.md): 창 재사용·대화 ID·실제 복원의 구분.
- [Hermes worker](../architecture/hermes_worker.md): 제한 입력·구독 확인·전달·회수 구조.
- [이전 관리 워크플로 경로](../architecture/management_workflow.md): 운영 문서로 연결하는 이전 안내.
- [architecture 담당 기준](../architecture/AGENTS.md)

## 결정 — 무엇을 왜 선택했는가

- [ADR-0001: 기록과 설명의 책임 분리](../decisions/0001-workflow-records.md): 2026-10-27 채택 맥락, 사본 불일치를 줄이는 선택과 한계.
- [decisions 담당 기준](../decisions/AGENTS.md)

## 운영 — 어떤 조건에서 어떻게 확인하는가

- [관리 워크플로](../operations/management_workflow.md): 현행 관리·기획·위임·검토·인계의 기준 진입점.
- [과거 자동화 운영](../operations/historical_automation.md): 당시 인계·상태·재시도·비용·Hermes 회수 조건.
- [과거 세션 운영](../operations/historical_sessions.md): 당시 시작기·창·대화 복원 판정 조건.
- [과거 문서 점검](../operations/historical_document_checks.md): 보관 도구의 범위·실행 조건, 당시 예약 제안과 현재 예약 여부 미확인.
- [과거 자동화 검증의 판정 범위](../operations/automation_validation.md): 설치·모의 시험·실제 연결·전체 완료의 구분. 날짜별 결과는 아래 기록에서 확인한다.
- [operations 담당 기준](../operations/AGENTS.md)

## 기록 — 언제 무엇이 일어났는가

- [관리 작업 이력](../log/management_history_2026-10-13_2026-11-02.md): 2026-10-13~11-02 날짜별 변화와 근거. 당시 다음 작업은 현재 실행 지시가 아니다.
- [프로토타입 구축 이력](../log/prototype_build_history_2026-11-04.md): 구축·배치·검증과 개선 위치 정정.
- [HTML 점검 리뷰](../log/HTML_점검_자동화_리뷰.md): 2026-10-15 점검 결과와 입증하지 못한 효과.
- [자동화 검증 이력](../log/automation_validation_history.md): 시험·설치·호출의 당시 결과와 증거.
- [log 담당 기준](../log/AGENTS.md)

## 탐색과 편집 근거

- [내용 분류표](content_classification.md): 원문 절과 설명 페이지의 대응, 합성 경계와 확인 범위.
- [위키 편집 기준](../AGENTS.md) · [index 담당 기준](AGENTS.md)
- [최신 인계](../../docs/04_records/management_log.md): 프로젝트 역할·남은 업무·보류의 공식 진입점.

가이드 정식 제작과 기존 자료 전송 보류는 유지한다. 위키 재구성과 문서 검증은 기존 8개 프로토타입 업무의 수행이나 실제 자동화 구현 완료를 뜻하지 않는다.
