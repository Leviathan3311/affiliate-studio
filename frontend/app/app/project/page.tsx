"use client";

import { ArrowLeft, Library as LibraryIcon, X } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { ProjectChat } from "@/components/project/chat";
import { InputsSection } from "@/components/project/inputs";
import { Library } from "@/components/project/library";
import { JobsPanel, MediaSection, MediaView } from "@/components/project/media";
import { PublishSection } from "@/components/project/publish";
import { ReportView, ResearchSection } from "@/components/project/research";
import { CompareView, GenerateDialog, ScriptView } from "@/components/project/script";
import { Button, ErrorNote, Field, Panel, Pill, Skeleton } from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { api, ApiError, useApi } from "@/lib/api";
import { bytes, OBJECTIVE } from "@/lib/format";
import type { Artifact, EffectiveStyle, MediaJob, Project, Service, StylePack } from "@/lib/types";

type Section = "overview" | "inputs" | "research" | "scripts" | "media" | "shorts" | "publish";
const SECTIONS: { id: Section; label: string }[] = [
  { id: "overview", label: "Tổng quan" },
  { id: "inputs", label: "Đầu vào & tài liệu" },
  { id: "research", label: "Nghiên cứu" },
  { id: "scripts", label: "Kịch bản" },
  { id: "media", label: "Ảnh & Video" },
  { id: "shorts", label: "Shorts" },
  { id: "publish", label: "Xuất bản" },
];
const SECTION_OF: Record<Artifact["kind"], Section> = { research: "research", script: "scripts", image: "media", video: "media", short: "shorts" };

export default function ProjectPage() {
  return (
    <Suspense fallback={<Skeleton rows={8} />}>
      <Workspace />
    </Suspense>
  );
}

function Workspace() {
  const params = useSearchParams();
  const id = params.get("id")!;
  const project = useApi<Project>(`/projects/${id}`);
  const [polling, setPolling] = useState(20000);
  const artifacts = useApi<Artifact[]>(`/projects/${id}/artifacts`, polling);
  const jobs = useApi<MediaJob[]>(`/projects/${id}/jobs`, polling);
  const [section, setSection] = useState<Section>("overview");
  const [openId, setOpenId] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "selected">("all");
  const [compare, setCompare] = useState<string[]>([]);
  const [generateFor, setGenerateFor] = useState<string | null>(null);
  const [libraryOpen, setLibraryOpen] = useState(false);

  const all = artifacts.data ?? [];
  const busy = all.some((a) => a.status === "generating") || (jobs.data ?? []).some((j) => j.status === "queued" || j.status === "running");
  if ((busy ? 4000 : 20000) !== polling) setPolling(busy ? 4000 : 20000);

  const refresh = () => {
    project.reload();
    artifacts.reload();
    jobs.reload();
  };
  const open = all.find((a) => a.id === openId) ?? null;
  const openArtifact = (a: Artifact) => {
    setOpenId(a.id);
    setSection(SECTION_OF[a.kind]);
    setLibraryOpen(false);
  };

  if (project.error) return <ErrorNote error={project.error} onRetry={project.reload} />;
  if (!project.data) return <Skeleton rows={8} />;
  const p = project.data;
  const scripts = all.filter((a) => a.kind === "script");

  return (
    <div className="-m-4 flex h-[calc(100vh-48px)] flex-col sm:-m-6 lg:h-[calc(100vh-58px)]">
      <header className="flex flex-none flex-wrap items-center gap-3 border-b border-rule px-4 py-3 sm:px-6">
        <Link href="/app/projects" className="grid size-9 place-items-center rounded-lg text-muted hover:bg-raised" aria-label="Danh sách project">
          <ArrowLeft className="size-4" />
        </Link>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-lg font-semibold">{p.name}</h1>
          <p className="text-xs text-muted">{OBJECTIVE[p.objective] ?? p.objective} · {bytes(p.storage_bytes)} đã dùng</p>
        </div>
        {p.status === "deleted" && <Pill tone="negative">Trong thùng rác</Pill>}
        {all.some((a) => a.status === "approved") && (
          <Button variant="primary" onClick={() => setSection("publish")}>Xuất bản / Đặt lịch</Button>
        )}
        <Button variant="ghost" className="xl:hidden" onClick={() => setLibraryOpen(true)} aria-label="Mở thư viện phương án">
          <LibraryIcon className="size-4" /> <span className="hidden sm:inline">Các phương án</span>
        </Button>
      </header>

      <div className="flex min-h-0 flex-1">
        <nav aria-label="Mục của project" className="hidden w-48 flex-none flex-col gap-0.5 border-r border-rule p-3 md:flex">
          {SECTIONS.map((s) => (
            <button key={s.id} onClick={() => { setSection(s.id); setOpenId(null); }} aria-current={section === s.id ? "page" : undefined}
              className={`flex h-9 cursor-pointer items-center justify-between rounded-lg px-2.5 text-left text-sm ${section === s.id ? "bg-active font-medium" : "text-muted hover:bg-raised hover:text-ink"}`}>
              {s.label}
              <span className="text-xs">{countFor(s.id, all) || ""}</span>
            </button>
          ))}
        </nav>

        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex gap-1 overflow-x-auto border-b border-rule px-3 py-2 md:hidden" role="tablist" aria-label="Mục của project">
            {SECTIONS.map((s) => (
              <button key={s.id} role="tab" aria-selected={section === s.id} onClick={() => { setSection(s.id); setOpenId(null); }}
                className={`h-8 flex-none rounded-lg px-3 text-sm ${section === s.id ? "bg-active font-medium" : "text-muted"}`}>{s.label}</button>
            ))}
          </div>
          <main className="min-h-0 flex-1 space-y-6 overflow-y-auto p-4 sm:p-6">
            <JobsPanel jobs={jobs.data ?? []} onChanged={refresh} />
            {section === "overview" && <Overview project={p} artifacts={all} go={setSection} onChanged={refresh} />}
            {section === "inputs" && <InputsSection project={p} onChanged={refresh} />}
            {section === "research" && (open?.kind === "research"
              ? <ReportView a={open} />
              : <ResearchSection project={p} reports={all.filter((a) => a.kind === "research")} onChanged={refresh} />)}
            {section === "scripts" && (
              <ScriptsSection project={p} scripts={scripts} open={open?.kind === "script" ? open : null} compare={compare}
                setCompare={setCompare} onOpen={openArtifact} onChanged={refresh} onGenerate={setGenerateFor} />
            )}
            {(section === "media" || section === "shorts") && (open && open.kind !== "script" && open.kind !== "research"
              ? <MediaView a={open} onChanged={refresh} />
              : <MediaSection project={p} items={all} kinds={section === "shorts" ? ["short"] : ["image", "video"]} onOpen={openArtifact} onChanged={refresh} />)}
            {section === "publish" && <PublishSection project={p} artifacts={all} />}
          </main>
          <ProjectChat projectId={p.id} open={open} onChanged={refresh} onProposeGenerate={setGenerateFor} />
        </div>

        <aside aria-label="Thư viện phương án"
          className={`${libraryOpen ? "fixed inset-0 z-40 block bg-surface" : "hidden"} xl:static xl:block xl:w-[300px] xl:flex-none xl:border-l xl:border-rule`}>
          <div className="flex justify-end p-2 xl:hidden">
            <Button variant="ghost" onClick={() => setLibraryOpen(false)} aria-label="Đóng"><X className="size-4" /></Button>
          </div>
          <Library artifacts={all} openId={openId} onOpen={openArtifact} filter={filter} onFilter={setFilter} />
        </aside>
      </div>

      {generateFor && all.find((a) => a.id === generateFor) && (
        <GenerateDialog project={p} script={all.find((a) => a.id === generateFor)!} onClose={() => setGenerateFor(null)}
          onQueued={() => { refresh(); setSection("media"); setOpenId(null); }} />
      )}
    </div>
  );
}

function countFor(s: Section, all: Artifact[]) {
  const kinds: Partial<Record<Section, Artifact["kind"][]>> = { research: ["research"], scripts: ["script"], media: ["image", "video"], shorts: ["short"] };
  return all.filter((a) => kinds[s]?.includes(a.kind) && a.status !== "archived").length;
}

function ScriptsSection({ project, scripts, open, compare, setCompare, onOpen, onChanged, onGenerate }: {
  project: Project; scripts: Artifact[]; open: Artifact | null; compare: string[]; setCompare: (ids: string[]) => void;
  onOpen: (a: Artifact) => void; onChanged: () => void; onGenerate: (id: string) => void;
}) {
  const [count, setCount] = useState(3);
  const [instruction, setInstruction] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  async function write() {
    setBusy(true);
    setError(null);
    try {
      await api(`/projects/${project.id}/scripts`, { method: "POST", json: { count, instruction } });
      onChanged();
    } catch (e) {
      setError(e as ApiError);
    } finally {
      setBusy(false);
    }
  }

  const comparing = scripts.filter((s) => compare.includes(s.id));
  return (
    <div className="space-y-6">
      {comparing.length >= 2 && <CompareView items={comparing} onClose={() => setCompare([])} />}
      {open ? (
        <ScriptView a={open} project={project} onChanged={onChanged} onGenerate={() => onGenerate(open.id)} />
      ) : (
        <Panel title="Kịch bản quảng cáo">
          <div className="grid gap-3 sm:grid-cols-[110px_1fr_auto] sm:items-end">
            <label className="flex flex-col gap-1.5 text-sm font-medium">Số phương án
              <input type="number" min={1} max={5} value={count} onChange={(e) => setCount(Number(e.target.value))}
                className="h-9 rounded-[var(--radius-control)] border border-control px-2 font-normal" />
            </label>
            <Field label="Yêu cầu thêm (tuỳ chọn)" value={instruction} onChange={(e) => setInstruction(e.target.value)} placeholder="Ví dụ: một bản nhấn ưu đãi lần đầu" />
            <Button variant="primary" onClick={write} busy={busy}>Viết kịch bản</Button>
          </div>
          {error && <div className="mt-3"><ErrorNote error={error} /></div>}
          {scripts.length > 0 && (
            <ul className="mt-5 divide-y divide-rule">
              {scripts.map((s) => (
                <li key={s.id} className="flex items-center gap-3 py-2.5">
                  <input type="checkbox" aria-label={`So sánh ${s.display_name}`} checked={compare.includes(s.id)}
                    disabled={!compare.includes(s.id) && compare.length >= 3}
                    onChange={(e) => setCompare(e.target.checked ? [...compare, s.id] : compare.filter((x) => x !== s.id))}
                    className="size-4 accent-[var(--accent)]" />
                  <button onClick={() => onOpen(s)} className="min-w-0 flex-1 cursor-pointer truncate text-left text-sm font-medium hover:underline">{s.display_name}</button>
                  <span className="text-xs text-muted">{s.status === "selected" ? "Đã chọn" : s.status === "generating" ? "Đang viết…" : ""}</span>
                </li>
              ))}
            </ul>
          )}
          {scripts.length > 1 && <p className="mt-2 text-xs text-muted">Tick 2–3 kịch bản để so sánh cạnh nhau.</p>}
        </Panel>
      )}
    </div>
  );
}

function Overview({ project, artifacts, go, onChanged }: { project: Project; artifacts: Artifact[]; go: (s: Section) => void; onChanged: () => void }) {
  const has = (k: Artifact["kind"], st?: Artifact["status"]) => artifacts.some((a) => a.kind === k && (!st || a.status === st));
  const next: [string, Section] =
    !project.context ? ["Tải tài liệu và để AI đọc", "inputs"]
      : !project.context_confirmed_at ? ["Xác nhận Project Context", "inputs"]
      : !has("research") ? ["Nghiên cứu thị trường", "research"]
      : !has("script") ? ["Viết Kịch bản A/B/C", "scripts"]
      : !has("script", "selected") ? ["Chọn một kịch bản", "scripts"]
      : !has("image") && !has("video") ? ["Tạo ảnh & video", "scripts"]
      : !artifacts.some((a) => a.status === "approved") ? ["Xem và duyệt creative", "media"]
      : ["Lên lịch đăng", "publish"];
  const service = useApi<Service[]>("/services").data?.find((s) => s.id === project.service_id);
  return (
    <div className="space-y-6">
      <Panel title="Bước tiếp theo">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p>{next[0]}</p>
          <Button variant="primary" onClick={() => go(next[1])}>{next[0]}</Button>
        </div>
      </Panel>
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Thông tin chiến dịch">
          <dl className="space-y-2.5 text-sm">
            {([["Mục tiêu", OBJECTIVE[project.objective] ?? project.objective], ["Dịch vụ", service?.name ?? "—"], ["Khách hàng", project.audience || "—"],
              ["Khu vực", project.location || "—"], ["Thời gian", `${project.start_date ?? "?"} → ${project.end_date ?? "?"}`],
              ["Nguồn nghiên cứu", `${project.research_urls.length} link`]] as const).map(([k, v]) => (
              <div key={k} className="flex justify-between gap-4"><dt className="text-muted">{k}</dt><dd className="text-right">{v}</dd></div>
            ))}
          </dl>
          {project.brief && <p className="mt-4 whitespace-pre-wrap border-t border-rule pt-4 text-sm">{project.brief}</p>}
        </Panel>
        <StyleOverride project={project} />
      </div>
      <ProjectDanger project={project} onChanged={onChanged} />
    </div>
  );
}

function StyleOverride({ project }: { project: Project }) {
  const { can } = useWorkspace();
  const packs = useApi<StylePack[]>("/style-packs");
  const eff = useApi<Record<string, EffectiveStyle>>(`/style-assignments?project_id=${project.id}`);
  async function set(modality: string, value: string) {
    const body = value === "inherit" ? { modality, mode: "inherit" } : value === "off" ? { modality, mode: "off" } : { modality, mode: "pack", style_pack_id: value };
    await api(`/projects/${project.id}/style`, { method: "PUT", json: body });
    eff.reload();
  }
  return (
    <Panel title="Generation Style của project">
      <p className="mb-4 text-sm text-muted">Mặc định kế thừa style của workspace. Đổi ở đây chỉ ảnh hưởng project này.</p>
      <div className="space-y-3">
        {(["image", "video", "audio"] as const).map((m) => {
          const e = eff.data?.[m];
          const value = e?.source === "project" ? (e.pack_id ?? "off") : "inherit";
          return (
            <div key={m} className="flex flex-wrap items-center justify-between gap-3">
              <label htmlFor={`style-${m}`} className="text-sm">{{ image: "Ảnh", video: "Video", audio: "Nhạc nền" }[m]}</label>
              <select id={`style-${m}`} value={value} disabled={!can("admin", "marketing")} onChange={(ev) => set(m, ev.target.value)}
                className="h-9 min-w-56 rounded-[var(--radius-control)] border border-control px-2 text-sm">
                <option value="inherit">Kế thừa ({e?.source !== "project" ? (e?.pack_name ?? "không") : "workspace"})</option>
                {packs.data?.map((pk) => <option key={pk.id} value={pk.id}>{pk.name}</option>)}
                <option value="off">Không dùng style</option>
              </select>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

function ProjectDanger({ project, onChanged }: { project: Project; onChanged: () => void }) {
  const router = useRouter();
  const { can } = useWorkspace();
  if (!can("admin", "marketing")) return null;
  return (
    <Panel title="Quản lý project">
      <div className="flex flex-wrap gap-2">
        {project.status === "deleted" ? (
          <Button onClick={async () => { await api(`/projects/${project.id}/restore`, { method: "POST" }); onChanged(); }}>Khôi phục</Button>
        ) : (
          <>
            <Button onClick={async () => { await api(`/projects/${project.id}/archive`, { method: "POST" }); onChanged(); }}>Lưu trữ</Button>
            <Button variant="danger" onClick={async () => {
              if (!confirm(`Chuyển "${project.name}" vào thùng rác (${bytes(project.storage_bytes)})? Có thể khôi phục trong 30 ngày. Bài đã đăng trên Facebook không bị xoá.`)) return;
              await api(`/projects/${project.id}`, { method: "DELETE" });
              router.push("/app/projects");
            }}>Xoá project</Button>
          </>
        )}
      </div>
    </Panel>
  );
}
