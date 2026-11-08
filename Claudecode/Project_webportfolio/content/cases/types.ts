// CASE 상세 페이지 데이터 타입. 구조는 prototype/portfolio-mockup.html 425-935줄(#case1~3-detail)을 따른다.
// 표기 규칙
//  - 문자열 안의 "\n"은 <br> 줄바꿈이다(content/home.ts와 같은 규칙).
//  - 따옴표(“ ”)와 화살표(→ ←)는 문자 그대로 쓴다. HTML 엔티티는 쓰지 않는다.
//  - 목업의 <span class="ev">확인</span> 배지는 `ev: true`로 표현한다. 배지 글자는 컴포넌트가 "확인"으로 그린다.
//  - 섹션은 `sections` 배열 순서대로 그려진다(CASE마다 순서가 다르다: CASE 02는 폴더 구조·순서도 뒤에 실제 화면).
//  - 섹션 id는 목업과 같게 쓴다(c1-overview, c2-tree ...). 목차(`head.toc`)의 id와 맞아야 한다.

import type { ComponentType } from "react";

export type CaseSlug = "case-01" | "case-02" | "case-03";

export type Link = { label: string; href: string };

/** 머리(.detail-head) */
export type CaseHead = {
  back: Link; // ← AI Workflows로 돌아가기. href는 /#p-caseN
  eyebrow: string;
  title: string; // h1
  lead: string; // .section-lead, "\n" = <br>
  toc: { id: string; label: string }[]; // id는 섹션 id
  legend: CaseLegendItem[];
};

/** .legend 한 칸. badge가 있으면 앞에 굵은 배지(.ev)를 붙인다. */
export type CaseLegendItem = { badge?: string; text: string };

/** 상세 페이지 하단 이동 버튼(.detail-next). primary는 파란 버튼. */
export type CaseFooterLink = Link & { primary?: boolean };

// ── 섹션 안의 블록 ─────────────────────────────

/** 본문 단락. 섹션 첫머리 설명(.block > .wrap > p). */
export type ParagraphBlock = { type: "paragraph"; text: string };

/** 소제목 h3. ev가 true면 뒤에 확인 배지를 붙인다. */
export type HeadingBlock = { type: "heading"; text: string; ev?: boolean };

/** 수치 타일(.tiles > .tile). */
export type TilesBlock = {
  type: "tiles";
  items: { value: string; label: string }[];
};

/** 2칸 상자(.split). highlight는 연한 파란 배경(.me). */
export type SplitBlock = {
  type: "split";
  items: { title: string; text: string; highlight?: boolean }[];
};

export type StatusTone = "done" | "part" | "plain";
/** 표 칸. 문자열이거나 상태 배지(.st done/part/없음). */
export type TableCell = string | { status: string; tone: StatusTone };

/**
 * 표(.tbl). columns가 머리글.
 * rowHeader가 true면 각 행의 첫 칸이 <th scope="row">(굵게), false면 일반 칸(상태 배지 표 등).
 */
export type TableBlock = {
  type: "table";
  columns: string[];
  rowHeader: boolean;
  rows: TableCell[][];
};

/** 순서 카드(.flow > .step). highlight는 마지막 단계 강조(.step.how). */
export type StepsBlock = {
  type: "steps";
  items: { title: string; text: string; highlight?: boolean }[];
};

/** 실제 화면(.shots). src는 /img/... (public 기준), wide는 가로 전체 폭. */
export type ShotsBlock = {
  type: "shots";
  items: { src: string; alt: string; caption: string; wide?: boolean }[];
};

/**
 * 프로세스 순서도(figure.diagram).
 * Flow는 CASE별 컴포넌트(components/case/flow-case-0N.tsx)다. <svg>만 반환하고,
 * 칸·글자 클래스(.box .on .me .todo .t .s .me-t .me-s .lb .lbh)는 목업 이름 그대로 쓴다.
 */
export type DiagramBlock = {
  type: "diagram";
  Flow: ComponentType;
  caption: string;
};

/** 발생한 문제 카드 목록(.issues > .issue). 번호는 순서대로 자동 부여. */
export type IssuesBlock = {
  type: "issues";
  items: {
    title: string;
    rows: { label: string; text: string; ev?: boolean }[]; // 근거 / 원인 / 조치 / 영향 / 배경 ...
  }[];
};

/** 트리 한 줄 안의 조각: 일반 글자, 굵은 파란 글자(<b>), 흐린 주석(<i>). */
export type TreeSpan = string | { bold: string } | { note: string };
/** 폴더 구조(pre.tree). 줄마다 조각 배열. 들여쓰기와 ├─ 기호는 글자 그대로 넣는다. */
export type TreeBlock = { type: "tree"; lines: TreeSpan[][] };

export type CaseBlock =
  | ParagraphBlock
  | HeadingBlock
  | TilesBlock
  | SplitBlock
  | TableBlock
  | StepsBlock
  | ShotsBlock
  | DiagramBlock
  | IssuesBlock
  | TreeBlock;

/** 섹션(.block). id는 목업과 같게(c1-overview ...). */
export type CaseSection = {
  id: string;
  title: string; // h2
  blocks: CaseBlock[];
};

/** 상세 페이지 1개분. */
export type CaseData = {
  slug: CaseSlug;
  head: CaseHead;
  sections: CaseSection[];
  footerLinks: CaseFooterLink[];
};
