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

const btn =
  "inline-flex h-11 items-center gap-2 rounded-full border border-btn-line bg-card px-5 text-sm font-medium text-foreground no-underline transition-[transform,border-color] duration-150 hover:-translate-y-px hover:border-primary";

const proofBox =
  "rounded-[18px] border border-border bg-card px-5 py-[18px]";

export function Hero() {
  const { hero, proof } = home;

  return (
    <section id="home" className="scroll-mt-5 pb-[72px] pt-[150px]">
      <div className="mx-auto w-[min(1040px,calc(100%-32px))]">
        <div className="grid items-center gap-12 min-[961px]:grid-cols-[auto_1fr]">
          <div>
            <h1 className="text-[28px] font-extrabold break-keep min-[375px]:text-[clamp(34px,4.4vw,54px)]">
              <Lines text={hero.title} />
            </h1>
            <div className="mt-[26px] flex flex-wrap gap-2.5">
              {hero.actions.map((a) => (
                <a key={a.href} className={btn} href={a.href}>
                  {a.label}
                </a>
              ))}
            </div>
          </div>
          <div className="[&_p]:break-keep [&_p]:text-pretty">
            <p className="text-[15px] text-muted-foreground">{hero.hello}</p>
            <p className="mt-2.5 font-medium text-foreground">{hero.lead}</p>
            <p className="mt-3.5 text-[15px] text-muted-foreground">
              <Lines text={hero.sub} />
            </p>
          </div>
        </div>
        <div className="mt-16 grid gap-3 min-[641px]:grid-cols-3">
          {proof.map((p) => {
            const body = (
              <>
                <b className="block font-heading text-[26px] font-extrabold leading-[normal] tracking-[-0.03em]">
                  {p.value}
                </b>
                <span
                  className={
                    p.href
                      ? "text-[13.5px] text-accent-ink"
                      : "text-[13.5px] text-muted-foreground"
                  }
                >
                  {p.label}
                </span>
              </>
            );
            return p.href ? (
              <a
                key={p.value}
                href={p.href}
                className={`${proofBox} block text-inherit no-underline transition-colors duration-200 hover:border-primary focus-visible:border-primary`}
              >
                {body}
              </a>
            ) : (
              <div key={p.value} className={proofBox}>
                {body}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
