# Project_webportfolio 작업 기록

> 최종 갱신 2026-11-06 (ICT PC 세션) | 새 세션은 §0부터 읽는다. 경로는 저장소 루트(`aigit`) 기준 상대 경로다.

## 0. 인계 요약

### 현재 상태
- 블로그형 포트폴리오. 스택 세팅이 끝났다: Next.js 16.4.3(App Router) + TypeScript + Tailwind v4 + shadcn/ui + MDX(`@next/mdx`) + `next-themes` 다크 모드.
  - 다크 모드 적용 뒤 `npm run lint`(에러 없음), `npm run build`, `tsc --noEmit` 통과. dev 서버 `/` 200 확인.
  - `app/page.tsx`는 아직 템플릿 그대로이고, `app/layout.tsx`의 `title`·`lang="en"`도 그대로다. 구현 때 함께 바꾼다.
  - `create-next-app@16.4.3` 템플릿에 shadcn/ui가 초기화되어 있다(`components.json`, `components/ui/button.tsx`, `lib/utils.ts`). MDX도 설치되어 있다(`@next/mdx`, `@mdx-js/loader`, `@mdx-js/react`, `@types/mdx`; `next.config.ts`의 `createMDX`, 루트 `mdx-components.tsx`).
  - 실제 콘텐츠(`.mdx`)와 frontmatter 방식은 아직 정하지 않았다. `@next/mdx`는 기본적으로 frontmatter를 지원하지 않고 `export const metadata`를 쓴다.
- **목업을 포트폴리오 핵심 주제(CASE 01~03 + REFLECTION) 기준으로 다시 썼고, 사용자 검토 대기 중이다.** Next.js 페이지 구현은 시작하지 않았다.
  - 기준 파일: `Claudecode/Project_webportfolio/prototype/portfolio-mockup.html`(커밋하지 않은 수정). 실제 화면 캡처 편집본 15장은 `prototype/img/`, 원본은 `img/`(둘 다 git 미추적).
  - 게시본 https://claude.ai/artifact/WCkt39nNT6HVbXK44m9ToA (비공개)에 11-06 사용자 요청으로 반영했다(버전 `1793944948-1213`, `index.html` + `img/` 15장, 슬러그 UUID `ec7d3e9d-6cec-4131-a566-9ab19d6fd2bd`). 이후 다크 모드 버튼 수정과 CASE 01 화면 소개 문장 삭제도 포함된 상태다.
- Context7 MCP는 HOME PC와 ICT PC에서 정상 연결된다(11-03 ICT PC는 `resolve-library-id` 호출 확인).

### 콘텐츠·구조 결정 (2026-11-02 사용자 결정)
- **핵심 메시지:** AI로 문제 해결에 접근하는 방식이 어떤 사람인지 소개한다. 독자는 채용 담당자, 언어는 한국어.
- **비중:** 프로세스 개선(`gptgit/project-management`, `Project_process_manage`)이 메인, `Project-StudyAutomanage`는 보조 사례. `Project-NetworkEngineer`는 수강 과정 학습이라 카드에서 뺀다. 원칙 카드와 프로젝트를 1:1로 맞추지 않는다.
- **메뉴(임시):** Home / 일하는 방식 / AI 프로젝트. 메뉴는 중앙, 모드 버튼과 연락하기는 맨 우측. 분위기는 poulo.site 참고, 포인트 색 `#4B89DC`.
- **공개 제외:** 전화번호, 출생연도, 사진, 학력, 지각률, 회사명. 연락 메일은 `hanmir777@naver.com`(이력서의 메일과 다르다). 스크린샷은 사용자가 나중에 준다.
- **데이터:** 카드 내용은 데이터 파일로 분리한다. 수정은 그 파일을 로컬에서 직접 고치는 것으로 충분하고 수정 화면은 만들지 않는다.
- **진행률:** 대시보드는 아직 구현하지 않고 우측 슬롯 자리만 둔다. 나중에 수동으로 고치는 중간 파일을 읽게 한다. Phase 단위에 얽매이지 않으며, 사이트가 aigit 폴더를 직접 읽지 않는다.

### 상세 페이지 결정 (2026-11-03 사용자 결정)
- **이유:** 목업 내용만으로는 근거가 부족하다. 프로젝트 기준 상세 페이지 2개에서 자세히 설명한다.
- **기준 자료:** 프로세스 개선은 `gptgit/project-management`가 기준이고 `Claudecode/Project_process_manage`를 참고한다. 학습 자동화는 `gptgit/Project-StudyAutomanage`가 기준이고 `Claudecode/Project_Refactor`를 참고한다.
- **구성:** 개요, 분석 및 계획(요구사항), 폴더 구조(관련 구조만), 프로세스 순서도(간략화), 발생한 문제, 개선할 내용.
- **취약점:** `npm audit` 21건은 일단 그대로 둔다.

### 문구·버튼 결정 (2026-11-04 사용자 결정)
- **`추정` 표현:** 목업 문구에서 `추정`이라는 말을 뺀다. 내용은 지우지 않는다.
- **윤문 방식:** 화면 문구만 뽑아 `humanize-korean`으로 윤문하고, 수치·고유명사를 대조한 뒤 HTML에 다시 넣는다.
- **버튼:** "근거와 상세 내용 보기"에 "파란색"으로 답했다. 3개 모두 파란색으로 해석해 적용했다.
- **이전에 알린 문구 오류 4곳:** 다시 보고하지 않고 새로운 문제만 알린다. `:320`, `:321`, `:328`은 사용자가 직접 고쳤다.

### 핵심 주제 재구성 결정 (2026-11-06 사용자 결정)
- **구성:** CASE 01 사용자 관점의 완료 기준(학습 자동화) / CASE 02 프로젝트 구조와 협업 방식 / CASE 03 비용과 검증 범위의 조정 / REFLECTION 현재 위치와 다음 단계. CASE마다 상세 페이지 1개, REFLECTION은 AI Workflows 섹션 안 카드.
- **메뉴명:** Home / Working Style / AI Workflows. Working Style 원칙 카드 4개는 유지하고 01→CASE 01, 02→CASE 02, 03→CASE 03, 04→REFLECTION으로 연결한다.
- **맥락 분리:** 학습 자동화와 프로세스 개선은 독립 프로젝트다. 한 CASE 페이지에 섞지 않는다. Notion 관련 내용은 학습 자동화(CASE 01)에만 두고, CASE 02·03은 `gptgit/project-management`·`project-prototype` 기록(10.29 점검 보고서 `Claudecode/Project_process_manage/reports/2026-10-29_project-management.md` 등)을 근거로 쓴다.
- **이미지:** 누르면 가운데 팝업으로 연다. 크기가 다르면 작은 쪽에 맞춰 자른다. 카드 대표 이미지는 내용보다 디자인(카드 크기 통일)을 우선한다. 캡처의 관련 없는 부분, Windows 정품 인증 표시, 경로는 자르거나 가린다.
- **Home 수치 칸:** "31건" 대신 "4가지 기준 / AI Workflows에서 중요한 4가지 기준"(Working Style로 연결).
- **공개 범위 항목**(CASE 01의 PC 경로·실습 비밀번호 문제, CASE 03의 토큰 수치, 캡처 속 외부 URL)은 사용자가 신경 쓰지 않기로 했다. 다시 제안하지 않는다.

### 다른 PC에서 이어갈 때
- pull 후 이 폴더에서 `npm install`을 먼저 실행한다. `node_modules/`는 git에 없다. Node.js가 없으면 그것부터 설치한다.
- Context7 MCP는 `.mcp.json`으로 함께 옮겨지지만, PC마다 Claude Code에서 승인해야 한다.
- `humanize-korean` 플러그인은 2026-11-04에 DESKTOP-K58196E에서 설치했다. 다른 PC에서 쓰려면 설치 여부를 먼저 확인한다.

### 다음 단계
0. **11-06 재구성 목업을 사용자가 검토한다.** 아래 미결정 제안은 사용자가 나중에 정한다(실행 허가 아님).
   - REFLECTION 타임라인에 학습 자동화(10.19)와 프로세스 개선(10.29~11.06)이 한 카드에 함께 있다. 세 사례를 묶는 회고라 두었지만, 맥락 분리 기준을 엄격히 적용하면 프로젝트별로 나눌 수 있다.
   - CASE 02 카드 이미지(`prototype/img/case02-herdr-parallel.png`, 터미널 7개)는 카드 크기에서 글자가 읽히지 않는다. 대체 캡처를 받거나 Obsidian 위키 화면으로 바꾸는 안.
   - 카드의 교훈 문장(`.learn`)과 REFLECTION 타임라인 질문 문구는 기록을 보고 정리한 표현이다. 실제 경험담으로 바꿀지, 11.06 질문을 띄어쓰기 수정 없이 원문 그대로 인용할지.
   - CASE 01의 "화면 기준 5건": 11.06 게시 기록(`published.json`)에는 1건만 남아 있다. 학습 자동화 앱에서 게시 후 목록을 새로 고치면 기록과 맞춰진다.
   - 이전부터 남은 문구: Working Style 03 "확인 기준이 잘못되어 잘못 처리된" 표현, "AI가 처리한 일"과 "AI가 맡은 일" 용어 통일, 미사용 CSS `.chip`.
   - 정리되면 사용자 요청에 따라 게시본에 반영(HTML + `prototype/img/`)하고 커밋한다.
1. **화면 확인:** 이미지 팝업의 실제 클릭 동작, 다크 모드, 모바일 너비는 아직 보지 않았다. headless Edge는 창 최소 폭 때문에 모바일 캡처가 오른쪽이 잘려 실제 브라우저로 봐야 한다.
2. 상세 페이지 미확인 항목을 본다: 다크 모드, 모바일, 게시본의 버튼 동작, 마지막에 고친 프로세스 순서도 문구.
3. 승인되면 Next.js로 구현한다: 메뉴·좌측 레일·우측 슬롯(자리만), 카드 데이터 분리, 상세 페이지 2개의 라우트, `layout.tsx`의 제목과 `lang="ko"`, 토글 위치를 임시 고정 위치에서 상단 우측으로 이동. 목업의 해시 전환은 목업용이다.
4. 브라우저 확인: 다크 모드 토글·새로고침 시 깜빡임·시스템 설정 추종, 폰트 적용. 아직 직접 확인하지 못했다.
5. 스크린샷을 받으면 목업·구현에 반영한다.

## 1. 진행 내용

### 2026-11-06 (ICT PC) — 핵심 주제(CASE 01~03 + REFLECTION) 기준 목업 재작성
- **재작성:** Home 카드 3개 + REFLECTION, CASE별 상세 페이지 3개(개요·분석 및 계획·실제 화면·프로세스·발생한 문제·개선할 내용, CASE 02는 폴더 구조 포함). 근거는 `gptgit/project-prototype`·`project-management` 문서와 기록, `Claudecode/Project_Refactor/WORK_LOG.md`, 10.29 점검 보고서.
- **이미지:** Pillow 13.0.0을 `pip install --user`로 설치했다. `img/` 원본 14장 중 13장을 잘라 `prototype/img/case0N-*.png`로 저장했다(Notion 사이드바·업데이트 팝업·정품 인증·작업표시줄 제거, `notion 게시 작업.png`의 PC 경로 흐림). `case2 대체.png`는 CASE 03 카드용(`case03-card.png`)과 팝업용(`case03-question-full.png`)으로 잘랐다. `학습자료 분석 페이지2.png`(설정 화면), `병렬처리중2.png`(중복)는 쓰지 않았다.
- **사용자 수정 요청 반영:** 메뉴명 변경, 그림 설명 72자 너비 제한 제거(한 줄 표시), CASE 02·03 순서 교체(카드·상세·링크·이미지 파일명), CASE 03에서 Notion 수치(436회·288회·255자·재사용·0.124→0.040초)를 빼서 CASE 01 문제 5번과 개선표로 옮기고 project-management 수치(재지시 31건, 컨텍스트 94%·압축 7번, 자동 검토 약 151회·약 1,313만 토큰)로 대체, 이미지 가운데 팝업(`<dialog>`), 2열 이미지 16:10 통일.
- **추가 반영(사용자 승인 제안):** Home "4가지 기준" 칸을 Working Style(`#how`) 링크로 바꿨다. CASE 03 상세 머리말을 "여러 AI에게 일을 나눌수록 다시 하는 지시와 읽어야 할 맥락이 함께 늘었습니다"로 바꿨다.
- **상태 정정:** CASE 03 개선표의 "기록 자동 저장"은 `gptgit/project-prototype/docs/workflow.md:57`에 반영돼 있어 "시험 중"으로 적었다. "창 50% 마스터 교대"는 `project-prototype/docs/context-and-agents.md:51`에서 고정 기준으로 쓰지 않기로 되어 있어 그대로 적었다.
- **검증:** Python 스크립트로 태그 짝, 중복 id, 내부 링크·목차·이미지 경로, 미사용 이미지를 검사해 모두 0건. Notion 언급이 CASE 01 범위에만 있는지 확인했다. headless Edge(1400px)로 Home, AI Workflows 카드, CASE 01·03 상세를 캡처해 확인했다.
- **미확인:** 팝업 클릭 동작, 다크 모드, 모바일. 재설계 "9개 파일 965줄"은 실측으로 유지했다.

### 2026-11-04 (DESKTOP-K58196E) — 목업 문구 윤문과 버튼 통일
- **스킬 선정:** 한글 AI 문체 스킬 3종을 GitHub 정보와 `SKILL.md` 앞부분으로 비교해 `epoko77-ai/im-not-ai`(`humanize-korean`)를 추천했고, 사용자가 설치했다. 스크립트 코드는 검토하지 않았다.
- **`/humanize-scan`:** 6신호 중 C-8(대구 4회), E-1(100자 넘는 문장 0개), C-11(연결어미 뒤 쉼표 34회) 3개가 발동했다.
- **`추정` 표현 제거(5곳):** `:321` "확인과 미검증", `:339` "봤고", `:389` 범례 항목 삭제, `:517` "것으로 보입니다.", `:544` "예상치". `:517`과 `:544`는 단정이 되지 않도록 다른 말로 유보를 남겼고, 사용자가 단정을 원하는지는 확인하지 않았다.
- **윤문:** 작업 폴더는 세션 임시 폴더에 두어 저장소에 `_workspace/`를 만들지 않았다. 스킬이 light 경로를 골랐다. 31개 블록이 바뀌었고 대부분 쉼표 제거이며, 긴 문장 2개(`:340`, `:521`)를 나누고 `:299`, `:517`의 표현을 고쳤다. "A가 아니라 B" 4회와 "~습니다" 반복 구조는 그대로라 AI 느낌이 크게 줄었다고 보기는 어렵다.
- **버튼:** `:360`, `:373`에 `primary`를 더해 "근거와 상세 내용 보기" 3개를 파란색으로 맞췄다.
- **검증:** `verify_gates.py` 통과(문자 변경률 0.5%, 수치 주입·인용·문체 이상 없음). 블록별 수치·고유명사 대조에서 조사가 바뀐 `:299` 외에 차이가 없었다. 내부 링크 대상과 ID 중복에 이상이 없고, headless Edge로 PC 너비(1280px) Home을 한 번 캡처해 버튼 색을 확인했다.
- **미확인:** 윤문 후 상세 페이지, 모바일, 다크 모드는 화면으로 보지 않았다. `:517`의 `</dd>` 누락은 사용자 지시에 따라 그대로 두었다. `lint`, `build`는 실행하지 않았다(앱 코드 변경 없음).

### 2026-11-03 (ICT PC) — 환경 확인과 상세 페이지 목업
- **환경 확인:** 사용자가 `npm install`을 실행했다. 로컬과 원격 `main`이 `e5c9ed8`로 같고, Node v26.13.0, npm 11.20.0, 주요 패키지 버전, Context7 연결이 기록과 일치했다. `npm run lint`는 통과했다. `build`, `tsc --noEmit`, dev 서버는 이날 실행하지 않았다.
- **`npm audit`:** 21건(low 2, moderate 19)의 원인은 `minimatch`(ESLint 계열, `shadcn` → `ts-morph`)와 `deepmerge`(`shadcn` → `@shadcn/registry`) 두 권고다. `--omit=dev` 기준으로는 6건이 남고 모두 `shadcn` 경로다. `shadcn`이 `dependencies`에 있기 때문이며, 앱에서는 `app/globals.css:3`의 CSS import로만 쓴다. `npm audit fix --force`는 `shadcn@1.0.0`, `eslint@4.0.0`으로 내리므로 실행하지 않는다. 사용자 결정으로 그대로 둔다.
- **상세 페이지:** 목업에 해시 전환 방식(`#process-detail`, `#study-detail`)으로 2개를 추가하고, Home 카드에 진입 버튼을 넣었다. 게시 버전 `1793672112-56d1`. 각 프로젝트의 README, 설계·요구사항 문서, 작업기록, 리뷰 문서, 점검 보고서를 읽고 작성했다.
- **검증:** 내부 링크 대상과 ID 중복을 스크립트로 검사했고, headless Edge로 PC 너비(1280px) 두 페이지를 한 번 캡처했다. 끊어진 화살표와 칸을 넘는 글자를 고친 뒤에는 다시 캡처하지 않았다.
- **줄 수 실측:** 분석 프로그램(Python·HTML)은 `user_app` 34개 파일 5,900줄, 재설계 9개 파일 965줄이다. `Project_Refactor/WORK_LOG.md`의 "약 700줄"과 달라 목업에는 실측값을 썼다.

### 2026-11-02 (HOME PC) — 스택 마무리와 Home 목업
- **Context7:** 재시작 후 연결 확인. 이전 기록의 `CONNECTION_CLOSED`는 재현되지 않았다.
- **MDX:** `@next/mdx`, `@mdx-js/loader`, `@mdx-js/react`, `@types/mdx` 설치. `next.config.ts`를 `createMDX`로 감싸고 `pageExtensions`를 추가했으며 루트에 `mdx-components.tsx`를 만들었다. 임시 `app/mdx-check/page.mdx`로 정적 빌드를 확인한 뒤 지웠다.
- **다크 모드:** `next-themes` 0.4.6 설치. `app/layout.tsx`에 `ThemeProvider`(`attribute="class"`, 시스템 기본)와 `suppressHydrationWarning`을 넣었다. `components/theme-toggle.tsx`는 아이콘을 `dark:` CSS로 전환해 hydration 불일치를 피한다. 헤더가 없어 임시로 우상단에 고정했다.
- **`CLAUDE.md`:** shadcn·MDX 설치 상태, 다크 모드 방식을 실제에 맞게 고쳤다.
- **요구사항:** 사이트 제목 입력은 구현 작업이라, 먼저 요구사항을 정하고 목업으로 확인하는 순서로 돌렸다.
- **참고 사이트:** `poulo.site`는 Vercel 봇 방어(`X-Vercel-Mitigated: challenge`)로 자동 요청에 429를 준다. 우회하지 않고 사용자 동의 후 Claude in Chrome으로 열어 확인했다.
- **자료 읽기:** `gptgit/재취업 이력서`의 이력서 PDF 2개와 포트폴리오 PDF를 읽었다. `pdftotext`는 한글이 빠지고 Read 도구는 `pdftoppm`이 없어 실패해서, Windows 내장 PDF 렌더러(`Windows.Data.Pdf`, Windows PowerShell 5.1)로 이미지화했다. 이미지는 읽은 뒤 지웠다. 10/25 이력서 3~5쪽은 이미지로 보지 않았다.
- **목업:** 이력서·포트폴리오·프로젝트 작업기록(11-02까지)으로 내용을 채우고 프로세스 개선 중심으로 재구성했다. 스크린샷은 자리만 있다. 구현은 하지 않았다.

### 2026-11-02 (HOME PC) — shadcn 초기화
- **npm install:** 이 셸에서는 `npm`이 PATH에 없었다. Node.js는 `C:\Program Files\nodejs`에 이미 있었고(v26.13.0, npm 11.20.0), 시스템 PATH 레지스트리에도 있었다. 세션 안에서만 PATH에 추가해 설치했다(357개 패키지).
  - `npm audit`에서 moderate 16개가 보고됐다. 이전 기록(0개)과 다르며 원인은 확인하지 않았다. `npm audit fix --force`는 실행하지 않았다.
- **shadcn/ui 초기화:** `npx shadcn@latest init -d -y`(shadcn 4.23.0, 프리셋 `base-nova`, base-ui 기반, lucide, neutral, CSS 변수 사용).
  - 생성: `components.json`, `components/ui/button.tsx`, `lib/utils.ts`. 추가 의존성: `@base-ui/react`, `class-variance-authority`, `cn`, `lucide-react`, `shadcn`, `tw-animate-css`.
  - Tailwind의 Turbopack 로더 구조(`postcss.config.*`, `tailwind.config.*` 없음)와 충돌하지 않았다.
  - **직접 수정:** init이 `app/globals.css`에 `--font-sans: var(--font-sans)`(자기참조)를 써서 Geist가 적용되지 않을 상태였다. `--font-geist-sans`를 가리키도록 고쳤다(`app/globals.css:10`).
  - `lib/utils.ts`의 `cn`은 `clsx`/`tailwind-merge`가 아니라 `cn` npm 패키지(0.5.2)에서 가져온다. 이 shadcn 버전이 생성한 그대로이며 shadcn 자체도 이 패키지에 의존한다.
- **Context7 `CONNECTION_CLOSED` 진단:** `.mcp.json`의 `cmd /c npx -y @upstash/context7-mcp`는 Node 경로를 PATH에 넣고 직접 실행하면 정상 동작한다. Claude Code 프로세스가 Node 경로가 반영되기 전에 시작된 것으로 추정된다(서버 stderr는 확인하지 못했다). `/mcp` 재연결만으로는 PATH가 갱신되지 않으므로 완전한 재시작이 필요하다.
- 이 세션에서는 Context7이 안 돼 shadcn 공식 문서를 확인하지 못했다. CLI `--help`와 실행 결과만 근거로 했다.

### 2026-10-30 (ICT PC)
- **Node.js 설치:** ICT PC에 Node.js가 없었다. 사용자 확인 후 `winget install OpenJS.NodeJS.LTS`로 v26.13.0(npm 11.20.0)을 설치했다.
- **프로젝트 생성:** `create-next-app .`은 폴더명 대문자 때문에 실패했다("name can no longer contain capital letters").
  - 세션 임시 폴더에 `project-webportfolio`로 생성하고(`--skip-install`) 이 폴더로 복사한 뒤 `npm install` 했다. 패키지 357개, 취약점 0개.
  - 사용한 옵션: `--ts --tailwind --eslint --app --import-alias "@/*" --use-npm --disable-git --no-agent-feedback`. `src/`는 쓰지 않는다.
- **Context7 MCP:** `claude mcp add --scope project context7 -- cmd /c npx -y @upstash/context7-mcp`로 등록했다.
  - `.mcp.json`이 먼저 있으면 create-next-app이 폴더가 비어 있지 않다고 실패할 수 있어 프로젝트 생성 뒤로 순서를 바꿨다.
- **CLAUDE.md:** `/init`으로 작성했다. 생성된 `AGENTS.md`는 `@AGENTS.md`로 불러온다.
- 커밋·push: `0498cca 20261030_ICTwork_webportfolio_init`.

## 2. 확인한 사실
- 설치 버전: Next 16.4.3, React 19.3.0, Tailwind 4.3.3, ESLint 9, TypeScript 5, shadcn 4.23.0.
- `next.config.ts`에 `cacheComponents: true`, `partialPrefetching: true`가 기본으로 켜져 있다.
- Tailwind는 `@tailwindcss/turbopack` 로더로 처리된다. 토큰은 `app/globals.css`의 `@theme inline`에서 정의한다.
- `AGENTS.md`의 nextjs-agent-rules 블록은 `next dev`가 자동으로 다시 쓴다.
- Next.js 공식 문서가 `node_modules/next/dist/docs/`에 들어 있다.
- `npm install` 시 `unrs-resolver` postinstall 스크립트가 allowScripts 대상이 아니라는 경고가 나온다. 설치·lint·build에는 영향이 없다.
- headless Edge 캡처는 명령이 끝난 뒤 파일이 늦게 생긴다(11-06 ICT PC에서 Git Bash로도 기다리면 생성됨). 같은 프로필로 동시에 실행하면 충돌한다. 해시로 섹션을 지정하면 빈 화면이 찍혀, 다른 섹션을 숨기고 `<base href>`를 넣은 임시 사본을 찍었다. 경로: `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`.
- 목업 수정과 게시는 `Claudecode/Project_webportfolio/prototype/portfolio-mockup.html`을 기준으로 한다. 사용자가 이 파일을 직접 고치므로 게시본을 읽어 수정하지 않는다.
- `LayoutProps` 같은 전역 타입은 `next build`/`next dev` 후에 생성된다. 빌드 전 `tsc --noEmit`은 실패할 수 있다.
- winget 설치 직후 열려 있던 셸·프로세스에는 Node.js 경로가 반영되지 않는다. 터미널과 Claude Code를 다시 열어야 한다.

## 3. 참고
- commit과 push는 사용자가 요청할 때만 한다.
- 커밋 메시지 형식: `날짜_장소_간단한 내용`. 장소는 집이면 `HOMEwork`, ICT PC면 `ICTwork`.
