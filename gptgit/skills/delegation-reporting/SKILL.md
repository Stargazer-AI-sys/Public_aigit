---
name: delegation-reporting
description: Coordinate authorized agents through Herdr worker tabs with explicit role/model checks, minimal task handoffs, result collection, and project-owned reporting. Use for delegated work in gptgit; does not authorize new work or impose one project's roles or report paths on another.
---

# 공통 담당 위임과 결과 회수

> 버전 0.4 · 2026-11-06 · 기존 관리 전용 0.3을 공통화

정책은 [공통 AGENTS](../../AGENTS.md), 역할·권한·기록은 대상 프로젝트 README·AGENTS와 로컬 위임 규칙을 따른다. 공유 스킬의 위치를 실제 작업 cwd로 사용하지 않는다. 관리 프로젝트의 날짜 보고 승인을 다른 프로젝트로 확대하지 않는다. 개인 설치·앱 등록은 별도이며 이 원본의 연결로 설치됐다고 주장하지 않는다.

## 실행 순서

1. 승인 범위·Task·입출력·완료 조건·파일 소유권·프로젝트별 기록 위치를 정한다. 기획/개발/검토/QA/문서화의 기존 제공자 계약을 유지한다.
2. herdr 내부인지 확인하고 설치된 `herdr --skill`을 읽는다. 실제 탭·pane·cwd·세션을 확인한다. **마스터 대화 탭을 분할하지 않는다. 담당용 새 탭을 생성하고 그 안에서만 pane을 분할한다.** 같은 작업 묶음의 담당 탭은 확인 후 공유할 수 있다. 작업 묶음이 바뀌면 새 담당 탭을 준비한다. 사용자 요청 없이 포커스를 옮기거나 기존 창·서버를 종료하지 않는다.
3. 하위 Codex는 Luna 또는 Terra의 정확한 ID를 명시한다. Astra는 마스터만 사용한다. 단순 작업은 Luna, 복잡한 작업·독립 검토는 Terra가 기본이다. 허용 목록은 [검사 코드](../../tools/check_agent_model.py)에 구현되어 있으며 모델 공급 여부는 별도 확인한다. 임의 alias·자동 fallback·모델 생략을 허용하지 않는다.
4. 프로젝트 시작 도구로 검사 후 담당을 시작한다. 관리 프로젝트는 `tools/start_agent.ps1`, 프로토타입은 `tools/dispatch_task.py`와 `tools/start_role.ps1`를 쓴다. 지원 범위와 CheckOnly·훅은 [실행 참고](references/runtime.md)를 읽는다. 범용 시작 도구로 프로젝트 고유 packet·권한 검사를 우회하지 않는다.
5. **시작 성공은 Task 전달 승인이 아니다.** CLI 상태 화면에서 요청/실제 모델·권한을 확인하고 pane 및 세션 ID를 연결한 뒤 최소 Task를 전달한다. 재개·기존 세션 재사용·모델 변경 뒤에도 재확인한다. 모델 미확인·불일치는 전달 차단이다. 검사 코드가 사용자 예외를 자동 승인하지 않는다.
6. 독립 작업은 병렬 처리하되 같은 파일을 동시에 수정하지 않는다. 검토자는 제작 원본을 읽기 전용으로 확인한다. 마스터가 진행 확인·회수·수정 반환·통합을 맡고 최종 증거를 대조한다. agent started, submitted, working, response recovered, accepted를 구분한다. 불명확 전달은 실제 상태를 확인하기 전 재전송하지 않는다.
7. 터미널 결과는 완료 후 recent-unwrapped로 회수한다. 충분한 줄을 읽어도 잘린 경우에만 대상 프로젝트가 허용한 임시/결과 경로 한 파일로 반환하도록 한다. 보고에는 요청/실제 모델·확인 방법·tab/pane/session·입출력·검사·미확인·예외 승인 범위를 남긴다. 기록 위치·갱신 조건은 프로젝트 규칙을 따른다.

herdr 사용 불가 시 내장 서브에이전트로 임의 대체하지 않고 원인·대안과 방식 변경을 확인한다. 구독 범위·읽기 전용 QA·자동 승인 심사·보류·Git 권한을 유지한다. 승인 심사 거절을 우회하지 않는다. 일반 Codex는 `--approve-for-me`, 독립 QA는 프로젝트의 read-only 조건을 함께 지킨다.

## 모델 제한과 훅의 경계

시작 도구는 잘못된 모델을 실행 전에 거부한다. 보조 PreToolUse 훅은 지원되는 직접 실행 명령을 검사한다. shell 별칭·동적 코드·인코딩·다른 실행 경로까지 완전히 통제하는 보안 경계는 아니다. PreModelRequest는 진단용이며 차단 수단이 아니다. 훅 등록, 사용자 신뢰, 실제 이벤트 호출·차단 시험을 각각 구분하며 비활성/미신뢰 상태를 정상 작동으로 보고하지 않는다.

검증: 모델 허용/거부·미지정·프로젝트 경계·새 탭·Task 미전달·읽기 전용 유지·훅 허용/거부·실패 경계를 검사한다. 스킬 메타데이터·링크 검사와 실제 모델 호출/전체 프로세스 시험은 별개다.
