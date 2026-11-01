"use client";

import { useEffect, useRef, useState } from "react";
import { Button, Empty, ErrorNote, Panel, Pill, Skeleton } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { dateTime } from "@/lib/format";
import type { Artifact, Project, ResearchReport } from "@/lib/types";

const DEPTH = [
  { id: "quick", label: "Nhanh", hint: "khoảng 30 giây" },
  { id: "standard", label: "Chuẩn", hint: "1–3 phút" },
  { id: "deep", label: "Chuyên sâu", hint: "3–10 phút" },
] as const;

const CONFIDENCE = { low: ["Độ tin cậy thấp", "warning"], medium: ["Độ tin cậy vừa", "neutral"], high: ["Độ tin cậy cao", "positive"] } as const;

/** Opening this step starts the research when there is none yet: no extra click, no setup step. */
export function ResearchSection({ project, reports, onChanged }: { project: Project; reports: Artifact[]; onChanged: () => void }) {
  const [depth, setDepth] = useState<(typeof DEPTH)[number]["id"]>("standard");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const started = useRef(false);
  const latest = reports[0];
  const running = latest?.status === "generating";

  async function run(mode: string) {
    setBusy(true);
    setError(null);
    try {
      await api(`/projects/${project.id}/research`, { method: "POST", json: { mode } });
      onChanged();
    } catch (e) {
      setError(e as ApiError);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!reports.length && !started.current) {
      started.current = true;
      run("standard");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reports.length]);

  const sources = project.research_urls.length;
  return (
    <div className="space-y-[14px]">
      <Panel title="Nghiên cứu thị trường">
        <p className="text-sm text-muted">
          AI đọc tài liệu của dự án{sources ? ` và ${sources} nguồn bạn đã thêm` : ""}, rồi tóm tắt khách hàng, đối thủ, xu hướng và cơ hội nội dung.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <div role="radiogroup" aria-label="Độ sâu" className="flex rounded-full bg-ground p-1">
            {DEPTH.map((d) => (
              <button key={d.id} role="radio" aria-checked={depth === d.id} title={d.hint} onClick={() => setDepth(d.id)}
                className={`h-8 cursor-pointer rounded-full px-4 text-sm transition-colors ${depth === d.id ? "bg-raised font-medium text-ink" : "text-faint hover:text-ink"}`}>
                {d.label}
              </button>
            ))}
          </div>
          <Button variant="primary" onClick={() => run(depth)} busy={busy} disabled={running}>
            {reports.length ? "Nghiên cứu lại" : "Nghiên cứu"}
          </Button>
          <span className="text-xs text-faint">{DEPTH.find((d) => d.id === depth)?.hint}</span>
        </div>
        {error && <div className="mt-3"><ErrorNote error={error} /></div>}
      </Panel>
      {!latest && !busy && !error && <Empty title="Chưa có báo cáo" />}
      {!latest && busy && <Panel title="Đang bắt đầu"><Skeleton rows={4} /></Panel>}
      {latest && <ReportView a={latest} />}
    </div>
  );
}

export function ReportView({ a }: { a: Artifact }) {
  if (a.status === "generating") return <Panel title={a.display_name}><Skeleton rows={6} /><p className="mt-3 text-sm text-muted">AI đang nghiên cứu, thường mất 1–3 phút. Bạn có thể chuyển sang mục khác.</p></Panel>;
  if (a.status === "failed") return <Panel title={a.display_name}><ErrorNote error={new Error("Chưa nghiên cứu xong được. Bấm \"Nghiên cứu lại\" để thử lần nữa.")} /></Panel>;
  const r = a.current?.content as unknown as ResearchReport | undefined;
  if (!r) return null;
  const [label, tone] = CONFIDENCE[r.confidence];
  const list = (title: string, items: string[]) =>
    items?.length ? (
      <section>
        <h3 className="text-sm font-semibold">{title}</h3>
        <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm text-muted marker:text-faint">{items.map((x, i) => <li key={i}>{x}</li>)}</ul>
      </section>
    ) : null;
  return (
    <Panel title={a.display_name} action={<span className="flex items-center gap-2"><Pill tone={tone}>{label}</Pill><span className="text-xs text-muted">{a.current && dateTime(a.current.created_at)}</span></span>}>
      <p className="max-w-[75ch] text-[15px] leading-relaxed">{r.research_summary}</p>
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
              {e.claim} <a href={e.source_url} target="_blank" rel="noreferrer" className="text-faint underline hover:text-ink">({e.source_title || "nguồn"})</a>
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
