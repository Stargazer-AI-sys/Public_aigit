import type { MetadataRoute } from "next";

// 링크를 아는 사람만 보게 한다(2026-11-08 사용자 결정). 크롤러에는 색인하지 말라고 알리는 것이며 접근을 막지는 않는다.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", disallow: "/" },
  };
}
