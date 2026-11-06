# 새 컴퓨터 개발환경 세팅 가이드 (초안)

새 PC에서 PowerShell 7, Node.js, Python, Docker, Claude Code, Codex, herdr와 프로젝트 의존성을 같은 방식으로 다시 설치하기 위한 문서와 스크립트다.
다른 프로젝트 폴더와 섞이지 않도록 이 폴더에만 모아 둔다.

| 파일 | 역할 |
|---|---|
| `README.md` | 이 문서. 순서와 용어 설명 |
| `setup.ps1` | 프로그램과 프로젝트 의존성을 설치하는 PowerShell 스크립트 |
| `herdr_workspaces.ps1` | 프로젝트별 herdr 워크스페이스를 만드는 스크립트 |
| `.env.example` | 환경변수(API 키 등) 견본 |

## 1. 사용 순서

1. `aigit`을 받는다. OneDrive 폴더 밖에 `git clone` 하는 것을 권장한다. `.git`을 OneDrive로 동기화하면 저장소가 충돌하거나 손상될 수 있다.
2. PowerShell을 열고 이 폴더로 이동한다.
   ```powershell
   cd "<aigit 위치>\Claudecode\Project_dev_env_setup"
   ```
3. **먼저 미리보기**로 무엇을 설치할지 확인한다 (아무것도 설치되지 않음).
   ```powershell
   .\setup.ps1 -DryRun
   ```
4. 문제없으면 실제로 설치한다.
   ```powershell
   .\setup.ps1
   ```
5. 터미널을 **완전히 닫았다가 다시 열고** `claude`, `codex`에 각각 로그인한다. 로그인 정보는 복사하지 않는다.
6. `.\setup.ps1`을 **한 번 더** 실행한다. 로그인 후 생긴 설정 폴더에 herdr integration이 설치된다.
7. `herdr`를 실행하고, herdr 안의 PowerShell pane에서 워크스페이스를 만든다.
   ```powershell
   .\herdr_workspaces.ps1 -DryRun
   .\herdr_workspaces.ps1
   ```
8. `Docker Desktop`은 처음 한 번 직접 실행해 초기 설정을 마친다. 재부팅이나 WSL 설정을 요구할 수 있다.

## 1-1. git pull 후 갱신

`git pull`은 저장소 파일만 바꾼다. 아래 항목은 저장소 밖에 있거나 Git에서 제외되어 있어 함께 갱신되지 않는다.

| 항목 | 위치 | Git으로 옮겨지는 것 | 갱신 방법 |
|---|---|---|---|
| PowerShell 7, Git, Node, Python, Docker | `Program Files`, `AppData` 등 | `setup.ps1`의 버전 목록 | `.\setup.ps1` |
| Claude, Codex, herdr | `AppData`, 사용자 폴더 등 | `setup.ps1`의 목록 | 없으면 `.\setup.ps1`, 있으면 아래 업데이트 명령 |
| herdr integration | `~/.claude`, `~/.codex` | `setup.ps1`의 목록 | `.\setup.ps1` |
| 워크스페이스 | `%APPDATA%\herdr` | `herdr_workspaces.ps1`의 목록 | `.\herdr_workspaces.ps1` |
| 프로젝트 라이브러리 | 각 프로젝트의 `node_modules` (`aigit` 안, Git 제외) | `package.json`, `package-lock.json` | `.\setup.ps1` |

**`git pull` 후에는 `.\setup.ps1`을 다시 실행한다.** 이미 맞는 항목은 건너뛰고, 잠금 파일이 바뀐 프로젝트만 `npm ci`와 `npm run build`를 실행한다. 실행 중인 개발 서버는 먼저 끈다.

이미 설치된 도구는 스크립트가 업데이트하지 않으므로 필요할 때 직접 실행한다.

```powershell
npm install -g @openai/codex@latest
claude update
herdr update
```

## 1-2. 버전 기준

기준 PC(2026-11-03)와 같은 버전으로 고정한다. 바꾸려면 `setup.ps1`의 `$wingetPackages`를 고친다.

| 프로그램 | 버전 |
|---|---|
| Node.js | 26.13.0 |
| Python | 3.14.7 |
| Docker Desktop | 4.97.0 |

설치된 버전이 기준보다 낮으면 올리고, 높으면 경고만 표시하고 낮추지 않는다. PowerShell 7, Git, npm 전역 도구, herdr는 고정하지 않는다.

winget이 아닌 방식(Microsoft Store, 직접 설치 등)으로 이미 설치된 프로그램은 `setup.ps1`이 경고를 내고 건너뛴다. `winget list`에 없어도 `pwsh`, `git`, `node`, `python`, `docker` 명령이 실제로 동작하면 설치된 것으로 본다. 이 경우 기준 버전과 맞는지는 검사하지 않으므로 `python --version` 등으로 직접 확인한다.

PowerShell 7(`Microsoft.PowerShell`)은 최신 버전을 설치하고, 설치된 뒤에는 `setup.ps1`이 갱신하지 않는다. 명령어는 `pwsh`다. 새 PC에는 기본으로 PowerShell 5.1(`powershell`)만 있고, `setup.ps1`은 5.1에서도 실행된다. 설치 직후에는 터미널을 닫았다가 다시 열어야 `pwsh`가 인식된다.

```powershell
winget upgrade --id Microsoft.PowerShell   # PowerShell 7 업데이트
```

Python은 프로그램만 설치한다. `requirements.txt`의 패키지와 `compose.yaml`의 컨테이너는 설치하거나 실행하지 않는다.

> 스크립트 실행이 "이 시스템에서 스크립트를 실행할 수 없습니다"라며 막히면:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 를 한 번 실행한다.
> (내 계정에서만, 내가 만든 스크립트는 허용하는 설정이다.)

## 1-3. 관리자 권한으로 PowerShell 7 실행

herdr 안의 pane은 herdr를 실행한 프로그램의 권한을 그대로 물려받는다(Windows에서 자식 프로세스는 부모 권한을 상속한다). 그래서 일반 권한으로 연 터미널에서 herdr를 실행하면 pane 안에서는 관리자 권한을 얻을 수 없다. 관리자 권한이 필요하면 **herdr를 관리자 PowerShell 7에서 실행**한다.

관리자 PowerShell 7을 여는 방법(아무거나 하나):

1. 시작 메뉴에서 `PowerShell 7`을 찾아 우클릭 → **관리자 권한으로 실행**
2. 이미 열린 PowerShell에서:
   ```powershell
   Start-Process pwsh -Verb RunAs
   ```
3. Windows Terminal 설정에서 PowerShell 7 프로필의 "관리자 권한으로 이 프로필 실행"을 켠다.

관리자 창이 열리면 아래로 권한을 확인한 뒤 `herdr`를 실행한다.

```powershell
([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)   # True면 관리자
```

주의:
- 관리자 권한은 필요한 작업에만 쓴다. 평소 개발은 일반 권한으로 한다. 관리자 pane에서 `claude`, `codex`를 실행하면 그 도구가 하는 모든 작업이 관리자 권한으로 실행된다.
- 일반 권한 herdr 서버가 이미 떠 있으면 관리자 창에서 `herdr`를 실행해도 그 서버에 붙어 pane이 일반 권한일 수 있다. 위 `True/False` 확인을 pane 안에서 다시 하고, `False`면 herdr를 모두 종료한 뒤 관리자 창에서 다시 시작한다. (herdr가 서버에 붙는 방식은 문서로 확인하지 못한 추정이다.)
- 한 명령만 관리자로 실행하고 싶다면 Windows 11의 `sudo`를 쓸 수 있다. 설정 → 시스템 → 개발자용 → "sudo 사용"을 켜면 `sudo <명령>`으로 실행된다.

## 2. 용어 설명

| 용어 | 뜻 |
|---|---|
| **PATH** | 터미널이 명령어(`node`, `npm` 등)를 찾아보는 폴더 목록. 설치는 됐는데 "인식되지 않습니다"가 뜨면 대부분 PATH 문제다 |
| **환경변수** | 컴퓨터나 프로그램이 읽는 설정값. PATH도 환경변수의 하나다 |
| **winget** | Windows 기본 프로그램 설치 도구. 명령어 한 줄로 설치한다 |
| **Node.js** | 자바스크립트를 컴퓨터에서 실행하는 프로그램 |
| **npm** | Node.js와 함께 설치되는 라이브러리/도구 설치 프로그램 |
| **LTS** | Long Term Support. 오래 지원되는 안정 버전. 특별한 이유 없으면 LTS를 쓴다 |
| **전역 설치(`-g`)** | 어느 폴더에서나 쓸 수 있게 컴퓨터 전체에 설치하는 것 |
| **`.env` 파일** | API 키 같은 비밀값을 담는 파일. git에 올리면 안 된다 |
| **DryRun** | 실제 실행 없이 "이렇게 할 예정"만 보여주는 연습 모드 |

## 3. 명령어 옵션 설명

### `setup.ps1` 옵션

| 옵션 | 의미 |
|---|---|
| `-DryRun` | 설치하지 않고 계획만 출력한다. 처음 실행할 때 권장 |

### 스크립트 안에서 쓰는 `winget install` 옵션

| 옵션 | 의미 |
|---|---|
| `--id <ID>` | 설치할 프로그램의 고유 이름 |
| `--exact` | 이름이 정확히 같은 것만 설치한다 (비슷한 이름의 다른 프로그램 방지) |
| `--silent` | 설치 창을 띄우지 않고 조용히 설치한다 |
| `--accept-package-agreements` | 프로그램 사용 약관에 자동 동의한다 |
| `--accept-source-agreements` | winget 저장소 약관에 자동 동의한다 |

### `npm install -g` 옵션

| 옵션 | 의미 |
|---|---|
| `install` | 설치한다 |
| `-g` | 전역(global) 설치. 어느 폴더에서나 명령어를 쓸 수 있다 |

## 4. 프로그램 추가·제거하는 법

`setup.ps1` 맨 위의 목록만 고치면 된다.

- winget 프로그램: `$wingetPackages` 에 ID와 버전 한 줄 추가. ID는 `winget search 이름` 으로 찾는다.
- npm 전역 도구: `$npmGlobalPackages` 에 패키지 이름과 명령어 한 줄 추가.
- 프로젝트 의존성: `$projects` 에 프로젝트 경로와 설치·확인 명령 추가. 라이브러리 이름은 적지 않는다.
- 워크스페이스: `herdr_workspaces.ps1` 의 `$workspaces` 에 라벨과 경로 한 줄 추가.

## 5. 자주 나는 문제

| 증상 | 원인과 해결 |
|---|---|
| 설치 직후 `npm`이 인식되지 않음 | 열려 있던 터미널은 새 PATH를 모른다. 터미널을 닫고 다시 연다 |
| `codex` 등 전역 도구가 인식되지 않음 | `npm config get prefix` 로 나온 폴더(보통 `%APPDATA%\npm`)가 PATH에 있는지 확인한다 |
| 어떤 `node`가 실행되는지 모르겠음 | `Get-Command node` 로 실제 경로를 확인한다 |
| winget 설치가 "다른 버전이 이미 설치되어 있습니다"(종료 코드 1638, `-1978334963`)로 실패 | Store나 직접 설치처럼 winget 밖에서 설치된 경우다. 최신 `setup.ps1`은 자동으로 건너뛴다. 이전 버전 스크립트라면 `git pull` 후 다시 실행한다 |
| winget이 없다고 나옴 | Microsoft Store에서 "앱 설치 관리자"를 업데이트한다 |

## 6. 주의사항

- 이 스크립트는 **초안이다.** 기준 PC에서 `-DryRun`만 확인했고 실제 설치는 아직 실행해 보지 않았다. 처음엔 반드시 `-DryRun` 으로 확인한다.
- `.env`, `.local`처럼 Git에서 제외된 파일과 Claude·Codex 대화 기록은 옮겨지지 않는다.
- `.env` 에 실제 키를 넣었다면 git에 커밋하지 않는다. 비밀값은 비밀번호 관리자에 따로 보관한다.
- 패키지 이름(`@anthropic-ai/claude-code`, `@openai/codex`)은 설치 전에 각 공식 문서에서 현재 이름을 한 번 더 확인하는 것이 안전하다.
