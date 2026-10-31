"use client";

import { useState } from "react";
import { Button, ErrorNote, Field, Panel, Pill, Skeleton } from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { api, ApiError, useApi } from "@/lib/api";
import type { ComposedPrompt, EffectiveStyle, StyleBlock, StylePack } from "@/lib/types";

const MODALITY = { image: "Ảnh", video: "Video", audio: "Nhạc nền" } as const;
type Modality = keyof typeof MODALITY;

/** Workspace Settings -> AI Generation Styles (BRD MOD-04 Style Packs). */
export function StyleLibrary() {
  const { can } = useWorkspace();
  const admin = can("admin");
  const packs = useApi<StylePack[]>("/style-packs");
  const eff = useApi<Record<Modality, EffectiveStyle>>("/style-assignments");
  const [editing, setEditing] = useState<StylePack | "new" | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  async function setDefault(m: Modality, packId: string) {
    const current = Object.fromEntries(
      (Object.keys(MODALITY) as Modality[]).map((k) => [k, eff.data?.[k]?.source === "workspace" ? eff.data[k].pack_id : null]),
    );
    try {
      await api("/style-assignments", { method: "PUT", json: { ...current, [m]: packId || null } });
      eff.reload();
    } catch (e) {
      setError(e as ApiError);
    }
  }

  async function duplicate(p: StylePack) {
    const copy = await api<StylePack>(`/style-packs/${p.id}/duplicate`, { method: "POST" });
    await packs.reload();
    setEditing(copy);
  }

  return (
    <div className="max-w-5xl space-y-6">
      <Panel title="Style mặc định của workspace">
        <p className="mb-4 text-sm text-muted">Tự động ghép vào mọi prompt gửi tới FLUX.2, MiniMax H3 và ACE-Step. Project có thể đổi riêng.</p>
        {error && <div className="mb-3"><ErrorNote error={error} /></div>}
        <div className="grid gap-4 sm:grid-cols-3">
          {(Object.keys(MODALITY) as Modality[]).map((m) => (
            <label key={m} className="flex flex-col gap-1.5 text-sm font-medium">{MODALITY[m]}
              <select disabled={!admin} value={eff.data?.[m]?.source === "workspace" ? eff.data[m].pack_id ?? "" : ""}
                onChange={(e) => setDefault(m, e.target.value)} className="h-9 rounded-[var(--radius-control)] border border-control px-2 font-normal">
                <option value="">Preset hệ thống ({eff.data?.[m]?.source === "platform" ? eff.data[m].pack_name : "—"})</option>
                {packs.data?.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </label>
          ))}
        </div>
      </Panel>

      {editing ? (
        <PackEditor pack={editing === "new" ? null : editing} onDone={() => { setEditing(null); packs.reload(); }} />
      ) : (
        <Panel title="Style Packs" action={admin && <Button onClick={() => setEditing("new")}>Tạo pack</Button>}>
          {packs.loading && <Skeleton rows={3} />}
          <ul className="divide-y divide-rule">
            {packs.data?.map((p) => (
              <li key={p.id} className="flex flex-wrap items-center gap-3 py-3">
                <div className="min-w-0 flex-1">
                  <p className="font-medium">{p.name} {p.is_preset && <Pill>Preset</Pill>}</p>
                  <p className="truncate text-sm text-muted">{p.description || `${p.blocks.length} block`} · v{p.version_number}</p>
                </div>
                <div className="flex flex-wrap gap-1">
                  {p.blocks.slice(0, 4).map((b) => <Pill key={b.id ?? b.name}>{b.name}</Pill>)}
                </div>
                {admin && (p.is_preset
                  ? <Button className="h-8 text-xs" onClick={() => duplicate(p)}>Nhân bản để sửa</Button>
                  : <Button className="h-8 text-xs" onClick={() => setEditing(p)}>Sửa</Button>)}
              </li>
            ))}
          </ul>
        </Panel>
      )}
    </div>
  );
}

const EMPTY_BLOCK: StyleBlock = { name: "", category: "art_direction", content: "", priority: 50, applies_to: ["image", "video"], enabled: true };

function PackEditor({ pack, onDone }: { pack: StylePack | null; onDone: () => void }) {
  const [name, setName] = useState(pack?.name ?? "");
  const [description, setDescription] = useState(pack?.description ?? "");
  const [blocks, setBlocks] = useState<StyleBlock[]>(pack?.blocks.length ? pack.blocks : [{ ...EMPTY_BLOCK }]);
  const [summary, setSummary] = useState("");
  const [preview, setPreview] = useState<ComposedPrompt | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  const update = (i: number, patch: Partial<StyleBlock>) => setBlocks((bs) => bs.map((b, j) => (j === i ? { ...b, ...patch } : b)));
  const move = (i: number, d: -1 | 1) => setBlocks((bs) => {
    const next = [...bs];
    [next[i], next[i + d]] = [next[i + d], next[i]];
    return next;
  });

  async function save() {
    setBusy(true);
    setError(null);
    try {
      const body = { name, description, blocks, change_summary: summary };
      await api(pack ? `/style-packs/${pack.id}` : "/style-packs", { method: pack ? "PUT" : "POST", json: body });
      onDone();
    } catch (e) {
      setError(e as ApiError);
      setBusy(false);
    }
  }

  return (
    <Panel title={pack ? `Sửa ${pack.name} (lưu thành v${(pack.version_number ?? 0) + 1})` : "Style pack mới"}
      action={<Button variant="ghost" onClick={onDone}>Đóng</Button>}>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Tên pack" value={name} onChange={(e) => setName(e.target.value)} error={error?.fields.name} />
        <Field label="Mô tả" value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>
      <h3 className="mt-6 text-sm font-semibold">Style blocks (thứ tự = ưu tiên khi ghép)</h3>
      <ol className="mt-2 space-y-3">
        {blocks.map((b, i) => (
          <li key={i} className="rounded-[var(--radius-card)] border border-border p-3">
            <div className="grid gap-3 sm:grid-cols-[1fr_160px_90px]">
              <Field label="Tên block" value={b.name} onChange={(e) => update(i, { name: e.target.value })} />
              <label className="flex flex-col gap-1.5 text-sm font-medium">Loại
                <select value={b.category} onChange={(e) => update(i, { category: e.target.value })} className="h-9 rounded-[var(--radius-control)] border border-control px-2 font-normal">
                  {["art_direction", "color_palette", "lighting", "composition", "camera_motion", "materials", "typography", "music", "negative_constraints", "other"].map((c) => <option key={c}>{c}</option>)}
                </select>
              </label>
              <Field label="Ưu tiên" type="number" min={0} max={100} value={b.priority} onChange={(e) => update(i, { priority: Number(e.target.value) })} />
            </div>
            <div className="mt-3">
              <Field label="Mô tả phong cách (tiếng Anh cho model)" textarea value={b.content} onChange={(e) => update(i, { content: e.target.value })} />
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-4 text-sm">
              {(Object.keys(MODALITY) as Modality[]).map((m) => (
                <label key={m} className="flex items-center gap-1.5">
                  <input type="checkbox" checked={b.applies_to.includes(m)} className="size-4 accent-[var(--accent)]"
                    onChange={(e) => update(i, { applies_to: e.target.checked ? [...b.applies_to, m] : b.applies_to.filter((x) => x !== m) })} />
                  {MODALITY[m]}
                </label>
              ))}
              <label className="flex items-center gap-1.5">
                <input type="checkbox" checked={b.enabled} onChange={(e) => update(i, { enabled: e.target.checked })} className="size-4 accent-[var(--accent)]" /> Bật
              </label>
              <span className="ml-auto flex gap-1">
                <Button variant="ghost" className="h-8 text-xs" disabled={i === 0} onClick={() => move(i, -1)} aria-label="Lên">↑</Button>
                <Button variant="ghost" className="h-8 text-xs" disabled={i === blocks.length - 1} onClick={() => move(i, 1)} aria-label="Xuống">↓</Button>
                <Button variant="danger" className="h-8 text-xs" onClick={() => setBlocks((bs) => bs.filter((_, j) => j !== i))}>Xoá</Button>
              </span>
            </div>
          </li>
        ))}
      </ol>
      <Button className="mt-3" onClick={() => setBlocks((bs) => [...bs, { ...EMPTY_BLOCK }])}>Thêm block</Button>
      <div className="mt-6 grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end">
        <Field label="Ghi chú thay đổi" value={summary} onChange={(e) => setSummary(e.target.value)} placeholder="Ví dụ: giảm tông ấm" />
        <div className="flex gap-2">
          {pack && <Button onClick={async () => setPreview(await api<ComposedPrompt>(`/style-packs/${pack.id}/preview`, { method: "POST", json: { modality: "image" } }))}>Xem prompt mẫu</Button>}
          <Button variant="primary" onClick={save} busy={busy}>Lưu phiên bản</Button>
        </div>
      </div>
      {preview && <pre className="mt-3 max-h-56 overflow-auto whitespace-pre-wrap rounded-md bg-raised p-3 text-xs">{preview.prompt}</pre>}
      {error && <div className="mt-3"><ErrorNote error={error} /></div>}
    </Panel>
  );
}
