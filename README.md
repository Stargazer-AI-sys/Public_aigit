# Aigit

AI(Claude Code, Codex/GPT)와 함께 일하는 방식을 만들고 시험해 온 개인 작업 저장소입니다.
프로젝트마다 AI에게 주는 지침(`CLAUDE.md`, `AGENTS.md`), 작업 절차와 스킬, 작업기록(`WORK_LOG.md`), 실제 결과물을 함께 둡니다.

> 이 저장소는 비공개 작업 저장소의 공개본입니다. 커밋된 파일 내용만 복사해 올리며, 커밋 이력은 옮기지 않습니다. 이력서·개인 자료와 공개하지 않기로 한 일부 프로젝트는 제외했습니다.

## 폴더 구성

| 폴더 | 내용 |
| --- | --- |
| [`Claudecode/`](Claudecode/) | Claude Code로 진행한 프로젝트. 공통 작업 지침은 [`Claudecode/CLAUDE.md`](Claudecode/CLAUDE.md) |
| [`gptgit/`](gptgit/) | Codex/GPT로 진행한 프로젝트와 공통 도구·스킬. 운영 방법은 [`gptgit/README.md`](gptgit/README.md) |
| [`automation-agents/`](automation-agents/) | 프로젝트 관리 자동화에 참여하는 Claude용 지침과 스킬 원본 |

## 주요 프로젝트

### Claudecode

| 프로젝트 | 설명 |
| --- | --- |
| [`Project_webportfolio`](Claudecode/Project_webportfolio/) | 블로그형 포트폴리오 사이트. Next.js(App Router) + TypeScript + Tailwind CSS v4 + shadcn/ui. 개발기획서를 먼저 쓰고 Task 단위로 하위 모델 서브에이전트에게 맡기는 방식으로 개발 |
| [`project_hermes_test`](Claudecode/project_hermes_test/) | 역할별 Hermes 에이전트 인스턴스를 만들어 서버에 배포·관리하는 스크립트와 설정 예시(Slack 연동 llmwiki 봇) |
| [`Project_process_manage`](Claudecode/Project_process_manage/) | 다른 프로젝트의 AI 작업 절차를 점검한 보고서. 코드 품질보다 사용자가 결정해야 하는 지점과 비용을 본다 |
| [`Project_Refactor`](Claudecode/Project_Refactor/) | 학습자료 분석 프로그램 재설계 작업과 시험 결과 |

### gptgit

| 프로젝트 | 설명 |
| --- | --- |
| [`project-management`](gptgit/project-management/) | 여러 프로젝트에 적용할 공통 실행 환경·작업 절차·기본 틀을 만들고 개선 |
| [`project-prototype`](gptgit/project-prototype/) | 승인된 작업을 작은 범위로 기획·제작·검증하는 시험 프로젝트 |
| [`Project-StudyAutomanage`](gptgit/Project-StudyAutomanage/) | 학습자료를 수집·분석·재구성해 사용자 승인 후 Notion에 반영하는 시스템 |
| [`Project-NetworkEngineer`](gptgit/Project-NetworkEngineer/) | 사내망·Linux·웹서비스·AWS/Hybrid 구조와 통신 흐름 실습 |
| [`skills/`](gptgit/skills/), [`tools/`](gptgit/tools/) | 프로젝트 공통 스킬(계획·인계·위임 보고 등)과 에이전트 실행 도구 |

## 읽는 법

- 각 프로젝트는 `CLAUDE.md` 또는 `AGENTS.md`(AI 작업 규칙)와 `README.md`에서 시작합니다.
- 진행 상황과 결정 이유는 `WORK_LOG.md` 또는 `docs/` 아래 작업기록에 있습니다. 기록은 작성 당시의 내용입니다.
- 커밋 이력이 없으므로 날짜는 각 문서에 적힌 날짜를 기준으로 봅니다.
