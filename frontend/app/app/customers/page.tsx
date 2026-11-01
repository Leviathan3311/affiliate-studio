"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";
import { Button, Empty, ErrorNote, Field, Initials, PageTitle, Panel, Pill, Select, Skeleton } from "@/components/ui";
import { api, ApiError, useApi } from "@/lib/api";
import { ago, BOOKING, dateTime, LEAD, vnd } from "@/lib/format";
import type { Customer, Customer360, LeadStatus } from "@/lib/types";

export default function CustomersPage() {
  return (
    <Suspense fallback={<Skeleton rows={6} />}>
      <Customers />
    </Suspense>
  );
}

function Customers() {
  const params = useSearchParams();
  const router = useRouter();
  const id = params.get("id");
  const [q, setQ] = useState("");
  const [creating, setCreating] = useState(false);
  const list = useApi<Customer[]>(`/customers?limit=100${q ? `&q=${encodeURIComponent(q)}` : ""}`);

  if (id) return <Profile id={id} onBack={() => router.push("/app/customers")} onChanged={list.reload} />;

  return (
    <>
      <PageTitle
        title="Khách hàng"
        sub={list.data ? `${list.data.length.toLocaleString("vi-VN")} khách${q ? " khớp tìm kiếm" : ""}` : undefined}
        actions={<Button variant="primary" onClick={() => setCreating((v) => !v)}>Thêm khách</Button>}
      />
      {creating && <CreateCustomer onDone={(c) => router.push(`/app/customers?id=${c.id}`)} />}
      <label htmlFor="cust-search" className="sr-only">Tìm khách</label>
      <input
        id="cust-search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Tìm theo tên, số điện thoại hoặc email"
        className="mb-4 h-9 w-full max-w-sm rounded-[var(--radius-control)] border border-control px-3 text-sm focus:border-ink focus:outline-none"
      />
      {list.error && <ErrorNote error={list.error} onRetry={list.reload} />}
      {list.loading && <Skeleton rows={6} />}
      {list.data?.length === 0 && (
        <Empty title={q ? "Không tìm thấy khách" : "Chưa có khách hàng"}>
          Khách nhắn Messenger được tự động thêm vào đây, mỗi người một hồ sơ.
        </Empty>
      )}
      {!!list.data?.length && (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="text-left text-xs text-muted">
                <th className="h-9 font-normal">Khách</th>
                <th className="font-normal">Liên hệ</th>
                <th className="font-normal">Nhãn</th>
                <th className="text-right font-normal">Tương tác gần nhất</th>
              </tr>
            </thead>
            <tbody>
              {list.data.map((c) => (
                <tr key={c.id} className="border-t border-rule hover:bg-raised">
                  <td className="py-2.5 pr-4">
                    <Link href={`/app/customers?id=${c.id}`} className="flex items-center gap-3">
                      <Initials name={c.display_name} />
                      <span className="font-medium">{c.display_name}</span>
                      {c.opted_out_at && <Pill tone="negative">Từ chối nhận tin</Pill>}
                    </Link>
                  </td>
                  <td className="pr-4 text-muted">{c.phone || c.email || "—"}</td>
                  <td className="pr-4">
                    <span className="flex flex-wrap gap-1">{c.tags.length ? c.tags.map((t) => <Pill key={t}>{t}</Pill>) : <span className="text-muted">—</span>}</span>
                  </td>
                  <td className="text-right text-muted">{ago(c.last_interaction_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

function CreateCustomer({ onDone }: { onDone: (c: Customer) => void }) {
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.currentTarget)) as Record<string, string>;
    setBusy(true);
    try {
      onDone(
        await api<Customer>("/customers", {
          method: "POST",
          json: { display_name: f.display_name, phone: f.phone || null, email: f.email || null },
        }),
      );
    } catch (err) {
      setError(err as ApiError);
      setBusy(false);
    }
  }
  return (
    <Panel title="Khách mới" className="mb-6">
      <form onSubmit={submit} className="grid gap-4 sm:grid-cols-3" noValidate>
        <Field label="Tên hiển thị" name="display_name" required error={error?.fields.display_name} />
        <Field label="Số điện thoại" name="phone" inputMode="tel" error={error?.fields.phone} />
        <Field label="Email" name="email" type="email" error={error?.fields.email} />
        <div className="flex items-center gap-3 sm:col-span-3">
          <Button variant="primary" type="submit" busy={busy}>Lưu khách</Button>
          {error && !Object.keys(error.fields).length && <ErrorNote error={error} />}
        </div>
      </form>
    </Panel>
  );
}

function Profile({ id, onBack, onChanged }: { id: string; onBack: () => void; onChanged: () => void }) {
  const { data: c, error, reload } = useApi<Customer360>(`/customers/${id}`);
  const [saveError, setSaveError] = useState<ApiError | null>(null);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  if (error) return <ErrorNote error={error} onRetry={reload} />;
  if (!c) return <Skeleton rows={8} />;

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.currentTarget)) as Record<string, string>;
    setBusy(true);
    setSaveError(null);
    try {
      await api(`/customers/${id}`, {
        method: "PATCH",
        json: {
          display_name: f.display_name,
          phone: f.phone || null,
          email: f.email || null,
          notes: f.notes,
          tags: f.tags.split(",").map((t) => t.trim()).filter(Boolean),
          consent_marketing: f.consent_marketing === "on",
        },
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
      reload();
      onChanged();
    } catch (err) {
      setSaveError(err as ApiError);
    } finally {
      setBusy(false);
    }
  }

  async function setLead(leadId: string, status: LeadStatus) {
    await api(`/leads/${leadId}`, { method: "PATCH", json: { status } });
    reload();
  }

  async function suppress() {
    if (!confirm(`Ngừng mọi tin tự động gửi tới ${c!.display_name}?`)) return;
    await api(`/customers/${id}/suppressions`, { method: "POST", json: { reason: "admin_block" } });
    reload();
  }

  const fe = saveError?.fields ?? {};
  return (
    <>
      <button onClick={onBack} className="mb-4 inline-flex cursor-pointer items-center gap-1.5 text-sm text-muted hover:text-ink">
        <ArrowLeft className="size-4" aria-hidden /> Khách hàng
      </button>
      <PageTitle
        title={c.display_name}
        sub={`Tương tác gần nhất: ${ago(c.last_interaction_at)} · Kênh: ${c.channels.join(", ") || "nhập tay"}`}
        actions={
          <>
            {c.conversation_ids[0] && (
              <Link href={`/app/inbox?c=${c.conversation_ids[0]}`} className="inline-flex h-9 items-center rounded-[var(--radius-control)] bg-active px-3 text-sm font-medium">
                Mở hội thoại
              </Link>
            )}
            <Link href={`/app/bookings?new=1&customer=${c.id}`} className="inline-flex h-9 items-center rounded-[var(--radius-control)] bg-ink px-3 text-sm font-medium text-ground">
              Tạo lịch hẹn
            </Link>
          </>
        }
      />
      <div className="grid gap-6 xl:grid-cols-3">
        <Panel title="Thông tin" className="xl:col-span-2">
          <form onSubmit={save} className="grid gap-4 sm:grid-cols-2" noValidate>
            <Field label="Tên hiển thị" name="display_name" defaultValue={c.display_name} error={fe.display_name} />
            <Field label="Số điện thoại" name="phone" inputMode="tel" defaultValue={c.phone ?? ""} error={fe.phone} hint="Chỉ lưu khi khách tự cung cấp" />
            <Field label="Email" name="email" type="email" defaultValue={c.email ?? ""} error={fe.email} />
            <Field label="Nhãn" name="tags" defaultValue={c.tags.join(", ")} hint="Ngăn cách bằng dấu phẩy" />
            <div className="sm:col-span-2">
              <Field label="Ghi chú nội bộ" name="notes" textarea defaultValue={c.notes} />
            </div>
            <label className="flex cursor-pointer items-center gap-2 text-sm sm:col-span-2">
              <input type="checkbox" name="consent_marketing" defaultChecked={c.consent_marketing} className="size-4 accent-[var(--accent)]" />
              Khách đã đồng ý nhận tin ưu đãi
            </label>
            <div className="flex items-center gap-3 sm:col-span-2">
              <Button variant="primary" type="submit" busy={busy}>Lưu thay đổi</Button>
              <span role="status" className="text-sm text-positive">{saved ? "Đã lưu" : ""}</span>
              {saveError && !Object.keys(fe).length && <ErrorNote error={saveError} />}
            </div>
          </form>
        </Panel>

        <div className="flex flex-col gap-6">
          <Panel title="Khách tiềm năng">
            {c.leads.length === 0 && <p className="text-sm text-muted">—</p>}
            {c.leads.map((l) => (
              <div key={l.id} className="space-y-2">
                <Select label={`Nguồn: ${l.source} · điểm ${l.score}/100`} value={l.status} onChange={(e) => setLead(l.id, e.target.value as LeadStatus)}>
                  {Object.entries(LEAD).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </Select>
              </div>
            ))}
          </Panel>
          <Panel title="Lịch hẹn">
            {c.bookings.length === 0 && <p className="text-sm text-muted">Chưa có lịch hẹn.</p>}
            <ul className="divide-y divide-rule">
              {c.bookings.map((b) => (
                <li key={b.id} className="flex justify-between gap-3 py-2 text-sm">
                  <span>{dateTime(b.start_at)} · {BOOKING[b.status]}</span>
                  <span className="text-right">{vnd(b.actual_revenue ?? b.expected_value)}</span>
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title="Chăm sóc tự động">
            {c.suppressed ? (
              <p className="text-sm">
                {c.opted_out_at ? "Khách đã yêu cầu dừng nhận tin." : "Đã ngừng chăm sóc tự động."} Mọi tin tự động bị chặn.
              </p>
            ) : (
              <Button variant="danger" onClick={suppress} className="px-0">Ngừng gửi tin tự động cho khách này</Button>
            )}
          </Panel>
        </div>
      </div>
    </>
  );
}
