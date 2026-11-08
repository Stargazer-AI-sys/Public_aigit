"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

import { useActiveSection } from "@/hooks/use-active-section"

const railItems = [
  { id: "home", label: "Home", href: "/#home" },
  { id: "how", label: "Working Style", href: "/#how" },
  { id: "projects", label: "AI Workflows", href: "/#projects" },
] as const

export function SectionRail() {
  const active = useActiveSection()
  // 목업처럼 상세 페이지(/cases/*)에서는 좌측 레일을 숨긴다.
  if (usePathname().startsWith("/cases/")) return null

  return (
    <nav
      aria-label="섹션 이동"
      className="fixed top-1/2 left-4 z-10 flex -translate-y-1/2 flex-col gap-0.5 rounded-full border border-border bg-card/80 p-1.5 shadow-[0_6px_24px_rgba(30,60,110,0.08)] backdrop-blur-[14px] max-[960px]:hidden"
    >
      {railItems.map((item) => (
        <Link
          key={item.id}
          href={item.href}
          aria-label={item.label}
          aria-current={active === item.id ? "true" : "false"}
          className="group relative grid h-10 w-8 place-items-center rounded-full"
        >
          <span
            aria-hidden="true"
            className="h-1.5 w-1.5 rounded-full bg-muted-foreground opacity-45 transition-[height,background-color,opacity] duration-200 group-hover:opacity-100 group-aria-[current=true]:h-7 group-aria-[current=true]:bg-primary group-aria-[current=true]:opacity-100"
          />
          <span className="pointer-events-none absolute top-1/2 left-11 -translate-y-1/2 rounded-full bg-btn-dark px-[11px] py-1 text-[12.5px] font-medium whitespace-nowrap text-btn-dark-ink opacity-0 transition-opacity duration-150 group-hover:opacity-100 group-focus-visible:opacity-100">
            {item.label}
          </span>
        </Link>
      ))}
    </nav>
  )
}
