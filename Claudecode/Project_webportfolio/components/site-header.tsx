"use client"

import { ArrowRight, FlaskConical, House, Sparkles } from "lucide-react"
import Link from "next/link"
import type { MouseEvent } from "react"
import { usePathname } from "next/navigation"

import { ThemeToggle } from "@/components/theme-toggle"
import { siteConfig } from "@/content/site"
import { SECTION_IDS, useActiveSection } from "@/hooks/use-active-section"

// 메뉴 항목 순서(Home, Working Style, AI Workflows)에 맞춘 목업 아이콘.
const navIcons = [House, FlaskConical, Sparkles]

// 주소가 이미 같은 해시(예: /#how)이면 next/link가 이동을 건너뛰어, 스크롤로 벗어난 뒤 다시 눌러도 반응이 없다.
// 이 경우에만 직접 스크롤한다. 해시가 바뀌는 이동은 Next 라우터가 그대로 처리한다.
function scrollIfSameHash(e: MouseEvent<HTMLAnchorElement>, href: string, pathname: string) {
  const hash = href.slice(href.indexOf("#"))
  const samePage = href.startsWith("#") || href.slice(0, href.indexOf("#")) === pathname
  if (!samePage || window.location.hash !== hash) return
  const target = document.getElementById(hash.slice(1))
  if (!target) return
  e.preventDefault()
  target.scrollIntoView()
}

// 메뉴 순서는 SECTION_IDS와 같다. 섹션이 없는 페이지에서는 active가 null이라 현재 표시가 없다.
// 상세 페이지(/cases/*)는 AI Workflows 하위이므로 그 항목을 현재 위치로 표시한다.
export function SiteHeader() {
  const sectionActive = useActiveSection()
  const pathname = usePathname()
  const active = pathname.startsWith("/cases/") ? "projects" : sectionActive

  return (
    <header>
      <nav
        aria-label="주 메뉴"
        className="fixed top-4 left-1/2 z-20 -translate-x-1/2"
      >
        <div className="flex gap-0.5 rounded-full border border-border bg-card/80 p-[5px] shadow-[0_6px_24px_rgba(30,60,110,0.08)] backdrop-blur-[14px]">
          {siteConfig.nav.map((item, i) => {
            const Icon = navIcons[i]
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={(e) => scrollIfSameHash(e, item.href, pathname)}
                aria-current={active === SECTION_IDS[i] ? "true" : "false"}
                className="inline-flex h-[38px] items-center gap-[7px] rounded-full px-[13px] text-sm font-medium whitespace-nowrap text-muted-foreground transition-colors hover:bg-accent-soft hover:text-foreground aria-[current=true]:bg-accent-soft aria-[current=true]:text-accent-ink max-sm:px-3"
              >
                <Icon className="size-[17px] flex-none" strokeWidth={1.8} />
                <span className="max-sm:hidden">{item.label}</span>
              </Link>
            )
          })}
        </div>
      </nav>
      <div className="fixed top-4 right-4 z-20 flex items-center gap-2 max-sm:right-2.5 max-sm:gap-1.5">
        <ThemeToggle />
        <Link
          href="#contact"
          onClick={(e) => scrollIfSameHash(e, "#contact", pathname)}
          className="inline-flex h-12 items-center gap-2.5 rounded-full bg-btn-dark py-0 pr-5 pl-2 text-sm font-bold whitespace-nowrap text-btn-dark-ink max-sm:h-10 max-sm:px-1"
        >
          <i className="grid size-8 place-items-center rounded-full bg-primary not-italic">
            <ArrowRight className="size-4 text-white" strokeWidth={2} />
          </i>
          <span className="max-sm:hidden">연락하기</span>
        </Link>
      </div>
    </header>
  )
}
