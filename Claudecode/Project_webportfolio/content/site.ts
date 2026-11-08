// 사이트 공통 문구. 값은 prototype/portfolio-mockup.html 에서 그대로 가져온다.

export const siteConfig = {
  // 배포 주소(Vercel). 공유 미리보기(OG) 이미지 주소의 기준이 된다. 도메인을 바꾸면 여기만 고친다.
  url: "https://stargazer-folio.vercel.app",
  // 목업 hero h1 ("AI가 만들고,<br>기준은 제가 세웁니다")에서 줄바꿈을 뺀 문구
  title: "AI가 만들고, 기준은 제가 세웁니다",
  // 목업 hero 소개 문장(.lead). 검색 결과·공유 미리보기에 보이므로 인사말보다 하는 일을 설명하는 문장을 쓴다.
  description:
    "금융거래 플랫폼을 8년간 운영하며 익힌 확인과 기록의 습관으로 AI의 결과를 검토합니다.",
  nav: [
    { label: "Home", href: "/#home" },
    { label: "Working Style", href: "/#how" },
    { label: "AI Workflows", href: "/#projects" },
  ],
  contactEmail: "hanmir777@naver.com",
} as const;
