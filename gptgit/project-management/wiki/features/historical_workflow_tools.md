---
type: concept
tags: [tools, historical, workflow]
created: 2026-11-05
updated: 2026-11-05
confidence: medium
source_status: reviewed
status: historical
sources: [../../raw/docs/02_design/automation_workflow.md, ../../raw/docs/02_design/hermes_worker.md, ../../raw/docs/03_verification/automation_validation.md, ../../AGENTS.md]
---
# 과거 워크플로 도구의 제공 범위

과거 로컬 도구가 무엇을 다루도록 구현됐는지 설명한다. 보관된 소스의 존재나 당시 시험 결과는 현재 실행 가능성·자동화 운영 승인을 뜻하지 않는다. [근거: 현행 규칙](../../AGENTS.md#작업과-과거-자동화-자료)

## 상태·증거 관리

`workflow.py`는 승인 명세를 입력받아 단계의 시작·제출·검토·완료·차단·재개·재평가와 재작업 상태를 관리하도록 만들었다. 상태·보고는 기록된 실행의 단계와 문제를 조회하고 timeline은 사건 색인을 재구성한다. operation ID는 중복 요청을 식별하며 같은 ID에 다른 입력을 섞지 않는다. 재작업은 후속 승인을 무효화하되 과거 제출과 검토·증거의 해시 스냅샷을 보존한다. [근거: 로컬 상태 도구](../../raw/docs/02_design/automation_workflow.md#7-로컬-상태-도구)

도구는 입력 형식, 파일 존재·해시, 상태 전이를 검사하지만 검토자 신원이나 진실한 시험 수행을 인증하지 않는다. 명시 제출된 JSON만 원문으로 다루며 채팅 전체를 자동 수집하지 않는다. 증거는 파일당 20MB 이하였고 알려진 인증 문자열을 거절했지만 이미지나 임의 형식 비밀까지 탐지하지 못한다. 종료 코드 0은 명령 처리 성공, 1은 조회된 증거 무결성 문제, 2는 입력·상태·파일 오류였으며 0 자체는 전체 작업 완료가 아니다. [근거: 상태 도구의 범위와 한계](../../raw/docs/02_design/automation_workflow.md#7-로컬-상태-도구)

## 기록 초안 전달과 점검

제한형 Hermes worker는 명시 packet과 허용 원문 일부로 기록 요약 또는 wiki 초안을 요청하고 반환과 증거를 저장하는 범위였다. 기본 source가 비어 있으면 문서 자동 전송은 없고, 입력·결과·세션을 마스터가 대조해야 한다. 중복 ID와 구독 확인 실패는 차단하며 불명확한 호출을 자동 재전송하지 않는다. 도구 목록 제한과 빈 디렉터리는 OS 격리가 아니다. [근거: Hermes 입력과 결과](../../raw/docs/02_design/hermes_worker.md#결과중단재전송)

당시 process_debug는 제공된 기록으로 세션·문서 범위·사용량의 추가 요약을 돕는 보조 기능이었다. 전체 대화나 다른 세션의 자동 관찰, 실제 구독 차감량 측정을 뜻하지 않았다. **그 사용 의무는 종료**됐다. 로컬 상태 도구의 모의 시험, Hermes의 합성 실제 호출, 독립 QA와 전체 완주는 서로 다르다. 당시 연결과 결과의 구체적 범위는 [검증 원문](../../raw/docs/03_verification/automation_validation.md)과 [Hermes 검증](../../raw/docs/02_design/hermes_worker.md#검증-범위)을 참조한다.
