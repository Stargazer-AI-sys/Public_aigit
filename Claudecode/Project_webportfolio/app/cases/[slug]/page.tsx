import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { Suspense } from "react"

import { CaseDetail } from "@/components/case/case-sections"
import { caseSlugs, getCase } from "@/content/cases"

// slug는 content/cases/index.ts의 3개만 정적으로 만든다.
// cacheComponents에서는 dynamicParams 설정을 쓸 수 없어, 목록 밖 slug는 notFound()로 404 처리한다.
export function generateStaticParams() {
  return caseSlugs.map((slug) => ({ slug }))
}

export async function generateMetadata({
  params,
}: PageProps<"/cases/[slug]">): Promise<Metadata> {
  const { slug } = await params
  const data = getCase(slug)
  return data ? { title: data.head.title } : {}
}

// params를 읽는 부분만 Suspense 안으로 옮겨, 공유 셸이 URL 데이터에 묶이지 않게 한다.
async function Case({ params }: Pick<PageProps<"/cases/[slug]">, "params">) {
  const { slug } = await params
  const data = getCase(slug)
  if (!data) notFound()

  return <CaseDetail data={data} />
}

export default function CasePage({ params }: PageProps<"/cases/[slug]">) {
  return (
    <Suspense fallback={null}>
      <Case params={params} />
    </Suspense>
  )
}
