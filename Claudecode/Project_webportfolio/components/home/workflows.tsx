import Image from "next/image";
import Link from "next/link";
import { Fragment } from "react";

import { ZoomImage } from "@/components/lightbox";
import { home, type CaseCard, type ReflectionCard } from "@/content/home";

// 목업 section#projects(.plist .pcard)를 옮긴 것. 문구는 content/home.ts 값만 쓴다.

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

function Learn({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[14.5px] font-medium text-accent-ink">{children}</p>
  );
}

const cardBase =
  "scroll-mt-[84px] rounded-[24px] border border-border bg-card p-[26px]";

function FlowStep({
  label,
  text,
  highlight,
}: {
  label: string;
  text: string;
  highlight?: boolean;
}) {
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

function WideCard({ card }: { card: CaseCard }) {
  return (
    <article
      id={card.id}
      className={`${cardBase} col-span-full grid grid-cols-1 gap-7 min-[961px]:grid-cols-[1fr_1.25fr] [&>*]:min-w-0`}
    >
      <div className="flex flex-col gap-3.5">
        <div className="flex flex-wrap items-center justify-between gap-2.5">
          <Tag>{card.tag}</Tag>
          <State>{card.state}</State>
        </div>
        <h3 className="text-[22px]">{card.title}</h3>
        <p className="text-[15px] text-muted-foreground">{card.summary}</p>
        <div className="grid gap-2.5">
          <FlowStep label="문제" text={card.flow.problem} />
          <FlowStep label="제 판단" text={card.flow.judgment} highlight />
          <FlowStep label="결과" text={card.flow.result} />
        </div>
        <Learn>{card.learn}</Learn>
        <Link
          href={card.detailHref}
          className="inline-flex h-11 items-center gap-2 self-start rounded-full border border-primary bg-primary px-5 text-sm font-bold text-primary-foreground transition hover:-translate-y-px"
        >
          {card.detailLabel}
        </Link>
        <div className="mt-auto flex flex-wrap gap-1.5">
          {card.techTags.map((t) => (
            <Tag key={t}>{t}</Tag>
          ))}
        </div>
      </div>
      {/* 카드 이미지는 같은 영역·같은 방식(왼쪽 위 기준 cover)으로 잘라 크기를 통일한다.
          cover는 카드 높이(약 640px)에 맞춰 늘리므로 가로로 넓은 이미지(CASE 02)는 표시 폭이 1100px을 넘는다.
          sizes를 카드 폭(580px)으로 두면 640w 이미지를 받아 확대해 흐려지므로 표시 폭 기준으로 준다. */}
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
    </article>
  );
}

function FeatureCard({ card }: { card: ReflectionCard }) {
  return (
    <article
      id={card.id}
      className={`${cardBase} col-span-full flex flex-col gap-[18px]`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2.5">
        <Tag>{card.tag}</Tag>
        <State>{card.state}</State>
      </div>
      <h3 className="text-[clamp(24px,3vw,30px)]">{card.title}</h3>
      <p className="text-[15px] text-muted-foreground">{card.summary}</p>
      <ol className="m-0 list-none p-0">
        {card.timeline.map((item) => (
          <li
            key={item.time}
            className="grid grid-cols-1 gap-1 border-t border-border py-4 min-[641px]:grid-cols-[96px_1fr] min-[641px]:gap-3.5"
          >
            <time className="pt-[3px] font-heading text-[13px] font-bold tabular-nums text-accent-ink">
              {item.time}
            </time>
            <div>
              <b className="mb-[3px] block text-base font-bold">{item.title}</b>
              <p className="text-[14.5px] text-muted-foreground">
                {item.text}{" "}
                <a
                  href={item.evidence.href}
                  className="text-xs font-medium text-accent-ink underline"
                >
                  {item.evidence.label}
                </a>
              </p>
            </div>
          </li>
        ))}
      </ol>
      <div className="grid grid-cols-1 gap-3 min-[641px]:grid-cols-2">
        <div className="rounded-[18px] border border-transparent bg-accent-soft px-5 py-4">
          <b className="mb-1 block font-heading text-[13px] font-bold text-accent-ink">
            {card.current.title}
          </b>
          <span className="text-[14.5px]">{card.current.text}</span>
        </div>
        <div className="rounded-[18px] border border-border bg-card px-5 py-4">
          <b className="mb-1 block font-heading text-[13px] font-bold text-accent-ink">
            {card.next.title}
          </b>
          <span className="text-[14.5px]">{card.next.text}</span>
        </div>
      </div>
      <Learn>{card.learn}</Learn>
    </article>
  );
}

export function Workflows() {
  const { eyebrow, title, lead, cases, reflection } = home.projects;

  return (
    <section id="projects" className="scroll-mt-5 py-16 min-[641px]:py-24">
      <div className="mx-auto w-[min(1040px,calc(100%-32px))]">
        <p className="mb-3.5 font-heading text-[13px] font-bold tracking-[.04em] text-accent-ink">
          {eyebrow}
        </p>
        <h2 className="text-[clamp(28px,3.4vw,40px)] font-extrabold">{title}</h2>
        <p className="mt-3.5 text-pretty break-keep text-muted-foreground">
          <Lines text={lead} />
        </p>
        <div className="mt-8 grid grid-cols-1 gap-3.5 min-[641px]:grid-cols-2">
          {cases.map((card) => (
            <WideCard key={card.id} card={card} />
          ))}
          <FeatureCard card={reflection} />
        </div>
      </div>
    </section>
  );
}
