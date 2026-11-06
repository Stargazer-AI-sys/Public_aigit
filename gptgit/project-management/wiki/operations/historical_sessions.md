---
type: operation
tags: [sessions, historical]
created: 2026-11-05
updated: 2026-11-05
confidence: medium
source_status: reviewed
status: historical
sources: [../../raw/docs/02_design/agent_session_lifecycle.md, ../../raw/docs/02_design/project_entry.md, ../../docs/04_records/management_log.md]
---
# 과거 세션 판정과 요청 처리

이 문서는 당시 시작기·수신기 설계의 조건을 설명하며 현재 실행 지시가 아니다. 현재 경로·설치·인증·호환 여부는 별도 확인이 필요하다. [근거: 세션 수명주기 원문](../../raw/docs/02_design/agent_session_lifecycle.md)

## 창·대화·복원의 구분

같은 프로젝트와 역할의 창 하나가 확인되면 idle·done·working·blocked라도 창을 유지하고 명령을 자동 전송하지 않도록 했다. 경로·상태가 불명확하거나 중복 창이 있으면 차단한다. 창이 없고 확인된 저장 대화가 있을 때에만 명시적 재개와 정확한 ID를 사용한다. 저장 ID가 없으면 인증 후 빈 셸에서 새 대화를 시작하는 설계였다. 현재 UUID와 저장 ID가 충돌하면 차단하고, 없는 UUID는 불일치가 아니라 미확인이다. [근거: 시작 판정](../../raw/docs/02_design/agent_session_lifecycle.md#시작-판정)

창의 유지 가능성, 현재 ID 일치, 실제 복원 시험은 독립된 확인이다. 저장 기록만 보는 기본 조회는 현재 창 확인이 아니며 `CheckOnly`도 실행·복원 시험이 아니다. 재개 실패 시 새 대화로 자동 대체하지 않고, `--last`처럼 최근 대화를 추측하지 않는다. 기록 저장은 확인된 프로젝트·역할·실제 ID의 근거를 요구하고 잠금과 원자적 교체로 이전 기록을 보존했다. 시작기 잠금은 수동 CLI까지 통제하지 않는다. [근거: 창 유지와 ID 검증](../../raw/docs/02_design/agent_session_lifecycle.md#창-유지와-대화-id-검증의-분리)

## 요청·수신과 불명확 처리

화면은 요청 파일을 저장하고 관리 세션을 열지만 Desktop에서 내부 상태를 위조하거나 기존 AI 창에 명령을 보내지 않는다. 수신기는 별도 herdr 내부 셸에서 실행되어야 하고 기본은 기존 창 유지다. 누락 역할 시작은 별도 옵션과 인증·재확인 조건이 필요하며, 빈 PowerShell 전경 프로세스가 확인되지 않으면 차단한다. 요청 처리 완료는 대화 복원이나 자동화 완료가 아니다. [근거: 요청과 내부 처리](../../raw/docs/02_design/agent_session_lifecycle.md#시작-화면의-요청과-내부-처리)

실행 전 전달 이력과 배타 잠금으로 중복을 줄이고, 시작 전 실패는 blocked, 전달 중 결과를 확인하지 못하면 uncertain으로 남긴다. uncertain·processing 요청은 실제 창과 전달 여부를 확인하지 않고 교체하거나 재전송하지 않는다. 타임아웃이나 오류가 나도 이미 만든 창을 임의 종료하지 않는다. 상태 파일의 최근 응답은 프로세스 생존이나 복원 성공을 보증하지 않는다. [근거: 자동 요청 수신](../../raw/docs/02_design/agent_session_lifecycle.md#자동-요청-수신)

## 경로와 당시 검증

당시 Codex 선택은 명시 경로, 독립 CLI, 앱 후보 순이었다. 잘못된 명시 경로를 조용히 대체하지 않고 버전 오류 시 멈춘다. 로그인은 명시 요청, NoDaemon은 선택 시에만 사용하며 실패 후 자동 재시도하지 않는다. herdr 0.9.5/protocol 22에 한정된 확인을 현재 다른 버전의 호환성으로 확대하지 않는다. [근거: Codex 업데이트·PC 변경](../../raw/docs/02_design/agent_session_lifecycle.md#codex-업데이트pc-변경-시-시작기--2026-11-02)

모의 검사는 실제 herdr 창 제어·모델 호출이 아니었다. 일부 Live·ReuseOnly 결과는 사용자가 전달했으며 원문 출력은 제공되지 않았다. 당시 대화 ID와 복원은 미확인이고 실제 수신기 전체 경로·창 생성·재개·폴더 이동 후 연결은 별도 검증이 남았다. 현재 창이나 서버를 이 설명만으로 종료하거나 재시작하지 않는다. [근거: 검증과 남은 범위](../../raw/docs/02_design/agent_session_lifecycle.md#검증과-남은-범위)
