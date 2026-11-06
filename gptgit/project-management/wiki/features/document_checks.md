---
type: concept
tags: [document-checks, historical]
created: 2026-11-05
updated: 2026-11-05
confidence: medium
source_status: reviewed
status: historical
sources: [../../raw/docs/02_design/management_workflow.md, ../../raw/tools/check_project_docs.ps1, ../../raw/tools/test_check_project_docs.ps1]
---
# 과거 문서 구조 점검 도구의 제공 범위

과거 점검 도구는 지정한 Markdown과 HTML을 읽어 일반적인 상대 파일·폴더 링크의 존재를 확인하고, HTML에서는 같은 문서의 목차 대상과 중복 ID를 점검하도록 만들었다. 원문이나 보고서를 저장하지 않는 읽기 전용 검사이며 JSON 결과에 문제와 검사 제외 사유·실제 검사 수를 구분했다. 기본 문서 목록은 당시 경로 기준이므로 문서 이동 후에도 그대로 유효하다고 가정할 수 없다. PowerShell 7과 접근 가능한 입력이 당시 실행 조건이었다. [근거: 과거 수동 문서 점검 5.1~5.2](../../raw/docs/02_design/management_workflow.md#51-현재-구현과-실행), [보관 소스](../../raw/tools/check_project_docs.ps1)

지원 범위는 전체 문서의 의미 검증이 아니다. Markdown 제목 연결·참조형이나 복잡한 링크, 다른 문서 내부 ID, 외부 URL·절대경로·이미지·동적 링크 등은 제외하거나 일부만 검사했다. HTML의 코드 예시·주석과 `base href`가 있는 문서도 해당 제외 조건을 확인해야 한다. 같은 문서의 HTML ID 검사 통과는 화면 가독성·내용의 정확성·명령의 실제 동작·원격 최신성을 보증하지 않는다. [근거: HTML 지원과 검사 제외](../../raw/docs/02_design/management_workflow.md#52-html-지원과-가벼운-운영)

결과 코드 0은 검사한 범위에 문제를 발견하지 못했다는 뜻이고 1은 발견된 문제, 2는 실행 조건 오류다. 실행 정책이나 도구 부재로 시작하지 못한 경우 결과 코드의 정상 판정과 구분한다. 원문에는 당시 12개 사례와 실제 가이드의 구조 확인이 기록되어 있으나, 이는 해당 시점의 결과이며 이번에 재실행하거나 현재 환경의 기능을 확인한 것은 아니다. [근거: 당시 검증과 유지 기준](../../raw/docs/02_design/management_workflow.md#53-검증-결과와-유지-기준), [보관된 시험 소스](../../raw/tools/test_check_project_docs.ps1)

수정한 가이드 중심의 점검 범위와 차단 시 처리, 재검사 조건은 [과거 문서 점검 운영](../operations/historical_document_checks.md)에서 다룬다. 정기 예약은 당시 결정되지 않았으며 이 설명이 예약·설치·Git·외부 서비스 실행을 승인하지 않는다. 공통 스킬의 공유 원본과 개인 설치본도 별도다. [근거: 스킬과 예약 조건](../../raw/docs/02_design/management_workflow.md#7-예약-점검과-효과-확인)
