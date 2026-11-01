"use client";

import { useState } from "react";
import { Button, Empty, ErrorNote, Panel, Pill } from "@/components/ui";
import { api, ApiError, useApi } from "@/lib/api";
import { ago, ARTIFACT_STATUS, JOB_STAGE } from "@/lib/format";
import type { Artifact, MediaJob, Project, ProjectInput } from "@/lib/types";
import { statusTone, Thumb } from "./library";

export function JobsPanel({ jobs, onChanged }: { jobs: MediaJob[]; onChanged: () => void }) {
  const active = jobs.filter((j) => j.status === "queued" || j.status === "running");
  const recent = jobs.filter((j) => !active.includes(j)).slice(0, 3);
  if (!jobs.length) return null;
  return (
    <Panel title="Hàng đợi GPU (Kaggle)">
      <ul className="divide-y divide-rule">
        {[...active, ...recent].map((j) => (
          <li key={j.id} className="flex flex-wrap items-center gap-3 py-2.5 text-sm">
            <span className="w-40 font-medium">{j.kind === "studio" ? "Ảnh + video quảng cáo" : "Cắt Shorts 9:16"}</span>
            <Pill tone={j.status === "succeeded" ? "positive" : j.status === "failed" ? "negative" : j.status === "running" ? "accent" : "neutral"}>
              {JOB_STAGE[j.status]}
            </Pill>
            {j.status === "running" && (
              <span className="flex min-w-40 flex-1 items-center gap-2">
                <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-raised">
                  <span className="block h-full rounded-full bg-accent" style={{ width: `${Math.round(j.progress * 100)}%` }} />
                </span>
                <span className="text-xs text-muted">{j.stage} · {Math.round(j.progress * 100)}%</span>
              </span>
            )}
            {j.status === "queued" && <span className="flex-1 text-xs text-muted">Notebook sẽ nhận khi phiên Kaggle đang chạy · tạo {ago(j.created_at)}</span>}
            {j.error && <span className="flex-1 text-xs text-negative">{j.error}</span>}
            {active.includes(j) && (
              <Button variant="ghost" className="h-8 text-xs" onClick={async () => { await api(`/media-jobs/${j.id}/cancel`, { method: "POST" }); onChanged(); }}>Huỷ</Button>
            )}
          </li>
        ))}
      </ul>
    </Panel>
  );
}

export function MediaSection({
  project,
  items,
  kinds,
  onOpen,
  onChanged,
}: {
  project: Project;
  items: Artifact[];
  kinds: ("image" | "video" | "short")[];
  onOpen: (a: Artifact) => void;
  onChanged: () => void;
}) {
  const shown = items.filter((a) => kinds.includes(a.kind as "image"));
  return (
    <div className="space-y-6">
      {kinds.includes("short") && <ShortsLauncher project={project} videos={items.filter((a) => a.kind === "video" && a.current?.url)} onChanged={onChanged} />}
      {!shown.length && (
        <Empty title={kinds.includes("short") ? "Chưa có Shorts" : "Chưa có ảnh/video"}>
          {kinds.includes("short") ? "Chọn video quảng cáo hoặc video spa tự quay để cắt thành Reels 9:16." : 'Chọn một kịch bản rồi bấm "Tạo ảnh & video".'}
        </Empty>
      )}
      <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {shown.map((a) => (
          <li key={a.id}>
            <button onClick={() => onOpen(a)} className="block w-full cursor-pointer overflow-hidden rounded-[var(--radius-card)] border border-border bg-surface text-left hover:border-control">
              <Thumb a={a} className={`w-full ${a.kind === "image" ? "aspect-[9/16] max-h-80" : "aspect-[9/16] max-h-80"}`} />
              <span className="block p-3">
                <span className="block truncate text-sm font-medium">{a.display_name}</span>
                <span className="mt-1 flex items-center gap-2"><Pill tone={statusTone(a.status)}>{ARTIFACT_STATUS[a.status]}</Pill><span className="text-xs text-muted">v{a.version_count}</span></span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ShortsLauncher({ project, videos, onChanged }: { project: Project; videos: Artifact[]; onChanged: () => void }) {
  const inputs = useApi<ProjectInput[]>(`/projects/${project.id}/inputs`);
  const uploaded = inputs.data?.filter((i) => i.mime_type.startsWith("video/")) ?? [];
  const [source, setSource] = useState("");
  const [count, setCount] = useState(3);
  const [cta, setCta] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  async function go() {
    const [kind, id] = source.split(":");
    setBusy(true);
    setError(null);
    try {
      await api(`/projects/${project.id}/shorts`, {
        method: "POST",
        json: { [kind === "a" ? "source_artifact_id" : "source_input_id"]: id, target_count: count, cta },
      });
      onChanged();
    } catch (e) {
      setError(e as ApiError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel title="Cắt video thành Shorts 9:16">
      <p className="mb-4 text-sm text-muted">Notebook 2: WhisperX bóc băng → Gemini chọn 2–5 đoạn 15–30 giây có hook mạnh → bám mặt cắt dọc 9:16 + phụ đề karaoke.</p>
      <div className="grid gap-3 sm:grid-cols-[1fr_120px_1fr_auto] sm:items-end">
        <label className="flex flex-col gap-1.5 text-sm font-medium">Video nguồn
          <select value={source} onChange={(e) => setSource(e.target.value)} className="h-9 rounded-[var(--radius-control)] border border-control px-2 font-normal">
            <option value="">Chọn video</option>
            {videos.map((v) => <option key={v.id} value={`a:${v.id}`}>{v.display_name}</option>)}
            {uploaded.map((u) => <option key={u.id} value={`i:${u.id}`} disabled={!u.usage_confirmed}>{u.filename}{u.usage_confirmed ? "" : " (cần xác nhận quyền dùng)"}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-sm font-medium">Số đoạn
          <input type="number" min={1} max={5} value={count} onChange={(e) => setCount(Number(e.target.value))} className="h-9 rounded-[var(--radius-control)] border border-control px-2 font-normal" />
        </label>
        <label className="flex flex-col gap-1.5 text-sm font-medium">CTA
          <input value={cta} onChange={(e) => setCta(e.target.value)} placeholder="Nhắn Page để giữ chỗ" className="h-9 rounded-[var(--radius-control)] border border-control px-2 font-normal" />
        </label>
        <Button variant="primary" onClick={go} busy={busy} disabled={!source}>Cắt Shorts</Button>
      </div>
      {error && <div className="mt-3"><ErrorNote error={error} /></div>}
    </Panel>
  );
}

export function MediaView({ a, onChanged }: { a: Artifact; onChanged: () => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const v = a.current;
  const meta = (v?.content ?? {}) as Record<string, unknown>;

  async function act(name: string, path: string, json?: unknown, method = "POST") {
    setBusy(name);
    setError(null);
    try {
      await api(path, { method, json });
      onChanged();
    } catch (e) {
      setError(e as ApiError);
    } finally {
      setBusy(null);
    }
  }

  return (
    <Panel title={a.display_name} action={<span className="flex items-center gap-2"><Pill tone={statusTone(a.status)}>{ARTIFACT_STATUS[a.status]}</Pill><span className="text-xs text-muted">v{a.version_count} · {v?.model}</span></span>}>
      {a.status === "failed" && <ErrorNote error={new Error(a.error ?? "Tạo thất bại")} />}
      {v?.url && (
        <div className="mx-auto max-w-sm overflow-hidden rounded-[var(--radius-card)] bg-black">
          {v.mime_type?.startsWith("video/") ? (
            <video src={v.url} controls playsInline className="aspect-[9/16] w-full" />
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={v.url} alt={a.display_name} className="w-full" />
          )}
        </div>
      )}
      {v?.model?.includes("minimax") && (
        // MiniMax H3 community licence: the product UI must display "MiniMax H3".
        <p className="mt-2 text-center text-xs text-muted">Video tạo bởi MiniMax H3 · nhạc nền ACE-Step 1.5</p>
      )}
      {a.kind === "short" && (
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
          <div><dt className="text-xs text-muted">Đoạn gốc</dt><dd>{String(meta.start)}s → {String(meta.end)}s</dd></div>
          <div><dt className="text-xs text-muted">Hook</dt><dd>{String(meta.hook ?? "—")}</dd></div>
          <div><dt className="text-xs text-muted">Lý do chọn</dt><dd>{String(meta.reason ?? "—")}</dd></div>
        </dl>
      )}
      {error && <div className="mt-3"><ErrorNote error={error} /></div>}
      <div className="mt-5 flex flex-wrap gap-2">
        {(a.status === "ready" || a.status === "selected") && (
          <Button variant="primary" busy={busy === "approve"} onClick={() => act("approve", `/artifacts/${a.id}/approve`)}>Duyệt (Approve)</Button>
        )}
        {v?.url && <a href={v.url} download className="inline-flex h-9 items-center rounded-[var(--radius-control)] bg-active px-3 text-sm font-medium">Tải xuống</a>}
        <Button variant="danger" busy={busy === "delete"} onClick={() => confirm("Xoá phương án này và tệp trên R2?") && act("delete", `/artifacts/${a.id}`, undefined, "DELETE")}>Xoá</Button>
      </div>
    </Panel>
  );
}
