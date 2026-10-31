"use client";

import { Plus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Button, Empty, ErrorNote, Field, PageTitle, Pill, Select, Skeleton } from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { api, ApiError, useApi } from "@/lib/api";
import { ago, bytes, OBJECTIVE } from "@/lib/format";
import type { Project, Service } from "@/lib/types";

const COUNT_LABEL: [keyof Project["counts"], string][] = [
  ["script", "kịch bản"],
  ["image", "ảnh"],
  ["video", "video"],
  ["short", "shorts"],
];

export default function ProjectsPage() {
  const { can } = useWorkspace();
  const list = useApi<Project[]>("/projects");
  const [creating, setCreating] = useState(false);

  return (
    <>
      <PageTitle
        title="Dự án quảng cáo"
        sub="Mỗi chiến dịch là một project: tài liệu, nghiên cứu, kịch bản, ảnh, video và lịch đăng ở cùng một chỗ."
        actions={
          can("admin", "marketing") && (
            <Button variant="primary" onClick={() => setCreating(true)}>
              <Plus className="size-4" aria-hidden /> Tạo project mới
            </Button>
          )
        }
      />
      {creating && <Wizard onClose={() => setCreating(false)} />}
      {list.error && <ErrorNote error={list.error} onRetry={list.reload} />}
      {list.loading && <Skeleton rows={4} />}
      {list.data?.length === 0 && !creating && (
        <Empty title="Chưa có project nào">
          Tạo project cho đợt quảng bá đầu tiên: tải ảnh sản phẩm, để AI nghiên cứu và viết Kịch bản A/B/C.
        </Empty>
      )}
      <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {list.data?.map((p) => (
          <li key={p.id}>
            <Link
              href={`/app/project?id=${p.id}`}
              className="group flex h-full flex-col overflow-hidden rounded-[var(--radius-card)] border border-border bg-surface transition-colors hover:border-control"
            >
              <div className="aspect-[16/7] bg-raised">
                {p.cover_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={p.cover_url} alt="" className="size-full object-cover" />
                ) : (
                  <div className="grid size-full place-items-center text-sm text-muted">Chưa có ảnh</div>
                )}
              </div>
              <div className="flex flex-1 flex-col gap-2 p-4">
                <div className="flex items-start justify-between gap-3">
                  <p className="font-semibold group-hover:underline">{p.name}</p>
                  {p.status === "draft" && <Pill>Nháp</Pill>}
                  {p.status === "archived" && <Pill>Lưu trữ</Pill>}
                </div>
                <p className="text-sm text-muted">{OBJECTIVE[p.objective] ?? p.objective} · tạo {ago(p.created_at)}</p>
                <p className="mt-auto text-sm">
                  {COUNT_LABEL.map(([k, label]) => `${p.counts[k] ?? 0} ${label}`).join(" · ")}
                  <span className="text-muted"> · {bytes(p.storage_bytes)}</span>
                </p>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}

const STEPS = ["Mục tiêu", "Khách hàng & thời gian", "Brief & nguồn nghiên cứu"] as const;

function Wizard({ onClose }: { onClose: () => void }) {
  const router = useRouter();
  const services = useApi<Service[]>("/services");
  const [step, setStep] = useState(0);
  const [project, setProject] = useState<Project | null>(null);
  const [form, setForm] = useState({
    name: "",
    objective: "promote_service",
    service_id: "",
    audience: "",
    location: "",
    start_date: "",
    end_date: "",
    brief: "",
    research_urls: "",
  });
  const [error, setError] = useState<ApiError | null>(null);
  const [saving, setSaving] = useState<"idle" | "saving" | "saved">("idle");
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const payload = (f = form) => ({
    name: f.name,
    objective: f.objective,
    service_id: f.service_id || null,
    audience: f.audience,
    location: f.location,
    start_date: f.start_date || null,
    end_date: f.end_date || null,
    brief: f.brief,
    research_urls: f.research_urls.split(/\s+/).filter(Boolean),
  });

  // Autosave after the project exists (BRD MOD-02A: wizard autosave, nothing lost on reload).
  useEffect(() => {
    if (!project) return;
    clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      setSaving("saving");
      try {
        await api(`/projects/${project.id}`, { method: "PATCH", json: payload() });
        setSaving("saved");
        setError(null);
      } catch (e) {
        setError(e as ApiError);
        setSaving("idle");
      }
    }, 600);
    return () => clearTimeout(timer.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form, project]);

  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function next() {
    setError(null);
    if (!project) {
      try {
        setProject(await api<Project>("/projects", { method: "POST", json: payload() }));
      } catch (e) {
        return setError(e as ApiError);
      }
    }
    if (step < STEPS.length - 1) setStep(step + 1);
    else router.push(`/app/project?id=${project!.id}`);
  }

  const fe = error?.fields ?? {};
  return (
    <section className="mb-8 rounded-[var(--radius-card)] border border-border bg-surface p-5" aria-label="Tạo project mới">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <ol className="flex flex-wrap gap-4 text-sm">
          {STEPS.map((s, i) => (
            <li key={s} aria-current={i === step ? "step" : undefined} className={i === step ? "font-semibold" : "text-muted"}>
              {i + 1}. {s}
            </li>
          ))}
        </ol>
        <span role="status" className="text-xs text-muted">
          {saving === "saving" ? "Đang lưu…" : saving === "saved" ? "Đã lưu" : ""}
        </span>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {step === 0 && (
          <>
            <Field label="Tên project" value={form.name} onChange={set("name")} placeholder="Ví dụ: Đá nóng tháng 11" error={fe.name} />
            <Select label="Mục tiêu" value={form.objective} onChange={set("objective")}>
              {Object.entries(OBJECTIVE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </Select>
            <Select label="Dịch vụ chính" value={form.service_id} onChange={set("service_id")}>
              <option value="">Chọn sau</option>
              {services.data?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </Select>
          </>
        )}
        {step === 1 && (
          <>
            <Field label="Khách hàng mục tiêu" textarea value={form.audience} onChange={set("audience")} placeholder="Nữ văn phòng 25–40 tuổi, hay mỏi vai gáy" />
            <Field label="Khu vực" value={form.location} onChange={set("location")} placeholder="Quận 3, TP.HCM" />
            <Field label="Bắt đầu" type="date" value={form.start_date} onChange={set("start_date")} error={fe.start_date} />
            <Field label="Kết thúc" type="date" value={form.end_date} onChange={set("end_date")} error={fe.end_date} />
          </>
        )}
        {step === 2 && (
          <>
            <div className="sm:col-span-2">
              <Field label="Brief chiến dịch" textarea rows={5} value={form.brief} onChange={set("brief")}
                placeholder="Muốn đẩy dịch vụ gì, ưu đãi gì (nếu có), thông điệp mong muốn, điều không được nói…" />
            </div>
            <div className="sm:col-span-2">
              <Field label="Nguồn để AI nghiên cứu (mỗi dòng một link)" textarea rows={3} value={form.research_urls} onChange={set("research_urls")}
                hint="Trang/fanpage công khai của đối thủ, bài báo ngành. AI chỉ trích dẫn từ các nguồn này." error={fe.research_urls} />
            </div>
          </>
        )}
      </div>
      {error && !Object.keys(fe).length && <div className="mt-4"><ErrorNote error={error} /></div>}
      <div className="mt-5 flex items-center gap-2">
        <Button variant="primary" onClick={next} disabled={!form.name.trim()}>
          {step < STEPS.length - 1 ? "Tiếp tục" : "Mở project"}
        </Button>
        {step > 0 && <Button variant="ghost" onClick={() => setStep(step - 1)}>Quay lại</Button>}
        <Button variant="ghost" onClick={onClose} className="ml-auto">Đóng</Button>
      </div>
    </section>
  );
}
