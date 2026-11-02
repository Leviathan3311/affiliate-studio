"use client";

import { useEffect, useState } from "react";
import { Button, Dialog, ErrorNote, Field, Panel, Pill, Skeleton } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { ARTIFACT_STATUS, FLAG } from "@/lib/format";
import type { Artifact, EffectiveStyle, Project, Script } from "@/lib/types";
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
    return <Panel title={a.display_name}><Skeleton rows={6} /><p className="mt-3 text-sm text-muted">AI đang viết kịch bản…</p></Panel>;
  }
  if (!s) return <Panel title={a.display_name}><ErrorNote error={new Error("Kịch bản này chưa viết xong. Nhắn trợ lý AI để viết lại.")} /></Panel>;

  return (
    <Panel
      title={a.display_name}
      action={<span className="flex items-center gap-2"><Pill tone={statusTone(a.status)}>{ARTIFACT_STATUS[a.status]}</Pill><span className="text-xs text-faint">bản {a.version_count}</span></span>}
    >
      {s.flags?.map((f) => (
        <p key={f} className="mb-3 rounded-[var(--radius-input)] bg-[var(--pill-warning-bg)] px-3 py-2 text-sm text-[var(--pill-warning-ink)]">
          {FLAG[f] ?? f}: kiểm tra lại giá/ưu đãi trước khi dùng.
        </p>
      ))}
      <dl className="grid gap-4 sm:grid-cols-2">
        {([["Góc tiếp cận", s.angle], ["Điều khách quan tâm", s.insight], ["Câu mở đầu (3 giây đầu)", s.hook], ["Thông điệp chính", s.key_message], ["Lời kêu gọi", s.cta], ["Thời lượng", `${s.duration_seconds} giây · 9:16`]] as const).map(([k, v]) => (
          <div key={k}>
            <dt className="text-xs text-faint">{k}</dt>
            <dd className="mt-1 text-[15px] leading-relaxed">{v || "—"}</dd>
          </div>
        ))}
      </dl>
      {s.continuity && (s.continuity.product || s.continuity.talent || s.continuity.setting) && (
        <>
          <h3 className="mt-7 text-sm font-semibold">Giữ giống nhau ở mọi cảnh</h3>
          <p className="mt-1 text-xs text-faint">AI tạo hình đọc phần này (tiếng Anh) để mọi cảnh có cùng sản phẩm, cùng người, cùng căn phòng.</p>
          <dl className="mt-3 grid gap-4 sm:grid-cols-3">
            {([["Sản phẩm", s.continuity.product], ["Người trên hình", s.continuity.talent], ["Bối cảnh", s.continuity.setting]] as const).map(([k, v]) => (
              <div key={k}>
                <dt className="text-xs text-faint">{k}</dt>
                <dd className="mt-1 text-sm leading-relaxed">{v || "—"}</dd>
              </div>
            ))}
          </dl>
        </>
      )}
      <h3 className="mt-7 text-sm font-semibold">Các cảnh quay · {s.shots.length}</h3>
      <div className="mt-2 overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="text-left text-xs text-faint">
              <th className="h-8 w-10 font-normal">#</th>
              <th className="font-normal">Cảnh</th>
              <th className="font-normal">Lời đọc</th>
              <th className="font-normal">Chữ trên màn hình</th>
              <th className="font-normal">Âm thanh</th>
              <th className="text-right font-normal">Giây</th>
            </tr>
          </thead>
          <tbody>
            {s.shots.map((shot, i) => (
              <tr key={i} className="border-t border-rule align-top">
                <td className="py-2 text-muted">{i + 1}</td>
                <td className="py-2.5 pr-3">{shot.description}<p className="text-xs text-faint">{shot.motion}</p></td>
                <td className="py-2 pr-3">{shot.voiceover || "—"}</td>
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
          <p className="text-xs text-faint">Nội dung bài đăng gợi ý</p>
          <p className="mt-0.5 whitespace-pre-wrap">{s.caption} {s.hashtags?.join(" ")}</p>
        </div>
      )}
      {error && <div className="mt-4"><ErrorNote error={error} /></div>}
      <div className="mt-6 flex flex-wrap gap-2">
        {a.status !== "selected" ? (
          <Button variant="primary" busy={busy === "select"} onClick={() => act("select", `/artifacts/${a.id}/select`)}>Chọn bản này</Button>
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
        <Button variant="danger" busy={busy === "delete"} onClick={() => confirm(`Xoá “${a.display_name}”? Không thể khôi phục.`) && act("delete", `/artifacts/${a.id}`, undefined, "DELETE")}>Xoá</Button>
      </div>
      <p className="mt-3 text-xs text-faint">Muốn sửa? Nhắn trợ lý kịch bản; bản cũ vẫn được giữ.</p>
      <span className="sr-only">{project.name}</span>
    </Panel>
  );
}

/** Compare 2–3 variants side by side (BRD §6.2.1); no AI scores presented as facts. */
export function CompareView({ items, onClose }: { items: Artifact[]; onClose: () => void }) {
  const rows: [string, (s: Script) => string][] = [
    ["Góc tiếp cận", (s) => s.angle],
    ["Câu mở đầu", (s) => s.hook],
    ["Thông điệp", (s) => s.key_message],
    ["Lời kêu gọi", (s) => s.cta],
    ["Thời lượng", (s) => `${s.duration_seconds} giây · ${s.shots.length} cảnh`],
    ["Cần lưu ý", (s) => (s.flags?.length ? s.flags.map((f) => FLAG[f] ?? f).join("; ") : "—")],
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

/** Confirmation before generating: what will be made, how long it takes, the style, one optional note. */
export function GenerateDialog({ project, script, note = "", onClose, onQueued }: {
  project: Project; script: Artifact; note?: string; onClose: () => void; onQueued: () => void;
}) {
  const [style, setStyle] = useState<Record<string, EffectiveStyle> | null>(null);
  const [extra, setExtra] = useState(note);
  const [off, setOff] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const s = script.current?.content as unknown as Script;
  const scenes = Math.min(3, s.shots.length);

  useEffect(() => {
    api<Record<string, EffectiveStyle>>(`/style-assignments?project_id=${project.id}`).then(setStyle, setError);
  }, [project.id]);

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

  const styleName = style?.image?.pack_name;
  return (
    <Dialog title={`Tạo ảnh & video cho “${script.display_name}”`} onClose={onClose}
      footer={<><Button variant="ghost" onClick={onClose}>Huỷ</Button><Button variant="primary" onClick={go} busy={busy}>Bắt đầu tạo</Button></>}>
      <p className="text-sm leading-relaxed text-muted">
        AI sẽ tạo ảnh chính, ảnh bìa, {scenes} cảnh video có âm thanh và nhạc nền, rồi ghép thành một video {s.duration_seconds} giây.
        Thường mất 20–40 phút; bạn có thể đóng trang, kết quả sẽ hiện ở mục Ảnh & Video.
      </p>
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-input)] bg-ground px-4 py-3">
        <span className="text-sm">
          <span className="text-faint">Phong cách </span>
          {style ? (off || !styleName ? "Không dùng" : styleName) : "…"}
        </span>
        {styleName && (
          <label className="flex cursor-pointer items-center gap-2 text-sm text-muted">
            <input type="checkbox" checked={off} onChange={(e) => setOff(e.target.checked)} className="size-4 accent-[var(--text)]" />
            Bỏ phong cách lần này
          </label>
        )}
      </div>
      <div className="mt-4">
        <Field label="Ghi chú thêm (tuỳ chọn)" value={extra} onChange={(e) => setExtra(e.target.value)} placeholder="Ví dụ: tông màu nhẹ, nhiều ánh sáng tự nhiên" />
      </div>
      {error && <div className="mt-3"><ErrorNote error={error} /></div>}
    </Dialog>
  );
}
