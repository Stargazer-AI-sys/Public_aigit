"use client"

import { useSyncExternalStore } from "react"

// 섹션 id 순서. Home 페이지의 섹션 id와 같다(content/site.ts 메뉴 순서).
export const SECTION_IDS = ["home", "how", "projects"] as const
export type SectionId = (typeof SECTION_IDS)[number]

// 목업 spy(): 뷰포트 높이의 35% 지점을 지난 마지막 섹션이 현재 위치다.
function readActive(): SectionId | null {
  const sections = SECTION_IDS.map((id) => [id, document.getElementById(id)] as const)
  // 섹션이 하나도 없는 페이지(예: 상세 페이지)에서는 현재 위치를 두지 않는다.
  if (sections.every(([, el]) => el === null)) return null

  const y = window.scrollY + window.innerHeight * 0.35
  let current: SectionId = "home"
  for (const [id, el] of sections) {
    if (el && el.offsetTop <= y) current = id
  }
  return current
}

function subscribe(onChange: () => void) {
  window.addEventListener("scroll", onChange, { passive: true })
  window.addEventListener("resize", onChange)
  window.addEventListener("hashchange", onChange)
  return () => {
    window.removeEventListener("scroll", onChange)
    window.removeEventListener("resize", onChange)
    window.removeEventListener("hashchange", onChange)
  }
}

// 서버·hydration 시점에는 null이라 서버 HTML과 일치한다.
export function useActiveSection(): SectionId | null {
  return useSyncExternalStore(subscribe, readActive, () => null)
}
