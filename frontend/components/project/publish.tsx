"use client";

import { useState } from "react";
import { Button, Empty, ErrorNote, Field, Panel, Pill, Select } from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { api, ApiError, useApi } from "@/lib/api";
import { dateTime, PUBLISH_STATUS } from "@/lib/format";
import type { Artifact, Project, PublishingJob, Script, SocialAccount } from "@/lib/types";

/** Publish/schedule approved creatives to a Facebook Page or Instagram (BRD §6.2 step 9-10, MOD-05). */
export function PublishSection({ project, artifacts }: { project: Project; artifacts: Artifact[] }) {
  const { workspace } = useWorkspace();
  const pages = useApi<SocialAccount[]>("/integrations/social-accounts");
  const jobs = useApi<PublishingJob[]>(`/publishing-jobs?project_id=${project.id}`, 15000);
  const approved = artifacts.filter((a) => a.status === "approved" && a.current?.url);
  const selectedScript = artifacts.find((a) => a.kind === "script" && a.status === "selected");
  const defaultCaption = (() => {
    const s = selectedScript?.current?.content as unknown as Script | undefined;
    return s ? `${s.caption}\n\n${s.hashtags?.join(" ") ?? ""}`.trim() : "";
  })();
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<"now" | "later">("later");

  async function submit(form: HTMLFormElement) {
    const f = Object.fromEntries(new FormData(form)) as Record<string, string>;
    setBusy(true);
    setError(null);
    try {
      await api("/publishing-jobs", {
        method: "POST",
        json: {
          artifact_id: f.artifact_id,
          social_account_id: f.social_account_id,
          caption: f.caption,
          scheduled_at: mode === "now" ? null : new Date(f.when).toISOString(),
        },
      });
      jobs.reload();
    } catch (e) {
      setError(e as ApiError);
    } finally {
      setBusy(false);
    }
  }

  const connected = pages.data?.filter((p) => p.status === "connected") ?? [];
  return (
    <div className="space-y-6">
      <Panel title="Đăng bài lên Facebook, Instagram">
        {!approved.length && <Empty title="Chưa có ảnh hoặc video đã duyệt">Bấm “Duyệt” ở một ảnh, video hoặc Short trước khi đăng.</Empty>}
        {approved.length > 0 && !connected.length && (
          <p className="text-sm">Chưa kết nối Page nào. Vào <a href="/app/settings?tab=integrations" className="font-medium underline">Cài đặt → Facebook & Instagram</a>.</p>
        )}
        {approved.length > 0 && connected.length > 0 && (
          <form onSubmit={(e) => { e.preventDefault(); submit(e.currentTarget); }} className="grid gap-4 sm:grid-cols-2" noValidate>
            <Select label="Ảnh hoặc video" name="artifact_id">
              {approved.map((a) => <option key={a.id} value={a.id}>{a.display_name}</option>)}
            </Select>
            <Select label="Đăng lên" name="social_account_id">
              {connected.map((p) => <option key={p.id} value={p.id}>{p.name || p.external_id} · {p.provider === "instagram" ? "Instagram" : "Facebook"}</option>)}
            </Select>
            <div className="sm:col-span-2"><Field label="Nội dung bài đăng" name="caption" textarea rows={4} defaultValue={defaultCaption} /></div>
            <fieldset className="flex flex-wrap items-end gap-4 sm:col-span-2">
              <legend className="mb-1.5 text-sm font-medium">Thời điểm</legend>
              <label className="flex items-center gap-2 text-sm"><input type="radio" checked={mode === "now"} onChange={() => setMode("now")} className="accent-[var(--accent)]" /> Đăng ngay</label>
              <label className="flex items-center gap-2 text-sm"><input type="radio" checked={mode === "later"} onChange={() => setMode("later")} className="accent-[var(--accent)]" /> Đặt lịch</label>
              {mode === "later" && <input type="datetime-local" name="when" required aria-label="Thời điểm đăng" className="h-9 rounded-[var(--radius-control)] border border-control px-2 text-sm" />}
              <span className="text-xs text-muted">{workspace.timezone === "Asia/Ho_Chi_Minh" ? "Giờ Việt Nam" : `Giờ theo ${workspace.timezone}`}</span>
            </fieldset>
            {error && <div className="sm:col-span-2"><ErrorNote error={error} /></div>}
            <div className="sm:col-span-2"><Button variant="primary" type="submit" busy={busy}>{mode === "now" ? "Đăng ngay" : "Lên lịch đăng"}</Button></div>
          </form>
        )}
      </Panel>
      <Panel title="Lịch đăng của dự án">
        {jobs.data?.length === 0 && <p className="text-sm text-muted">Chưa có bài nào.</p>}
        <ul className="divide-y divide-rule">
          {jobs.data?.map((j) => (
            <li key={j.id} className="flex flex-wrap items-center gap-3 py-2.5 text-sm">
              <span className="w-28 font-medium">{dateTime(j.scheduled_at)}</span>
              <span className="min-w-40 flex-1 truncate">{j.artifact_name} → {j.page_name}</span>
              <Pill tone={j.status === "published" ? "positive" : j.status === "failed" ? "negative" : "neutral"}>{PUBLISH_STATUS[j.status]}</Pill>
              {j.last_error && <span className="w-full text-xs text-negative">Chưa đăng được: {j.last_error}</span>}
              {j.status === "scheduled" && (
                <Button variant="ghost" className="h-8 text-xs" onClick={async () => { await api(`/publishing-jobs/${j.id}/cancel`, { method: "POST" }); jobs.reload(); }}>Huỷ</Button>
              )}
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
