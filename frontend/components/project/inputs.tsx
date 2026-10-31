"use client";

import { Upload } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";
import { Button, Empty, ErrorNote, Field, Panel, Pill, Skeleton } from "@/components/ui";
import { api, ApiError, useApi } from "@/lib/api";
import { bytes, INPUT_ROLE } from "@/lib/format";
import type { Project, ProjectContext, ProjectInput } from "@/lib/types";

const ACCEPT = ".pdf,.docx,.txt,.jpg,.jpeg,.png,.webp,.mp4,.mov";

function guessRole(f: File): string {
  if (f.type.startsWith("video/")) return "source_video";
  if (f.type.startsWith("image/")) return /logo/i.test(f.name) ? "logo" : "product";
  return "brief";
}

export function InputsSection({ project, onChanged }: { project: Project; onChanged: () => void }) {
  const inputs = useApi<ProjectInput[]>(`/projects/${project.id}/inputs`);
  const [uploading, setUploading] = useState<string[]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [drag, setDrag] = useState(false);
  const picker = useRef<HTMLInputElement>(null);

  async function upload(files: FileList | File[]) {
    setError(null);
    for (const file of Array.from(files)) {
      setUploading((u) => [...u, file.name]);
      try {
        const pre = await api<{ object_id: string; upload_url: string; headers: Record<string, string> }>(
          `/projects/${project.id}/inputs/presign`,
          { method: "POST", json: { filename: file.name, content_type: file.type || "application/octet-stream", byte_size: file.size } },
        );
        const put = await fetch(pre.upload_url, { method: "PUT", body: file, headers: pre.headers });
        if (!put.ok) throw new ApiError(put.status, `Tải lên ${file.name} thất bại (${put.status})`);
        await api(`/projects/${project.id}/inputs`, { method: "POST", json: { object_id: pre.object_id, role: guessRole(file) } });
      } catch (e) {
        setError(e as ApiError);
      } finally {
        setUploading((u) => u.filter((n) => n !== file.name));
      }
    }
    inputs.reload();
    onChanged();
  }

  async function patch(inp: ProjectInput, body: Partial<ProjectInput>) {
    await api(`/project-inputs/${inp.id}`, { method: "PATCH", json: body });
    inputs.reload();
  }

  return (
    <div className="space-y-6">
      <Panel title="Tài liệu & hình ảnh đầu vào" action={<span className="text-sm text-muted">{inputs.data?.length ?? 0} tệp</span>}>
        <div
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e: DragEvent) => { e.preventDefault(); setDrag(false); upload(e.dataTransfer.files); }}
          className={`flex flex-col items-center gap-2 rounded-[var(--radius-card)] border border-dashed px-4 py-8 text-center transition-colors ${drag ? "border-accent bg-[var(--pill-accent-bg)]" : "border-control"}`}
        >
          <Upload className="size-5 text-muted" aria-hidden />
          <p className="text-sm">Kéo thả ảnh sản phẩm, logo, brief PDF, bảng giá hoặc video vào đây</p>
          <Button onClick={() => picker.current?.click()} busy={uploading.length > 0}>Chọn tệp</Button>
          <input ref={picker} type="file" multiple accept={ACCEPT} className="sr-only" aria-label="Chọn tệp tải lên"
            onChange={(e) => e.target.files && upload(e.target.files)} />
          {uploading.length > 0 && <p role="status" className="text-xs text-muted">Đang tải: {uploading.join(", ")}</p>}
        </div>
        {error && <div className="mt-3"><ErrorNote error={error} /></div>}
        {inputs.loading && <div className="mt-4"><Skeleton rows={3} /></div>}
        <ul className="mt-4 divide-y divide-rule">
          {inputs.data?.map((inp) => (
            <li key={inp.id} className="flex flex-wrap items-center gap-3 py-3">
              {inp.mime_type.startsWith("image/") ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={inp.url} alt="" className="size-12 flex-none rounded-md bg-raised object-cover" />
              ) : (
                <div className="grid size-12 flex-none place-items-center rounded-md bg-raised text-xs text-muted">
                  {inp.filename.split(".").pop()?.toUpperCase()}
                </div>
              )}
              <div className="min-w-48 flex-1">
                <a href={inp.url} target="_blank" rel="noreferrer" className="block truncate text-sm font-medium hover:underline">{inp.filename}</a>
                <p className="text-xs text-muted">{bytes(inp.byte_size)}</p>
              </div>
              <label className="sr-only" htmlFor={`role-${inp.id}`}>Vai trò</label>
              <select id={`role-${inp.id}`} value={inp.role} onChange={(e) => patch(inp, { role: e.target.value })}
                className="h-9 rounded-[var(--radius-control)] border border-control px-2 text-sm">
                {Object.entries(INPUT_ROLE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
              <label className="flex cursor-pointer items-center gap-1.5 text-sm">
                <input type="checkbox" checked={inp.preserve} onChange={(e) => patch(inp, { preserve: e.target.checked })} className="size-4 accent-[var(--accent)]" />
                Giữ nguyên khi AI tạo ảnh
              </label>
              <label className="flex cursor-pointer items-center gap-1.5 text-sm">
                <input type="checkbox" checked={inp.usage_confirmed} onChange={(e) => patch(inp, { usage_confirmed: e.target.checked })} className="size-4 accent-[var(--accent)]" />
                Có quyền sử dụng
              </label>
              <Button variant="danger" className="h-8 text-xs" onClick={async () => {
                if (!confirm(`Xoá ${inp.filename}? Tệp sẽ bị xoá khỏi kho lưu trữ.`)) return;
                await api(`/project-inputs/${inp.id}`, { method: "DELETE" });
                inputs.reload();
                onChanged();
              }}>Xoá</Button>
            </li>
          ))}
        </ul>
      </Panel>
      <ContextPanel project={project} onChanged={onChanged} />
    </div>
  );
}

const lines = (v: string) => v.split("\n").map((s) => s.trim()).filter(Boolean);

function ContextPanel({ project, onChanged }: { project: Project; onChanged: () => void }) {
  const [building, setBuilding] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [saving, setSaving] = useState(false);
  const ctx = project.context;

  async function build() {
    setBuilding(true);
    setError(null);
    try {
      await api(`/projects/${project.id}/context/build`, { method: "POST" });
      // built in the background: poll until the context changes
      for (let i = 0; i < 40; i++) {
        await new Promise((r) => setTimeout(r, 3000));
        const p = await api<Project>(`/projects/${project.id}`);
        if (JSON.stringify(p.context) !== JSON.stringify(ctx)) break;
      }
      onChanged();
    } catch (e) {
      setError(e as ApiError);
    } finally {
      setBuilding(false);
    }
  }

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
    try {
      await api(`/projects/${project.id}/context`, { method: "PATCH", json: { context: next, confirm: true } });
      onChanged();
    } catch (e) {
      setError(e as ApiError);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Panel
      title="Project Context"
      action={
        <div className="flex items-center gap-2">
          {project.context_confirmed_at ? <Pill tone="positive">Đã xác nhận</Pill> : ctx ? <Pill tone="warning">Chờ xác nhận</Pill> : null}
          <Button onClick={build} busy={building}>{ctx ? "AI đọc lại tài liệu" : "AI đọc tài liệu"}</Button>
        </div>
      }
    >
      {error && <div className="mb-3"><ErrorNote error={error} /></div>}
      {!ctx && !building && (
        <Empty title="Chưa có context">AI đọc brief, PDF và ảnh để tóm tắt dịch vụ, thông điệp, dữ kiện và những gì còn thiếu. Bạn sửa rồi xác nhận trước khi tạo kịch bản.</Empty>
      )}
      {building && <Skeleton rows={4} />}
      {ctx && !building && (
        <form key={JSON.stringify(ctx)} onSubmit={(e) => { e.preventDefault(); save(e.currentTarget); }} className="grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2"><Field label="Tóm tắt" name="summary" textarea defaultValue={ctx.summary} /></div>
          <Field label="Thông điệp chính (mỗi dòng một ý)" name="key_messages" textarea defaultValue={ctx.key_messages.join("\n")} />
          <Field label="Khách hàng" name="audience" textarea defaultValue={ctx.audience} />
          <div className="sm:col-span-2">
            <Field label="Dữ kiện (dữ kiện | nguồn)" name="key_facts" textarea rows={4}
              defaultValue={ctx.key_facts.map((k) => `${k.fact} | ${k.source}`).join("\n")}
              hint='Giá, ưu đãi, thời hạn phải có nguồn; "unverified" = chưa xác minh, AI sẽ không dùng để báo giá' />
          </div>
          <Field label="Giọng điệu" name="brand_voice" textarea defaultValue={ctx.brand_voice} />
          <Field label="Ràng buộc" name="constraints" textarea defaultValue={ctx.constraints.join("\n")} />
          <div className="sm:col-span-2"><Field label="Còn thiếu" name="missing" textarea defaultValue={ctx.missing.join("\n")} /></div>
          <div className="sm:col-span-2"><Button variant="primary" type="submit" busy={saving}>Lưu và xác nhận context</Button></div>
        </form>
      )}
    </Panel>
  );
}
