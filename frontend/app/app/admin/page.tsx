"use client";

import { useState } from "react";
import { Button, Dialog, Empty, ErrorNote, Field, PageTitle, Panel, Pill, Skeleton } from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { api, ApiError, useApi } from "@/lib/api";
import { ROLE, vnd } from "@/lib/format";
import type { AdminUser, AdminWorkspace, BankTx, Billing } from "@/lib/types";

const date = (iso: string) => new Date(iso).toLocaleDateString("vi-VN");

export default function AdminPage() {
  const { me } = useWorkspace();
  const [q, setQ] = useState("");
  const list = useApi<AdminWorkspace[]>(me.is_platform_admin ? `/admin/workspaces?q=${encodeURIComponent(q)}` : null);
  const price = useApi<Billing>("/billing").data?.price_vnd ?? 0;
  const [paying, setPaying] = useState<AdminWorkspace | null>(null);
  const [tab, setTab] = useState<"shops" | "users">("shops");

  if (!me.is_platform_admin) return <Empty title="Trang này chỉ dành cho quản trị GrowthPilot" />;
  return (
    <>
      <PageTitle title="Quản trị" sub="Tất cả cửa hàng và tài khoản dùng GrowthPilot. Khi tiền chuyển khoản về, tìm theo nội dung (GP …) rồi gia hạn." />
      <div role="tablist" aria-label="Mục quản trị" className="mb-6 flex gap-5 border-b border-border">
        {(["shops", "users"] as const).map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            onClick={() => setTab(t)}
            className={`-mb-px cursor-pointer border-b-2 pb-2 text-sm ${tab === t ? "border-accent font-semibold" : "border-transparent text-muted hover:text-ink"}`}
          >
            {t === "shops" ? "Cửa hàng" : "Tài khoản"}
          </button>
        ))}
      </div>
      {tab === "users" ? <Accounts /> : <>
      <Panel>
        <div className="mb-4 max-w-sm">
          <Field label="Tìm" name="q" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Mã GP, tên cửa hàng hoặc email" />
        </div>
        {list.error && <ErrorNote error={list.error} onRetry={list.reload} />}
        {!list.data ? (
          <Skeleton rows={5} />
        ) : !list.data.length ? (
          <Empty title="Không có cửa hàng nào khớp" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="text-xs text-muted">
                <tr>
                  <th className="py-2 pr-3 font-medium">Cửa hàng</th>
                  <th className="py-2 pr-3 font-medium">Mã chuyển khoản</th>
                  <th className="py-2 pr-3 font-medium">Tạo ngày</th>
                  <th className="py-2 pr-3 font-medium">Dùng đến</th>
                  <th className="py-2 pr-3 text-right font-medium">Đã trả</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody>
                {list.data.map((w) => (
                  <tr key={w.id} className="border-t border-rule">
                    <td className="py-2.5 pr-3">
                      <p className="font-medium">{w.name}</p>
                      <p className="text-xs text-muted">{w.owner_email}</p>
                    </td>
                    <td className="py-2.5 pr-3 font-mono">{w.transfer_code}</td>
                    <td className="py-2.5 pr-3">{date(w.created_at)}</td>
                    <td className="py-2.5 pr-3">
                      <Pill tone={w.active ? "positive" : "negative"}>{date(w.access_until)}</Pill>
                    </td>
                    <td className="py-2.5 pr-3 text-right tabular-nums">{vnd(w.paid_total_vnd)}</td>
                    <td className="py-2.5 text-right">
                      <Button onClick={() => setPaying(w)}>Gia hạn</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
      <Unmatched shops={list.data ?? []} price={price} onDone={list.reload} />
      </>}
      {paying && <PayDialog ws={paying} price={price} onClose={() => setPaying(null)} onDone={list.reload} />}
    </>
  );
}

function PayDialog({ ws, price, onClose, onDone }: { ws: AdminWorkspace; price: number; onClose: () => void; onDone: () => void }) {
  const [months, setMonths] = useState(1);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  return (
    <Dialog
      title={`Gia hạn ${ws.name}`}
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Huỷ</Button>
          <Button variant="primary" form="pay" type="submit" busy={busy}>
            Xác nhận đã nhận tiền
          </Button>
        </>
      }
    >
      <form
        id="pay"
        className="flex flex-col gap-4"
        onSubmit={async (e) => {
          e.preventDefault();
          const f = new FormData(e.currentTarget);
          setBusy(true);
          setError(null);
          try {
            await api(`/admin/workspaces/${ws.id}/payments`, {
              method: "POST",
              json: { months, amount_vnd: Number(f.get("amount_vnd")), note: f.get("note") },
            });
            onDone();
            onClose();
          } catch (err) {
            setError(err as ApiError);
            setBusy(false);
          }
        }}
      >
        {error && <ErrorNote error={error} />}
        <p className="text-sm text-muted">
          Chỉ bấm xác nhận khi tiền với nội dung <b className="text-ink">{ws.transfer_code}</b> đã về tài khoản.
        </p>
        <Field label="Số tháng" name="months" type="number" min={1} max={36} value={months} onChange={(e) => setMonths(Number(e.target.value) || 1)} />
        <Field label="Số tiền đã nhận (đ)" name="amount_vnd" type="number" min={0} key={months} defaultValue={price * months} />
        <Field label="Ghi chú" name="note" placeholder="Ví dụ: VCB 09/11, mã giao dịch…" />
      </form>
    </Dialog>
  );
}

/** Transfers SePay saw that did not extend a shop by themselves (no code, wrong code, too little). */
function Unmatched({ shops, price, onDone }: { shops: AdminWorkspace[]; price: number; onDone: () => void }) {
  const txs = useApi<BankTx[]>("/admin/bank-transactions?status=unmatched");
  const [error, setError] = useState<ApiError | null>(null);
  const [pick, setPick] = useState<Record<string, string>>({});
  if (!txs.data?.length) return null;
  async function act(t: BankTx, path: "assign" | "ignore") {
    setError(null);
    try {
      const ws = pick[t.id] ?? t.workspace_id ?? "";
      await api(`/admin/bank-transactions/${t.id}/${path}`, {
        method: "POST",
        json: path === "assign" ? { workspace_id: ws, months: Math.max(1, Math.floor(t.amount_vnd / (price || 1))) } : undefined,
      });
      txs.reload();
      onDone();
    } catch (err) {
      setError(err as ApiError);
    }
  }
  return (
    <Panel title="Chuyển khoản chưa khớp" className="mt-6">
      <p className="mb-3 text-sm text-muted">Tiền đã về nhưng không tự gia hạn được: thiếu mã GP, sai mã hoặc chưa đủ một tháng. Chọn cửa hàng rồi gán, hoặc bỏ qua.</p>
      {error && <ErrorNote error={error} />}
      <div className="flex flex-col divide-y divide-rule">
        {txs.data.map((t) => (
          <div key={t.id} className="flex flex-wrap items-center gap-3 py-3 text-sm">
            <div className="min-w-0 flex-1">
              <p className="font-medium tabular-nums">{vnd(t.amount_vnd)} · {date(t.created_at)}</p>
              <p className="truncate text-muted">{t.content || "(không có nội dung)"}</p>
            </div>
            <select
              aria-label="Cửa hàng"
              value={pick[t.id] ?? t.workspace_id ?? ""}
              onChange={(e) => setPick({ ...pick, [t.id]: e.target.value })}
              className="h-9 max-w-56 rounded-[var(--radius-control)] border border-control bg-ground px-2"
            >
              <option value="">Chọn cửa hàng…</option>
              {shops.map((w) => (
                <option key={w.id} value={w.id}>{w.name} · {w.transfer_code}</option>
              ))}
            </select>
            <Button disabled={!(pick[t.id] ?? t.workspace_id)} onClick={() => act(t, "assign")}>Gán và gia hạn</Button>
            <Button variant="ghost" onClick={() => act(t, "ignore")}>Bỏ qua</Button>
          </div>
        ))}
      </div>
    </Panel>
  );
}

/** Every account that signed up: who it is, which shops it is in, and a lock for abuse. */
function Accounts() {
  const [q, setQ] = useState("");
  const users = useApi<AdminUser[]>(`/admin/users?q=${encodeURIComponent(q)}`);
  const [error, setError] = useState<ApiError | null>(null);
  async function toggle(u: AdminUser) {
    setError(null);
    try {
      await api(`/admin/users/${u.id}/${u.disabled ? "enable" : "disable"}`, { method: "POST" });
      users.reload();
    } catch (e) {
      setError(e as ApiError);
    }
  }
  return (
    <Panel>
      <div className="mb-4 max-w-sm">
        <Field label="Tìm" name="uq" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Email hoặc họ tên" />
      </div>
      {(error || users.error) && <ErrorNote error={(error || users.error)!} />}
      {!users.data ? (
        <Skeleton rows={5} />
      ) : !users.data.length ? (
        <Empty title="Không có tài khoản nào khớp" />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="text-xs text-muted">
              <tr>
                <th className="py-2 pr-3 font-medium">Tài khoản</th>
                <th className="py-2 pr-3 font-medium">Cửa hàng</th>
                <th className="py-2 pr-3 font-medium">Đăng ký</th>
                <th className="py-2 pr-3 font-medium">Bảo mật</th>
                <th className="py-2" />
              </tr>
            </thead>
            <tbody>
              {users.data.map((u) => (
                <tr key={u.id} className="border-t border-rule">
                  <td className="py-2.5 pr-3">
                    <p className="font-medium">{u.full_name || u.email}</p>
                    <p className="text-xs text-muted">{u.email}</p>
                  </td>
                  <td className="py-2.5 pr-3">
                    {u.shops.length ? u.shops.map((s) => `${s.name} (${ROLE[s.role]})`).join(", ") : <span className="text-muted">Chưa tạo cửa hàng</span>}
                  </td>
                  <td className="py-2.5 pr-3">{date(u.created_at)}</td>
                  <td className="py-2.5 pr-3">
                    <div className="flex flex-wrap gap-1">
                      {u.is_platform_admin && <Pill tone="accent">Quản trị</Pill>}
                      {u.mfa_enabled && <Pill tone="positive">2 lớp</Pill>}
                      {u.disabled && <Pill tone="negative">Đã khoá</Pill>}
                    </div>
                  </td>
                  <td className="py-2.5 text-right">
                    {!u.is_platform_admin && (
                      <Button variant={u.disabled ? "secondary" : "danger"} onClick={() => toggle(u)}>
                        {u.disabled ? "Mở khoá" : "Khoá"}
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}
