"use client";

import { Upload } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";
import { Button, ErrorNote } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import type { Project } from "@/lib/types";

export const ACCEPT = ".pdf,.docx,.txt,.jpg,.jpeg,.png,.webp,.mp4,.mov";

function guessRole(f: File): string {
  if (f.type.startsWith("video/")) return "source_video";
  if (f.type.startsWith("image/")) return /logo/i.test(f.name) ? "logo" : "product";
  return "brief";
}

/** Ask the AI to (re)read the project's documents; resolves once the summary has changed. */
export async function readDocuments(project: Project) {
  const before = JSON.stringify(project.context);
  await api(`/projects/${project.id}/context/build`, { method: "POST" });
  for (let i = 0; i < 40; i++) {
    await new Promise((r) => setTimeout(r, 3000));
    const p = await api<Project>(`/projects/${project.id}`);
    if (JSON.stringify(p.context) !== before) return;
  }
}

/** Drop zone that uploads straight to storage (presigned PUT) and registers each file on the project. */
export function UploadZone({ projectId, onUploaded, compact }: { projectId: string; onUploaded: (names: string[]) => void; compact?: boolean }) {
  const [uploading, setUploading] = useState<string[]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [drag, setDrag] = useState(false);
  const picker = useRef<HTMLInputElement>(null);

  async function upload(files: FileList | File[]) {
    setError(null);
    const done: string[] = [];
    for (const file of Array.from(files)) {
      setUploading((u) => [...u, file.name]);
      try {
        const pre = await api<{ object_id: string; upload_url: string; headers: Record<string, string> }>(
          `/projects/${projectId}/inputs/presign`,
          { method: "POST", json: { filename: file.name, content_type: file.type || "application/octet-stream", byte_size: file.size } },
        );
        const put = await fetch(pre.upload_url, { method: "PUT", body: file, headers: pre.headers });
        if (!put.ok) throw new ApiError(put.status, `Tải lên ${file.name} chưa được, thử lại nhé`);
        await api(`/projects/${projectId}/inputs`, { method: "POST", json: { object_id: pre.object_id, role: guessRole(file) } });
        done.push(file.name);
      } catch (e) {
        setError(e as ApiError);
      } finally {
        setUploading((u) => u.filter((n) => n !== file.name));
      }
    }
    if (done.length) onUploaded(done);
  }

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e: DragEvent) => { e.preventDefault(); setDrag(false); upload(e.dataTransfer.files); }}
        className={`flex flex-wrap items-center gap-4 rounded-[var(--radius-card)] border border-dashed px-5 transition-colors ${compact ? "py-4" : "py-7"} ${drag ? "border-accent bg-[var(--pill-accent-bg)]" : "border-control bg-ground"}`}
      >
        <Upload className="size-5 flex-none text-muted" aria-hidden />
        <div className="min-w-48 flex-1">
          <p className="text-sm font-medium">Kéo thả tài liệu vào đây</p>
          <p className="text-xs text-muted">Brief, bảng giá (PDF, DOCX, TXT), ảnh sản phẩm, logo, video cửa hàng · AI sẽ tự đọc</p>
        </div>
        <Button onClick={() => picker.current?.click()} busy={uploading.length > 0}>Chọn tệp</Button>
        <input ref={picker} type="file" multiple accept={ACCEPT} className="sr-only" aria-label="Chọn tệp tải lên"
          onChange={(e) => { if (e.target.files) upload(e.target.files); e.target.value = ""; }} />
      </div>
      {uploading.length > 0 && <p role="status" className="mt-2 text-xs text-muted">Đang tải lên: {uploading.join(", ")}</p>}
      {error && <div className="mt-3"><ErrorNote error={error} /></div>}
    </div>
  );
}
