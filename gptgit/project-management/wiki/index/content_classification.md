---
type: concept
tags: [wiki, classification]
created: 2026-11-05
updated: 2026-11-05
confidence: medium
source_status: reviewed
status: current
sources:
  - ../AGENTS.md
  - ../../README.md
  - ../../AGENTS.md
  - ../../docs/04_records/management_log.md
  - ../../raw/docs/00_rules/roles.md
  - ../../raw/docs/02_design/project_entry.md
  - ../../raw/docs/02_design/management_workflow.md
  - ../../raw/docs/02_design/hermes_worker.md
  - ../../raw/docs/02_design/automation_workflow.md
  - ../../raw/docs/02_design/agent_session_lifecycle.md
  - ../../raw/docs/01_requirements/신규_개발_프로젝트_요구사항_작성양식.md
  - ../../raw/wiki/adr/0001-workflow-records.md
  - ../../raw/docs/03_verification/automation_validation.md
  - ../../raw/review_docs/HTML_점검_자동화_리뷰.md
  - ../../raw/docs/04_records/prototype_build_history_2026-11-04.md
  - ../../raw/docs/04_records/management_history_2026-10-13_2026-11-02.md
---

# 위키 내용 분류표

이 표는 기존 위키 본문 12개를 40개 내용 단위로 나누어 재구성한 설명 페이지와 연결하는 지도다. 원문 칸은 편집 전 내용을 보존한 raw를 가리키며, 실제 결과물은 아래 대응표에서 찾는다. 파일 위치만 바꾸지 않고 구조·기능·운영·기록의 질문에 맞게 분해·합성했다. 분류 기준은 [위키 공통 기준](../AGENTS.md), 기존 위치는 [전체 문서 색인](README.md)을 따른다.

원문에 적힌 설계·시험·제안의 상태는 서로 다르다. 특히 자동화 운영과 process_debug 적용 의무는 현행이 아니며, 현재 역할과 보류는 [최신 인계](../../docs/04_records/management_log.md)와 [현행 행동 규칙](../../AGENTS.md)이 우선한다. 아래 조건 칸은 이 차이를 보존하기 위한 편집 주의사항이며 공식 상태 원장을 대체하지 않는다.

## 읽는 방법과 확인 범위

- 원문 절과 출처는 raw 보관본 기준이다. 표의 연결 주제는 아래 실제 결과물에 반영했으며, 기획 때의 페이지 후보를 실재 파일과 연결했다.
- 원문의 중요한 조건·보류·정정은 설명에 보존한다. 선택 이유가 단편적으로 남은 사건은 log에서 설명하고, 새로운 채택 결정을 만들지 않는다.
- 제작 담당은 긴 관리 이력의 날짜별 절을 나누어 읽고 관련 증빙을 대조했다. 개별 주장의 확인 범위는 각 페이지의 sources와 본문을 따른다. 모든 과거 시험 재실행, 외부 서비스 현재 조건, 증거 진위의 전수 검증은 하지 않았다.
- 이 지도는 운영 규칙이나 공식 상태 원장이 아니다. `reviewed`는 원문 분류·편집 대조이며 기능 동작 확인을 뜻하지 않는다. 상태 current는 이 분류표와 설명 페이지의 현재 대응을 뜻하며 과거 자동화 기능의 상태가 아니다.

## 1. 역할·자동화 구조와 운영

| ID | 원문과 절 | 연결할 주제·분류 | 보존할 조건과 합성 관계 |
| --- | --- | --- | --- |
| A01 | [roles](../../raw/docs/00_rules/roles.md) · 책임과 경계 | 기존 architecture/roles.md: 역할 간 책임·전달 관계 | 과거 설계. 역할 정의와 실제 연결을 구분. A04의 단계 구조와 연결한다. |
| A02 | 같은 원문 · 세션과 모델 | 역할별 세션 관계는 기존 roles, 모델·제공자 선택 조건은 operations/historical_automation.md | 독립 세션과 다른 제공자의 교차 검증은 별개다. 현재 모델 배분 규칙은 루트 AGENTS를 참조한다. |
| A03 | 같은 원문 · 인계와 충돌 해결 | operations/historical_automation.md: 과거 인계·판정 절차 | A05·A06과 합성. process_debug 의무를 복원하지 않는다. 일반 재개 기준은 공통 작업 흐름을 참조한다. |
| A04 | [automation_workflow](../../raw/docs/02_design/automation_workflow.md) · 1. 목표와 적용 범위, 2. 요구사항과 단계 | 기존 architecture/automation_workflow.md: 과거 단계와 구성 관계 | 목표·설계·구현·연결을 구분. A01과 역할 책임을 중복 서술하지 않고 연결한다. |
| A05 | 같은 원문 · 2.1 Task 설계와 세션 전환, 2.2 맥락 복원 | Task와 세션 관계는 기존 automation_workflow, 인계·복원 방법은 operations/historical_automation.md | 과거 자동화와 현행 공통 재개 절차를 분리. 실제 전달·회수 성공은 별도 증거가 필요하다. |
| A06 | 같은 원문 · 3. 상태·증거·재시도 | 상태 전이 관계는 기존 automation_workflow, 재시도·재평가 조건은 operations/historical_automation.md | 도구의 상태 일관성과 검토자 신원·증거 진위는 별개다. |
| A07 | 같은 원문 · 4. 기록과 문서 책임, 4.1 process_debug On/Off | 기록 관계는 기존 automation_workflow, debug 절차는 operations/historical_automation.md | 선택 이유는 D01에 연결. 과거 실행 경로는 현행 wiki 구조가 아니며 debug 현행 의무는 종료됐다. |
| A08 | 같은 원문 · 5. 환경·도구·비용 | 구성 의존 관계는 기존 automation_workflow, 환경·구독 조건은 operations/historical_automation.md | 2026-10-27 시점의 설명. 현재 구독·연결 확인 아님. Docker만으로 완전 격리를 주장하지 않는다. |
| A09 | 같은 원문 · 6. 구현·검증 순서, 7. 로컬 상태 도구 | 당시 계획·판정 조건은 operations/historical_automation.md, 도구 제공 범위는 features/historical_workflow_tools.md | 계획은 실행 사건과 다르므로 log에는 실제 실행 근거가 있는 내용만 연결. 종료 코드와 전체 완료를 구분하며 현재 도구 실행 가능 여부는 미확인이다. |
| A10 | [hermes_worker](../../raw/docs/02_design/hermes_worker.md) · 입력과 실행 | 기존 architecture/hermes_worker.md: packet·허용 source·worker 관계; 기능은 features/historical_workflow_tools.md | 과거 제한형 설계. 당시 허용 경로와 현재 raw 보관 경로를 구분한다. |
| A11 | 같은 원문 · 호출·비용 경계, 결과·중단·재전송 | operations/historical_automation.md: Hermes 호출·회수 조건 | A08과 공통 비용 조건을 합성. 불명확 결과의 자동 재전송 금지와 구독 확인 조건 보존. OS 격리 보장이 아니다. |
| A12 | 같은 원문 · 검증 범위 | log/automation_validation_history.md: 오프라인 시험·합성 실제 호출의 당시 근거 | 실제 호출 1회의 범위를 품질·독립 QA·전체 완주로 확대하지 않는다. V01 및 H08과 중복 시험 식별 후 합성한다. |

## 2. 프로젝트 진입점과 세션

| ID | 원문과 절 | 연결할 주제·분류 | 보존할 조건과 합성 관계 |
| --- | --- | --- | --- |
| E01 | [project_entry](../../raw/docs/02_design/project_entry.md) · 목적과 책임, 구현된 흐름 | 기능은 features/project_entry.md, 관리·개별 프로젝트 및 요청 전달 관계는 기존 architecture/project_entry.md | 개설·선택·점검의 제공 범위와 AI 호출을 구분. 프로젝트 개설은 기획·제작 승인이 아니다. |
| E02 | 같은 원문 · 공통 기본 틀 | 생성 문서와 책임 관계는 기존 project_entry, 생성되는 항목은 features/project_entry.md | 관리 이력·인증·보류를 복사하지 않으며 기존 프로젝트를 자동 갱신하지 않는다. 기본 틀 보관본과 현재 동작 여부를 구분한다. |
| E03 | 같은 원문 · 아직 연결하지 않은 기능, 검증과 제한 | 기능·구조 설명에 제한을 인접 배치; 날짜별 시험은 기존 관리 이력과 연결 | 세션 시작·복원 및 전체 자동화는 로컬 검사만으로 입증되지 않는다. 후속 세션 문서 E04~E06과 시점 대조가 필요하다. |
| E04 | [agent_session_lifecycle](../../raw/docs/02_design/agent_session_lifecycle.md) · 경계와 저장, 시작 판정, 창 유지와 대화 ID 검증의 분리 | 관계는 기존 architecture/agent_session_lifecycle.md, 판정 절차는 operations/historical_sessions.md | 창 재사용·대화 ID 일치·실제 복원은 서로 다른 확인이다. 사용자 보고와 직접 검증을 구분한다. |
| E05 | 같은 원문 · 실행 연결과 조회, Codex 업데이트·PC 변경 시 시작기 | 시작기·상태 확인기 관계는 기존 agent_session_lifecycle, 실행 조건은 operations/historical_sessions.md | herdr 내부 실행 조건과 명시적 ID 재개 조건 보존. CheckOnly는 실제 복원 시험이 아니며 현 버전 호환성은 미확인이다. |
| E06 | 같은 원문 · 검증과 남은 범위, 시작 화면의 요청과 내부 처리, 자동 요청 수신 | 요청·수신기·실행기 관계는 기존 agent_session_lifecycle, 시험 사건은 기존 관리 이력 | 모의 시험과 실제 수신기·창 생성·복원을 구분한다. E01·E03과 합성하되 당시 미검증 및 후속 사용자 보고의 시점을 유지한다. |

## 3. 관리·입력·문서 점검

| ID | 원문과 절 | 연결할 주제·분류 | 보존할 조건과 합성 관계 |
| --- | --- | --- | --- |
| M01 | [management_workflow](../../raw/docs/02_design/management_workflow.md) · 1. 기본 흐름, 2. 초기 기획 | operations/management_workflow.md: 관리·기획의 입력과 결과·절차 | 현행 AGENTS와 공유 기획 스킬을 기준으로 참조 중심 합성. 과거 자동화 절차와 일반 관리 흐름을 구분한다. |
| M02 | 같은 원문 · 3. 실행과 검토의 분담, 문서 점검 확장 작업의 검토·종료 기준 | operations/management_workflow.md: 분담·검토·종료 조건 | 에이전트 사용 및 파일 변경 권한을 새로 부여하지 않는다. 읽기 전용 독립 검토와 파일 소유권 조건 유지. |
| M03 | 같은 원문 · 4. 인계 점검 | operations/management_workflow.md: 공통 인계 기준의 진입점 | 공통 작업 흐름과 project-handoff가 상세 기준. process_debug 의무 문구는 과거로 한정한다. |
| M04 | 같은 원문 · 5. 수동 문서 점검, 5.1~5.3 | 검사 제공 범위는 features/document_checks.md, 과거 명령·운영 조건은 operations/historical_document_checks.md, 시험 사건은 L01·H02 | raw 도구의 현재 실행 가능 여부는 미확인. 형식 검사와 최신성·내용·화면 품질 검토를 구분한다. |
| M05 | 같은 원문 · 6. 스킬 원본과 PC 설치, 6.1 생성·수정 요청마다 수행할 절차, 7. 예약 점검과 효과 확인 | operations/management_workflow.md: 공통 원본·개인 설치 구분 및 점검 조건 | 공통 절차를 복제하지 않고 현행 원본에 연결. 예약은 수동 검증 후 추후 결정이며 실제 예약 운영으로 쓰지 않는다. |
| F01 | [요구사항 양식](../../raw/docs/01_requirements/신규_개발_프로젝트_요구사항_작성양식.md) · 프로젝트 기본 정보, 1~10 | 기존 features 양식: 목적·사용자·장면·범위·판단 경계·환경·확장·운영 부담·성공 기준의 입력 | 미작성 양식과 예시는 확정 요구가 아니다. 기능 목록이 아니라 요구를 입력하는 양식 자체의 제공 기능이다. |
| F02 | 같은 원문 · 작성 방법, AI에게 맡길 기획·설계와 협업 기준 | 양식 사용 설명은 기존 features 양식, 기획 절차는 M01과 연결 | 1~4·10 우선 작성과 미정 표기 보존. 양식 전달이 파일 수정·실행 허가가 되지 않는다. |

## 4. 결정과 검증·구축 이력

| ID | 원문과 절 | 연결할 주제·분류 | 보존할 조건과 합성 관계 |
| --- | --- | --- | --- |
| D01 | [ADR-0001](../../raw/wiki/adr/0001-workflow-records.md) · 배경, 결정, 영향과 한계 | 기존 decisions/0001-workflow-records.md: 명세·실행계획·기록·wiki·가이드 책임을 나눈 이유 | 2026-10-27 채택 맥락을 유지. 실행 경로 설계는 A07, 운영은 과거 운영 페이지에 연결. 자동 수집·Obsidian·LLM 연결 완료 근거가 아니다. 당시 ‘현재 설명’ 표현과 현행 위키의 과거 자료 설명 역할을 구분한다. |
| V01 | [automation_validation](../../raw/docs/03_verification/automation_validation.md) · 실제 결과, 수행한 시험, 상대경로 기준 재검증 | log/automation_validation_history.md: 2026-10-27 시험과 결과 | 초기 18건·최종 24건, 정적 교차 검토·별도 QA를 구분. H05와 동일 시험은 중복 서술하지 않고 증거를 모은다. |
| V02 | 같은 원문 · 설치와 검증을 구분, 미완료와 다음 검증 | 시험 판정의 한계는 operations/historical_automation.md, 당시 미완료 상태는 V01에 인접 배치 | 재시작 전 목록을 현재 업무로 승계하지 않는다. 당시 절대경로 우회와 현행 상대경로 우선 기준, 설치·실행·전체 완주의 차이를 보존한다. |
| L01 | [HTML 점검 자동화 리뷰](../../raw/review_docs/HTML_점검_자동화_리뷰.md) · 본문 전체(소제목 없음) | 기존 log 유지: 2026-10-15 1회 점검 결과; 점검 조건은 M04에 연결 | 당시 링크 4·목차 3·ID 3, exit 0 기록. 시간·토큰 절감 및 오류 감소는 입증되지 않았고 구조 검사는 화면·내용 검토를 대체하지 않는다. |
| L02 | [프로토타입 구축 이력](../../raw/docs/04_records/prototype_build_history_2026-11-04.md) · 요청과 결정, 이 절 작성 시 확인된 작업 | 기존 log 유지: 당시 구축과 결정 기록; 확인된 선택 이유만 기존 log의 선택 이유 설명 | 개선 원본을 prototype으로 옮긴다는 서술은 최신 인계에서 정정됐다. 폐기된 주장을 현행 구조로 합성하지 않는다. |
| L03 | 같은 원문 · 통합 검증과 남은 작업, 마스터 통합 결과 — 배치 전, 최종 배치·검증 | 기존 log 유지: 구축·시험·배치 순서 | 24+13+8 모의 통과·symlink 1개 제외와 실제 모델·전체 루프·GUI 미검증을 구분. 현재 8개 업무의 원장은 최신 인계이며 이 표에 복제하지 않는다. |

## 5. 긴 관리 이력의 주제 연결

원문은 [2026-10-13~11-02 관리 이력](../../raw/docs/04_records/management_history_2026-10-13_2026-11-02.md)이다. 날짜별 이력은 기존 log에 유지하고 아래 주제 설명에 필요한 절만 근거로 연결한다. 이 표는 날짜·주제군 수준의 탐색 정보다. 상세 설명과 근거는 재구성한 관리 이력에 있으며, 과거 시험을 이번에 다시 실행한 것은 아니다.

| ID | 원문 날짜·절 | 연결할 주제·분류 | 보존할 조건 |
| --- | --- | --- | --- |
| H01 | 10-13 초기 운영 기준 수립 · 요청과 목적, 확정한 사항, 수행 내역 | 실제 발생은 기존 log, PM·디렉터·조언자 및 반영 경계의 선택 이유는 기존 log의 선택 이유 설명 | 현행 권한의 원본은 루트 AGENTS다. 과거 기록을 새 행동 규칙으로 복제하지 않는다. |
| H02 | 10-14 Library 전체 이전 및 Git 관리; 10-15 Git 운영·가이드·공통 스킬·PC 확인·점검 자동화 관련 절 | 이관·작성·확인 사건은 log, 스킬의 제공 조건은 features 및 공유 원본 연결, 점검은 M04·L01 | PC 경로·설치·원격 확인은 당시 사실. Git 실행 권한과 가이드 제작 기록은 구분한다. |
| H03 | 10-16 PC 이동 후 작업 재개, 공유 스킬 저장·검증·보고, 다른 프로젝트 적용, 전체 프로젝트 프로세스·공통 구조 정리 | 실행 시점은 log, 절차는 M03·M05 및 공통 작업 흐름 참조 | 프로젝트별 원본·보류·권한을 유지. 개인 설치와 공유 원본은 별개다. |
| H04 | 10-19 누락 내용 보완·스킬 동작 확인·문서 최적화 위험 검토 · 1~4 | 당시 설치·검토는 log, 자동 설치·갱신 구상은 제안 기록으로 보존 | 제안·미구현을 채택 결정이나 제공 기능으로 승격하지 않는다. 다른 프로젝트의 현재 상태는 그 원본에서 확인한다. |
| H05 | 10-27 자동화 기반 구현·설치; 상대경로 우선 기준 변경·재검증; 재시작 후 검증·Claude 운영 폴더 분리 | 시험 사건은 V01과 합성, 선택 이유는 근거 확인 후 기존 log의 선택 이유 설명, 절차는 operations | 설치·로컬 시험·실제 실행·전체 자동화 완료를 구분. 이전 권한 문제나 재시작 전 미완료가 현재도 같다고 추정하지 않는다. |
| H06 | 10-27 공통 진입점·herdr 연결 검증 완료 범위와 Hermes 로그인 중단 | 제공 기능은 E01, 연결 구조는 E04~E06, 당시 사건·사용자 보고는 log | herdr 사용자 확인과 직접 검증을 구분. Hermes 중단은 후속 절과 시점 대조한다. |
| H07 | 10-28 Task 세션·process_debug 반영; process_debug On과 다음 세션 인계 시험 | 역할·세션 구조는 A05·E04, 당시 실행·관찰은 log | process_debug 현행 의무 종료. 당시 다음 시험은 새 실행 요청이 아니다. |
| H08 | 10-28 herdr 직접 실행·3개 AI 연결 확인과 다음 시험 인계 | 역할·세션·Hermes 설명은 A01·A12·E04~E06, 연결 관측은 log | 사용자 전달과 직접 관측을 구분. 구독·불명확 재전송 조건, 가이드·자료 전송 보류, 전체 완주 미검증 보존. |
| H09 | 11-02 Codex 시작기 경로 개선; 3번 역할 분담 시험과 wiki 초안 검토 | 경로 선택 구조는 E05, 모의·실제 시험과 결함은 log | CheckOnly와 모의 시험은 창 제어 증거가 아니다. 단일 응답 성공과 대화창 연동, 당시 파일 저장·Obsidian 확인 미실행을 구분한다. |

각 문서에 있는 변경 이력은 기존 문서 식별자·버전의 근거로 유지한다. 변경 이력만으로 본문의 기능이 구현·검증됐다고 판단하지 않는다. 원문에 선택 이유가 없는 내용을 decisions로 새로 확정하지 않는다.

## 실제 설명 페이지와 반영 범위

| 분류 ID | 결과물 | 편집 범위 |
| --- | --- | --- |
| A01~A03 | [역할 관계](../architecture/roles.md), [과거 자동화 운영](../operations/historical_automation.md) | 역할 관계와 인계·검증 조건 분리 |
| A04~A09 | [자동화 구조](../architecture/automation_workflow.md), [과거 자동화 운영](../operations/historical_automation.md), [과거 도구 기능](../features/historical_workflow_tools.md) | 단계·상태·기록 구조, 운영 조건, 제공 기능 분리 |
| A10~A12 | [Hermes 구조](../architecture/hermes_worker.md), [과거 자동화 운영](../operations/historical_automation.md), [과거 도구 기능](../features/historical_workflow_tools.md), [검증 이력](../log/automation_validation_history.md) | 입력·회수 구조와 비용·재전송 조건, 실제 호출 근거 분리 |
| E01~E03 | [진입점 기능](../features/project_entry.md), [진입점 구조](../architecture/project_entry.md) | 생성·선택 범위와 구성 관계, 미연결 제한 |
| E04~E06 | [세션 구조](../architecture/agent_session_lifecycle.md), [과거 세션 운영](../operations/historical_sessions.md) | 창·ID·복원 구조와 판정 조건 분리 |
| M01~M03,M05 | [관리 워크플로](../operations/management_workflow.md), [과거 점검 운영](../operations/historical_document_checks.md), [이전 경로 안내](../architecture/management_workflow.md) | 현행 기준 진입점, 종료된 의무·보관 명령 분리 및 원문 이력 보존 |
| M04 | [문서 점검 기능](../features/document_checks.md), [과거 점검 운영](../operations/historical_document_checks.md) | 검사 제공 범위와 과거 실행 조건·한계 |
| F01~F02 | [요구사항 양식](../features/신규_개발_프로젝트_요구사항_작성양식.md) | 미작성 입력 양식 보존, 목적·조건·기획 연결 |
| D01 | [ADR-0001](../decisions/0001-workflow-records.md) | 당시 채택 이유·영향·현행 범위 구분 |
| V01~V02 | [검증 이력](../log/automation_validation_history.md), [과거 검증 판정](../operations/automation_validation.md) | 날짜별 결과와 판정 조건 분리 |
| L01 | [HTML 점검 리뷰](../log/HTML_점검_자동화_리뷰.md) | 1회 시험과 미입증 효과 구분 |
| L02~L03 | [프로토타입 구축 이력](../log/prototype_build_history_2026-11-04.md) | 구축·배치·시험·개선 위치 정정 |
| H01~H09 | [관리 이력](../log/management_history_2026-10-13_2026-11-02.md), [검증 이력](../log/automation_validation_history.md) | 날짜별 변화와 선택 이유, 시험 수치·사용자 보고·직접 검증 구분 |

기존 문서 식별자와 이력은 본문 또는 raw 원문 링크로 보존했다. architecture의 관리 워크플로 옛 경로는 운영 문서 안내로 유지한다. 다섯 구조 문서는 목표 설계·당시 구현 관계를 Mermaid와 본문으로 설명하며 실제 연결 성공을 주장하지 않는다.

## 검증 범위

형식·로컬 경로 검사는 내용 검토와 분리한다. 최종 결과와 담당별 실행 근거는 [날짜 보고](../../report_docs/2026-11-05.md)에 남긴다. 과거 시험의 재실행·전체 자동화 완주·외부 서비스의 현재 상태·Mermaid 화면 렌더링은 문서 재구성 완료와 구별한다. raw 보관본을 수정·이동·삭제하지 않으며, 기존 8개 프로토타입 업무와 가이드·자료 전송 보류를 재개하지 않는다.
