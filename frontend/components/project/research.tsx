"use client";

import { useState } from "react";
import { Button, Empty, ErrorNote, Panel, Pill, Skeleton } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { dateTime } from "@/lib/format";
import type { Artifact, Project, ResearchReport } from "@/lib/types";

const MODES = [
  { id: "quick", label: "Quick Insight", hint: "10–30 giây, dùng lại báo cáo còn mới" },
  { id: "standard", label: "Nghiên cứu chuẩn", hint: "1–3 phút" },
  { id: "deep", label: "Deep Research", hint: "3–10 phút, kiểm tra chéo nhiều vòng" },
] as const;

const CONFIDENCE = { low: ["Độ tin cậy thấp", "warning"], medium: ["Độ tin cậy vừa", "neutral"], high: ["Độ tin cậy cao", "positive"] } as const;

export function ResearchSection({ project, reports, onChanged }: { project: Project; reports: Artifact[]; onChanged: () => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const latest = reports[0];

  async function run(mode: string) {
    setBusy(mode);
    setError(null);
    try {
      await api(`/projects/${project.id}/research`, { method: "POST", json: { mode } });
      onChanged();
    } catch (e) {
      setError(e as ApiError);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <Panel title="Nghiên cứu thị trường">
        <p className="mb-4 text-sm text-muted">
          {project.research_urls.length
            ? `AI chỉ trích dẫn từ ${project.research_urls.length} nguồn bạn đã thêm vào project.`
            : "Chưa có nguồn: thêm link đối thủ/fanpage công khai ở bước tạo project để báo cáo có bằng chứng."}
        </p>
        <div className="flex flex-wrap gap-3">
          {MODES.map((m) => (
            <Button key={m.id} onClick={() => run(m.id)} busy={busy === m.id} disabled={!!busy} title={m.hint}>{m.label}</Button>
          ))}
        </div>
        {error && <div className="mt-3"><ErrorNote error={error} /></div>}
      </Panel>
      {!latest && <Empty title="Chưa có báo cáo">Chạy nghiên cứu để có insight trước khi viết kịch bản.</Empty>}
      {latest && <ReportView a={latest} />}
    </div>
  );
}

export function ReportView({ a }: { a: Artifact }) {
  if (a.status === "generating") return <Panel title={a.display_name}><Skeleton rows={6} /><p className="mt-3 text-sm text-muted">Gemini đang đọc nguồn và tổng hợp…</p></Panel>;
  if (a.status === "failed") return <Panel title={a.display_name}><ErrorNote error={new Error(a.error ?? "Nghiên cứu thất bại")} /></Panel>;
  const r = a.current?.content as unknown as ResearchReport | undefined;
  if (!r) return null;
  const [label, tone] = CONFIDENCE[r.confidence];
  const list = (title: string, items: string[]) =>
    items?.length ? (
      <section>
        <h3 className="text-sm font-semibold">{title}</h3>
        <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm">{items.map((x, i) => <li key={i}>{x}</li>)}</ul>
      </section>
    ) : null;
  return (
    <Panel title={a.display_name} action={<span className="flex items-center gap-2"><Pill tone={tone}>{label}</Pill><span className="text-xs text-muted">{a.current && dateTime(a.current.created_at)}</span></span>}>
      <p className="leading-relaxed">{r.research_summary}</p>
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        {list("Khách hàng mục tiêu", r.target_audience)}
        {list("Nỗi đau / rào cản", r.customer_pain_points)}
        {list("Câu hỏi thường gặp", r.customer_questions)}
        {list("Đối thủ", r.competitor_insights)}
        {list("Xu hướng nội dung", r.social_trends)}
        {list("Cơ hội nội dung", r.content_opportunities)}
      </div>
      <section className="mt-6">
        <h3 className="text-sm font-semibold">Bằng chứng có nguồn · {r.evidence.length}</h3>
        <ul className="mt-2 space-y-2 text-sm">
          {r.evidence.map((e, i) => (
            <li key={i}>
              {e.claim} <a href={e.source_url} target="_blank" rel="noreferrer" className="text-muted underline">({e.source_title || "nguồn"})</a>
            </li>
          ))}
        </ul>
      </section>
      <div className="mt-6 grid gap-5 lg:grid-cols-3">
        {list("Giả định (chưa kiểm chứng)", r.assumptions)}
        {list("Rủi ro / phản ví dụ", [...(r.risks ?? []), ...(r.counterexamples ?? [])])}
        {list("Chưa biết", r.unknowns)}
      </div>
      {r.unreachable_sources?.length > 0 && <p className="mt-4 text-xs text-muted">Không tải được: {r.unreachable_sources.join("; ")}</p>}
    </Panel>
  );
}
