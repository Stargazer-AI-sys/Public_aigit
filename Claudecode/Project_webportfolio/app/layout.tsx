import type { Metadata } from "next";
import { Manrope, Noto_Sans_KR } from "next/font/google";
import { ThemeProvider } from "next-themes";

import { ProgressSlot } from "@/components/progress-slot";
import { SectionRail } from "@/components/section-rail";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { SkyBackground } from "@/components/sky-background";
import { siteConfig } from "@/content/site";
import "./globals.css";

// 목업과 같은 글꼴. 제목은 Manrope, 본문은 Noto Sans KR을 쓴다.
// Noto Sans KR은 가변 글꼴이 아니므로 목업이 쓰는 굵기를 명시한다.
const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

const notoSansKr = Noto_Sans_KR({
  variable: "--font-noto-sans-kr",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  metadataBase: new URL(siteConfig.url),
  title: siteConfig.title,
  description: siteConfig.description,
  // 링크를 아는 사람만 보게 한다. robots.ts와 함께 검색엔진 색인을 막는다.
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="ko"
      suppressHydrationWarning
      className={`${manrope.variable} ${notoSansKr.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <SkyBackground />
          <SiteHeader />
          <SectionRail />
          <ProgressSlot />
          {/* 목업 .page처럼 본문을 배경 장식(z-0) 위로 올린다. */}
          <div className="relative z-[1] flex flex-1 flex-col">
            {children}
            <SiteFooter />
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
