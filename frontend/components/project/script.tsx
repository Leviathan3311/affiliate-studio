"use client";

import { useEffect, useState } from "react";
import { Button, ErrorNote, Field, Panel, Pill, Skeleton } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { ARTIFACT_STATUS, FLAG } from "@/lib/format";
import type { Artifact, ComposedPrompt, EffectiveStyle, Project, Script } from "@/lib/types";
import { statusTone } from "./library";

export function ScriptView({
  a,
  project,
  onChanged,
  onGenerate,
}: {
  a: Artifact;
  project: Project;
  onChanged: () => void;
  onGenerate: () => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const s = a.current?.content as unknown as Script | undefined;

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

  if (a.status === "generating") {
    return <Panel title={a.display_name}><Skeleton rows={6} /><p className="mt-3 text-sm text-muted">Gemini đang viết…</p></Panel>;
  }
  if (!s) return <Panel title={a.display_name}><ErrorNote error={new Error(a.error ?? "Kịch bản chưa có nội dung")} /></Panel>;

  return (
    <Panel
      title={a.display_name}
      action={<span className="flex items-center gap-2"><Pill tone={statusTone(a.status)}>{ARTIFACT_STATUS[a.status]}</Pill><span className="text-xs text-muted">v{a.version_count}</span></span>}
    >
      {s.flags?.map((f) => (
        <p key={f} className="mb-3 rounded-md bg-[var(--pill-warning-bg)] px-3 py-2 text-sm text-[var(--pill-warning-ink)]">
          {FLAG[f] ?? f}: kiểm tra lại giá/ưu đãi trước khi dùng.
        </p>
      ))}
      <dl className="grid gap-4 sm:grid-cols-2">
        {([["Góc tiếp cận", s.angle], ["Insight", s.insight], ["Hook (3 giây đầu)", s.hook], ["Thông điệp chính", s.key_message], ["CTA", s.cta], ["Thời lượng", `${s.duration_seconds} giây · 9:16`]] as const).map(([k, v]) => (
          <div key={k}>
            <dt className="text-xs text-muted">{k}</dt>
            <dd className="mt-0.5">{v || "—"}</dd>
          </div>
        ))}
      </dl>
      <h3 className="mt-6 text-sm font-semibold">Shot list · {s.shots.length}</h3>
      <div className="mt-2 overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="text-left text-xs text-muted">
              <th className="h-8 w-10 font-normal">#</th>
              <th className="font-normal">Cảnh</th>
              <th className="font-normal">Chữ trên màn hình</th>
              <th className="font-normal">Âm thanh</th>
              <th className="text-right font-normal">Giây</th>
            </tr>
          </thead>
          <tbody>
            {s.shots.map((shot, i) => (
              <tr key={i} className="border-t border-rule align-top">
                <td className="py-2 text-muted">{i + 1}</td>
                <td className="py-2 pr-3">{shot.description}<p className="text-xs text-muted">{shot.motion}</p></td>
                <td className="py-2 pr-3">{shot.on_screen_text || "—"}</td>
                <td className="py-2 pr-3">{shot.sfx || "—"}</td>
                <td className="py-2 text-right">{shot.duration_seconds}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {s.caption && (
        <div className="mt-5">
          <p className="text-xs text-muted">Caption đề xuất</p>
          <p className="mt-0.5 whitespace-pre-wrap">{s.caption} {s.hashtags?.join(" ")}</p>
        </div>
      )}
      {error && <div className="mt-4"><ErrorNote error={error} /></div>}
      <div className="mt-6 flex flex-wrap gap-2">
        {a.status !== "selected" ? (
          <Button variant="primary" busy={busy === "select"} onClick={() => act("select", `/artifacts/${a.id}/select`)}>Dùng kịch bản này</Button>
        ) : (
          <Button variant="primary" onClick={onGenerate}>Tạo ảnh & video</Button>
        )}
        <Button busy={busy === "dup"} onClick={() => act("dup", `/artifacts/${a.id}/duplicate`)}>Nhân bản</Button>
        <Button busy={busy === "pin"} onClick={() => act("pin", `/artifacts/${a.id}`, { pinned: !a.pinned }, "PATCH")}>{a.pinned ? "Bỏ ghim" : "Ghim"}</Button>
        <Button variant="ghost" onClick={() => {
          const name = prompt("Tên mới", a.display_name);
          if (name) act("rename", `/artifacts/${a.id}`, { display_name: name }, "PATCH");
        }}>Đổi tên</Button>
        <Button variant="ghost" busy={busy === "archive"} onClick={() => act("archive", `/artifacts/${a.id}`, { archived: true }, "PATCH")}>Lưu trữ</Button>
      </div>
      <p className="mt-3 text-xs text-muted">Muốn sửa? Nhắn ở khung chat bên dưới; mỗi lần sửa thành một phiên bản mới, bản cũ vẫn giữ.</p>
      <span className="sr-only">{project.name}</span>
    </Panel>
  );
}

/** Compare 2–3 variants side by side (BRD §6.2.1); no AI scores presented as facts. */
export function CompareView({ items, onClose }: { items: Artifact[]; onClose: () => void }) {
  const rows: [string, (s: Script) => string][] = [
    ["Góc tiếp cận", (s) => s.angle],
    ["Hook", (s) => s.hook],
    ["Thông điệp", (s) => s.key_message],
    ["CTA", (s) => s.cta],
    ["Thời lượng", (s) => `${s.duration_seconds} giây · ${s.shots.length} shot`],
    ["Cờ kiểm tra", (s) => (s.flags?.length ? s.flags.map((f) => FLAG[f] ?? f).join("; ") : "—")],
  ];
  return (
    <Panel title={`So sánh ${items.length} phương án`} action={<Button variant="ghost" onClick={onClose}>Đóng</Button>}>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="text-left">
              <th className="w-32" />
              {items.map((a) => <th key={a.id} className="pb-2 pr-4 font-semibold">{a.display_name}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map(([label, get]) => (
              <tr key={label} className="border-t border-rule align-top">
                <td className="py-2 text-xs text-muted">{label}</td>
                {items.map((a) => <td key={a.id} className="py-2 pr-4">{a.current ? get(a.current.content as unknown as Script) : "—"}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

/** Confirmation before any GPU job: active style chips, optional one-off instruction, prompt preview. */
export function GenerateDialog({ project, script, onClose, onQueued }: { project: Project; script: Artifact; onClose: () => void; onQueued: () => void }) {
  const [style, setStyle] = useState<Record<string, EffectiveStyle> | null>(null);
  const [extra, setExtra] = useState("");
  const [off, setOff] = useState(false);
  const [preview, setPreview] = useState<ComposedPrompt | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const s = script.current?.content as unknown as Script;

  useEffect(() => {
    api<Record<string, EffectiveStyle>>(`/style-assignments?project_id=${project.id}`).then(setStyle, setError);
  }, [project.id]);

  async function showPrompt() {
    setPreview(await api<ComposedPrompt>("/style-preview", {
      method: "POST",
      json: { modality: "image", brief: s.shots[0]?.visual_prompt ?? s.hook, extra_instruction: extra, project_id: project.id },
    }));
  }

  async function go() {
    setBusy(true);
    setError(null);
    try {
      await api(`/projects/${project.id}/generate`, { method: "POST", json: { script_artifact_id: script.id, extra_instruction: extra, disable_style: off } });
      onQueued();
      onClose();
    } catch (e) {
      setError(e as ApiError);
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4" role="dialog" aria-modal aria-labelledby="gen-title">
      <div className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-[var(--radius-sheet)] bg-surface p-6 shadow-xl">
        <h2 id="gen-title" className="text-lg font-semibold">Tạo ảnh & video từ {script.display_name}</h2>
        <p className="mt-1 text-sm text-muted">
          Notebook 1 trên Kaggle sẽ tạo: ảnh studio + thumbnail (FLUX.2), {Math.min(3, s.shots.length)} cảnh video có âm thanh (MiniMax H3), nhạc nền (ACE-Step) và trộn nhạc ở mức 25%.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {style ? Object.entries(style).map(([m, st]) => (
            <Pill key={m} tone={off ? "neutral" : "accent"}>
              {{ image: "Ảnh", video: "Video", audio: "Nhạc" }[m]}: {off || !st.pack_name ? "không style" : `${st.pack_name} v${st.version_number}`}
            </Pill>
          )) : <Skeleton rows={1} />}
        </div>
        <label className="mt-3 flex cursor-pointer items-center gap-2 text-sm">
          <input type="checkbox" checked={off} onChange={(e) => setOff(e.target.checked)} className="size-4 accent-[var(--accent)]" />
          Tắt style cho lần này
        </label>
        <div className="mt-4">
          <Field label="Yêu cầu riêng cho lần này (không đổi style mặc định)" value={extra} onChange={(e) => setExtra(e.target.value)} placeholder="Ví dụ: tông màu watercolor nhẹ" />
        </div>
        <button onClick={showPrompt} className="mt-3 cursor-pointer text-sm font-medium underline">Xem prompt đã ghép</button>
        {preview && (
          <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap rounded-md bg-raised p-3 text-xs">
            {preview.prompt}
            {preview.unsupported.length > 0 && `\n\n[Ghi chú model: ${preview.unsupported.join(", ")}]`}
          </pre>
        )}
        {error && <div className="mt-3"><ErrorNote error={error} /></div>}
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>Huỷ</Button>
          <Button variant="primary" onClick={go} busy={busy}>Gửi sang Kaggle</Button>
        </div>
      </div>
    </div>
  );
}
