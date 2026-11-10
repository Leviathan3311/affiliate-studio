"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Button, Dialog, Empty, ErrorNote, Field, PageTitle, Pill, Skeleton } from "@/components/ui";
import { api, ApiError, useApi } from "@/lib/api";
import { PUBLISH_STATUS, time } from "@/lib/format";
import type { PublishingJob, SocialAccount } from "@/lib/types";

const FILTERS = [
  { id: "", label: "Tất cả" },
  { id: "scheduled", label: "Đã lên lịch" },
  { id: "published", label: "Đã đăng" },
  { id: "failed", label: "Lỗi" },
] as const;

/** Publishing calendar across projects (BRD MOD-05), grouped by local day. */
export default function PublishingPage() {
  const [status, setStatus] = useState("");
  const list = useApi<PublishingJob[]>(`/publishing-jobs${status ? `?status=${status}` : ""}`, 20000);
  const byDay = new Map<string, PublishingJob[]>();
  for (const j of list.data ?? []) {
    const day = new Date(j.scheduled_at).toLocaleDateString("vi-VN", { weekday: "long", day: "2-digit", month: "2-digit", year: "numeric" });
    byDay.set(day, [...(byDay.get(day) ?? []), j]);
  }
  const failed = list.data?.filter((j) => j.status === "failed").length ?? 0;
  const [photo, setPhoto] = useState(false);

  return (
    <>
      <PageTitle
        title="Lịch đăng bài"
        sub={list.data ? `${list.data.length} bài${failed ? ` · ${failed} bài lỗi cần xử lý` : ""}` : undefined}
        actions={<Button variant="primary" onClick={() => setPhoto(true)}>Đăng ảnh</Button>}
      />
      {photo && <PhotoPost onClose={() => setPhoto(false)} onDone={list.reload} />}
      <div role="tablist" aria-label="Lọc trạng thái" className="mb-6 flex gap-5 border-b border-border">
        {FILTERS.map((f) => (
          <button key={f.id} role="tab" aria-selected={status === f.id} onClick={() => setStatus(f.id)}
            className={`-mb-px cursor-pointer border-b-2 pb-2 text-sm ${status === f.id ? "border-accent font-semibold" : "border-transparent text-muted"}`}>{f.label}</button>
        ))}
      </div>
      {list.error && <ErrorNote error={list.error} onRetry={list.reload} />}
      {list.loading && <Skeleton rows={5} />}
      {list.data?.length === 0 && <Empty title="Chưa có bài nào">Duyệt ảnh hoặc video trong một dự án rồi mở bước “Đăng bài”.</Empty>}
      {[...byDay.entries()].map(([day, jobs]) => (
        <section key={day} className="mb-8">
          <h2 className="mb-2 text-sm font-semibold capitalize">{day}</h2>
          <ul className="divide-y divide-rule">
            {jobs.map((j) => (
              <li key={j.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 py-3">
                <span className="w-14 font-medium">{time(j.scheduled_at)}</span>
                <div className="min-w-48 flex-1">
                  {j.project_id ? <Link href={`/app/project?id=${j.project_id}`} className="font-medium hover:underline">{j.artifact_name}</Link> : j.artifact_name}
                  <p className="text-sm text-muted">{j.page_name} · {j.media_type === "video" ? "Video" : "Ảnh"}</p>
                </div>
                <Pill tone={j.status === "published" ? "positive" : j.status === "failed" ? "negative" : "neutral"}>{PUBLISH_STATUS[j.status]}</Pill>
                {(j.status === "scheduled" || j.status === "failed") && (
                  <span className="flex gap-1">
                    <Button className="h-8 text-xs" onClick={async () => { await api(`/publishing-jobs/${j.id}/publish-now`, { method: "POST" }); list.reload(); }}>Đăng ngay</Button>
                    <Button variant="ghost" className="h-8 text-xs" onClick={async () => { await api(`/publishing-jobs/${j.id}/cancel`, { method: "POST" }); list.reload(); }}>Huỷ</Button>
                  </span>
                )}
                {j.last_error && <p className="w-full text-xs text-negative">{j.last_error}</p>}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </>
  );
}

/** Post the shop's own picture (menu, new arrivals, a happy customer) without making a video. */
function PhotoPost({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const accounts = useApi<SocialAccount[]>("/integrations/social-accounts");
  const [file, setFile] = useState<File | null>(null);
  const [caption, setCaption] = useState("");
  const [picked, setPicked] = useState<string[] | null>(null);
  const [when, setWhen] = useState("");
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [objectId, setObjectId] = useState("");
  const [uploading, setUploading] = useState(false);
  const [hint, setHint] = useState("");
  const [writing, setWriting] = useState(false);
  const connected = (accounts.data ?? []).filter((a) => a.status === "connected");
  const chosen = picked ?? connected.map((a) => a.id);
  const preview = useMemo(() => (file ? URL.createObjectURL(file) : ""), [file]);

  // Upload as soon as a photo is picked, so the AI can look at it before posting.
  async function choose(f: File | null) {
    setFile(f);
    setObjectId("");
    setError(null);
    if (!f) return;
    setUploading(true);
    try {
      const up = await api<{ object_id: string; upload_url: string; headers: Record<string, string> }>(
        "/publishing-jobs/photos/presign",
        { method: "POST", json: { filename: f.name, content_type: f.type, byte_size: f.size } },
      );
      const put = await fetch(up.upload_url, { method: "PUT", headers: up.headers, body: f });
      if (!put.ok) throw new ApiError(put.status, "Tải ảnh lên chưa được, thử lại");
      setObjectId(up.object_id);
    } catch (e) {
      setError(e as ApiError);
    }
    setUploading(false);
  }

  async function write() {
    setWriting(true);
    setError(null);
    try {
      const { caption: text } = await api<{ caption: string }>("/publishing-jobs/photos/caption", {
        method: "POST",
        json: { object_id: objectId, hint },
      });
      setCaption(text);
    } catch (e) {
      setError(e as ApiError);
    }
    setWriting(false);
  }

  async function submit() {
    if (!objectId) return setError(new ApiError(422, "Chọn một ảnh"));
    setBusy(true);
    setError(null);
    try {
      await api("/publishing-jobs/photos", {
        method: "POST",
        json: {
          object_id: objectId,
          caption,
          social_account_ids: chosen,
          scheduled_at: when ? new Date(when).toISOString() : null,
        },
      });
      onDone();
      onClose();
    } catch (e) {
      setError(e as ApiError);
      setBusy(false);
    }
  }

  return (
    <Dialog
      title="Đăng ảnh"
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Huỷ</Button>
          <Button variant="primary" busy={busy} disabled={!objectId || !chosen.length} onClick={submit}>
            {when ? "Lên lịch" : "Đăng ngay"}
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4 text-sm">
        {error && <ErrorNote error={error} />}
        <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-[var(--radius-card)] border border-dashed border-control p-4 text-muted hover:text-ink">
          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview} alt="Ảnh sẽ đăng" className="max-h-64 rounded-md object-contain" />
          ) : (
            <span>Chọn ảnh JPG, PNG hoặc WEBP, tối đa 8 MB</span>
          )}
          <input type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={(e) => choose(e.target.files?.[0] ?? null)} />
          {uploading && <span>Đang tải ảnh lên…</span>}
        </label>
        <div className="flex items-end gap-2">
          <div className="min-w-0 flex-1">
            <Field label="Gợi ý cho AI (không bắt buộc)" name="hint" value={hint} onChange={(e) => setHint(e.target.value)} placeholder="Ví dụ: món mới, giảm 10% tuần này" />
          </div>
          <Button busy={writing} disabled={!objectId} onClick={write}>AI viết nội dung</Button>
        </div>
        <Field label="Nội dung bài đăng" name="caption" textarea rows={4} value={caption} onChange={(e) => setCaption(e.target.value)} hint="Instagram nhận tối đa 2.200 ký tự" />
        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1 font-medium">Đăng lên</legend>
          {connected.length === 0 && <p className="text-muted">Chưa kết nối Facebook hoặc Instagram (Cài đặt → Facebook &amp; Instagram).</p>}
          {connected.map((a) => (
            <label key={a.id} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={chosen.includes(a.id)}
                onChange={(e) => setPicked(e.target.checked ? [...chosen, a.id] : chosen.filter((x) => x !== a.id))}
              />
              {a.name} · {a.provider === "instagram" ? "Instagram" : "Facebook"}
            </label>
          ))}
        </fieldset>
        <Field label="Hẹn giờ (để trống là đăng ngay)" name="when" type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} />
      </div>
    </Dialog>
  );
}
