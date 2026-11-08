import { readFile } from "node:fs/promises";
import { join } from "node:path";

import { ImageResponse } from "next/og";

import { siteConfig } from "@/content/site";

export const alt = siteConfig.title;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// ImageResponse는 한글 글꼴을 직접 받아야 한다. 아래 글꼴은 제목·소개 문장에 쓰는 글자만 담은 부분집합이다.
// content/site.ts의 title·description 글자를 바꾸면 없는 글자가 빈칸으로 나오므로 글꼴을 다시 만든다:
//   https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@700&text=<필요한 글자> 의 url(...)을 받아 저장.
const font = await readFile(join(process.cwd(), "assets/og/NotoSansKR-Bold-subset.ttf"));

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "72px 84px",
          background: "linear-gradient(135deg, #4B89DC 0%, #2F66B8 100%)",
          color: "#ffffff",
          fontFamily: "Noto Sans KR",
        }}
      >
        {/* app/icon.svg와 같은 망원경(lucide telescope). 흰 선으로 그린다. */}
        <svg
          width="96"
          height="96"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#ffffff"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="m10.065 12.493-6.18 1.318a.934.934 0 0 1-1.108-.702l-.537-2.15a1.07 1.07 0 0 1 .691-1.265l13.504-4.44" />
          <path d="m13.56 11.747 4.332-.924" />
          <path d="m16 21-3.105-6.21" />
          <path d="M16.485 5.94a2 2 0 0 1 1.455-2.425l1.09-.272a1 1 0 0 1 1.212.727l1.515 6.06a1 1 0 0 1-.727 1.213l-1.09.272a2 2 0 0 1-2.425-1.455z" />
          <path d="m6.158 8.633 1.114 4.456" />
          <path d="m8 21 3.105-6.21" />
          <circle cx="12" cy="13" r="2" />
        </svg>
        <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
          {/* hero h1처럼 쉼표 뒤에서 두 줄로 나눈다. */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              fontSize: 88,
              fontWeight: 700,
              lineHeight: 1.2,
            }}
          >
            {siteConfig.title.split(", ").map((line, i, lines) => (
              <div key={line}>{i < lines.length - 1 ? `${line},` : line}</div>
            ))}
          </div>
          <div style={{ fontSize: 32, lineHeight: 1.5, opacity: 0.88, wordBreak: "keep-all" }}>
            {siteConfig.description}
          </div>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [{ name: "Noto Sans KR", data: font, style: "normal", weight: 700 }],
    },
  );
}
