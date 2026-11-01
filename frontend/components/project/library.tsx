"use client";

import { FileText, Film, Image as ImageIcon, Loader2, Pin, Scissors, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { Pill } from "@/components/ui";
import { api } from "@/lib/api";
import { ago, ARTIFACT_STATUS } from "@/lib/format";
import type { Artifact, ArtifactKind } from "@/lib/types";

const GROUPS: { kind: ArtifactKind; label: string; icon: typeof FileText }[] = [
  { kind: "script", label: "Kịch bản", icon: FileText },
  { kind: "image", label: "Ảnh", icon: ImageIcon },
  { kind: "video", label: "Video", icon: Film },
  { kind: "short", label: "Shorts", icon: Scissors },
  { kind: "research", label: "Nghiên cứu", icon: Search },
];

export function statusTone(s: Artifact["status"]) {
  return s === "approved" ? "positive" : s === "selected" ? "accent" : s === "failed" ? "negative" : s === "generating" ? "warning" : "neutral";
}

/** Delete from wherever the item is listed, after one confirm that names it. */
export function DeleteButton({ a, onDeleted, className = "" }: { a: Artifact; onDeleted: () => void; className?: string }) {
  const [busy, setBusy] = useState(false);
  if (a.status === "generating") return null;
  return (
    <button aria-label={`Xoá ${a.display_name}`} title="Xoá" disabled={busy}
      onClick={async (e) => {
        e.stopPropagation();
        if (!confirm(`Xoá “${a.display_name}”? Không thể khôi phục.`)) return;
        setBusy(true);
        try {
          await api(`/artifacts/${a.id}`, { method: "DELETE" });
          onDeleted();
        } catch (err) {
          alert((err as Error).message);
          setBusy(false);
        }
      }}
      className={`grid size-8 flex-none cursor-pointer place-items-center rounded-full text-faint transition-colors hover:bg-raised hover:text-negative disabled:opacity-50 ${className}`}>
      {busy ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <Trash2 className="size-4" aria-hidden />}
    </button>
  );
}

export function Thumb({ a, className = "" }: { a: Artifact; className?: string }) {
  const v = a.current;
  if (a.status === "generating") {
    return (
      <div className={`grid place-items-center bg-raised text-muted ${className}`}>
        <Loader2 className="size-4 animate-spin" aria-label="Đang tạo" />
      </div>
    );
  }
  if (v?.url && v.mime_type?.startsWith("image/")) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={v.url} alt="" className={`bg-raised object-cover ${className}`} />;
  }
  if (v?.url && v.mime_type?.startsWith("video/")) {
    return <video src={`${v.url}#t=1`} muted preload="metadata" className={`bg-black object-cover ${className}`} />;
  }
  const Icon = GROUPS.find((g) => g.kind === a.kind)?.icon ?? FileText;
  return (
    <div className={`grid place-items-center bg-raised text-muted ${className}`}>
      <Icon className="size-4" strokeWidth={1.6} aria-hidden />
    </div>
  );
}

/** Right panel "Project Library / Các phương án" (BRD §6.2.1): vertical cards grouped by kind. */
export function Library({
  artifacts,
  openId,
  onOpen,
  onChanged,
  filter,
  onFilter,
}: {
  artifacts: Artifact[];
  openId: string | null;
  onOpen: (a: Artifact) => void;
  onChanged: () => void;
  filter: "all" | "selected";
  onFilter: (f: "all" | "selected") => void;
}) {
  const shown = filter === "selected" ? artifacts.filter((a) => a.status === "selected" || a.status === "approved") : artifacts;
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-end px-4 pt-3">
        <div role="tablist" aria-label="Lọc thư viện" className="flex gap-3 text-sm">
          {(["all", "selected"] as const).map((f) => (
            <button key={f} role="tab" aria-selected={filter === f} onClick={() => onFilter(f)}
              className={`cursor-pointer border-b-2 pb-0.5 ${filter === f ? "border-ink font-medium" : "border-transparent text-faint hover:text-ink"}`}>
              {f === "all" ? "Tất cả" : "Đã chọn"}
            </button>
          ))}
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-4">
        {GROUPS.map(({ kind, label }) => {
          const items = shown.filter((a) => a.kind === kind);
          if (!items.length) return null;
          return (
            <section key={kind} className="mt-4">
              <h3 className="px-2 text-xs text-faint">{label} · {items.length}</h3>
              <ul className="mt-1">
                {items.map((a) => (
                  <li key={a.id} className={`group flex items-center rounded-2xl pr-1 transition-colors duration-150 ${a.id === openId ? "bg-surface" : "hover:bg-surface"}`}>
                    <Card a={a} active={a.id === openId} onClick={() => onOpen(a)} />
                    <DeleteButton a={a} onDeleted={onChanged} className="opacity-0 focus:opacity-100 group-hover:opacity-100 [@media(hover:none)]:opacity-100" />
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
        {!shown.length && (
          <p className="px-2 pt-6 text-sm text-muted">
            {filter === "selected" ? "Chưa chọn phương án nào." : "Kịch bản, ảnh và video sẽ được lưu ở đây."}
          </p>
        )}
      </div>
    </div>
  );
}

function Card({ a, active, onClick }: { a: Artifact; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} aria-current={active ? "true" : undefined}
      className="flex min-w-0 flex-1 cursor-pointer items-center gap-3 p-2 text-left">
      <Thumb a={a} className="size-11 flex-none rounded-xl" />
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-1">
          {a.pinned && <Pin className="size-3 flex-none text-muted" aria-label="Đã ghim" />}
          <span className="truncate text-sm font-medium">{a.display_name}</span>
        </span>
        <span className="mt-1 flex items-center gap-2">
          <Pill tone={statusTone(a.status)}>{ARTIFACT_STATUS[a.status]}</Pill>
          <span className="truncate text-xs text-faint">{ago(a.updated_at ?? a.created_at)}</span>
        </span>
      </span>
    </button>
  );
}
