import Image from "next/image";
import Link from "next/link";
import { Fragment } from "react";

import { ZoomImage } from "@/components/lightbox";
import { home, type SideCard, type SideFlowStep } from "@/content/home";

// 목업 section#side(article#p-side1)를 옮긴 것. 문구는 content/home.ts 값만 쓴다.
// workflows.tsx의 WideCard 모양을 따르며, 공통 조각은 그 파일을 고치지 않으려고 복사했다.

function Lines({ text }: { text: string }) {
  const parts = text.split("\n");
  return (
    <>
      {parts.map((part, i) => (
        <Fragment key={i}>
          {i > 0 ? <br /> : null}
          {part}
        </Fragment>
      ))}
    </>
  );
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-block rounded-full bg-accent-soft px-[11px] py-[3px] text-[12.5px] font-medium text-accent-ink">
      {children}
    </span>
  );
}

function State({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full border border-border px-2.5 py-0.5 text-[12.5px] text-muted-foreground">
      {children}
    </span>
  );
}

function FlowStep({ label, text, highlight }: SideFlowStep) {
  return (
    <div
      className={`grid grid-cols-[78px_1fr] gap-3 rounded-2xl border px-4 py-3.5 ${
        highlight
          ? "border-transparent bg-accent-soft"
          : "border-border bg-background"
      }`}
    >
      <b className="pt-0.5 font-heading text-[12.5px] font-bold tracking-[.03em] text-accent-ink">
        {label}
      </b>
      <p className="text-[14.5px]">{text}</p>
    </div>
  );
}

// 이미지가 오기 전까지 카드 크기를 맞추는 자리 표시(목업 .shot .frame).
function ImagePlaceholder() {
  return (
    <div
      aria-hidden="true"
      className="relative grid min-h-[320px] place-items-center overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-accent-soft to-sky"
    >
      <div className="flex h-[68%] w-[72%] flex-col gap-2 rounded-[14px] border border-border bg-card p-3.5 shadow-[0_14px_40px_rgba(30,60,110,.14)]">
        <span className="block h-2 w-[38%] rounded-lg bg-border" />
        <span className="block h-2.5 w-[90%] rounded-lg bg-accent-soft" />
        <span className="block h-2.5 w-[72%] rounded-lg bg-accent-soft" />
        <span className="mt-auto block h-6 w-[34%] rounded-full bg-accent opacity-85" />
      </div>
      <small className="absolute bottom-3 left-4 text-xs text-muted-foreground">
        Slack 대화 화면 · 이미지 준비 중
      </small>
    </div>
  );
}

function SideWideCard({ card }: { card: SideCard }) {
  return (
    <article
      id={card.id}
      className="col-span-full grid scroll-mt-[84px] grid-cols-1 gap-7 rounded-[24px] border border-border bg-card p-[26px] min-[961px]:grid-cols-[1fr_1.25fr] [&>*]:min-w-0"
    >
      <div className="flex flex-col gap-3.5">
        <div className="flex flex-wrap items-center justify-between gap-2.5">
          <Tag>{card.tag}</Tag>
          <State>{card.state}</State>
        </div>
        <h3 className="text-[22px]">{card.title}</h3>
        <p className="text-[15px] text-muted-foreground">{card.summary}</p>
        <div className="grid gap-2.5">
          {card.flow.map((step) => (
            <FlowStep key={step.label} {...step} />
          ))}
        </div>
        <p className="text-[14.5px] font-medium text-accent-ink">{card.learn}</p>
        <Link
          href={card.detailHref}
          className="inline-flex h-11 items-center gap-2 self-start rounded-full border border-primary bg-primary px-5 text-sm font-bold text-primary-foreground transition hover:-translate-y-px"
        >
          {card.detailLabel}
        </Link>
        <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-[13.5px]">
          {card.repoLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-accent-ink"
            >
              {link.label}
            </a>
          ))}
        </div>
        <div className="mt-auto flex flex-wrap gap-1.5">
          {card.techTags.map((t) => (
            <Tag key={t}>{t}</Tag>
          ))}
        </div>
      </div>
      {card.image ? (
        <ZoomImage
          src={card.image.fullSrc}
          alt={card.image.alt}
          className="relative block min-h-[320px] cursor-zoom-in overflow-hidden rounded-2xl border border-border bg-card"
        >
          <Image
            src={card.image.src}
            alt={card.image.alt}
            fill
            sizes="(max-width: 960px) 100vw, 1200px"
            className="object-cover object-left-top"
          />
        </ZoomImage>
      ) : (
        <ImagePlaceholder />
      )}
    </article>
  );
}

export function SideProjects() {
  const { eyebrow, title, lead, cards } = home.side;

  return (
    <section id="side" className="scroll-mt-5 py-16 min-[641px]:py-24">
      <div className="mx-auto w-[min(1040px,calc(100%-32px))]">
        <p className="mb-3.5 font-heading text-[13px] font-bold tracking-[.04em] text-accent-ink">
          {eyebrow}
        </p>
        <h2 className="text-[clamp(28px,3.4vw,40px)] font-extrabold">{title}</h2>
        <p className="mt-3.5 text-pretty break-keep text-muted-foreground">
          <Lines text={lead} />
        </p>
        <div className="mt-8 grid grid-cols-1 gap-3.5 min-[641px]:grid-cols-2">
          {cards.map((card) => (
            <SideWideCard key={card.id} card={card} />
          ))}
        </div>
      </div>
    </section>
  );
}
