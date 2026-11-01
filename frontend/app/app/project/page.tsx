"use client";

import { ArrowLeft, ArrowRight, Library as LibraryIcon, X } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { ProjectChat } from "@/components/project/chat";
import { ContextCard, InputsSection } from "@/components/project/inputs";
import { Library } from "@/components/project/library";
import { JobStrip, MediaSection, MediaView } from "@/components/project/media";
import { PublishSection } from "@/components/project/publish";
import { ReportView, ResearchSection } from "@/components/project/research";
import { CompareView, GenerateDialog, ScriptView } from "@/components/project/script";
import { readDocuments } from "@/components/project/upload";
import { Button, ErrorNote, Field, Panel, Pill, Skeleton } from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { api, ApiError, useApi } from "@/lib/api";
import { bytes, OBJECTIVE } from "@/lib/format";
import type { Artifact, EffectiveStyle, MediaJob, Project, Service, StylePack } from "@/lib/types";

type Section = "overview" | "inputs" | "research" | "scripts" | "media" | "shorts" | "publish";
const SECTIONS: { id: Section; label: string }[] = [
  { id: "overview", label: "Tổng quan" },
  { id: "inputs", label: "Tài liệu" },
  { id: "research", label: "Nghiên cứu" },
  { id: "scripts", label: "Kịch bản" },
  { id: "media", label: "Ảnh & Video" },
  { id: "shorts", label: "Shorts" },
  { id: "publish", label: "Đăng bài" },
];
const SECTION_OF: Record<Artifact["kind"], Section> = { research: "research", script: "scripts", image: "media", video: "media", short: "shorts" };
const MEDIA: Artifact["kind"][] = ["image", "video", "short"];
const BACK: Record<Artifact["kind"], string> = { script: "Tất cả kịch bản", research: "Báo cáo mới nhất", image: "Tất cả ảnh & video", video: "Tất cả ảnh & video", short: "Tất cả Shorts" };

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
  const [polling, setPolling] = useState(20000);
  const project = useApi<Project>(`/projects/${id}`, polling);
  const artifacts = useApi<Artifact[]>(`/projects/${id}/artifacts`, polling);
  const jobs = useApi<MediaJob[]>(`/projects/${id}/jobs`, polling);
  const [section, setSection] = useState<Section>("overview");
  const [openId, setOpenId] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "selected">("all");
  const [compare, setCompare] = useState<string[]>([]);
  const [generateFor, setGenerateFor] = useState<string | null>(null);
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [reading, setReading] = useState(false);
  const [openedAt] = useState(() => Date.now());

  // A failed render leaves empty image/video records behind; the failure is shown once, on the job.
  const all = (artifacts.data ?? []).filter((a) => !(a.status === "failed" && MEDIA.includes(a.kind)));
  const jobList = jobs.data ?? [];
  // The wizard starts reading the documents; the summary arrives a minute or so after creation.
  const awaitingSummary = !!project.data && !project.data.context && openedAt - Date.parse(project.data.created_at) < 180_000;
  const busy = awaitingSummary || all.some((a) => a.status === "generating") || jobList.some((j) => j.status === "queued" || j.status === "running");
  if ((busy ? 4000 : 20000) !== polling) setPolling(busy ? 4000 : 20000);

  const refresh = () => {
    project.reload();
    artifacts.reload();
    jobs.reload();
  };
  const go = (s: Section) => {
    setSection(s);
    setOpenId(null);
  };
  const open = all.find((a) => a.id === openId) ?? null;
  const openArtifact = (a: Artifact) => {
    setOpenId(a.id);
    setSection(SECTION_OF[a.kind]);
    setLibraryOpen(false);
  };
  async function reread() {
    if (!project.data) return;
    setReading(true);
    try {
      await readDocuments(project.data);
    } finally {
      setReading(false);
      refresh();
    }
  }

  if (project.error) return <ErrorNote error={project.error} onRetry={project.reload} />;
  if (!project.data) return <Skeleton rows={8} />;
  const p = project.data;
  const scripts = all.filter((a) => a.kind === "script");
  const selected = scripts.find((a) => a.status === "selected");
  const next = nextStep(p, all, jobList);

  return (
    <div className="-m-4 flex h-[calc(100vh-48px)] flex-col sm:-m-6">
      <header className="flex flex-none flex-wrap items-center gap-3 px-4 pt-4 sm:px-7">
        <Link href="/app/projects" className="grid size-9 place-items-center rounded-full text-muted hover:bg-raised hover:text-ink" aria-label="Danh sách dự án">
          <ArrowLeft className="size-4" />
        </Link>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-xl font-semibold">{p.name}</h1>
          <p className="text-xs text-faint">{OBJECTIVE[p.objective] ?? p.objective}{p.location ? ` · ${p.location}` : ""}</p>
        </div>
        {p.status === "deleted" && <Pill tone="negative">Trong thùng rác</Pill>}
        {next && section !== next.section && (
          <span className="hidden sm:block">
            <Button variant="primary" onClick={() => go(next.section)}>
              {next.label} <ArrowRight className="size-4" aria-hidden />
            </Button>
          </span>
        )}
        <Button variant="ghost" className="xl:hidden" onClick={() => setLibraryOpen(true)} aria-label="Mở thư viện">
          <LibraryIcon className="size-4" /> <span className="hidden sm:inline">Thư viện</span>
        </Button>
      </header>

      <nav aria-label="Các bước của dự án" className="mt-3 flex flex-none gap-6 overflow-x-auto border-b border-rule px-4 [scrollbar-width:none] sm:px-7">
        {SECTIONS.map((s) => {
          const n = countFor(s.id, all);
          const current = section === s.id;
          return (
            <button key={s.id} onClick={() => go(s.id)} aria-current={current ? "page" : undefined}
              className={`-mb-px flex h-11 flex-none cursor-pointer items-center gap-1.5 border-b-2 text-sm transition-colors ${current ? "border-ink font-medium text-ink" : "border-transparent text-faint hover:text-ink"}`}>
              {s.label}
              {n > 0 && <span className="text-xs text-faint">{n}</span>}
            </button>
          );
        })}
      </nav>

      <div className="flex min-h-0 flex-1">
        <div className="flex min-w-0 flex-1 flex-col">
          <main className="min-h-0 flex-1 space-y-[14px] overflow-y-auto px-4 py-5 sm:px-7">
            <JobStrip jobs={jobList} onChanged={refresh} />
            {open && (
              <button onClick={() => setOpenId(null)}
                className="-ml-1 flex h-8 cursor-pointer items-center gap-1.5 rounded-full pl-1 pr-3 text-sm text-muted transition-colors hover:bg-raised hover:text-ink">
                <ArrowLeft className="size-4" aria-hidden /> {BACK[open.kind]}
              </button>
            )}
            {section === "overview" && (
              <Overview project={p} next={next} go={go} reading={reading || awaitingSummary} onReread={reread} onChanged={refresh} />
            )}
            {section === "inputs" && <InputsSection project={p} onChanged={refresh} />}
            {section === "research" && (open?.kind === "research"
              ? <ReportView a={open} />
              : <ResearchSection project={p} reports={all.filter((a) => a.kind === "research")} onChanged={refresh} />)}
            {section === "scripts" && (
              <ScriptsSection project={p} scripts={scripts} open={open?.kind === "script" ? open : null} compare={compare}
                setCompare={setCompare} onOpen={openArtifact} onChanged={refresh} onGenerate={setGenerateFor} />
            )}
            {(section === "media" || section === "shorts") && (open && MEDIA.includes(open.kind)
              ? <MediaView a={open} onChanged={refresh} />
              : <MediaSection project={p} items={all} jobs={jobList} kinds={section === "shorts" ? ["short"] : ["image", "video"]}
                  onOpen={openArtifact} onChanged={refresh} onRetry={selected ? () => setGenerateFor(selected.id) : undefined} />)}
            {section === "publish" && <PublishSection project={p} artifacts={all} />}
          </main>
          <ProjectChat projectId={p.id} open={open} onChanged={refresh} onProposeGenerate={setGenerateFor} />
        </div>

        <aside aria-label="Thư viện"
          className={`${libraryOpen ? "fixed inset-0 z-40 block bg-ground" : "hidden"} xl:static xl:block xl:w-[300px] xl:flex-none xl:border-l xl:border-rule`}>
          <div className="flex justify-end p-2 xl:hidden">
            <Button variant="ghost" onClick={() => setLibraryOpen(false)} aria-label="Đóng"><X className="size-4" /></Button>
          </div>
          <Library artifacts={all} openId={openId} onOpen={openArtifact} filter={filter} onFilter={setFilter} />
        </aside>
      </div>

      {generateFor && all.find((a) => a.id === generateFor) && (
        <GenerateDialog project={p} script={all.find((a) => a.id === generateFor)!} onClose={() => setGenerateFor(null)}
          onQueued={() => { refresh(); go("media"); }} />
      )}
    </div>
  );
}

type Next = { label: string; why: string; section: Section };

/** The one thing to do now. Reading documents happens on its own, so it is never a step. */
function nextStep(p: Project, all: Artifact[], jobs: MediaJob[]): Next | null {
  // A failed attempt does not count as done.
  const has = (k: Artifact["kind"], st?: Artifact["status"]) => all.some((a) => a.kind === k && (st ? a.status === st : a.status !== "failed"));
  const rendering = jobs.some((j) => j.kind === "studio" && (j.status === "queued" || j.status === "running"));
  if (!has("research")) return { label: "Nghiên cứu thị trường", why: "AI tìm hiểu khách hàng, đối thủ và xu hướng trước khi viết.", section: "research" };
  if (!has("script")) return { label: "Viết kịch bản", why: "AI viết 3 phương án kịch bản video từ nghiên cứu.", section: "scripts" };
  if (!has("script", "selected")) return { label: "Chọn kịch bản", why: "Mở từng phương án và bấm “Dùng kịch bản này” cho bản ưng nhất.", section: "scripts" };
  if (rendering) return { label: "Xem tiến độ", why: "Ảnh và video đang được tạo, bạn có thể đóng trang.", section: "media" };
  if (!has("image") && !has("video")) return { label: "Tạo ảnh & video", why: "Mở kịch bản đã chọn và bấm “Tạo ảnh & video”.", section: "scripts" };
  if (!all.some((a) => a.status === "approved")) return { label: "Duyệt ảnh & video", why: "Xem kết quả và duyệt bản sẽ đăng.", section: "media" };
  return { label: "Lên lịch đăng", why: "Đăng ngay hoặc hẹn giờ lên Facebook.", section: "publish" };
}

function countFor(s: Section, all: Artifact[]) {
  const kinds: Partial<Record<Section, Artifact["kind"][]>> = { scripts: ["script"], media: ["image", "video"], shorts: ["short"] };
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
  if (open) return <ScriptView a={open} project={project} onChanged={onChanged} onGenerate={() => onGenerate(open.id)} />;
  return (
    <div className="space-y-[14px]">
      {comparing.length >= 2 && <CompareView items={comparing} onClose={() => setCompare([])} />}
      {scripts.length > 0 && (
        <Panel title="Các phương án" action={scripts.length > 1 ? <span className="text-xs text-faint">Tick 2–3 bản để so sánh</span> : undefined}>
          <ul>
            {scripts.map((s) => {
              const c = s.current?.content as { hook?: string; duration_seconds?: number } | undefined;
              return (
                <li key={s.id} className="flex items-center gap-4 border-b border-rule py-3 last:border-0">
                  <input type="checkbox" aria-label={`So sánh ${s.display_name}`} checked={compare.includes(s.id)}
                    disabled={!compare.includes(s.id) && compare.length >= 3}
                    onChange={(e) => setCompare(e.target.checked ? [...compare, s.id] : compare.filter((x) => x !== s.id))}
                    className="size-4 accent-[var(--text)]" />
                  <button onClick={() => onOpen(s)} className="min-w-0 flex-1 cursor-pointer text-left">
                    <span className="block truncate font-medium hover:underline">{s.display_name}</span>
                    <span className="block truncate text-sm text-faint">
                      {s.status === "generating" ? "AI đang viết…" : c?.hook ? `“${c.hook}” · ${c.duration_seconds} giây` : ""}
                    </span>
                  </button>
                  {s.status === "selected" && <Pill tone="accent">Đã chọn</Pill>}
                </li>
              );
            })}
          </ul>
        </Panel>
      )}
      <Panel title={scripts.length ? "Viết thêm phương án" : "Viết kịch bản video"}>
        <div className="grid gap-3 sm:grid-cols-[120px_1fr_auto] sm:items-end">
          <label className="flex flex-col gap-1.5 text-sm font-medium">Số phương án
            <input type="number" min={1} max={5} value={count} onChange={(e) => setCount(Number(e.target.value))}
              className="h-9 rounded-[var(--radius-input)] border border-control px-3 font-normal" />
          </label>
          <Field label="Yêu cầu thêm (tuỳ chọn)" value={instruction} onChange={(e) => setInstruction(e.target.value)} placeholder="Ví dụ: một bản nhấn ưu đãi lần đầu" />
          <Button variant="primary" onClick={write} busy={busy}>Viết kịch bản</Button>
        </div>
        {error && <div className="mt-3"><ErrorNote error={error} /></div>}
      </Panel>
    </div>
  );
}

function Overview({ project, next, go, reading, onReread, onChanged }: {
  project: Project; next: Next | null; go: (s: Section) => void; reading: boolean; onReread: () => void; onChanged: () => void;
}) {
  const service = useApi<Service[]>("/services").data?.find((s) => s.id === project.service_id);
  return (
    <div className="space-y-[14px]">
      {next && (
        <section className="flex flex-wrap items-center justify-between gap-4 rounded-[var(--radius-card)] bg-surface px-[22px] py-5">
          <div className="min-w-60 flex-1">
            <h2 className="text-base font-semibold">Tiếp theo: {next.label}</h2>
            <p className="mt-1 text-sm text-muted">{next.why}</p>
          </div>
          <Button variant="primary" onClick={() => go(next.section)}>{next.label} <ArrowRight className="size-4" aria-hidden /></Button>
        </section>
      )}
      <ContextCard project={project} reading={reading} onReread={onReread} onChanged={onChanged} />
      <div className="grid gap-[14px] lg:grid-cols-2">
        <Panel title="Thông tin chiến dịch">
          <dl className="space-y-2.5 text-sm">
            {([["Mục tiêu", OBJECTIVE[project.objective] ?? project.objective], ["Dịch vụ", service?.name ?? "—"], ["Khách hàng", project.audience || "—"],
              ["Khu vực", project.location || "—"], ["Thời gian", project.start_date ? `${project.start_date} → ${project.end_date ?? "?"}` : "—"],
              ["Nguồn tham khảo", project.research_urls.length ? `${project.research_urls.length} link` : "—"]] as const).map(([k, v]) => (
              <div key={k} className="flex justify-between gap-4"><dt className="text-faint">{k}</dt><dd className="text-right">{v}</dd></div>
            ))}
          </dl>
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
    <Panel title="Phong cách hình ảnh">
      <div className="space-y-3">
        {(["image", "video", "audio"] as const).map((m) => {
          const e = eff.data?.[m];
          const value = e?.source === "project" ? (e.pack_id ?? "off") : "inherit";
          return (
            <div key={m} className="flex flex-wrap items-center justify-between gap-3">
              <label htmlFor={`style-${m}`} className="text-sm text-faint">{{ image: "Ảnh", video: "Video", audio: "Nhạc nền" }[m]}</label>
              <select id={`style-${m}`} value={value} disabled={!can("admin", "marketing")} onChange={(ev) => set(m, ev.target.value)}
                className="h-9 min-w-56 rounded-[var(--radius-control)] border border-control px-3 text-sm">
                <option value="inherit">Mặc định ({e?.source !== "project" ? (e?.pack_name ?? "không") : "của spa"})</option>
                {packs.data?.map((pk) => <option key={pk.id} value={pk.id}>{pk.name}</option>)}
                <option value="off">Không dùng phong cách</option>
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
    <div className="flex flex-wrap items-center gap-2 px-1 pt-2">
      <span className="mr-auto text-xs text-faint">Đã dùng {bytes(project.storage_bytes)} lưu trữ</span>
      {project.status === "deleted" ? (
        <Button onClick={async () => { await api(`/projects/${project.id}/restore`, { method: "POST" }); onChanged(); }}>Khôi phục</Button>
      ) : (
        <>
          <Button variant="ghost" onClick={async () => { await api(`/projects/${project.id}/archive`, { method: "POST" }); onChanged(); }}>Lưu trữ dự án</Button>
          <Button variant="danger" onClick={async () => {
            if (!confirm(`Chuyển "${project.name}" vào thùng rác? Có thể khôi phục trong 30 ngày. Bài đã đăng trên Facebook không bị xoá.`)) return;
            await api(`/projects/${project.id}`, { method: "DELETE" });
            router.push("/app/projects");
          }}>Xoá dự án</Button>
        </>
      )}
    </div>
  );
}
