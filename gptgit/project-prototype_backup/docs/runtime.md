# 프로젝트 실행 환경

> 버전 0.2 | 2026-11-04

## 독립 실행기

config/runtime.example.json은 설정 양식이다. 실제 환경은 config/runtime.local.json에 이 프로젝트 전용 설치 또는 시스템 공용 CLI 위치를 지정한다. 다른 프로젝트 내부 실행 파일·설정·인증·세션을 참조하지 않는다. local 설정에는 실행 경로만 저장하고 인증값은 넣지 않는다. 실행기가 없으면 해당 연결을 준비되지 않은 상태로 보고하며 설치·로그인을 완료로 가정하지 않는다.

기본 예시는 Claude/herdr를 .local/bin 아래 프로젝트 전용 설치에서 찾고 Codex/Python/PowerShell은 공용 명령을 사용한다. 현재 설치 여부는 마스터가 실행 전에 확인한다. PATH에서 찾은 공용 명령도 실제 위치가 다른 프로젝트 전용 설치이면 사용하지 않는다.

## 시작과 권한

마스터가 tools/start_role.ps1로 역할을 시작한다. master 외 역할에는 검증된 packet이 필요하다. -CheckOnly는 인수 구성 검사이며 인증·모델을 호출하지 않는다. 실제 역할 시작은 herdr 내부에서 수행한다.

Codex는 on-request＋auto_review와 workspace-write를 사용한다. QA는 read-only이며 test_write_scope의 .local/qa/<task_id>/ 출력만 필요한 권한 심사를 거쳐 쓴다. 원본 수정은 금지한다. auto_review는 승인 검토 담당을 바꾸며 조직 정책·샌드박스를 우회하지 않는다. [공식 설명](https://learn.chatgpt.com/docs/sandboxing/auto-review).

Claude는 이 프로젝트의 CLAUDE.md·명시 Task를 사용한다. 기획 검토는 Read/Grep/Glob만 제공한다. auto 권한 모드와 마스터의 산출물 승인은 구분한다. 구독 판정이 null이면 차단하며 API로 전환하지 않는다. 훅 설정과 herdr 감지의 호환은 실제 연결에서 확인한다.

## 전달과 결과

tools/dispatch_task.py는 기본적으로 입력 검사만 한다. 마스터가 승인 범위와 소유권을 확인한 뒤 --apply로 새 pane을 생성한다. 호출 pane의 cwd·새 pane의 실제 ID·프로세스를 대조하고 .local/dispatch의 영수증으로 동일 Task 중복 시작을 막는다.

submitted_unverified는 시작 명령 접수일 뿐 성공이 아니다. 마스터가 herdr agent get/read로 세션·응답을 확인하고 상태 원장에 근거를 연결한다. 자동 결과 수집·창 재사용 판단은 미구현이다. 불명확 응답은 실제 요청 도달 여부를 확인하기 전 재전송하지 않는다.

docs/workflows/<run_id>가 실행 원장이다. packet의 provider는 호출 adapter(codex/claude/hermes), 원장의 provider는 실제 모델 제공자다. Codex는 gpt로 대응하고 Hermes의 모델 제공자는 관측값을 기록한다. Hermes adapter는 미구현이며 호출 성공을 가정하지 않는다.
