import { Fragment } from "react";

import { home } from "@/content/home";

// content/home.ts 규칙: 문자열 안의 "\n"은 <br>로 렌더링한다.
function Lines({ text }: { text: string }) {
  return text.split("\n").map((line, i) => (
    <Fragment key={i}>
      {i > 0 && <br />}
      {line}
    </Fragment>
  ));
}

const splitBox = "rounded-[18px] border border-border bg-card px-5 py-4";
const splitTitle =
  "mb-1 block font-heading text-[13px] font-bold text-accent-ink";

export function WorkingStyle() {
  const { eyebrow, title, lead, split, principles } = home.how;

  return (
    <section id="how" className="scroll-mt-5 py-16 min-[641px]:py-24">
      <div className="mx-auto w-[min(1040px,calc(100%-32px))]">
        <p className="mb-3.5 font-heading text-[13px] font-bold tracking-[0.04em] text-accent-ink">
          {eyebrow}
        </p>
        <h2 className="text-[clamp(28px,3.4vw,40px)] font-extrabold">
          {title}
        </h2>
        <p className="mt-3.5 text-pretty break-keep text-muted-foreground">
          <Lines text={lead} />
        </p>
        <div className="mt-7 grid gap-3 min-[641px]:grid-cols-2">
          <div className="rounded-[18px] border border-transparent bg-accent-soft px-5 py-4">
            <b className={splitTitle}>{split.me.title}</b>
            <span className="text-[14.5px]">{split.me.text}</span>
          </div>
          <div className={splitBox}>
            <b className={splitTitle}>{split.ai.title}</b>
            <span className="text-[14.5px]">{split.ai.text}</span>
          </div>
        </div>
        <div className="mt-9 grid gap-3.5 min-[641px]:grid-cols-2">
          {principles.map((p) => (
            <article
              key={p.n}
              className="rounded-[22px] border border-border bg-card p-[26px]"
            >
              <span className="font-heading text-[13px] font-extrabold text-accent-ink">
                {p.n}
              </span>
              <h3 className="my-2 text-[21px]">{p.title}</h3>
              <dl className="mt-3.5 grid gap-3">
                <div className="grid grid-cols-[78px_1fr] gap-2.5">
                  <dt className="pt-0.5 font-heading text-[12.5px] font-bold text-accent-ink">
                    운영에서
                  </dt>
                  <dd className="m-0 text-[14.5px] text-muted-foreground">
                    {p.onSite}
                  </dd>
                </div>
                <div className="grid grid-cols-[78px_1fr] gap-2.5">
                  <dt className="pt-0.5 font-heading text-[12.5px] font-bold text-accent-ink">
                    AI와 함께
                  </dt>
                  <dd className="m-0 text-[14.5px] text-muted-foreground">
                    {p.withAi}
                  </dd>
                </div>
              </dl>
              <a
                className="mt-4 inline-block text-[13.5px] font-medium text-accent-ink underline"
                href={p.link.href}
              >
                {p.link.label}
              </a>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
