import Image from "next/image";
import Link from "next/link";
import { Fragment } from "react";

import { ZoomImage } from "@/components/lightbox";
import type {
  CaseBlock,
  CaseData,
  CaseFooterLink,
  CaseHead,
  CaseSection,
  StatusTone,
  TableCell,
  TreeSpan,
} from "@/content/cases/types";

// 목업 #case1~3-detail(portfolio-mockup.html 425-935줄)과 <style>의 상세 페이지 CSS(183-238, 273-288줄)를 옮긴 것.
// 문구는 모두 content/cases/case-0N.ts 값이다. 문자열 안의 "\n"은 <br>로 그린다.

const wrap = "mx-auto w-[min(1040px,calc(100%-2rem))]";
const evBadge = "text-xs font-medium text-accent-ink";

function Lines({ text }: { text: string }) {
  return text.split("\n").map((line, i) => (
    <Fragment key={i}>
      {i > 0 && <br />}
      {line}
    </Fragment>
  ));
}

function Ev() {
  return <b className={evBadge}>확인</b>;
}

// ── 머리 ─────────────────────────────────────────

export function CaseHeader({ head }: { head: CaseHead }) {
  return (
    <header className="pt-[120px] max-sm:pt-24">
      <div className={wrap}>
        <Link
          href={head.back.href}
          className="mb-[22px] inline-block text-sm font-medium text-accent-ink hover:underline"
        >
          {head.back.label}
        </Link>
        {head.eyebrow ? (
          <p className="mb-3.5 font-heading text-[13px] font-bold tracking-[0.04em] text-accent-ink">
            {head.eyebrow}
          </p>
        ) : null}
        <h1 className="mt-3.5 break-keep text-[clamp(28px,4.4vw,50px)] font-extrabold max-sm:text-2xl">
          {head.title}
        </h1>
        {head.lead ? (
          <p className="mt-3.5 text-pretty break-keep text-[17px] text-muted-foreground">
            <Lines text={head.lead} />
          </p>
        ) : null}
        {head.toc.length > 0 ? (
          <nav
            aria-label="상세 페이지 목차"
            className="mt-[26px] flex flex-wrap gap-1.5"
          >
            {head.toc.map((item) => (
              <a
                key={item.id}
                href={`#${item.id}`}
                className="rounded-full border border-border bg-card px-3.5 py-1.5 text-[13.5px] text-muted-foreground hover:border-primary hover:text-foreground"
              >
                {item.label}
              </a>
            ))}
          </nav>
        ) : null}
        {head.legend.length > 0 ? (
          <p className="mt-[18px] flex flex-wrap gap-x-[18px] gap-y-2 text-[13px] text-muted-foreground">
            {head.legend.map((item, i) => (
              <span key={i}>
                {item.badge ? (
                  <>
                    <b className={evBadge}>{item.badge}</b>{" "}
                  </>
                ) : null}
                {item.text}
              </span>
            ))}
          </p>
        ) : null}
      </div>
    </header>
  );
}

// ── 블록 ─────────────────────────────────────────

const statusClass: Record<StatusTone, string> = {
  done: "border-primary bg-primary text-white",
  part: "border-transparent bg-accent-soft text-accent-ink",
  plain: "border-border text-muted-foreground",
};

function Cell({ cell }: { cell: TableCell }) {
  if (typeof cell === "string") return cell;
  return (
    <span
      className={`inline-block rounded-full border px-[9px] py-px text-xs font-medium whitespace-nowrap ${statusClass[cell.tone]}`}
    >
      {cell.status}
    </span>
  );
}

const cellBase = "border-t border-border px-4 py-[13px] text-left align-top";

function Tree({ lines }: { lines: TreeSpan[][] }) {
  return (
    <pre className="mt-4 overflow-x-auto rounded-[18px] border border-border bg-card px-[22px] py-5 font-mono text-[13.5px] leading-[1.75] whitespace-pre text-foreground">
      {lines.map((line, i) => (
        <Fragment key={i}>
          {i > 0 && "\n"}
          {line.map((span, j) =>
            typeof span === "string" ? (
              <Fragment key={j}>{span}</Fragment>
            ) : "bold" in span ? (
              <b key={j} className="font-bold text-accent-ink">
                {span.bold}
              </b>
            ) : (
              <i key={j} className="text-muted-foreground not-italic">
                {span.note}
              </i>
            ),
          )}
        </Fragment>
      ))}
    </pre>
  );
}

// 순서도 SVG의 클래스 이름(.box .on .me .todo .t .s .me-t .me-s .lb .lbh)은 목업 그대로 쓴다.
// 목업의 ".scroll-x .box" 같은 CSS를 이 래퍼의 하위 선택자로 옮겼다.
const diagramSvgClass = [
  "[&_svg]:block [&_svg]:h-auto [&_svg]:w-full [&_svg]:min-w-[760px] [&_svg]:text-muted-foreground",
  "[&_.box]:fill-background [&_.box]:stroke-border [&_.box]:[stroke-width:1.5]",
  "[&_.box.on]:fill-accent-soft [&_.box.on]:stroke-primary",
  "[&_.box.me]:fill-btn-dark [&_.box.me]:stroke-btn-dark",
  "[&_.box.todo]:fill-none [&_.box.todo]:stroke-muted-foreground [&_.box.todo]:[stroke-dasharray:5_4]",
  "[&_.t]:fill-foreground [&_.t]:font-sans [&_.t]:text-[14px] [&_.t]:font-bold [&_.t]:[text-anchor:middle]",
  "[&_.s]:fill-muted-foreground [&_.s]:font-sans [&_.s]:text-[12px] [&_.s]:font-normal [&_.s]:[text-anchor:middle]",
  "[&_.me-t]:fill-btn-dark-ink [&_.me-t]:font-sans [&_.me-t]:text-[14px] [&_.me-t]:font-bold [&_.me-t]:[text-anchor:middle]",
  "[&_.me-s]:fill-btn-dark-ink [&_.me-s]:font-sans [&_.me-s]:text-[12px] [&_.me-s]:font-normal [&_.me-s]:opacity-75 [&_.me-s]:[text-anchor:middle]",
  "[&_.lb]:fill-muted-foreground [&_.lb]:font-sans [&_.lb]:text-[12px] [&_.lb]:font-medium",
  "[&_.lbh]:fill-accent-ink [&_.lbh]:font-sans [&_.lbh]:text-[13px] [&_.lbh]:font-bold",
].join(" ");

const splitTitle =
  "mb-1 block font-heading text-[13px] font-bold text-accent-ink";

function Block({ block }: { block: CaseBlock }) {
  switch (block.type) {
    case "paragraph":
      return (
        <p className="mt-3 text-pretty break-keep text-muted-foreground">
          <Lines text={block.text} />
        </p>
      );

    case "heading":
      return (
        <h3 className="mt-[30px] mb-3 text-lg font-bold">
          {block.text}
          {block.ev ? (
            <>
              {" "}
              <Ev />
            </>
          ) : null}
        </h3>
      );

    case "tiles":
      return (
        <div className="mt-6 grid grid-cols-4 gap-3 max-[760px]:grid-cols-2">
          {block.items.map((item, i) => (
            <div
              key={i}
              className="rounded-[18px] border border-border bg-card p-[18px]"
            >
              <b className="block font-heading text-2xl font-extrabold tracking-[-0.03em] tabular-nums">
                {item.value}
              </b>
              <span className="mt-0.5 block text-[13.5px] text-muted-foreground">
                {item.label}
              </span>
            </div>
          ))}
        </div>
      );

    case "split":
      return (
        <div className="mt-7 grid grid-cols-2 gap-3 max-[640px]:grid-cols-1">
          {block.items.map((item, i) => (
            <div
              key={i}
              className={`rounded-[18px] border px-5 py-4 ${
                item.highlight
                  ? "border-transparent bg-accent-soft"
                  : "border-border bg-card"
              }`}
            >
              <b className={splitTitle}>{item.title}</b>
              <span className="text-[14.5px]">{item.text}</span>
            </div>
          ))}
        </div>
      );

    case "table":
      return (
        <div className="mt-4 overflow-x-auto rounded-[18px] border border-border bg-card">
          <table className="w-full min-w-[620px] border-collapse text-[14.5px]">
            <thead>
              <tr>
                {block.columns.map((col, i) => (
                  <th
                    key={i}
                    scope="col"
                    className="px-4 py-[13px] text-left align-top font-heading text-[12.5px] font-bold tracking-[0.03em] whitespace-nowrap text-accent-ink"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {block.rows.map((row, r) => (
                <tr key={r}>
                  {row.map((cell, c) =>
                    block.rowHeader && c === 0 ? (
                      <th
                        key={c}
                        scope="row"
                        className={`${cellBase} font-bold whitespace-nowrap`}
                      >
                        <Cell cell={cell} />
                      </th>
                    ) : (
                      <td
                        key={c}
                        className={`${cellBase} text-muted-foreground`}
                      >
                        <Cell cell={cell} />
                      </td>
                    ),
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );

    case "steps":
      return (
        <div className="mt-4 grid gap-2.5">
          {block.items.map((item, i) => (
            <div
              key={i}
              className={`grid grid-cols-[78px_1fr] gap-3 rounded-2xl border px-4 py-3.5 ${
                item.highlight
                  ? "border-transparent bg-accent-soft"
                  : "border-border bg-background"
              }`}
            >
              <b className="pt-0.5 font-heading text-[12.5px] font-bold tracking-[0.03em] text-accent-ink">
                {item.title}
              </b>
              <p className="text-[14.5px] text-foreground">{item.text}</p>
            </div>
          ))}
        </div>
      );

    case "shots":
      return (
        <div className="mt-5 grid grid-cols-2 gap-[18px] max-[640px]:grid-cols-1">
          {block.items.map((item) => (
            <figure
              key={item.src}
              className={`m-0 ${item.wide ? "col-span-full" : ""}`}
            >
              <ZoomImage
                src={item.src}
                alt={item.alt}
                caption={item.caption}
                className="block cursor-zoom-in overflow-hidden rounded-[18px] border border-border bg-card"
              >
                {/* 원본 크기는 이미지마다 달라 width/height 0 + h-auto로 원래 비율을 따른다. */}
                <Image
                  src={item.src}
                  alt={item.alt}
                  width={0}
                  height={0}
                  sizes={item.wide ? "(max-width: 1072px) 100vw, 1040px" : "(max-width: 640px) 100vw, 520px"}
                  className={`block h-auto w-full ${
                    item.wide
                      ? ""
                      : "aspect-[16/10] object-cover object-left-top"
                  }`}
                />
              </ZoomImage>
              <figcaption className="mt-2.5 text-[13.5px] text-muted-foreground">
                {item.caption}
              </figcaption>
            </figure>
          ))}
        </div>
      );

    case "diagram": {
      const { Flow } = block;
      return (
        <figure className="mt-5 mb-0">
          <div
            tabIndex={0}
            role="group"
            aria-label="프로세스 순서도, 좁은 화면에서는 가로로 스크롤합니다"
            className={`overflow-x-auto rounded-[18px] border border-border bg-card p-[18px] ${diagramSvgClass}`}
          >
            <Flow />
          </div>
          <figcaption className="mt-3 text-[13.5px] text-muted-foreground">
            {block.caption}
          </figcaption>
        </figure>
      );
    }

    case "issues":
      return (
        <div className="mt-5 grid gap-3">
          {block.items.map((issue, i) => (
            <article
              key={i}
              className="grid grid-cols-[34px_1fr] gap-x-3 gap-y-1 rounded-[20px] border border-border bg-card px-6 py-[22px] max-[640px]:grid-cols-1"
            >
              <span className="pt-px font-heading text-[15px] font-extrabold text-accent-ink tabular-nums">
                {i + 1}
              </span>
              <h3 className="m-0 text-[17px] font-bold">
                {issue.title}
              </h3>
              <dl className="col-start-2 mt-2.5 grid gap-[7px] max-[640px]:col-start-1">
                {issue.rows.map((row, j) => (
                  <div
                    key={j}
                    className="grid grid-cols-[56px_1fr] gap-2.5 max-[640px]:grid-cols-1 max-[640px]:gap-0"
                  >
                    <dt className="pt-0.5 font-heading text-[12.5px] font-bold text-accent-ink">
                      {row.label}
                    </dt>
                    <dd className="m-0 text-[14.5px] text-muted-foreground">
                      {row.text}
                      {row.ev ? (
                        <>
                          {" "}
                          <span className={evBadge}>확인</span>
                        </>
                      ) : null}
                    </dd>
                  </div>
                ))}
              </dl>
            </article>
          ))}
        </div>
      );

    case "tree":
      return <Tree lines={block.lines} />;
  }
}

// ── 섹션 ─────────────────────────────────────────

export function CaseSectionView({ section }: { section: CaseSection }) {
  return (
    <section id={section.id} className="scroll-mt-[60px] pt-16">
      <div className={wrap}>
        <h2 className="text-[clamp(24px,2.8vw,32px)] font-extrabold">
          {section.title}
        </h2>
        {section.blocks.map((block, i) => (
          <Block key={i} block={block} />
        ))}
      </div>
    </section>
  );
}

// ── 하단 이동 버튼(.detail-next) ───────────────────

const btn =
  "inline-flex h-11 items-center gap-2 rounded-full border px-5 text-sm transition-[transform,border-color] duration-150 hover:-translate-y-px hover:border-primary";

export function CaseFooterNav({ links }: { links: CaseFooterLink[] }) {
  if (links.length === 0) return null;
  return (
    <div className="mt-14 flex flex-wrap justify-between gap-3">
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={`${btn} ${
            link.primary
              ? "border-primary bg-primary font-bold text-white"
              : "border-btn-line bg-card font-medium text-foreground"
          }`}
        >
          {link.label}
        </Link>
      ))}
    </div>
  );
}

// ── 페이지 전체 ──────────────────────────────────

export function CaseDetail({ data }: { data: CaseData }) {
  return (
    <main>
      <CaseHeader head={data.head} />
      {data.sections.map((section) => (
        <CaseSectionView key={section.id} section={section} />
      ))}
      <div className={`${wrap} pb-10`}>
        <CaseFooterNav links={data.footerLinks} />
      </div>
    </main>
  );
}
