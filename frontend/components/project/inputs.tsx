"use client";

import { ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import { useState } from "react";
import { Button, ErrorNote, Field, Panel, Pill, Skeleton } from "@/components/ui";
import { api, ApiError, useApi } from "@/lib/api";
import { bytes, INPUT_ROLE } from "@/lib/format";
import type { Project, ProjectContext, ProjectInput } from "@/lib/types";
import { readDocuments, UploadZone } from "./upload";

export function InputsSection({ project, onChanged }: { project: Project; onChanged: () => void }) {
  const inputs = useApi<ProjectInput[]>(`/projects/${project.id}/inputs`);
  const [reading, setReading] = useState(false);

  async function reread() {
    setReading(true);
    try {
      await readDocuments(project);
    } finally {
      setReading(false);
      onChanged();
    }
  }

  async function patch(inp: ProjectInput, body: Partial<ProjectInput>) {
    await api(`/project-inputs/${inp.id}`, { method: "PATCH", json: body });
    inputs.reload();
  }

  return (
    <div className="space-y-[14px]">
      <ContextCard project={project} reading={reading} onReread={reread} onChanged={onChanged} defaultOpen />
      <Panel title="Tài liệu & hình ảnh" action={<span className="text-sm text-faint">{inputs.data?.length ?? 0} tệp</span>}>
        {/* New files are read automatically: no separate "AI đọc" step. */}
        <UploadZone projectId={project.id} compact={!!inputs.data?.length} onUploaded={() => { inputs.reload(); reread(); }} />
        {inputs.loading && <div className="mt-4"><Skeleton rows={3} /></div>}
        <ul className="mt-2">
          {inputs.data?.map((inp) => (
            <li key={inp.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-rule py-3 last:border-0">
              {inp.mime_type.startsWith("image/") ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={inp.url} alt="" className="size-12 flex-none rounded-xl bg-raised object-cover" />
              ) : (
                <div className="grid size-12 flex-none place-items-center rounded-xl bg-raised text-xs text-muted">
                  {inp.filename.split(".").pop()?.toUpperCase()}
                </div>
              )}
              <div className="min-w-40 flex-1">
                <a href={inp.url} target="_blank" rel="noreferrer" className="block truncate text-sm font-medium hover:underline">{inp.filename}</a>
                <p className="text-xs text-faint">{bytes(inp.byte_size)}</p>
              </div>
              <label className="sr-only" htmlFor={`role-${inp.id}`}>Loại tệp</label>
              <select id={`role-${inp.id}`} value={inp.role} onChange={(e) => patch(inp, { role: e.target.value })}
                className="h-9 rounded-[var(--radius-control)] border border-control px-3 text-sm">
                {Object.entries(INPUT_ROLE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
              {inp.mime_type.startsWith("image/") && (
                <label className="flex cursor-pointer items-center gap-1.5 text-sm text-muted">
                  <input type="checkbox" checked={inp.preserve} onChange={(e) => patch(inp, { preserve: e.target.checked })} className="size-4 accent-[var(--text)]" />
                  Giữ nguyên khi tạo ảnh
                </label>
              )}
              <label className="flex cursor-pointer items-center gap-1.5 text-sm text-muted">
                <input type="checkbox" checked={inp.usage_confirmed} onChange={(e) => patch(inp, { usage_confirmed: e.target.checked })} className="size-4 accent-[var(--text)]" />
                Có quyền sử dụng
              </label>
              <Button variant="ghost" aria-label={`Xoá ${inp.filename}`} onClick={async () => {
                if (!confirm(`Xoá ${inp.filename}?`)) return;
                await api(`/project-inputs/${inp.id}`, { method: "DELETE" });
                inputs.reload();
                onChanged();
              }}><Trash2 className="size-4" /></Button>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}

const lines = (v: string) => v.split("\n").map((s) => s.trim()).filter(Boolean);

/** What the AI understood from the documents: short by default, the full editor on demand. */
export function ContextCard({ project, reading, onReread, onChanged, defaultOpen = false }: {
  project: Project; reading: boolean; onReread: () => void; onChanged: () => void; defaultOpen?: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [expanded, setExpanded] = useState(defaultOpen);
  const [error, setError] = useState<ApiError | null>(null);
  const [saving, setSaving] = useState(false);
  const ctx = project.context;

  async function save(form: HTMLFormElement) {
    const f = Object.fromEntries(new FormData(form)) as Record<string, string>;
    const next: ProjectContext = {
      summary: f.summary,
      services: ctx?.services ?? [],
      key_messages: lines(f.key_messages),
      brand_voice: f.brand_voice,
      audience: f.audience,
      key_facts: lines(f.key_facts).map((l) => {
        const [fact, source] = l.split(" | ");
        return { fact, source: source || "unverified" };
      }),
      constraints: lines(f.constraints),
      missing: lines(f.missing),
    };
    setSaving(true);
    setError(null);
    try {
      await api(`/projects/${project.id}/context`, { method: "PATCH", json: { context: next, confirm: true } });
      setEditing(false);
      onChanged();
    } catch (e) {
      setError(e as ApiError);
    } finally {
      setSaving(false);
    }
  }

  const toggle = (
    <button onClick={() => setExpanded((v) => !v)} aria-expanded={expanded}
      className="flex cursor-pointer items-center gap-1 text-sm text-muted hover:text-ink">
      {expanded ? <>Thu gọn <ChevronUp className="size-4" /></> : <>Xem thêm <ChevronDown className="size-4" /></>}
    </button>
  );

  return (
    <Panel title="AI hiểu dự án như sau" action={ctx && !editing && !reading ? toggle : undefined}>
      {error && <div className="mb-3"><ErrorNote error={error} /></div>}
      {reading && (
        <div className="space-y-3">
          <p className="text-sm text-muted">AI đang đọc tài liệu…</p>
          <Skeleton rows={3} />
        </div>
      )}
      {!ctx && !reading && <p className="text-sm text-muted">Tải tài liệu lên, AI sẽ tự đọc và tóm tắt dịch vụ, thông điệp và những gì còn thiếu.</p>}

      {ctx && !reading && !editing && (
        <div>
          <p className={`max-w-[75ch] leading-relaxed ${expanded ? "" : "line-clamp-2"}`}>{ctx.summary}</p>
          {expanded && (
            <div className="mt-5 grid gap-5 md:grid-cols-2">
              <Facts title="Thông điệp chính" items={ctx.key_messages} />
              <Facts title="Khách hàng" items={ctx.audience ? [ctx.audience] : []} />
              <Facts title="Dữ kiện" items={ctx.key_facts.map((k) => (k.source === "unverified" ? `${k.fact} (chưa xác minh)` : k.fact))} />
              <Facts title="Giọng điệu" items={ctx.brand_voice ? [ctx.brand_voice] : []} />
              {ctx.missing.length > 0 && <Facts title="Còn thiếu, nên bổ sung" items={ctx.missing} warn />}
            </div>
          )}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            {!project.context_confirmed_at && <Pill tone="warning">Chưa kiểm tra</Pill>}
            <Button onClick={() => { setEditing(true); setExpanded(true); }}>Sửa</Button>
            <Button variant="ghost" onClick={onReread}>Đọc lại tài liệu</Button>
          </div>
        </div>
      )}

      {ctx && !reading && editing && (
        <form onSubmit={(e) => { e.preventDefault(); save(e.currentTarget); }} className="grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2"><Field label="Tóm tắt" name="summary" textarea defaultValue={ctx.summary} /></div>
          <Field label="Thông điệp chính (mỗi dòng một ý)" name="key_messages" textarea rows={4} defaultValue={ctx.key_messages.join("\n")} />
          <Field label="Khách hàng" name="audience" textarea rows={4} defaultValue={ctx.audience} />
          <div className="sm:col-span-2">
            <Field label="Dữ kiện (dữ kiện | nguồn)" name="key_facts" textarea rows={5}
              defaultValue={ctx.key_facts.map((k) => `${k.fact} | ${k.source}`).join("\n")}
              hint='Giá, ưu đãi, thời hạn cần có nguồn; ghi "unverified" nếu chưa chắc, AI sẽ không dùng để báo giá' />
          </div>
          <Field label="Giọng điệu" name="brand_voice" textarea defaultValue={ctx.brand_voice} />
          <Field label="Điều không được nói" name="constraints" textarea defaultValue={ctx.constraints.join("\n")} />
          <div className="sm:col-span-2"><Field label="Còn thiếu" name="missing" textarea defaultValue={ctx.missing.join("\n")} /></div>
          <div className="flex gap-2 sm:col-span-2">
            <Button variant="primary" type="submit" busy={saving}>Lưu</Button>
            <Button variant="ghost" type="button" onClick={() => setEditing(false)}>Huỷ</Button>
          </div>
        </form>
      )}
    </Panel>
  );
}

function Facts({ title, items, warn }: { title: string; items: string[]; warn?: boolean }) {
  if (!items.length) return null;
  return (
    <section>
      <h3 className={`text-sm font-semibold ${warn ? "text-warning" : ""}`}>{title}</h3>
      <ul className="mt-1.5 space-y-1 text-sm text-muted">
        {items.map((x, i) => <li key={i}>{x}</li>)}
      </ul>
    </section>
  );
}
