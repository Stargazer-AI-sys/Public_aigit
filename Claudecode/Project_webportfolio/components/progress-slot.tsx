// 대시보드를 구현하기 전까지 화면에서 숨긴다(2026-11-08 사용자 요청). 다시 보이려면 `hidden`을 지우고 `max-[960px]:hidden`을 되돌린다.
export function ProgressSlot() {
  return (
    <aside
      aria-label="진행률 자리(예약)"
      className="hidden fixed top-1/2 right-3.5 z-10 w-[72px] -translate-y-1/2 rounded-2xl border-[1.5px] border-dashed border-border bg-card/60 px-1.5 py-3 text-center text-[11px] leading-[1.4] text-muted-foreground"
    >
      <b className="block font-heading text-xs font-bold text-accent-ink">
        진행률
      </b>
      대시보드
      <br />
      예약 영역
    </aside>
  )
}
