---
type: concept
tags: [project-entry, template]
created: 2026-11-05
updated: 2026-11-05
confidence: medium
source_status: reviewed
status: historical
sources: [../../raw/docs/02_design/project_entry.md, ../../raw/templates/project-v1/README.md, ../../raw/docs/02_design/agent_session_lifecycle.md, ../../docs/04_records/management_log.md]
---
# 과거 프로젝트 진입점과 기본 틀의 제공 범위

과거 진입점은 Windows 화면에서 새 프로젝트 개설, 기존 프로젝트 선택, 관리 환경 열기를 구분하도록 만들었다. 이름·목적·상위 위치를 확인하고 사용자가 생성할 때만 새 폴더를 만들며 같은 이름의 기존 폴더는 덮어쓰지 않는 범위였다. 기존 폴더 선택은 그 프로젝트의 문서·규칙을 바꾸거나 기본 틀을 주입하지 않았다. 관리 환경을 여는 것만으로 시험·설치·모델 호출이 시작되는 구조도 아니었다. 이 설명은 당시 구현 범위이며 현재 이 PC의 동작을 확인한 결과는 아니다. [근거: 진입점의 목적과 구현된 흐름](../../raw/docs/02_design/project_entry.md#구현된-흐름)

기본 틀 1.0은 새 프로젝트의 README, 작업 규칙, 목적·요구사항 문서, 작업기록과 개설 메타데이터를 마련하도록 설계됐다. 보관된 README 틀도 각 문서의 책임을 나누고, 공통 틀을 개선해도 개별 프로젝트를 자동으로 덮어쓰지 않는다고 명시한다. 관리 프로젝트의 시험·보류·인증·대화 이력을 복제하지 않고 전문 구조는 실제 요구에 따라 추가한다. 사용자가 다른 위치를 선택하면 그 위치의 적용 규칙을 따로 확인해야 한다. [근거: 공통 기본 틀](../../raw/docs/02_design/project_entry.md#공통-기본-틀), [보관된 README 틀](../../raw/templates/project-v1/README.md)

초기 목적 입력과 개설은 기획 완료나 제작 승인에 해당하지 않는다. 당시 관리 AI 연결·재개 요청 기능은 화면의 요청 저장과 herdr 내부 수신·판정을 구분했으며, 요청 저장만으로 내부 수신기가 시작되지는 않았다. 신규 프로젝트의 AI 자동 연결·닫힌 탭 복원은 별도 확인 대상이었다. 빈 대화 연결 정보나 경로 해시는 실제 복원이나 보안 격리를 뜻하지 않는다. 원문의 초기 미연결 설명과 후속 구현·모의 시험은 시점이 다르므로, 실제 창 생성과 복원·인증은 별도 근거로 판정해야 한다. [근거: 미연결과 제한](../../raw/docs/02_design/project_entry.md#아직-연결하지-않은-기능), [후속 세션 설계](../../raw/docs/02_design/agent_session_lifecycle.md#검증과-남은-범위)

관리 프로젝트는 프로세스 개선 원본, project-prototype은 독립적으로 적용하는 시험 프로젝트라는 역할 정정이 이후 인계에서 우선한다. 보류된 가이드 제작·자료 전송이나 자동화 운영 재개의 허가는 이 기능 설명에 포함되지 않는다. [근거: 최신 인계](../../docs/04_records/management_log.md#확정된-역할)
