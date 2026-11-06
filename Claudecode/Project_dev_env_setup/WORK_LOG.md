# Project_dev_env_setup 작업 기록

> 최종 갱신 2026-11-05 (ICT PC 세션) | 새 세션은 §0부터 읽는다. 경로는 저장소 루트(`aigit`) 기준 상대 경로다.

## 0. 인계 요약

### 현재 상태
- herdr `default` 세션에 프로젝트별 워크스페이스를 만들어 사용 중이다. 프로젝트 폴더로 일일이 이동하는 대신 워크스페이스를 전환해 `claude`, `codex`를 실행한다.
- 새 PC 복원 절차를 스크립트로 만들어 커밋·푸시했다(`fbfc7ce`).
  - `Claudecode/Project_dev_env_setup/setup.ps1`: 프로그램(PowerShell 7 포함), herdr integration, 프로젝트 의존성 설치. 2026-11-05에 PowerShell 7(`Microsoft.PowerShell`, 최신 버전)을 winget 목록에 추가했다. 2026-11-05에 커밋했다.
  - `Claudecode/Project_dev_env_setup/herdr_workspaces.ps1`: 없는 워크스페이스만 생성
  - `Claudecode/Project_dev_env_setup/README.md`: 새 PC 순서, `git pull` 후 갱신 방법, 버전 기준

### 다음 단계
0. 이 PC에서 `.\setup.ps1`을 실제 실행해 Docker, Codex CLI, herdr 설치를 검증한다. Python은 Store 설치 3.14.8을 그대로 쓴다.
1. 새 PC에서 `.\setup.ps1 -DryRun`부터 실행해 실제 설치를 처음 검증한다. 실패하면 오류를 보고 스크립트를 고친다.
2. herdr 안에서 `.\herdr_workspaces.ps1 -DryRun`을 실행해 중복 판정이 맞는지 확인한다.
3. 필요 없으면 `aigit` 최상위를 가리키는 이름 없는 워크스페이스를 사용자가 herdr에서 닫는다.
4. 사용자 PATH에 남은 옛 Codex 경로(`...\OpenAI\Codex\bin\08d187884f2330d1`)를 정리할지 정한다. 동작에는 지장이 없을 것으로 보여 그대로 두었다.

## 1. 사용자 결정
- 프로젝트는 세션을 나누지 않고 한 세션의 워크스페이스로 관리한다. `프로젝트 관리 열기` 바로가기는 수정하지 않았으며, 이 바로가기로 열면 별도 세션이 생긴다.
- 워크스페이스 대상은 8개다.
  - `Claudecode`: `Project_director`, `Project_process_manage`, `Project_Refactor`, `Project_webportfolio`
  - `gptgit`: `project-management`, `Project-NetworkEngineer`, `Project-StudyAutomanage`, `재취업 이력서`
- `dev-env-setup` 워크스페이스는 두지 않는다. 폴더 자체는 Git으로 계속 관리한다.
- Codex는 앱에 포함된 실행 파일을 PATH에 등록하지 않고 별도 CLI로 설치한다.
- Node, Python, Docker는 이 PC와 같은 버전으로 설치한다.
- 프로젝트 라이브러리는 스크립트에 적지 않고 프로젝트별 잠금 파일에서 설치한다.
- winget 밖에서 설치된 프로그램은 설치하지 않고 건너뛴다(2026-11-05). 위 Python 실패의 해결책이며, `Command`가 동작하면 설치된 것으로 보고 버전 기준은 검사하지 않는다.
- PowerShell 7은 버전을 고정하지 않고 최신 버전으로 설치한다(2026-11-05). 한 번 설치되면 스크립트 재실행으로 갱신되지 않는다.

## 2. 확인한 사실
- **Codex 실행 오류 원인:** 사용자 PATH에 등록된 앱 내부 해시 폴더가 사라져 있었다. 앱 업데이트 때문으로 추정한다. `npm install -g @openai/codex@0.166.0`으로 해결했고, 사용자가 herdr pane에서 실행을 확인했다.
- **대화 복원:** 설정 화면에서 integration을 설치했다(`claude` v11, `codex` v10). 사용자가 herdr 서버 재시작 후 Claude 대화가 이어지는 것을 확인했다.
- **Windows hook 파일:** `.sh`가 아니라 `.ps1`로 설치된다(`~/.claude/hooks/herdr-agent-state.ps1`).
- **자동 복원 제외:** `gptgit/project-management/tools/start_claude.ps1`은 `--setting-sources project`로 실행하므로 사용자 설정의 hook을 읽지 않는다. pane에서는 `claude`를 직접 실행한다.
- **`git pull`의 범위:** 프로그램, integration, 로그인 정보, 워크스페이스는 `aigit` 밖에 있고, `node_modules`는 `aigit` 안에 있지만 Git에서 제외된다. 그래서 `git pull` 후 `.\setup.ps1`을 다시 실행해야 한다.
- **Python 설치 실패(2026-11-05, ICT PC):** `setup.ps1`이 `Python.Python.3.14` 설치에서 종료 코드 1638(`-1978334963`, 다른 버전이 이미 설치됨)로 실패했다. 이 PC의 Python은 3.14.8이며 Microsoft Store(`msstore`, `9NCVDN91XZQP`)로 설치되어 있고 winget ID `Python.Python.3.14`로는 조회되지 않는다. 설치 경로는 `AppData\Local\Programs\Python\Python314`다. VS Code로 설치했는지는 확인하지 못했다.
- **기준 버전(winget 제공 확인):** Node 26.13.0, Python 3.14.7, Docker Desktop 4.97.0.

## 3. 검증 결과
- 두 스크립트 모두 PowerShell 7과 5.1에서 문법 오류가 없다.
- `setup.ps1 -DryRun`은 7과 5.1에서 정상 종료했고, 이 PC에서는 전 항목이 건너뜀으로 나온다.
- `herdr_workspaces.ps1`은 herdr 밖에서 실제 실행을 거부한다.
- 2026-11-05(ICT PC, PowerShell 5.1): winget 목록 항목에 `Command`(`pwsh`, `git`, `node`, `python`, `docker`)를 추가하고 `Test-CommandWorks`로 `--version` 성공까지 확인하게 했다. `-DryRun`에서 Python은 "winget이 아닌 방식으로 설치됨" 경고와 함께 건너뛰었고, PowerShell 7.6.9.0은 설치된 것으로 인식했다. 실제 설치는 실행하지 않았다.
- 2026-11-05(ICT PC, PowerShell 5.1): `setup.ps1`에 PowerShell 7이 없던 것을 확인하고 `Microsoft.PowerShell`을 목록 맨 앞에 추가했으며, 마지막 버전 확인 목록에 `pwsh`도 넣었다. `setup.ps1 -DryRun`에서 `Microsoft.PowerShell`이 설치 대상으로 나왔고, 이 PC에는 PowerShell 7이 없다는 뜻이다. 같은 실행에서 Python, Docker, Codex CLI, herdr, herdr integration도 설치 대상으로 나왔다. Git, Node, Claude, 프로젝트 의존성은 건너뜀으로 나왔다. 위 "전 항목 건너뜀"은 기준 PC(2026-11-03)의 결과다.

## 4. 미확인 항목
- `setup.ps1`의 실제 설치(winget, herdr 설치, `npm ci`, `npm run build`). 실제 설치는 아직 한 번도 실행하지 않았다(2026-11-05 ICT PC도 `-DryRun`만 실행).
- PowerShell 7 winget 설치 자체(`Microsoft.PowerShell` ID로 실제 설치되는지, 설치 후 `pwsh` 인식). `-DryRun`으로 계획만 확인했다.
- Docker Desktop 무인 설치. 재부팅이나 WSL 설정을 요구할 수 있다.
- `herdr workspace list` 응답 형식. 공식 문서에 없어 문자열 값으로 중복을 찾으며, 표본 데이터로만 시험했다.
- Codex 대화 복원과 실제 PC 재부팅 후 복원. 서버 재시작 시 Claude 대화 복원만 확인했다.
- `dev-env-setup` 워크스페이스가 실제로 만들어졌었는지. 세션 파일, 스냅샷, 서버 로그에 흔적이 없다.

## 5. 범위에서 제외
- Python의 `requirements.txt` 패키지와 `gptgit/project-management/compose.yaml` 컨테이너는 설치하거나 실행하지 않는다.
- `.env`, `.local` 등 Git 제외 파일, 로그인 정보, Claude·Codex 대화 기록은 옮기지 않는다.
- 새 PC의 Claude는 `setup.ps1`대로 npm으로 설치된다. 이 PC는 `~/.local/bin/claude.exe`를 쓰므로 설치 경로와 업데이트 방식이 다를 수 있다.
