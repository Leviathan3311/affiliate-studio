"use client";

import Link from "next/link";
import { useState } from "react";
import { Button, Empty, ErrorNote, PageTitle, Pill, Skeleton } from "@/components/ui";
import { api, useApi } from "@/lib/api";
import { PUBLISH_STATUS, time } from "@/lib/format";
import type { PublishingJob } from "@/lib/types";

const FILTERS = [
  { id: "", label: "Tất cả" },
  { id: "scheduled", label: "Đã lên lịch" },
  { id: "published", label: "Đã đăng" },
  { id: "failed", label: "Lỗi" },
] as const;

/** Publishing calendar across projects (BRD MOD-05), grouped by local day. */
export default function PublishingPage() {
  const [status, setStatus] = useState("");
  const list = useApi<PublishingJob[]>(`/publishing-jobs${status ? `?status=${status}` : ""}`, 20000);
  const byDay = new Map<string, PublishingJob[]>();
  for (const j of list.data ?? []) {
    const day = new Date(j.scheduled_at).toLocaleDateString("vi-VN", { weekday: "long", day: "2-digit", month: "2-digit", year: "numeric" });
    byDay.set(day, [...(byDay.get(day) ?? []), j]);
  }
  const failed = list.data?.filter((j) => j.status === "failed").length ?? 0;

  return (
    <>
      <PageTitle title="Lịch đăng bài" sub={list.data ? `${list.data.length} bài${failed ? ` · ${failed} bài lỗi cần xử lý` : ""}` : undefined} />
      <div role="tablist" aria-label="Lọc trạng thái" className="mb-6 flex gap-5 border-b border-border">
        {FILTERS.map((f) => (
          <button key={f.id} role="tab" aria-selected={status === f.id} onClick={() => setStatus(f.id)}
            className={`-mb-px cursor-pointer border-b-2 pb-2 text-sm ${status === f.id ? "border-accent font-semibold" : "border-transparent text-muted"}`}>{f.label}</button>
        ))}
      </div>
      {list.error && <ErrorNote error={list.error} onRetry={list.reload} />}
      {list.loading && <Skeleton rows={5} />}
      {list.data?.length === 0 && <Empty title="Chưa có bài nào">Duyệt ảnh hoặc video trong một dự án rồi mở bước “Đăng bài”.</Empty>}
      {[...byDay.entries()].map(([day, jobs]) => (
        <section key={day} className="mb-8">
          <h2 className="mb-2 text-sm font-semibold capitalize">{day}</h2>
          <ul className="divide-y divide-rule">
            {jobs.map((j) => (
              <li key={j.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 py-3">
                <span className="w-14 font-medium">{time(j.scheduled_at)}</span>
                <div className="min-w-48 flex-1">
                  {j.project_id ? <Link href={`/app/project?id=${j.project_id}`} className="font-medium hover:underline">{j.artifact_name}</Link> : j.artifact_name}
                  <p className="text-sm text-muted">{j.page_name} · {j.media_type === "video" ? "Video" : "Ảnh"}</p>
                </div>
                <Pill tone={j.status === "published" ? "positive" : j.status === "failed" ? "negative" : "neutral"}>{PUBLISH_STATUS[j.status]}</Pill>
                {(j.status === "scheduled" || j.status === "failed") && (
                  <span className="flex gap-1">
                    <Button className="h-8 text-xs" onClick={async () => { await api(`/publishing-jobs/${j.id}/publish-now`, { method: "POST" }); list.reload(); }}>Đăng ngay</Button>
                    <Button variant="ghost" className="h-8 text-xs" onClick={async () => { await api(`/publishing-jobs/${j.id}/cancel`, { method: "POST" }); list.reload(); }}>Huỷ</Button>
                  </span>
                )}
                {j.last_error && <p className="w-full text-xs text-negative">{j.last_error}</p>}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </>
  );
}
