"use client"

import { useEffect, useRef, useState } from "react"

type CopyState = "idle" | "copied" | "failed"

const btnBase =
  "inline-flex h-12 items-center gap-2 rounded-full border px-5 text-sm font-bold transition-transform duration-150 hover:-translate-y-px"

// mailto:는 PC에 기본 메일 앱이 없으면 아무 반응이 없다. 그래서 주소 복사를 기본 동작으로 두고,
// 메일 앱이 있는 사람을 위한 mailto:와 웹메일 쓰기 링크를 함께 제공한다.
export function ContactActions({ email }: { email: string }) {
  const [state, setState] = useState<CopyState>("idle")
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  useEffect(() => () => clearTimeout(timer.current), [])

  async function copy() {
    try {
      await navigator.clipboard.writeText(email)
      setState("copied")
    } catch {
      // 비보안 환경이나 권한 거부 시에는 사용자가 직접 복사하도록 알린다.
      setState("failed")
    }
    clearTimeout(timer.current)
    timer.current = setTimeout(() => setState("idle"), 3000)
  }

  const to = encodeURIComponent(email)
  const gmail = `https://mail.google.com/mail/?view=cm&fs=1&to=${to}`
  const outlook = `https://outlook.live.com/mail/0/deeplink/compose?to=${to}`

  return (
    <div className="flex flex-col items-start gap-3 max-sm:w-full">
      <button
        type="button"
        onClick={copy}
        className={`${btnBase} cursor-pointer border-primary bg-primary text-primary-foreground`}
      >
        {state === "copied" ? "복사됨" : "메일 주소 복사"}
      </button>
      <p role="status" aria-live="polite" className="min-h-5 text-[13px] opacity-80">
        {state === "copied" && "메일 주소를 복사했습니다."}
        {state === "failed" && "복사하지 못했습니다. 위 주소를 직접 복사해 주세요."}
      </p>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[13px] font-medium">
        <a className="underline underline-offset-4" href={`mailto:${email}`}>
          메일 앱으로 열기
        </a>
        <a
          className="underline underline-offset-4"
          href={gmail}
          target="_blank"
          rel="noopener noreferrer"
        >
          Gmail에서 쓰기
        </a>
        <a
          className="underline underline-offset-4"
          href={outlook}
          target="_blank"
          rel="noopener noreferrer"
        >
          Outlook에서 쓰기
        </a>
      </div>
    </div>
  )
}
