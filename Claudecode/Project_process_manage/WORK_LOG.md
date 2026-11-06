# Project_process_manage 작업 기록

> 최종 갱신 2026-10-29 (Stargazer PC 세션) | 새 세션은 §0부터 읽는다. 경로는 저장소 루트(`aigit`) 기준 상대 경로다.

## 0. 인계 요약

### 현재 상태
- 첫 점검을 마쳤다. 대상은 `gptgit/project-management`의 자동화 프로토타입이다(herdr 안의 GPT 마스터 → Claude 제작 → Hermes 기록, 2026-10-27~28 작업).
  - 보고서: `reports/2026-10-29_project-management.md`
  - 스킬 후보: `skill_candidates.md` (6개, 아직 만들지 않음)
- 점검하는 동안 대상 폴더(`gptgit/`, `automation-agents/`)는 읽기만 했고, 점검 전후 Git 상태가 같았다.

### 다음 단계
1. **Codex 제안 검토(사용자 진행 중):** 사용자가 보고서와 검토 요청 프롬프트를 외부 Codex에 넘긴다.
   - 프롬프트는 이번 대화에서 작성했다. 파일 수정 없이 ① 사실 대조 ② 제안별 추천 ③ 수정 문안 ④ 충돌 검토 ⑤ 사용자 결정 목록을 받도록 요청한다.
   - 첨부는 보고서 1개만 한다. 대상 문서는 Codex가 직접 읽는다.
   - Codex가 결과를 돌려주면, ⑤에 따라 대상 프로젝트에 무엇을 반영할지 사용자가 정한다.
2. **Claude 시작 방식:** 사용자는 `start_claude.ps1`을 단순 실행기로 본다. herdr 안에서 Codex로 실행할 때와 무엇이 다른지 Codex를 통해 확인한 뒤 개선을 요청할 예정이다.
3. **보류 또는 나중에 확인할 것(사용자 답변 2026-10-29):**
   - Mermaid 가로 스크롤 개선: 보류
   - Claude Pro 창 크기: herdr 개선 확인 후
   - `permission-mode manual` 동작: 나중에 확인
   - 지연 원인: 다시 생기면 조사
4. 스킬 후보 6개: 사용자가 목록을 확인했다. 어떤 것을 적용할지는 내용을 확인한 뒤 지시한다.
5. 다음 점검 대상: 보류. 후보 A·B는 §3에 있다.

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
- ICT PC에는 `codex` 명령이 없다. 그래서 그 PC에서는 Claude가 Codex를 직접 호출할 수 없다.
- `gptgit` 아래 `AGENTS.md`는 5개다: `gptgit/`, `Project-StudyAutomanage/`, `Project-NetworkEngineer/`, `project-management/`, `project-management/templates/project-v1/`.
- 세션 기록 위치(Stargazer PC). 숫자만 뽑아 쓰고 본문은 옮기지 않는다.
  - Codex: `~/.codex/sessions/2026/`
  - 대상 Claude: `~/.claude/projects/C--Users-Stargazer-OneDrive-Desktop-aigit-gptgit-project-management/`
- 토큰 환산 비율은 글자당 약 0.88토큰이다(Claude Read 실측: 49,959자 → 44,021토큰). GPT는 오차가 있다.
- 이 PC에 Obsidian이 설치돼 있다. node, mermaid-cli, graphviz는 없다.

### 2-1. project-management 점검의 주요 발견 (상세는 보고서)
- GPT 마스터는 시작과 맥락 복원에 창의 약 30%를 쓰고, 작업 중 최대 94%까지 찬다. 압축이 7번 있었다. → 방해
- 다시 지시한 것: "작업기록 남겨줘" 9번, "진행해줘" 7번, 번호 선택 3번. 권한 상승 자동 검토는 약 151회(약 1,313만 토큰)였다.
- `claude`를 직접 실행하면 Claude 전용 지침과 보류 자료 Read 거부가 적용되지 않는다(세션 178b02bd에서 확인).
- 10-28 이후 작업은 외부 Codex에서 했다(사용자 확인). herdr는 개선이 끝난 뒤 쓸 예정이다.
- 루프 도입은 조건부 가능이다. 멈춤 조건은 이미 있고 "다음으로 진행" 규칙만 없다. `ralph-loop`은 훅이 꺼져 있어(`disableAllHooks`) 지금 구조에 맞지 않다.

## 3. 점검 대상 후보 (미착수)
- A. 학습자료 프로그램의 두 프로세스 비교
  - Codex: `gptgit/Project-StudyAutomanage/AGENTS.md`
  - Claude: `Claudecode/Project_Refactor/CLAUDE.md`·`WORK_LOG.md`
- B. 게시 인계 문서(`Project_Refactor/.../data/publish/GUIDE.md`)를 다른 AI가 그대로 따를 수 있는지

## 4. 참고
- 이번 점검에 쓴 세션 분석 스크립트는 세션 임시 폴더에만 있다(`session_metrics.py`, `short_prompts.py`). 저장소에는 없다. 스킬로 만들 때 다시 작성하거나 옮긴다.
- commit과 push는 사용자가 요청할 때만 한다. 2026-10-29에 사용자 요청으로 Claude가 커밋하고 push했다.
- 커밋 메시지 형식: `날짜_장소_간단한 내용`. 장소는 집이면 `HOMEwork`, ICT PC면 `ICTwork`.
