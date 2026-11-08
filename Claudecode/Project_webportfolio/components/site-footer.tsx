import { ContactActions } from "@/components/contact-actions"
import { siteConfig } from "@/content/site"

// 목업 footer#contact. 메일 주소는 content/site.ts 한 곳에서만 관리한다.
export function SiteFooter() {
  const mailto = `mailto:${siteConfig.contactEmail}`

  return (
    <footer id="contact" className="pt-18 pb-24">
      <div className="mx-auto w-[min(1040px,calc(100%-2rem))]">
        <div className="flex flex-wrap items-center justify-between gap-6 rounded-[28px] bg-btn-dark p-11 text-btn-dark-ink max-sm:p-[30px]">
          <div>
            <h2 className="text-[clamp(24px,3vw,32px)]">이야기 나눠 보고 싶으시다면</h2>
            <p className="mt-2 text-[15px] opacity-70">아래 메일로 연락해 주세요.</p>
            <a className="mt-2 inline-block text-base font-bold" href={mailto}>
              {siteConfig.contactEmail}
            </a>
          </div>
          <ContactActions email={siteConfig.contactEmail} />
        </div>
      </div>
    </footer>
  )
}
