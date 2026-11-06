---
type: operation
tags: [documents, validation, historical]
created: 2026-11-05
updated: 2026-11-05
confidence: medium
source_status: reviewed
status: historical
sources:
  - ../../raw/docs/02_design/management_workflow.md
  - ../../raw/docs/03_verification/automation_validation.md
  - ../../raw/docs/04_records/management_history_2026-10-13_2026-11-02.md
  - ../../raw/tools/check_project_docs.ps1
  - ../../raw/tools/test_check_project_docs.ps1
  - ../../AGENTS.md
  - ../AGENTS.md
  - AGENTS.md
  - ../index/content_classification.md
  - ../../skills/wiki-editor/references/schema.md
classification_ids: [M04, M05]
page_version: 0.1
---

# 과거 문서 구조 점검 운영

이 페이지는 2026년 10월 문서 점검 운영안과 도구의 검사 경계를 보존한다. 도구·시험은 raw에 보관되어 있으므로 설명을 현재 실행 안내로 사용하지 않는다. 현재의 일반 관리 흐름은 [프로젝트 관리 워크플로](management_workflow.md), 기능 설명은 [문서 점검 기능](../features/document_checks.md)을 따른다.

## 5절 — 지정 문서의 수동 점검

원문은 가이드 작성·수정 뒤 변경한 HTML 등 지정 문서만 로컬에서 한 번 확인하고, 오류 수정 후 영향받은 문서만 재검사하도록 제안했다. 기본 대상은 프로젝트 문서였고 HTML 전체 자동 추가나 프로젝트 전체 재귀 검색은 하지 않았다. 파일 이동·이름 변경처럼 영향이 넓은 경우에만 관련 문서로 검사 범위를 넓히도록 했다. 이는 당시 절차이지 현행 실행 요청이 아니다. [원문 5절](../../raw/docs/02_design/management_workflow.md#5-수동-문서-점검)

당시 실행 조건은 PowerShell 7과 프로젝트 루트 기준 상대경로였다. 상대경로 실패는 작업 위치·파일 존재·경로 표기·실행기 검색·PowerShell 버전·실행 정책을 확인해 원인을 해결하고 같은 상대경로로 다시 확인하도록 했다. 절대경로로 바꾸거나 임시폴더·실행 정책을 완화해 실패를 우회하지 않았다. 권한 부족은 필요한 대상과 목적을 설명해 권한을 요청하도록 했다. 현재 일반 실행 원칙은 [루트 AGENTS](../../AGENTS.md)를 따른다.

도구 또는 자료를 사용할 수 없거나 실행 정책에 막힐 때 자동 설치·정책 변경·우회를 하지 않고 미점검 사유와 범위를 보고하도록 했다. 도구는 읽기 전용이며 원본 자동 수정·네트워크·Git·유료 API 실행을 하지 않았다. 검사 통과는 지원하는 구조 항목에만 해당하고 내용 정확성·최신성·명령 적절성·화면 품질·실제 동작 검증을 대신하지 않는다. [원문 검증·제외 범위](../../raw/docs/02_design/management_workflow.md#53-검증-결과와-유지-기준)

## 공유 원본과 개인 설치본

당시 스킬 기준은 공유 원본과 PC별 개인 설치본을 구분했다. 공유 원본을 갱신해도 개인 설치본·앱 등록이 자동 갱신되는 것은 아니며, 저장소 pull만으로 개인 설치가 업데이트된다고 간주하지 않았다. 설치·자동 배포는 별도 요청이 필요한 범위였다. 현재 공통 스킬 절차와 권한 경계는 [루트 AGENTS의 사용자 가이드 작성 기준](../../AGENTS.md#사용자-가이드-작성)에 둔다. 이 요약은 당시 설명을 보존하며 설치 절차를 새로 안내하지 않는다. [원문 6절](../../raw/docs/02_design/management_workflow.md#6-스킬-원본과-pc-설치)

## 7절 — 예약 점검은 추후 검토

원문은 수동 점검을 먼저 확인한 뒤 사용자가 정하는 시점에 예약 범위를 검토하도록 했다. 예약 전에는 대상 프로젝트, 시각, 실행 PC와 로컬 접근 조건을 정하고 읽기 전용 점검부터 고려한다. 자동 파일 반영·Git 동기화·유료 호출은 당시 제안에도 포함되지 않았다. 이 문서는 원문에 적힌 추후 조건만 보존한다. 현재 예약의 실제 생성 여부는 확인하지 않았다. [원문 7절](../../raw/docs/02_design/management_workflow.md#7-예약-점검과-효과-확인)

## 관련 근거

- [보관된 검사기](../../raw/tools/check_project_docs.ps1)와 [시험 코드](../../raw/tools/test_check_project_docs.ps1)
- [당시 검증 결과](../../raw/docs/03_verification/automation_validation.md)
- [과거 관리 이력](../../raw/docs/04_records/management_history_2026-10-13_2026-11-02.md)
