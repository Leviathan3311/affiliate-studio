import Link from "next/link";
import type { ReactNode } from "react";
import { Mark } from "./shell";

/** Who runs the service and where people write to; set at build time (Meta App Review needs both). */
export const OPERATOR = process.env.NEXT_PUBLIC_OPERATOR_NAME || "GrowthPilot AI";
export const CONTACT_EMAIL = process.env.NEXT_PUBLIC_CONTACT_EMAIL || "privacy@growthpilot-spa.online";
export const UPDATED = "01/11/2026";

export function Mail() {
  return <a href={`mailto:${CONTACT_EMAIL}`} className="font-medium text-ink underline">{CONTACT_EMAIL}</a>;
}

/** A public, readable page (no login): privacy policy and data deletion instructions. */
export function LegalPage({ title, children }: { title: string; children: ReactNode }) {
  return (
    <main className="min-h-screen bg-ground px-4 py-10 sm:py-16">
      <article className="mx-auto max-w-2xl">
        <Link href="/login" className="mb-10 flex items-center gap-2.5">
          <Mark size={28} />
          <span className="text-base font-semibold">GrowthPilot AI</span>
        </Link>
        <h1 className="text-[28px] font-semibold leading-tight">{title}</h1>
        <p className="mt-2 text-sm text-muted">Cập nhật lần cuối: {UPDATED} · Đơn vị vận hành: {OPERATOR}</p>
        <div className="mt-8 space-y-8 leading-relaxed [&_h2]:mb-2 [&_h2]:text-lg [&_h2]:font-semibold [&_li]:ml-5 [&_li]:list-disc [&_p+p]:mt-3 [&_ul+p]:mt-3 [&_ul]:mt-2 [&_ul]:space-y-1">
          {children}
        </div>
        <LegalLinks className="mt-12 border-t border-rule pt-6" />
      </article>
    </main>
  );
}

export function LegalLinks({ className = "" }: { className?: string }) {
  return (
    <p className={`flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-muted ${className}`}>
      <Link href="/privacy" className="hover:text-ink">Chính sách quyền riêng tư</Link>
      <Link href="/data-deletion" className="hover:text-ink">Xoá dữ liệu</Link>
    </p>
  );
}
