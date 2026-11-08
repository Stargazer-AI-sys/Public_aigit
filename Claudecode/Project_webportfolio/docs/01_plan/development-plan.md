# Project_webportfolio Development Plan

> 작성 2026-11-06 | 상태: **사용자 승인(2026-11-06)** | 근거: `WORK_LOG.md` §0 사용자 결정(11-02~11-06), `prototype/portfolio-mockup.html`(11-06 커밋 `59c7852` 기준), `CLAUDE.md`
> 진행 방식은 `.claude/skills/subagent-dev/SKILL.md`를 따른다. 담당자는 자기 Task 절과 1~3절만 읽으면 된다.

## 1. 목표와 범위

- **목표:** 사용자 검토를 마친 목업(`prototype/portfolio-mockup.html`)을 Next.js 앱으로 옮긴다. 화면 구성과 문구는 목업을 그대로 따르고, 카드 내용은 데이터 파일로 분리한다.
- **이번 범위에 넣는 것**
  - 공통 레이아웃: 상단 메뉴(Home / Working Style / AI Workflows, 중앙), 우측 끝 모드 버튼과 연락하기, 좌측 섹션 레일, 우측 진행률 슬롯(자리만), 배경 장식, 연락 푸터.
  - Home 한 페이지 안의 3섹션: Home(hero·수치), Working Style(원칙 카드 4개), AI Workflows(CASE 카드 3개 + REFLECTION 카드).
  - CASE 상세 페이지 3개: 개요, 분석 및 계획, 실제 화면, 프로세스 순서도, 발생한 문제, 개선할 내용(CASE 02는 폴더 구조 포함).
  - 이미지 가운데 팝업(lightbox), 다크 모드(`.dark` 클래스 방식 유지), `lang="ko"`와 사이트 제목.
- **이번 범위에서 빼는 것**
  - 진행률 대시보드 실제 구현(우측 슬롯 자리만 둔다), 내용 수정 화면, 배포, 새 스크린샷 반영(사용자가 줄 때 별도 진행).
  - 문구 수정. 목업 문구를 글자 그대로 옮긴다. 남은 문구 확인 2건(`WORK_LOG.md` 다음 단계 0)은 구현 뒤 데이터 파일에서 고친다.
  - `npm audit` 21건 조치(사용자 결정으로 보류).
- **결정(2026-11-06 사용자 승인, 마스터 추천안 채택)**
  1. **폰트:** 목업과 같은 Manrope + Noto Sans KR로 바꾼다. `next/font/google` 사용. Geist는 제거한다.
  2. **상세 페이지 콘텐츠 형식:** TypeScript 데이터 파일 + 공통 컴포넌트. 세 페이지 구성이 같고 순서도가 SVG라서다. MDX 설정은 그대로 두고 이후 글 작성용으로 남긴다.
  3. **상세 페이지 주소:** 별도 라우트 `/cases/case-01`~`/cases/case-03`. 목업의 해시 전환은 목업용이라는 기존 결정과 맞다.

## 2. 기술 기준

스택과 설정상 주의점(`cacheComponents`, Tailwind Turbopack 로더, `.dark` 클래스, 전역 타입 헬퍼)은 `CLAUDE.md`를 따른다. 이번 개발에서 새로 정하는 것만 적는다.

- **문구 원본:** 모든 화면 문구는 `prototype/portfolio-mockup.html`에서 그대로 복사한다. 담당자가 문구를 다듬거나 요약하지 않는다.
- **색상 토큰:** 목업 `:root`와 다크 변수(`portfolio-mockup.html:13-40`)를 `app/globals.css`의 shadcn 변수에 매핑한다. 목업에만 있는 값(`--sky`, `--accent-soft`, `--btn-line`, `--cloud` 등)은 같은 이름으로 추가하고 `@theme inline`에 연결한다. 목업의 `data-theme` / `prefers-color-scheme` 방식은 옮기지 않고 `.dark` 클래스로 바꾼다. 포인트 색은 `#4B89DC`.
- **데이터 파일:** `content/` 폴더에 둔다. 사이트는 aigit의 다른 폴더를 읽지 않는다.
- **이미지:** `prototype/img/`의 15장을 `public/img/`로 복사해 `next/image`로 쓴다. `prototype/img/`는 지우지 않는다.
- **클라이언트 컴포넌트:** 상태나 브라우저 API가 필요한 것(테마 토글, 섹션 레일의 현재 위치, lightbox)만 `"use client"`로 한다.
- **Next.js 코드 작성 전:** `node_modules/next/dist/docs/`의 해당 가이드를 읽는다(특히 동적 라우트·`generateStaticParams`, 캐싱 `01-app/01-getting-started/08-caching.md`, `next/image`, `next/font`).

## 3. 구조

- **라우트**
  - `/` — Home. 섹션 id `home`, `how`, `projects`. 메뉴와 레일은 이 id로 이동한다.
  - `/cases/[slug]` — `case-01`, `case-02`, `case-03`. `generateStaticParams`로 정적 생성한다.
- **컴포넌트(예정)**
  - `components/site-header.tsx`, `components/theme-toggle.tsx`(기존, 이동), `components/section-rail.tsx`, `components/progress-slot.tsx`, `components/site-footer.tsx`, `components/sky-background.tsx`
  - `components/home/hero.tsx`, `components/home/working-style.tsx`, `components/home/workflows.tsx`, `components/lightbox.tsx`
  - `components/case/case-sections.tsx`, `components/case/flow-case-0N.tsx`
- **데이터 파일(예정)**
  - `content/home.ts` — hero, 수치 3칸, 역할 구분, 원칙 카드 4개, CASE 카드 3개, REFLECTION 카드
  - `content/cases/case-0N.ts` — 상세 페이지 1개분
  - `content/site.ts` — 사이트 제목, 메뉴, 연락 메일(`hanmir777@naver.com`)

## 4. Phase / Task

상태: 대기 / 진행 / 검토 / 완료. 선행 조건이 풀렸고 변경 파일이 겹치지 않는 Task는 Phase가 달라도 동시에 돌린다(2026-11-06 사용자 지시). 동시에 돌릴 때 담당자는 자기 파일만 `npx eslint <파일>`·`npx tsc --noEmit --incremental false`로 확인하고, `npm run build`·dev 서버 확인은 마스터가 통합 때 한다(같은 `.next`를 동시에 쓰면 충돌한다). 여러 Task가 같은 파일에 연결해야 하면 담당자는 연결하지 않고 마스터가 통합 Task(`-I`)에서 연결한다.

### Phase 1 — 공통 레이아웃과 테마

완료 확인: dev 서버 `/`에서 상단 메뉴·모드 버튼·연락하기, 좌측 레일, 우측 슬롯, 배경, 푸터가 목업 위치에 보이고 라이트/다크 전환이 된다.

| ID | 목표 | 담당 | 변경 허용 파일 | 선행 | 상태 |
|---|---|---|---|---|---|
| P1-T1 | 목업 색상 토큰을 테마 변수로 매핑 | sonnet | `app/globals.css` | - | 완료 |
| P1-T2 | 언어·제목·폰트 교체 | haiku | `app/layout.tsx`, `content/site.ts`, `app/globals.css`(폰트 변수 줄만) | P1-T1 | 완료 |
| P1-T3 | 상단 메뉴와 우측 도구(토글·연락하기) | sonnet | `components/site-header.tsx`, `components/theme-toggle.tsx`, `app/layout.tsx`, `content/site.ts`(메뉴 링크만) | P1-T2 | 완료 |
| P1-T4 | 좌측 섹션 레일과 우측 진행률 슬롯, 메뉴 현재 위치 표시 | sonnet | `components/section-rail.tsx`, `components/progress-slot.tsx`, `hooks/use-active-section.ts`, `components/site-header.tsx` | P1-T3 | 완료 |
| P1-T5 | 배경 장식과 연락 푸터 | haiku | `components/sky-background.tsx`, `components/site-footer.tsx` | P1-T3 | 완료 |
| P1-I | P1-T4·T5 컴포넌트를 레이아웃에 연결, 통합 검증 | 마스터 | `app/layout.tsx` | P1-T4, P1-T5 | 완료 |

#### P1-T1 목업 색상 토큰을 테마 변수로 매핑
- 해야 할 일: 2절 "색상 토큰" 기준대로 `:root`와 `.dark`의 값을 목업 값으로 바꾸고 목업 전용 토큰을 추가한다. 목업의 `body`, `h1~h3` 기본 스타일(`portfolio-mockup.html:44-45`)을 `@layer base`에 옮긴다.
- 참고: `portfolio-mockup.html:12-45`, 현재 `app/globals.css`.
- 주의: `@import "tailwindcss"`, `@custom-variant dark` 구조는 유지한다. `tailwind.config.*`를 만들지 않는다. shadcn 변수 이름은 바꾸지 않는다(`components/ui/button.tsx`가 쓴다).
- 완료 조건: `npm run lint`, `npm run build` 통과. 변경한 변수 목록을 보고한다.

#### P1-T2 언어·제목·폰트 교체
- 해야 할 일: `lang="ko"`. `content/site.ts`를 만들어 사이트 제목·설명·메뉴 항목·연락 메일을 넣고 `metadata`에서 쓴다. 결정 1에 따라 폰트를 Manrope(제목용)와 Noto Sans KR(본문)로 바꾼다. `globals.css`의 `@theme inline` 폰트 줄(`--font-sans`, `--font-heading`, `--font-mono`)만 고쳐 `--font-heading`은 Manrope → Noto Sans KR 순, `--font-sans`는 Noto Sans KR을 가리키게 한다(P1-T1 이후 제목 기본 스타일이 `font-heading`을 쓴다). Geist는 제거하고, `--font-mono`는 목업에서 고정폭 글꼴을 쓰는 곳이 없으면 시스템 고정폭 글꼴로 둔다.
- 제목·설명 문구는 목업 `<title>`과 hero에서 가져오고, 새로 짓지 않는다.
- 완료 조건: `npm run build` 통과, 빌드 결과 HTML에 `lang="ko"`와 제목 확인.

#### P1-T3 상단 메뉴와 우측 도구
- 해야 할 일: 목업 `.nav`(`portfolio-mockup.html:294-304`)와 해당 CSS를 Tailwind 클래스로 옮긴다. 메뉴는 중앙, 모드 버튼과 연락하기는 맨 우측. `layout.tsx`의 임시 고정 토글을 지우고 헤더에 넣는다. 메뉴 항목은 `content/site.ts`에서 읽는다.
- 주의: 토글은 지금처럼 아이콘을 `dark:` CSS로 전환해 hydration 불일치를 피한다. 아이콘은 `lucide-react` 또는 목업 SVG.
- 완료 조건: lint·build 통과, dev 서버에서 토글이 동작하고 새로고침 시 콘솔 hydration 경고가 없음.

#### P1-T4 좌측 섹션 레일과 우측 진행률 슬롯
- 해야 할 일: 목업 `.rail`, `.slot`(`portfolio-mockup.html:306-307`)을 옮긴다. 레일은 현재 보이는 섹션에 `aria-current`를 붙인다(IntersectionObserver). 슬롯은 "진행률 / 대시보드 / 예약 영역" 자리만 둔다.
- 상단 메뉴의 `aria-current`(P1-T3에서 Home에 고정)도 같은 섹션 감지 훅(`hooks/use-active-section.ts`)으로 바꾼다. 메뉴 부분만 클라이언트 컴포넌트로 분리해도 된다.
- `layout.tsx`에는 연결하지 않는다(P1-I에서 마스터가 연결).
- 완료 조건: 자기 파일 eslint·tsc 통과. 상세 페이지(`/cases/*`)에서는 레일을 어떻게 할지 보고만 한다(구현은 P3에서 판단).

#### P1-T5 배경 장식과 연락 푸터
- 해야 할 일: 목업 `.sky`/`.cloud`(`:292`)와 `footer#contact`(`:936-943`)를 옮긴다. 메일 주소는 `content/site.ts`에서 읽는다.
- `layout.tsx`에는 연결하지 않는다(P1-I에서 마스터가 연결).
- 완료 조건: 자기 파일 eslint·tsc 통과, 다크 모드 색이 목업 다크 값과 같은 토큰을 쓰는지 보고.

### Phase 2 — Home (Home / Working Style / AI Workflows)

완료 확인: `/`가 목업 Home과 같은 문구·순서로 보이고, 카드 이미지를 누르면 가운데 팝업이 열린다.

| ID | 목표 | 담당 | 변경 허용 파일 | 선행 | 상태 |
|---|---|---|---|---|---|
| P2-T1 | 이미지 15장 복사 | haiku | `public/img/*` | - | 완료 |
| P2-T2 | Home 데이터 파일 | sonnet | `content/home.ts` | - | 완료 |
| P2-T3 | Hero·수치·Working Style 섹션 | sonnet | `components/home/hero.tsx`, `components/home/working-style.tsx` | P2-T2 | 완료 |
| P2-T4 | AI Workflows 카드 섹션(이미지 팝업 연결 포함) | sonnet | `components/home/workflows.tsx` | P2-T2, P2-T5 | 완료 |
| P2-T5 | 이미지 팝업 | sonnet | `components/lightbox.tsx` | - | 완료 |
| P2-T6 | Home 페이지 조립 | haiku | `app/page.tsx` | P2-T1, T3, T4, T5 | 완료 |

#### P2-T1 이미지 복사
- `prototype/img/`의 png 15장을 같은 파일명으로 `public/img/`에 복사한다. 원본은 지우지 않는다. 완료 조건: 두 폴더의 파일 목록과 크기가 같음.

#### P2-T2 Home 데이터 파일
- 해야 할 일: 목업 `portfolio-mockup.html:310-423`의 문구를 타입을 정의해 `content/home.ts`로 옮긴다. 카드마다 태그, 상태, 제목, 요약, 문제/제 판단/결과, 교훈, 기술 태그, 이미지 경로·alt, 상세 링크(`/cases/case-0N`)를 둔다. 원칙 카드의 연결 링크는 `#p-case1` 등 Home 안의 카드 id를 유지한다.
- 주의: 문구는 글자·따옴표·줄바꿈(`<br>`)까지 그대로 옮긴다. 줄바꿈은 문자열 배열이나 `\n`으로 표현하고 방식을 보고한다.
- 완료 조건: `npx tsc --noEmit` 통과(전역 타입 미생성으로 실패하면 build로 대신). 옮긴 항목 수(원칙 4, CASE 3, REFLECTION 1)를 보고한다.

#### P2-T3 Hero·수치·Working Style 섹션
- 목업 `#home`, `#how` 섹션과 CSS를 옮기고 `content/home.ts`에서 읽는다. 버튼 2개는 같은 모양(파란색, `↗` 없음).
- 완료 조건: lint·build 통과.

#### P2-T4 AI Workflows 카드 섹션
- 목업 `#projects`(카드 `wide` 3개 + `feature` 1개)와 CSS를 옮긴다. 카드 대표 이미지는 크기를 통일한다. "근거와 상세 내용 보기" 버튼 3개는 파란색(`primary`).
- 카드 이미지는 `components/lightbox.tsx`의 `ZoomImage`로 감싼다(`image.fullSrc`를 팝업에 연다).
- 완료 조건: 자기 파일 eslint·tsc 통과.

#### P2-T5 이미지 팝업
- 목업 `dialog.lightbox`(`:944`)와 스크립트(`:946` 이후)의 동작을 React로 옮긴다: 이미지를 누르면 가운데 팝업, 닫기 버튼·배경 클릭·Esc로 닫힘, 캡션 표시. 다른 컴포넌트에서 쓰도록 `ZoomImage` 같은 진입 컴포넌트를 함께 내보낸다.
- 완료 조건: lint·build 통과, 사용 예시를 보고에 적는다.

#### P2-T6 Home 페이지 조립
- `app/page.tsx`의 템플릿을 지우고 섹션을 순서대로 넣는다(섹션 id `home`, `how`, `projects`).
- 완료 조건: lint·build 통과, dev 서버 `/` 200, 메뉴·레일 이동 동작.

### Phase 3 — CASE 상세 페이지 3개

완료 확인: Home 카드의 "근거와 상세 내용 보기"로 각 상세 페이지가 열리고, 목업 상세 페이지와 문구·순서가 같다.

| ID | 목표 | 담당 | 변경 허용 파일 | 선행 | 상태 |
|---|---|---|---|---|---|
| P3-T1 | 상세 라우트와 공통 섹션 컴포넌트, 상세 페이지의 레일·메뉴 처리 | sonnet | `app/cases/[slug]/page.tsx`, `components/case/case-sections.tsx`, `content/cases/types.ts`, `content/cases/index.ts`, `components/section-rail.tsx`, `components/site-header.tsx` | P2-T5 | 완료 |
| P3-T2 | CASE 01 데이터와 순서도 | sonnet | `content/cases/case-01.ts`, `components/case/flow-case-01.tsx` | P3-T1 | 완료 |
| P3-T3 | CASE 02 데이터·폴더 구조·순서도 | sonnet | `content/cases/case-02.ts`, `components/case/flow-case-02.tsx` | P3-T1 | 완료 |
| P3-T4 | CASE 03 데이터와 순서도 | sonnet | `content/cases/case-03.ts`, `components/case/flow-case-03.tsx` | P3-T1 | 완료 |
| P3-T5 | 링크·이미지·id 점검(수정 없음) | haiku | 없음(보고만) | P3-T2~T4 | 완료 |

#### P3-T1 상세 라우트와 공통 섹션 컴포넌트
- 해야 할 일: `generateStaticParams`로 3개 slug를 정적 생성한다. 머리(태그·제목·머리말), 목차, 섹션 블록(개요·분석 및 계획·실제 화면·프로세스 순서도·발생한 문제·개선할 내용, 선택 섹션 폴더 구조)을 공통 컴포넌트로 만든다. 데이터 타입을 `content/cases/types.ts`에 정의하고, 없는 slug는 `notFound()`.
- 참고: 목업 `#case1-detail`(`:425-585`)의 구조와 CSS. Next 동적 라우트·`cacheComponents` 문서를 먼저 읽는다.
- 상세 페이지(`/cases/*`)에서는 목업처럼 좌측 레일을 숨기고, 상단 메뉴는 AI Workflows를 현재 위치(`aria-current`)로 표시한다(`usePathname`).
- `content/cases/index.ts`에 slug → 데이터 매핑을 두고, 아직 없는 CASE는 빈 자리(placeholder) 데이터로 둔다. P3-T2~T4가 각자 파일을 채운다.
- 완료 조건: 자기 파일 eslint·tsc 통과. build와 정적 생성 확인은 마스터가 한다.

#### P3-T2 ~ P3-T4 CASE별 데이터와 순서도
- 각 담당 범위: CASE 01 `:425-585`, CASE 02 `:586-793`, CASE 03 `:794-935`.
- 문구는 그대로 옮긴다. 인라인 SVG 순서도는 `flow-case-0N.tsx`로 옮기고, 색은 `currentColor`나 토큰 변수로 바꿔 다크 모드에서 보이게 한다. SVG `marker` id는 페이지마다 다르게 유지한다(`arrow-s`, `arrow-p`, `arrow-c`).
- 이미지는 P2-T5의 팝업 진입 컴포넌트를 쓴다.
- 완료 조건: lint·build 통과, 해당 페이지 dev 서버 200.

#### P3-T5 링크·이미지·id 점검
- 빌드 결과나 dev 서버 HTML에서 내부 링크 대상, 이미지 경로, 중복 id, 목업 대비 빠진 섹션을 검사해 목록으로 보고한다. 파일은 고치지 않는다.

### Phase 4 — 화면 검증과 마무리

완료 확인: 아래 검증이 모두 통과하고, 발견된 문제가 수정 Task로 처리됐다.

| ID | 목표 | 담당 | 변경 허용 파일 | 선행 | 상태 |
|---|---|---|---|---|---|
| P4-T1 | lint·tsc·build 실행과 결과 요약 | haiku | 없음(보고만) | P3 완료 | 완료 |
| P4-T2 | 브라우저 확인(다크 모드·모바일·팝업·목업 대조) | sonnet | 없음(보고만, 캡처는 scratchpad) | P4-T1 | 완료 |
| P4-T3 | 상세 페이지 hydration 불일치·params Suspense 오류·레일 미숨김 수정 | sonnet | `app/cases/[slug]/page.tsx` 외 3개 | 마스터 확인 | 완료 |
| P4-T4 | 목업 대비 스타일 차이(hero 버튼·링크 밑줄·hero 여백·수치 카드·LCP 이미지) | sonnet | `components/home/*.tsx`, `components/case/case-sections.tsx` | P4-T2 | 완료 |

#### P4-T2 브라우저 확인
- Playwright MCP(project `.mcp.json`)로 1400px·375px 너비에서 `/`와 `/cases/case-0N`을 캡처한다. 확인 항목: 다크 모드 토글과 새로고침 시 깜빡임, 시스템 설정 추종, 폰트 적용, 팝업 열고 닫기, 메뉴·레일 이동, 목업과 문구·순서 차이.
- 실행 중인 dev 서버가 있으면 그것을 쓰고, 없으면 새로 띄운 서버만 끝낸다. 기존 서버는 끄지 않는다.
- 보고: 문제 목록(화면, 너비, 모드, 증상), 캡처 경로.

## 5. 검증 계획

- **Task 단위:** 담당자가 완료 조건을 실행하고, 마스터가 `git diff`로 변경 범위를 확인한 뒤 lint·build를 다시 확인한다.
- **Phase 단위:** `npm run build`, dev 서버에서 Phase 완료 확인 항목을 사용자에게 보고한다. 다음 Phase는 사용자 확인 뒤 시작한다.
- `LayoutProps` 등 전역 타입은 build/dev 이후에 생기므로, 빌드 전 `tsc --noEmit` 실패는 build로 다시 확인한다.

## 6. 변경 이력

- 2026-11-06: 초안 작성(목업 `59c7852` 기준).
- 2026-11-06: 미정 3건을 추천안으로 확정, 사용자 승인. Phase 1 시작.
- 2026-11-06: 사용자 지시로 겹치지 않는 Task 병렬 실행. P1-T4·T5의 layout 연결을 마스터 통합 Task(P1-I)로 분리. 푸터의 목업 안내 문단("목업입니다…")은 목업 전용 표기라 제외. 상세 페이지에서는 목업처럼 레일을 숨기고 메뉴는 AI Workflows를 현재 위치로 표시한다(P3-T1). Phase 1 완료.
- 2026-11-06: Phase 2 완료(통합 build 통과, 1400px 화면·이미지 팝업·레일/메뉴 현재 위치 확인). P3-T1은 이미지 팝업만 필요해 P2와 병렬로 진행했다.
- 2026-11-06: Phase 3 완료(통합 lint·tsc·build 통과, 상세 3개 정적 생성, P3-T5 링크·이미지·id 점검 0건). P4-T1은 마스터 통합 검증으로 대신했다.
- 2026-11-06: P4-T3에서 `/cases/[slug]`의 params 읽기를 Suspense 안으로 옮겼다(근거 `adopting-partial-prefetching.md`). 그 결과 목록 밖 slug는 not-found 화면이 나오지만 HTTP 상태는 200이다(`not-found.md`의 스트리밍 동작). 상세 3개뿐이라 그대로 둔다.
- 2026-11-06: hero 버튼은 목업 `.btn`(흰 배경)을 따른다. `WORK_LOG.md`의 11-06 결정 문구("파란색·↗ 없음")와 엇갈려 사용자 확인 대상으로 남긴다.
- 2026-11-06: Phase 4 완료. P4-T4로 hero 버튼(목업 `.btn`), 본문 링크 밑줄, hero 상단 여백(150px), 수치 카드 높이(102px)를 맞췄다. LCP 경고 이미지는 첫 화면 밖이라 `loading="eager"`를 붙이지 않았고, 맨 위에서 새로 열었을 때 경고가 나오지 않음을 확인했다. 최종 lint·tsc·build 통과, 콘솔 오류·경고 0건.
