# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## 작업기록

- 작업 전에 `WORK_LOG.md`를 먼저 읽고 "현재 상태"와 "다음 단계"부터 이어간다.
- 사용자가 "작업기록"이라고 하면 이 폴더의 `WORK_LOG.md`를 뜻한다(다른 프로젝트의 같은 이름 문서와 구분).
- `WORK_LOG.md`는 작업 중 수시로 갱신하지 않는다. 사용자가 작업을 마칠 때 요청하면 한 번에 정리한다.

## 개발 진행 규칙 (이 프로젝트 전용)

개발 작업은 `subagent-dev` 스킬(`.claude/skills/subagent-dev/SKILL.md`)의 절차를 따른다. 핵심만 요약한다.

- **기획서 먼저:** `docs/01_plan/development-plan.md`를 만들고 사용자 승인을 받은 뒤, Phase 안의 Task 단위로 쪼개 위임한다. 기획서 없이 Task를 넘기지 않는다.
- **역할 분리:** Opus 5.5(현재 대화)는 마스터로서 판단·지시·검토·통합만 한다. 구현은 작업의 복잡성과 양에 따라 Sonnet 5.5 또는 Haiku 5.5 담당자에게 맡긴다.
- **herdr 작업 공간:** 실제 탭·pane·cwd·세션을 확인한 뒤 작업한다. 마스터 대화 탭은 분할하지 않고, 담당용 새 탭을 만들어 그 안에서만 pane을 분할한다. 같은 작업 묶음은 확인 후 담당 탭을 공유하고, 묶음이 바뀌면 새 담당 탭을 만든다. 사용자 요청 없이 포커스를 옮기거나 기존 창·서버를 종료하지 않는다.

## 프로젝트

Next.js App Router 기반 블로그형 포트폴리오. 목표 스택은 Next.js + TypeScript + Tailwind CSS v4 + shadcn/ui + MDX.

설치된 버전: Next 16.4.3, React 19.3.0, Tailwind 4.3.3, TypeScript 5, ESLint 9, shadcn CLI ^4.23.0. Node.js 26 / npm.

shadcn/ui 설정(`components.json`): style `base-nova`(Base UI 기반, `@base-ui/react`), baseColor `neutral`, CSS 변수 사용, 아이콘 `lucide`, RSC 켜짐. 별칭: `@/components`, `@/components/ui`, `@/lib/utils`, `@/hooks`. 컴포넌트 추가는 `npx shadcn@latest add <name>`.

## 명령어

패키지 매니저는 npm (`package-lock.json`).

```bash
npm run dev      # 개발 서버 (http://localhost:3000)
npm run build    # 프로덕션 빌드 (타입 검사 포함)
npm run start    # 빌드 결과 실행
npm run lint     # ESLint (flat config, eslint-config-next core-web-vitals + typescript)
npx tsc --noEmit # 타입 검사만
```

테스트 프레임워크는 아직 없다.

## 문서 확인 순서

- 학습 데이터의 Next.js와 다를 수 있다. Next.js 코드를 쓰기 전에 `node_modules/next/dist/docs/`의 해당 가이드를 먼저 읽는다 (AGENTS.md 규칙).
  - MDX: `01-app/02-guides/mdx.md`, `01-app/03-api-reference/03-file-conventions/mdx-components.md`
  - 캐싱: `01-app/01-getting-started/08-caching.md`
- 그 외 라이브러리(shadcn/ui, Tailwind v4, MDX 관련 패키지)는 Context7 MCP(`.mcp.json`, project scope)로 최신 문서를 확인한다.
- `AGENTS.md`의 nextjs-agent-rules 블록은 `next dev`가 자동으로 다시 쓴다. 수정·삭제하지 않는다.

## 아키텍처와 설정상 주의점

- **App Router만 사용**, `src/` 없이 루트 `app/`. import alias `@/*` → 프로젝트 루트(`./*`).
- **`next.config.ts`에 `cacheComponents: true`, `partialPrefetching: true`가 켜져 있다.** 데이터 페칭·캐싱·동적 렌더링 동작이 기존 Next.js와 다르므로 캐싱 가이드를 확인하고 작성한다.
- **Tailwind는 PostCSS가 아니라 Turbopack 로더(`@tailwindcss/turbopack`)로 처리된다.** `postcss.config.*`가 없는 것이 정상이다. 설정은 CSS-first: `app/globals.css`의 `@import "tailwindcss"`와 `@theme inline`에서 토큰을 정의하고 `tailwind.config.*`는 만들지 않는다(`components.json`의 `tailwind.config`도 빈 값). shadcn init 후에도 이 구조가 유지되며, v4에서 shadcn CLI는 설정 파일을 만들지 않는다.
- 테마 색상은 `globals.css`의 shadcn CSS 변수(`:root` / `.dark`의 `--background`, `--primary`, `--border` 등, oklch)를 `@theme inline`으로 Tailwind 색상에 매핑한다. 다크 모드는 `@custom-variant dark (&:is(.dark *))`로 **`.dark` 클래스 방식**이다(이전의 `prefers-color-scheme` 아님). `next-themes`의 `ThemeProvider`(`attribute="class"`, 시스템 설정 기본)가 `app/layout.tsx`에서 `<html>`에 `.dark`를 붙이고, `<html>`에는 `suppressHydrationWarning`이 필요하다. 토글은 `components/theme-toggle.tsx`(아이콘은 `dark:` CSS로 전환해 hydration 불일치를 피함)이며 헤더가 생기기 전까지 레이아웃의 고정 위치(우상단)에 임시로 두었다.
- 폰트는 `app/layout.tsx`에서 `next/font/google`(Geist, Geist Mono)을 CSS 변수로 주입한다.
- 레이아웃/페이지 props는 Next 16 전역 타입 헬퍼(`LayoutProps<"/">`, `PageProps<...>`)를 사용한다.

## 저장소

- 이 폴더는 상위 `Aigit` git 저장소의 하위 디렉터리다 (git root: `C:/Users/ICT/Desktop/Aigit`). 별도 git init을 하지 않는다.
- 폴더명 `Project_webportfolio`에 대문자가 있어 `create-next-app .`이 npm 이름 규칙으로 실패한다. 패키지명은 `project-webportfolio`.
- Windows 환경: MCP 등 npx 기반 stdio 서버는 `cmd /c npx ...` 형태로 등록한다.
