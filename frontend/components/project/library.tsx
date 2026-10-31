"use client";

import { FileText, Film, Image as ImageIcon, Loader2, Pin, Scissors, Search } from "lucide-react";
import type { ReactNode } from "react";
import { Pill } from "@/components/ui";
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
  filter,
  onFilter,
}: {
  artifacts: Artifact[];
  openId: string | null;
  onOpen: (a: Artifact) => void;
  filter: "all" | "selected";
  onFilter: (f: "all" | "selected") => void;
}) {
  const shown = filter === "selected" ? artifacts.filter((a) => a.status === "selected" || a.status === "approved") : artifacts;
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-4 pt-4">
        <h2 className="font-semibold">Các phương án</h2>
        <div role="tablist" aria-label="Lọc thư viện" className="flex gap-3 text-sm">
          {(["all", "selected"] as const).map((f) => (
            <button key={f} role="tab" aria-selected={filter === f} onClick={() => onFilter(f)}
              className={`cursor-pointer border-b-2 pb-0.5 ${filter === f ? "border-accent font-medium" : "border-transparent text-muted"}`}>
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
              <h3 className="px-2 text-xs text-muted">{label} · {items.length}</h3>
              <ul className="mt-1">
                {items.map((a) => (
                  <li key={a.id}>
                    <Card a={a} active={a.id === openId} onClick={() => onOpen(a)} />
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

function Card({ a, active, onClick }: { a: Artifact; active: boolean; onClick: () => void }): ReactNode {
  return (
    <button onClick={onClick} aria-current={active ? "true" : undefined}
      className={`flex w-full cursor-pointer items-center gap-3 rounded-lg p-2 text-left transition-colors duration-150 ${active ? "bg-active" : "hover:bg-raised"}`}>
      <Thumb a={a} className="size-11 flex-none rounded-md" />
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-1">
          {a.pinned && <Pin className="size-3 flex-none text-muted" aria-label="Đã ghim" />}
          <span className="truncate text-sm font-medium">{a.display_name}</span>
        </span>
        <span className="mt-1 flex items-center gap-2">
          <Pill tone={statusTone(a.status)}>{ARTIFACT_STATUS[a.status]}</Pill>
          <span className="truncate text-xs text-muted">v{a.version_count || 1} · {ago(a.updated_at ?? a.created_at)}</span>
        </span>
      </span>
    </button>
  );
}
