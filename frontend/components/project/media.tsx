"use client";

import { RotateCcw } from "lucide-react";
import { useState } from "react";
import { Button, Empty, ErrorNote, Panel, Pill, Progress } from "@/components/ui";
import { api, ApiError, useApi } from "@/lib/api";
import { ago, ARTIFACT_STATUS } from "@/lib/format";
import type { Artifact, MediaJob, Project, ProjectInput } from "@/lib/types";
import { statusTone, Thumb } from "./library";

const JOB_NAME = { studio: "Ảnh & video quảng cáo", shorts: "Cắt Shorts" } as const;

/** The worker's stage codes in words a spa owner reads (no model or machine names). */
export function stageLabel(j: MediaJob): string {
  if (j.status === "queued") return "Đang chờ đến lượt";
  const s = j.stage || "";
  const n = s.match(/(\d+)\/(\d+)/);
  if (s.startsWith("flux2:thumbnail")) return "Đang tạo ảnh bìa";
  if (s.startsWith("flux2")) return "Đang tạo ảnh chính";
  if (s.startsWith("minimax") && n) return `Đang dựng cảnh ${n[1]}/${n[2]}`;
  if (s.startsWith("ace-step")) return "Đang làm nhạc nền";
  if (s.startsWith("ffmpeg")) return "Đang ghép video";
  if (s.startsWith("whisperx")) return "Đang nghe lời thoại";
  if (s.startsWith("gemini")) return "Đang chọn đoạn hay nhất";
  if (s.startsWith("render") && n) return `Đang cắt đoạn ${n[1]}/${n[2]}`;
  if (s === "upload") return "Đang lưu kết quả";
  if (s === "retry") return "Đang thử lại";
  return "Đang chuẩn bị";
}

/** One line per running job, shown above every step so progress is never hidden. */
export function JobStrip({ jobs, onChanged }: { jobs: MediaJob[]; onChanged: () => void }) {
  const active = jobs.filter((j) => j.status === "queued" || j.status === "running");
  if (!active.length) return null;
  return (
    <div className="space-y-2">
      {active.map((j) => (
        <div key={j.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-[var(--radius-card)] bg-surface px-[22px] py-3.5">
          <span className="text-sm font-medium">{JOB_NAME[j.kind]}</span>
          <span className="text-sm text-muted">{stageLabel(j)}</span>
          <span className="flex min-w-40 flex-1 items-center gap-3">
            <Progress value={j.status === "queued" ? 0 : j.progress} label={`${JOB_NAME[j.kind]}: ${stageLabel(j)}`} />
            <span className="w-9 text-right text-xs text-faint">{j.status === "queued" ? "" : `${Math.round(j.progress * 100)}%`}</span>
          </span>
          <Button variant="ghost" className="h-8" onClick={async () => {
            if (!confirm("Dừng tạo? Phần đã làm sẽ không được lưu.")) return;
            await api(`/media-jobs/${j.id}/cancel`, { method: "POST" });
            onChanged();
          }}>Dừng</Button>
        </div>
      ))}
    </div>
  );
}

/** The last failed run, in plain words, with the one thing to do about it. */
function FailedJob({ job, onRetry }: { job: MediaJob; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-wrap items-center gap-3 rounded-[var(--radius-card)] bg-[var(--pill-negative-bg)] px-[22px] py-3.5">
      <div className="min-w-48 flex-1">
        <p className="text-sm font-medium text-[var(--pill-negative-ink)]">{JOB_NAME[job.kind]} chưa tạo xong</p>
        <p className="text-xs text-muted">Lần chạy {ago(job.created_at)} trước gặp sự cố ở bước “{stageLabel({ ...job, status: "running" }).replace("Đang ", "")}”. Ảnh đã tạo xong vẫn được giữ.</p>
      </div>
      {onRetry && <Button variant="primary" onClick={onRetry}><RotateCcw className="size-4" aria-hidden /> Tạo lại</Button>}
    </div>
  );
}

export function MediaSection({
  project,
  items,
  jobs,
  kinds,
  onOpen,
  onChanged,
  onRetry,
}: {
  project: Project;
  items: Artifact[];
  jobs: MediaJob[];
  kinds: ("image" | "video" | "short")[];
  onOpen: (a: Artifact) => void;
  onChanged: () => void;
  onRetry?: () => void;
}) {
  const shown = items.filter((a) => kinds.includes(a.kind as "image"));
  const kind = kinds.includes("short") ? "shorts" : "studio";
  const last = jobs.find((j) => j.kind === kind);
  return (
    <div className="space-y-[14px]">
      {last?.status === "failed" && <FailedJob job={last} onRetry={kind === "studio" ? onRetry : undefined} />}
      {kinds.includes("short") && <ShortsLauncher project={project} videos={items.filter((a) => a.kind === "video" && a.current?.url)} onChanged={onChanged} />}
      {!shown.length && (
        <Empty title={kinds.includes("short") ? "Chưa có Shorts" : "Chưa có ảnh/video"}>
          {kinds.includes("short") ? "Chọn video quảng cáo hoặc video spa tự quay để cắt thành Reels 9:16." : 'Mở một kịch bản, bấm "Dùng kịch bản này" rồi "Tạo ảnh & video".'}
        </Empty>
      )}
      <ul className="grid grid-cols-2 gap-[14px] md:grid-cols-3 2xl:grid-cols-4">
        {shown.map((a) => (
          <li key={a.id}>
            <button onClick={() => onOpen(a)} className="group block w-full cursor-pointer overflow-hidden rounded-[var(--radius-card)] bg-surface text-left">
              <Thumb a={a} className="aspect-[9/16] w-full transition-transform duration-300 group-hover:scale-[1.02]" />
              <span className="block px-4 py-3">
                <span className="block truncate text-sm font-medium">{a.display_name}</span>
                <span className="mt-1.5 flex items-center gap-2"><Pill tone={statusTone(a.status)}>{ARTIFACT_STATUS[a.status]}</Pill></span>
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
      <p className="mb-4 text-sm text-muted">AI nghe lời thoại, chọn 2–5 đoạn 15–30 giây cuốn nhất, cắt dọc theo khuôn mặt và thêm phụ đề.</p>
      <div className="grid gap-3 sm:grid-cols-[1fr_120px_1fr_auto] sm:items-end">
        <label className="flex flex-col gap-1.5 text-sm font-medium">Video nguồn
          <select value={source} onChange={(e) => setSource(e.target.value)} className="h-9 rounded-[var(--radius-control)] border border-control px-3 font-normal">
            <option value="">Chọn video</option>
            {videos.map((v) => <option key={v.id} value={`a:${v.id}`}>{v.display_name}</option>)}
            {uploaded.map((u) => <option key={u.id} value={`i:${u.id}`} disabled={!u.usage_confirmed}>{u.filename}{u.usage_confirmed ? "" : " (cần xác nhận quyền dùng)"}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-sm font-medium">Số đoạn
          <input type="number" min={1} max={5} value={count} onChange={(e) => setCount(Number(e.target.value))} className="h-9 rounded-[var(--radius-control)] border border-control px-3 font-normal" />
        </label>
        <label className="flex flex-col gap-1.5 text-sm font-medium">CTA
          <input value={cta} onChange={(e) => setCta(e.target.value)} placeholder="Nhắn Page để giữ chỗ" className="h-9 rounded-[var(--radius-control)] border border-control px-3 font-normal" />
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
    <Panel title={a.display_name} action={<span className="flex items-center gap-2"><Pill tone={statusTone(a.status)}>{ARTIFACT_STATUS[a.status]}</Pill><span className="text-xs text-faint">bản {a.version_count}</span></span>}>
      {a.status === "failed" && <ErrorNote error={new Error("Chưa tạo được. Bấm “Tạo lại” ở mục Ảnh & Video.")} />}
      {v?.url && (
        <div className="mx-auto max-w-sm overflow-hidden rounded-[var(--radius-card)] bg-ground">
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
        <p className="mt-2 text-center text-xs text-faint">Video tạo bằng MiniMax H3</p>
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
          <Button variant="primary" busy={busy === "approve"} onClick={() => act("approve", `/artifacts/${a.id}/approve`)}>Duyệt</Button>
        )}
        {v?.url && <a href={v.url} download className="inline-flex h-9 items-center rounded-[var(--radius-control)] bg-raised px-4 text-sm font-medium hover:bg-active">Tải xuống</a>}
        <Button variant="danger" busy={busy === "delete"} onClick={() => confirm("Xoá phương án này?") && act("delete", `/artifacts/${a.id}`, undefined, "DELETE")}>Xoá</Button>
      </div>
    </Panel>
  );
}
