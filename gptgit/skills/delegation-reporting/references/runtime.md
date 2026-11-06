# 실행 도구와 훅

## 공통과 프로젝트별 책임

- `gptgit/tools/check_agent_model.py`: role/provider/model 검증. 표준 라이브러리만 사용한다. master Codex는 gpt-6-astra, 하위 Codex는 gpt-6-luna 또는 gpt-6.1-terra. 누락·unknown은 실패한다. Claude/Hermes는 별도 프로젝트 계약과 명시 모델을 유지하며 실제 가용성은 검사하지 않는다.
- `project-management/tools/start_agent.ps1`: 공통 `start_managed_agent.py`를 호출하여 관리 역할의 모델·권한과 cwd를 검사하고 새 담당 탭에서 Codex를 시작한다. Task를 자동 전달하지 않는다.
- `project-prototype/tools/start_role.ps1` 및 `dispatch_task.py`: 기존 packet·구독·Claude 기획검토·독립 QA 조건을 보존하고 공통 모델 검사를 적용한다. Hermes 실제 adapter는 이 작업의 구현 범위가 아니다.
- `gptgit/tools/agent_model_hook.py`: PreToolUse stdin JSON을 읽는 보조 명령 가드. 두 도입 프로젝트 및 공통 영역 범위에 한정한다. 상세 지원/제외 명령은 코드와 회귀 시험을 따른다.

관리 프로젝트 루트 예시:

```powershell
./tools/start_agent.ps1 -Role researcher -Model gpt-6-luna -Name research-one -CheckOnly
./tools/start_agent.ps1 -Role researcher -Model gpt-6-luna -Name research-one
```

첫 명령은 모델을 호출하지 않는다. 두 번째 명령은 실제 담당 탭/세션을 생성하므로 승인된 위임 범위에서만 실행한다. 반환 상태가 awaiting_model_verification이면 담당 상태 화면의 모델·권한을 확인한 뒤 Task를 전송한다. 시작 실패/시간 초과 시 새 창이 생겼는지 확인하고 자동 재시도하지 않는다. 마스터 탭을 split하지 않으며 작업 묶음의 담당 탭 안에서 추가 pane을 나눌 수 있다.

## 훅 활성화

두 프로젝트의 `.codex/hooks.json`은 같은 공통 Python 파일을 참조한다. 프로젝트 cwd와 설치 경로에 의존하는 현 PC 등록이므로 PC 이동 시 해당 경로와 Python을 다시 확인한다. 사용자 전역 config를 덮어쓰지 않는다. Codex는 신뢰하지 않은 로컬 훅을 실행하지 않으므로 각 프로젝트의 `/hooks`에서 정의를 검토·신뢰해야 한다. 새 세션/설정 다시 읽기 뒤 실제 이벤트 차단을 확인하기 전까지 활성화 완료로 표시하지 않는다. 신뢰 우회 옵션은 사용하지 않는다.

공식 근거: [Codex Hooks](https://learn.chatgpt.com/docs/hooks). PreToolUse의 명시적 deny만 지원되는 도구 호출을 차단한다. 훅 오류·timeout·비지원 도구는 완전한 차단을 보장하지 않는다. PreModelRequest/PostModelRequest는 모델 정보를 받지만 요청을 막을 수 없다.

## 회귀 시험

gptgit 루트에서 `python -B -m unittest discover -s tests -p "test_agent*.py"`를 실행한다. 프로젝트 고유 시험은 각 프로젝트 tests에서 수행한다. 모의 호출 시험·실제 herdr 시작·실제 모델 확인·Task 수행·훅 신뢰 및 이벤트 실행을 구분한다. 개인 스킬 설치와 기존 기록 승인 범위는 변경하지 않는다.
