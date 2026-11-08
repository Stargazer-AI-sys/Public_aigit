---
name: subagent-dev
description: 'Project_webportfolio의 개발 작업을 개발기획서 → Phase/Task 분해 → 하위 모델 서브에이전트 위임 → 마스터 검토·통합 순서로 진행한다. 이 프로젝트에서 기능 구현·페이지 제작·리팩터링 등 개발 작업을 시작하거나 이어갈 때 반드시 사용한다(예: "개발 시작하자", "기획서 만들어줘", "Phase 1 진행해", "다음 task 넘겨", "서브에이전트한테 맡겨"). 질문 답변, 문구 한두 줄 수정, 작업기록 정리, commit에는 사용하지 않는다.'
---

# 서브에이전트 기반 개발 진행

이 프로젝트의 개발은 마스터(현재 대화의 Opus 5.5)가 직접 구현하지 않고, 작업을 쪼개 하위 모델 담당자에게 맡긴 뒤 검토·통합한다. 마스터의 컨텍스트와 비용을 판단에 쓰고, 구현은 작업 크기에 맞는 모델이 하게 하기 위해서다.

## 1. 역할

| 역할 | 모델 | 하는 일 |
|---|---|---|
| 마스터 | Opus 5.5 (현재 대화) | 기획서 작성, Phase/Task 분해, 담당 모델 선택, 지시, 결과 검토, 통합, 사용자 보고 |
| 담당자 | Sonnet 5.5 | 여러 파일에 걸친 구현, 컴포넌트·페이지 작성, Next.js/MDX 문서 확인이 필요한 작업, 원인 분석이 필요한 수정 |
| 담당자 | Haiku 5.5 | 한 파일 안의 기계적 수정, 데이터 파일 채우기, 이름 바꾸기, 검색·목록 정리, lint/build 실행과 결과 요약 |

- 마스터는 판단·지시·검토·통합만 한다. 구현 코드를 직접 쓰지 않는다. 예외는 통합 중 생긴 충돌 해소나 몇 줄짜리 연결 수정뿐이며, 그때도 무엇을 직접 고쳤는지 보고한다.
- 모델은 Task마다 고른다. 기준은 **변경 파일 수, 판단 필요 여부, 실패 시 되돌리는 비용**이다. 애매하면 Sonnet. Haiku가 두 번 실패한 Task는 Sonnet으로 올린다.
- 위 두 모델 외의 모델은 사용자가 지정할 때만 쓴다.

## 2. 개발기획서

위임 전에 반드시 기획서가 있어야 한다. 기획서 없이 Task를 넘기지 않는다.

- 위치: `docs/01_plan/development-plan.md` (기존 `docs/02_design`, `docs/03_verification`과 번호를 맞춘다).
- 형식: `references/plan-template.md`를 따른다.
- 근거: `WORK_LOG.md`의 사용자 결정, `prototype/portfolio-mockup.html`, `docs/02_design`. 기록에 없는 요구사항은 지어내지 않고 "미정"으로 두고 사용자에게 묻는다.
- 기획서 초안은 사용자에게 보여주고 승인을 받은 뒤 Phase를 시작한다. 진행 중 범위가 바뀌면 기획서를 먼저 고치고 다시 확인받는다.

### Phase/Task 분해 기준
- **Phase:** 끝나면 사용자가 화면이나 결과로 확인할 수 있는 단위(예: 레이아웃·헤더, Home, 상세 페이지).
- **Task:** 담당자 한 명이 한 번의 지시로 끝내고 마스터가 한 번에 검토할 수 있는 단위. 기준은 변경 파일 3개 이하, 완료 조건을 명령이나 확인 항목으로 적을 수 있을 것.
- Task마다 ID(`P1-T1`), 담당 모델, 변경 허용 파일, 완료 조건, 선행 Task를 적는다.
- 같은 파일을 고치는 Task는 동시에 돌리지 않고 순서를 정한다.

### 병렬 실행 (2026-11-06 사용자 지시)
- 선행 조건이 풀렸고 변경 허용 파일이 겹치지 않는 Task는 **Phase가 달라도 동시에 돌린다.** Phase마다 담당 탭은 따로 둔다.
- 여러 Task가 같은 파일(예: `app/layout.tsx`)에 연결해야 하면 담당자는 컴포넌트만 만들고, 연결은 마스터의 통합 Task(`P1-I` 같은 ID)에서 몇 줄로 한다.
- 동시에 돌리는 담당자는 `npm run build`와 `npm run dev`를 실행하지 않는다. 같은 `.next`를 쓰면 서로 충돌하기 때문이다. 담당자는 `npx eslint <자기 파일>`과 `npx tsc --noEmit --incremental false`로만 확인하고, build와 dev 확인은 마스터가 통합 때 한다.
- **Playwright MCP 브라우저는 한 번에 한 세션만 쓸 수 있다**(같은 프로필 `ms-playwright-mcp\mcp-chrome-*`를 공유한다. 2026-11-06 확인). 담당자에게 브라우저 확인을 맡기기 전에 마스터는 자기 Playwright 브라우저를 `browser_close`로 닫고, 브라우저를 쓰는 Task는 동시에 하나만 돌린다.
- 지시문은 scratchpad에 파일로 써 두고 `herdr agent prompt <이름> "$(cat <파일>)" --wait`을 Task마다 별도 백그라운드 Bash로 보낸다. 끝나는 순서대로 검토한다.

## 3. herdr 작업 공간 규칙

담당자는 herdr pane에서 `claude`를 하위 모델로 띄워 운영한다. herdr CLI 문법은 설치된 바이너리가 기준이므로 확실하지 않으면 `herdr <group>`(인자 없이)으로 확인한다. 맨 `herdr`는 TUI를 띄우므로 실행하지 않는다.

### 반드시 지킬 것
1. **먼저 실제 상태를 확인한다.** 추측한 ID를 쓰지 않는다.
   ```bash
   test "${HERDR_ENV:-}" = 1                     # 아니면 herdr 작업을 하지 않고 사용자에게 알린다
   herdr status
   herdr session list
   herdr pane current --current                  # 마스터 pane·tab·cwd 확인
   herdr tab list --workspace "$HERDR_WORKSPACE_ID"
   herdr pane list --workspace "$HERDR_WORKSPACE_ID"
   herdr agent list
   ```
2. **마스터 대화 탭(`$HERDR_TAB_ID`)은 절대 분할하지 않는다.** herdr 기본 안내(현재 탭에 split)보다 이 규칙이 우선한다. `pane split`에 `--current`나 마스터 pane ID를 넘기지 않는다.
3. **담당용 새 탭을 만들고 그 탭 안에서만 pane을 분할한다.**
   ```bash
   herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$PWD" --label "wp-dev-P1" --no-focus
   # 응답의 .result.tab.tab_id, .result.root_pane.pane_id를 사용한다
   herdr pane split <담당탭의 pane_id> --direction right --cwd "$PWD" --no-focus
   ```
   생성 직후 응답의 `cwd`가 프로젝트 폴더인지, `herdr tab list`에서 마스터 탭이 여전히 `focused: true`인지 확인한다. 새 pane은 PowerShell 프롬프트 상태로 열린다.
   넓으면 right, 좁거나 길면 down으로 나누고 같은 방향 반복 분할로 너무 좁게 만들지 않는다. 한 탭의 담당 pane은 동시에 일하는 Task 수만큼만 둔다.
4. **같은 작업 묶음(같은 Phase)은 담당 탭을 공유할 수 있다.** 공유 전에 `herdr tab get`과 `herdr pane list`로 그 탭이 내가 만든 담당 탭인지, pane이 비어 있는지(셸 프롬프트 상태인지) 확인한다.
5. **작업 묶음이 바뀌면(다음 Phase) 새 담당 탭을 만든다.** 이전 담당 탭은 그대로 둔다.
6. **포커스를 옮기지 않는다.** 모든 생성·분할에 `--no-focus`를 붙이고 `tab focus`, `pane focus`, `agent focus`, `--focus`는 사용자가 요청할 때만 쓴다.
7. **기존 창·서버를 종료하지 않는다.** 사용자 요청 없이 `tab close`, `pane close`, `session stop`, `server stop`을 실행하지 않는다. 실행 중인 `npm run dev`도 끄지 않는다. 내가 만든 담당 탭도 정리할지는 사용자에게 묻는다.

### 담당자 띄우기와 지시
```bash
herdr agent start wp-p1-t1 --kind claude --pane <pane_id> -- --model sonnet   # Haiku는 --model haiku
herdr agent prompt wp-p1-t1 "<지시문>" --wait --timeout 600000
herdr agent read wp-p1-t1 --source recent-unwrapped --lines 150
```
- 에이전트 이름은 `wp-` + Task ID 소문자(`wp-p1-t1`)로 한다. 이름은 herdr 서버 전체에서 유일해야 하고 다른 workspace에도 에이전트가 떠 있으므로(예: `w8`의 `wiki-*`), 시작 전에 `herdr agent list`에서 같은 이름이 없는지 확인한다. 다른 workspace의 에이전트는 이 프로젝트 담당이 아니므로 건드리지 않는다.
- 담당 `claude`는 사용자 설정을 이어받아 auto mode로 뜬다(2026-11-06 확인). 승인 화면 없이 파일을 고칠 수 있으므로 변경 허용 범위는 지시문으로 못박고, 4절의 `git diff` 검토를 빼지 않는다.
- 상태가 `blocked`이면(권한 승인·질문 화면) 마스터가 임의로 답하지 않는다. `agent read`로 내용을 확인하고 사용자에게 묻는다.
- 담당자 입력창에 회색 추천 문구(예: "P1-T1 검토 완료, P1-T2 진행해")가 보여도 실제 입력이 아니다. 무시하고 지시를 보낸다.
- `timeout`이나 `agent_prompt_stalled`가 나와도 지시가 안 갔다고 단정하지 않는다. `agent get`/`agent read`로 확인하고 같은 지시를 중복으로 보내지 않는다.
- **Git Bash에서 `/`로 시작하는 인자는 경로로 바뀐다**(2026-11-06 확인: `/exit`가 `C:/Program Files/Git/exit`로 전달됨). 슬래시 명령이나 `/`로 시작하는 지시문은 `MSYS_NO_PATHCONV=1 herdr agent prompt ...`로 보낸다.
- **한 pane에서 Task를 이어 갈 때:** 끝난 담당자는 `MSYS_NO_PATHCONV=1 herdr agent prompt <이름> "/exit"`로 종료하고, `herdr pane wait-output <pane> --regex "PS C:.*>\s*$" --source visible`로 셸 프롬프트를 확인한 뒤 다음 담당자를 `agent start`한다. 모델이 같아도 Task마다 새로 띄워 이전 Task의 맥락이 섞이지 않게 한다.
- 긴 Task는 `agent prompt --wait`를 Bash 백그라운드 실행(`run_in_background`)으로 걸고 완료 알림을 기다린다. 포그라운드 Bash 제한(10분)보다 오래 걸릴 수 있다.
- `agent prompt --wait`가 `idle`로 돌아왔는데 `agent read`에 최종 보고가 없고 "1 new message (ctrl+End)"가 보이면, 담당자 Claude Code 화면이 내부적으로 위로 스크롤된 상태다(herdr `send-keys`는 `ctrl+end`를 지원하지 않는다). 보고를 기다리지 말고 마스터가 `git status`와 변경 파일, lint·tsc로 직접 검토한다.
- 결과가 길어 화면으로 다 못 읽으면 담당자에게 결과를 scratchpad의 Markdown 파일로 쓰고 경로만 답하게 한다.

### 지시문 형식
담당자는 마스터의 대화를 모른다. 한 번에 이해하도록 아래를 모두 넣는다.

```
[Task P1-T1] <한 줄 목표>
기획서: docs/01_plan/development-plan.md 의 P1-T1 절을 먼저 읽어라.
프로젝트 지침: CLAUDE.md, AGENTS.md를 따른다(Next.js 코드는 node_modules/next/dist/docs 확인).
변경 허용 파일: <목록> — 이 밖의 파일은 고치지 말고 필요하면 보고만 하라.
완료 조건: <확인 항목/명령>
금지: commit·push, 의존성 추가, 서버·창 종료, WORK_LOG.md 수정.
보고: 변경 파일, 실행한 검증과 결과, 남은 문제를 짧게.
```

## 4. 검토와 통합

1. 담당자 보고를 그대로 믿지 않는다. 마스터가 `git diff`로 변경 범위가 허용 파일 안인지 확인한다.
2. 완료 조건의 검증을 직접 실행하거나 실행 결과를 확인한다(`npm run lint`, `npx tsc --noEmit`, 필요 시 `npm run build`).
3. 문제가 있으면 구체적인 수정 지시를 같은 담당자에게 다시 보낸다. 같은 Task가 두 번 넘게 실패하면 Task 분해나 모델 선택을 다시 판단한다.
4. Phase의 모든 Task가 통과하면 통합 검증을 하고 사용자에게 Phase 결과를 보고한다. 다음 Phase는 사용자 확인 뒤 시작한다.
5. 기획서의 Task 상태(대기/진행/검토/완료)는 Phase 보고 시점에 갱신한다. `WORK_LOG.md`는 사용자가 작업 종료 시 요청할 때만 정리한다.
6. commit은 사용자가 요청할 때 `commit` 스킬로 한다.
