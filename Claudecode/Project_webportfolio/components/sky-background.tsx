// 목업 .sky/.cloud 배경. 페이지 최상단에 깔리는 장식이라 스크린 리더에는 숨긴다.
// 위치 기준은 가장 가까운 positioned 조상이므로, 레이아웃에서 relative 래퍼 안에 넣어야 목업과 같은 위치가 된다.
export function SkyBackground() {
  return (
    <div
      aria-hidden="true"
      className="absolute inset-x-0 top-0 z-0 h-[760px] overflow-hidden bg-linear-to-b from-sky to-background"
    >
      <i className="absolute left-[1%] top-[70px] h-[70px] w-[240px] rounded-full bg-cloud blur-[22px]" />
      <i className="absolute left-[36%] top-[210px] h-[80px] w-[300px] rounded-full bg-cloud blur-[22px]" />
      <i className="absolute right-[4%] top-[60px] h-[60px] w-[220px] rounded-full bg-cloud blur-[22px]" />
      <i className="absolute right-[22%] top-[130px] h-[70px] w-[260px] rounded-full bg-cloud blur-[22px]" />
    </div>
  )
}
