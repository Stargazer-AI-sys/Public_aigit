# Project_process_manage 작업 기록

> 최종 갱신 2026-11-19 (ICT PC 세션) | 새 세션은 §0부터 읽는다. 경로는 저장소 루트(`aigit`) 기준 상대 경로다.

## 0. 인계 요약

### 현재 상태
- 점검 3건을 마쳤다.
  - 1차(2026-10-29): `gptgit/project-management` 자동화 프로토타입. 보고서 `reports/2026-10-29_project-management.md`
  - 2차(2026-11-10): `gptgit/project-prototype` 작업 흐름. 보고서 `reports/2026-11-10_project-prototype.md`
  - 3차(2026-11-19): project-prototype 개편(커밋 `ec504a9`) 전후 비교. 보고서 `reports/2026-11-19_project-prototype.md`(Mermaid 5개, 필수 개선 ①~⑥, 결정 목록 10개)
- 3차 개선안을 Codex에 넘길 프롬프트를 이번 대화에서 작성했다(적용 6항목, 금지 범위, 검증 3개, 보고 형식). 사용자가 전달할 예정이다. 프롬프트는 저장소에 파일로 두지 않았다.
- 3차 보고서는 파일만 작성했다(사용자 결정 2026-11-19). commit·push는 하지 않았다.
- 스킬 후보: `skill_candidates.md` (6개, 아직 만들지 않음)
- 세 점검 모두 대상 폴더는 읽기만 했다. 3차 작성 전후 `git status --short gptgit/` 변경 0건.

### 다음 단계
1. **3차 개선 결과 받기(사용자 진행):** 사용자가 Codex에 프롬프트를 넘긴다. 결과가 오면 Claude가 대상 폴더를 읽기만 하며 적용 여부를 다시 점검한다.
   - 적용 6항목: ① 훅 절대 경로 제거 ② 개발기획서 사용자 승인 문장·회차 기록 ③ 확대 해석 하네스 4줄 ④ work_log 옛 이력 분리 ⑤ `CLAUDE.md` 3·5번째 줄 ⑥ 작업기획서 → 목업 → 개발기획서 흐름(교차 검토는 개발기획서만), `templates/work-plan.md` 신설, "한 문서" 표현 교체
   - 프롬프트에 넣은 기본값: 하네스 기준 "변경 파일 3개 이상", 목업 위치 `docs/mockups/`. 사용자가 보내기 전에 바꿀 수 있다.
2. **보류한 결정(보고서 §6):** `project-prototype_backup/` 처리, dispatch·시험 축소(다음에 dispatcher를 고칠 때 함께), GG 공유 스킬 축소(project-management 영향 확인 후), 작업기획서 작성자(제안: 마스터).
3. **project-management 1차 점검의 Codex 제안 검토:** 반영 여부를 사용자에게 확인한다. 3차에서 project-management `hooks.json`도 다른 PC 경로로 바뀐 것을 확인했다(①에 포함).
4. **Claude 시작 방식(project-management):** `start_claude.ps1`과 herdr 안 Codex 실행의 차이를 Codex를 통해 확인한 뒤 개선을 요청할 예정이다.
5. **보류 또는 나중에 확인할 것(사용자 답변 2026-10-29):** Mermaid 가로 스크롤 개선은 보류, Claude Pro 창 크기는 herdr 개선 확인 후, `permission-mode manual` 동작은 나중에 확인, 지연 원인은 다시 생기면 조사.
6. 스킬 후보 6개: 사용자가 내용을 확인한 뒤 적용할 것을 지시한다.
7. 다음 점검 대상: 보류. 후보 A·B는 §3에 있다.

## 1. 배경 (2026-10-29 대화)
- Context7·Superpowers·poteto-mode를 Project_Refactor 작업 기준으로 검토했다. 결정 횟수나 비용을 줄였을 상황은 거의 없었다(10-28 오전에도 쓰지 않기로 결정).
- AI 작업 프로세스를 감사하는 전용 도구는 찾지 못했다. 가까운 것은 `claude-md-management`, `claude-code-setup` 플러그인이다(미설치).
- 그래서 점검 기준을 이 프로젝트 `CLAUDE.md`에 적어 두고 직접 점검하는 방식으로 실험한다. 반복해서 쓸 만하면 스킬로 만든다.

### 1-1. 사용자가 정한 점검 방식 (2026-10-29)
- 설치 없이 쓸 수 있는 도구는 바로 쓴다. 스킬로 만들 만한 절차는 `skill_candidates.md`에 따로 모은다.
- 비용은 `/cost`(사용자가 직접 확인)가 아니라 "문서를 읽느라 컨텍스트가 차서 작업에 방해되는 정도"를 대략 본다.
- Codex가 작업을 지시하므로 대상의 `AGENTS.md`도 분석한다.
- 요구사항 단계가 끝난 뒤 사용자가 프롬프트로 다시 결정하는 일을 막을 수 있는지 루프 엔지니어링 도입 가능성을 본다(보안 제외).
- 전체 구조는 그림으로 그린다. 도구가 없으면 제안하고 설치한다. 이번에는 Obsidian이 이미 있어 Mermaid로 그렸고 설치는 없었다.

## 2. 확인한 사실
- ICT PC: 2026-10-29 기록에는 `codex` 명령이 없다고 했다. 2026-11-10 확인 결과 지금은 `AppData/Roaming/npm/codex.cmd`와 herdr 0.9.5가 설치돼 있다. 이 Claude 셸에서 Codex를 실제로 호출해 보지는 않았다.
- `gptgit` 아래 `AGENTS.md`는 5개다: `gptgit/`, `Project-StudyAutomanage/`, `Project-NetworkEngineer/`, `project-management/`, `project-management/templates/project-v1/`.
- 세션 기록 위치(Stargazer PC). 숫자만 뽑아 쓰고 본문은 옮기지 않는다.
  - Codex: `~/.codex/sessions/2026/`
  - 대상 Claude: `~/.claude/projects/C--Users-Stargazer-OneDrive-Desktop-aigit-gptgit-project-management/`
- 토큰 환산 비율은 글자당 약 0.88토큰이다(Claude Read 실측: 49,959자 → 44,021토큰). GPT는 오차가 있다.
- 이 PC에 Obsidian이 설치돼 있다. node, mermaid-cli, graphviz는 없다.

- 세션 기록 위치(ICT PC, project-prototype): Codex `~/.codex/sessions/2026/11/`, Claude `~/.claude/projects/C--Users-ICT-Desktop-Aigit-gptgit-project-prototype/`

### 2-1. project-management 점검의 주요 발견 (상세는 보고서)
- GPT 마스터는 시작과 맥락 복원에 창의 약 30%를 쓰고, 작업 중 최대 94%까지 찬다. 압축이 7번 있었다. → 방해
- 다시 지시한 것: "작업기록 남겨줘" 9번, "진행해줘" 7번, 번호 선택 3번. 권한 상승 자동 검토는 약 151회(약 1,313만 토큰)였다.
- `claude`를 직접 실행하면 Claude 전용 지침과 보류 자료 Read 거부가 적용되지 않는다(세션 178b02bd에서 확인).
- 10-28 이후 작업은 외부 Codex에서 했다(사용자 확인). herdr는 개선이 끝난 뒤 쓸 예정이다.
- 루프 도입은 조건부 가능이다. 멈춤 조건은 이미 있고 "다음으로 진행" 규칙만 없다. `ralph-loop`은 훅이 꺼져 있어(`disableAllHooks`) 지금 구조에 맞지 않다.

### 2-2. project-prototype 점검의 주요 발견 (2026-11-10, 상세는 보고서)
- 마스터(GPT Astra, 세션 01a1bd9c)는 시작할 때 문서 약 20개를 읽는다. 이것만으로 창의 32%(약 8.2만 토큰)가 차고, 작업 중 최대 76%까지 찬다. 누적 입력은 약 1,936만 토큰이고 99%가 캐시다.
- 첫 번째 읽기 출력의 한글이 깨져서 같은 문서 6개를 다시 읽었다(약 2.3만 토큰). 출력에서 깨진 한자 1,103자를 확인했다.
- 담당(Claude 개발·smoke, Terra 검토)은 packet·spec·plan·관련 소스만 읽었다. 최소 전달 규칙이 지켜진다.
- 사용자 입력은 4번(요청 2번, "진행해줘", "작업기록 남겨줘")이었다. 권한 상승 요청은 89건이었고, 이 세션의 승인 검토자는 `user`였다.
- `workflow.py`(상태 원장)는 한 번도 실행되지 않았다. 실행 근거는 `evidence.md`에 마스터가 직접 썼다. Hermes 연결 도구는 없고, 위키 내용 문서는 0개다.
- 훅: Codex는 전역 SessionStart 훅과 프로젝트 PreToolUse 모델 검사 훅을 쓴다. Claude는 `disableAllHooks`로 훅을 모두 껐다. Codex 전역 플러그인 10개는 사용 흔적이 없다.
- 미확인: 89건 중 사용자가 직접 승인한 건수, 마스터의 실제 시작 명령(start_role을 썼는지), Claude 개발 세션의 컨텍스트 사용량, `.local/wiki-editor-venv`가 없는 이유(`docs/runtime.md:30`은 생성했다고 적음), Obsidian에서 Mermaid가 제대로 보이는지.

### 2-3. project-prototype 개편 재점검 (2026-11-19, 상세는 보고서)
- 개편 커밋 `ec504a9`(2026-11-19 00:05, 72개 파일 +279/−2,278줄)는 다른 PC에서 만들었다. 이 ICT PC에는 2026-11-18 이후 project-prototype Codex 세션이 없다. 그래서 비교는 문서·코드 기준이다.
- PP 규칙 문서는 약 1,000줄에서 약 150줄로 줄었다. GG 상위(`AGENTS.md` 59줄, 공유 스킬 4개)는 바뀌지 않았다. `workflow.py`, 위키 검사기, `docs/workflows/` 증빙은 삭제됐다. 11-10 제안 ①③④는 반영, ②는 확인 필요, ⑤는 미해결.
- 루프(기획→검토·개발→QA, 같은 결함 2회·검토 3회에서 멈춤)는 남아 있다(`PP/AGENTS.md:9-10`). 회차를 적을 곳은 없어졌다.
- 새 위험: `PP/.codex/hooks.json:10`과 `project-management/.codex/hooks.json:10`이 `C:/Users/Stargazer/...` 절대 경로를 가리키고, 이 PC에는 그 경로가 없다. 훅이 실패할 때 Codex가 막는지 통과시키는지는 미확인이다.
- 코드: `task_packet.py:11`이 이미 `work_spec`과 `development_plan`을 따로 받는다. 그래서 기획 흐름을 나눠도 코드는 바꿀 필요가 없다. `dispatch_task.py` 244줄 중 pane 준비 확인·진단 약 125줄은 `GG/tools/start_managed_agent.py` 방식으로 줄일 수 있다(추정). PP 시험은 실행하지 않았다.
- **결정(2026-11-19 사용자):** 기획 흐름은 요청사항 → 작업기획서 → 목업 → 개발기획서다. 작업기획서·목업은 사용자와 함께 검토하고, Codex↔Claude 교차 검토는 개발기획서에서만 한다. "한 문서 기획서"라는 이름은 쓰지 않는다.
- **결정(2026-11-19 사용자):** project-webportfolio는 별도 프로젝트다. 원하는 흐름을 구체적으로 보여 주는 참고였을 뿐이므로 보고서에는 그 프로젝트 내용을 넣지 않는다(넣었다가 뺐다). 흐름만 유지한다.

## 3. 점검 대상 후보 (미착수)
- A. 학습자료 프로그램의 두 프로세스 비교
  - Codex: `gptgit/Project-StudyAutomanage/AGENTS.md`
  - Claude: `Claudecode/Project_Refactor/CLAUDE.md`·`WORK_LOG.md`
- B. 게시 인계 문서(`Project_Refactor/.../data/publish/GUIDE.md`)를 다른 AI가 그대로 따를 수 있는지

## 4. 참고
- 세션 분석 스크립트는 세션 임시 폴더에만 있다. 1차는 `session_metrics.py`, `short_prompts.py`, 2차는 `session_reads.py`(Codex·Claude jsonl에서 읽은 파일·툴·토큰 집계)다. 저장소에는 없다. 스킬로 만들 때 다시 작성하거나 옮긴다.
- commit과 push는 사용자가 요청할 때만 한다. 2026-10-29와 2026-11-10에 사용자 요청으로 Claude가 커밋하고 push했다. 2026-11-19 작업은 커밋하지 않았다.
- 커밋 메시지 형식: `날짜_장소_간단한 내용`. 장소는 집이면 `HOMEwork`, ICT PC면 `ICTwork`.
- 2026-11-19 세션은 대화가 약 20만 토큰까지 쌓여 자동 압축(compaction)이 한 번 일어났다(세션 기록의 `trigger: auto`, `preTokens: 204,359`로 확인). 대상 파일·보고서를 여러 번 다시 읽은 것이 원인이다. 다음 점검은 보고서 작성과 프롬프트 작성 사이에 작업기록을 정리하고 새 세션으로 나눈다.
