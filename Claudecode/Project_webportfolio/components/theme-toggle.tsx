"use client"

import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"

// 서버에서는 테마를 알 수 없어 아이콘을 JS 상태가 아닌 `dark:` CSS로 전환한다(hydration 불일치 방지).
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()

  return (
    <button
      type="button"
      aria-label="라이트/다크 전환"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
      className="inline-flex size-12 cursor-pointer items-center justify-center rounded-full border border-btn-line bg-card/80 text-foreground backdrop-blur-[14px] transition-colors hover:bg-accent-soft max-sm:size-10"
    >
      <Sun className="size-5 dark:hidden" strokeWidth={1.8} />
      <Moon className="hidden size-5 dark:block" strokeWidth={1.8} />
    </button>
  )
}
