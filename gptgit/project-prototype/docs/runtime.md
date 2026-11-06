# 프로젝트 실행 환경

> 버전 0.4 | 2026-11-06

## 독립 실행기

config/runtime.example.json은 설정 양식이다. 실제 환경은 config/runtime.local.json에 이 프로젝트 전용 설치 또는 시스템 공용 CLI 위치를 지정한다. 다른 프로젝트 내부 실행 파일·설정·인증·세션을 참조하지 않는다. local 설정에는 실행 경로만 저장하고 인증값은 넣지 않는다. 실행기가 없으면 해당 연결을 준비되지 않은 상태로 보고하며 설치·로그인을 완료로 가정하지 않는다.

기본 예시는 Claude/herdr를 .local/bin 아래 프로젝트 전용 설치에서 찾고 Codex/Python/PowerShell은 공용 명령을 사용한다. 현재 설치 여부는 마스터가 실행 전에 확인한다. PATH에서 찾은 공용 명령도 실제 위치가 다른 프로젝트 전용 설치이면 사용하지 않는다.

## 시작과 권한

마스터가 tools/start_role.ps1로 역할을 시작한다. master 외 역할에는 검증된 packet이 필요하다. `-Model` 또는 담당 packet의 `session.model`을 명시하며 둘 다 있으면 일치해야 한다. 마스터는 `-Model gpt-6-astra`를 지정한다. 공유 `../tools/check_agent_model.py`가 역할·제공자·모델을 검사하며 누락이나 실패는 시작을 차단한다. `-CheckOnly`는 packet·모델과 인수 구성을 검사하며 인증·모델을 호출하지 않는다. 실제 역할 시작은 herdr 내부에서 수행한다.

Codex는 on-request＋auto_review와 workspace-write를 사용한다. QA는 read-only이며 test_write_scope의 .local/qa/<task_id>/ 출력만 필요한 권한 심사를 거쳐 쓴다. 원본 수정은 금지한다. auto_review는 승인 검토 담당을 바꾸며 조직 정책·샌드박스를 우회하지 않는다. [공식 설명](https://learn.chatgpt.com/docs/sandboxing/auto-review).

Claude는 이 프로젝트의 CLAUDE.md와 마스터가 확인 후 전달하는 명시 Task를 사용한다. 기획 검토는 Read/Grep/Glob만 제공한다. auto 권한 모드와 마스터의 산출물 승인은 구분한다. 구독 판정이 null이면 차단하며 API로 전환하지 않는다. 훅 설정과 herdr 감지의 호환은 실제 연결에서 확인한다.

## 전달과 결과

tools/dispatch_task.py는 기본 검사와 실제 시작 모두에서 packet 구조와 `session.model`을 공유 검사기로 확인한다. 모델이 없거나 허용되지 않으면 탭을 만들지 않는다. 마스터가 승인 범위와 소유권을 확인한 뒤 --apply로 `tab create --no-focus`를 사용해 별도 새 탭의 root pane을 생성한다. 마스터 탭을 분할하지 않는다. 추가 pane이 필요하면 담당 탭 안에서 분할한다. 호출 workspace를 지정하고 호출 탭과 다른 반환 탭 ID, root pane cwd·실제 ID·프로세스를 대조한다. 탭 ID는 영수증에 기록하고 .local/dispatch의 영수증으로 동일 Task 중복 시작을 막는다.

시작기는 검증한 packet의 Task를 초기 프롬프트로 보내지 않고 대기 지시만 보낸다. 마스터는 새 세션의 실제 적용 모델과 권한을 확인한 뒤 승인된 packet 범위를 해당 담당에게 전달한다. 모델이 미확인·불일치하면 전달하지 않는다. `submitted_unverified`는 시작 명령 접수일 뿐 모델 확인이나 Task 전달 성공이 아니다. 마스터가 herdr agent get/read로 세션·응답을 확인하고 상태 원장에 근거를 연결한다. 자동 결과 수집·창 재사용 판단은 미구현이다. 불명확 응답은 실제 요청 도달 여부를 확인하기 전 재전송하지 않는다.

docs/workflows/<run_id>가 실행 원장이다. packet의 provider는 호출 adapter(codex/claude/hermes), 원장의 provider는 실제 모델 제공자다. Codex는 gpt로 대응하고 Hermes의 모델 제공자는 관측값을 기록한다. Hermes adapter는 미구현이며 호출 성공을 가정하지 않는다.


## 위키 검사 환경

위키 검사에는 프로젝트 전용 `.local/wiki-editor-venv` 또는 PyYAML이 있는 시스템 공용 Python을 사용한다. 다른 프로젝트 내부 환경을 실행 경로로 연결하지 않는다. 2026-11-06 이 PC에서 시스템 Python 3.14로 본 프로젝트의 가상환경을 만들고 PyYAML 6.0.3을 설치했다. `.local`은 Git 제외이며 다른 PC에서는 환경을 별도로 준비·확인한다.

프로젝트 루트에서 지정 지식 문서를 검사한다. README·AGENTS·색인은 스키마 적용 대상에서 제외하고 별도 링크 검사한다.

```powershell
.local/wiki-editor-venv/Scripts/python.exe skills/wiki-editor/scripts/check_wiki.py wiki/분류/대상.md
```

위 경로는 입력 예시이며 실제 존재하는 작성 문서를 지정한다. 검사기는 원문·실제 모델 연결·내용 품질·도식 렌더링을 보증하지 않는다. 제공된 회귀 시험은 다음과 같이 실행한다.

```powershell
.local/wiki-editor-venv/Scripts/python.exe skills/wiki-editor/scripts/test_check_wiki.py
```

일반 Codex 담당의 새 CLI는 `--approve-for-me`, 기존 세션은 `/permissions`에서 현재 설정을 확인한다. 프로젝트 시작기의 기존 on-request·auto_review·workspace-write와 실제 CLI 지원을 대조하며, QA의 read-only·명시 test_write_scope는 유지한다. 시작기 변경의 모의 시험과 실제 연결·인증 검증은 구분한다. 자동 심사 거절·정책 차단은 우회하지 않는다.

## 변경 이력

| 날짜 | 버전 | 내용 |
| --- | --- | --- |
| 2026-11-06 | 0.3 | 독립 위키 검사 환경과 실행법, 일반 CLI 권한 및 QA 예외 구분 |
| 2026-11-06 | 0.4 | 명시 모델 검사, 새 탭, 모델 확인 후 Task 전달 절차 |
