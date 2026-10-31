"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";
import { Button, Empty, ErrorNote, Field, PageTitle, Panel, Pill, Select, Skeleton } from "@/components/ui";
import { api, ApiError, useApi } from "@/lib/api";
import { BOOKING, time, vnd } from "@/lib/format";
import type { Booking, BookingStatus, Branch, Customer, Service } from "@/lib/types";

const NEXT: Partial<Record<BookingStatus, BookingStatus[]>> = {
  pending: ["confirmed", "cancelled"],
  confirmed: ["arrived", "no_show", "cancelled"],
  arrived: ["completed"],
};
const TONE: Record<BookingStatus, "neutral" | "positive" | "negative" | "warning" | "accent"> = {
  pending: "warning",
  confirmed: "accent",
  arrived: "neutral",
  completed: "positive",
  cancelled: "neutral",
  no_show: "negative",
};

export default function BookingsPage() {
  return (
    <Suspense fallback={<Skeleton rows={6} />}>
      <Bookings />
    </Suspense>
  );
}

function startOfDay(d: Date) {
  const s = new Date(d);
  s.setHours(0, 0, 0, 0);
  return s;
}

function Bookings() {
  const params = useSearchParams();
  const [day, setDay] = useState(() => startOfDay(new Date()));
  const [creating, setCreating] = useState(params.get("new") === "1");
  const end = new Date(day);
  end.setDate(end.getDate() + 1);
  const list = useApi<Booking[]>(
    `/bookings?start=${encodeURIComponent(day.toISOString())}&end=${encodeURIComponent(end.toISOString())}`,
    30000,
  );
  const shift = (n: number) => setDay((d) => startOfDay(new Date(d.getTime() + n * 864e5 + 3600e3)));
  const isToday = day.getTime() === startOfDay(new Date()).getTime();
  const active = list.data?.filter((b) => b.status !== "cancelled") ?? [];

  return (
    <>
      <PageTitle
        title="Lịch hẹn"
        sub={list.data ? `${active.length} lịch trong ngày · dự kiến ${vnd(active.reduce((s, b) => s + (b.expected_value ?? 0), 0))}` : undefined}
        actions={<Button variant="primary" onClick={() => setCreating((v) => !v)}>Tạo lịch hẹn</Button>}
      />
      {creating && (
        <CreateBooking
          customerId={params.get("customer")}
          conversationId={params.get("conversation")}
          onDone={(b) => {
            setCreating(false);
            setDay(startOfDay(new Date(b.start_at)));
            list.reload();
          }}
        />
      )}

      <div className="mb-4 flex items-center gap-2">
        <Button variant="ghost" onClick={() => shift(-1)} aria-label="Ngày trước"><ChevronLeft className="size-4" /></Button>
        <p className="min-w-44 text-center font-medium">
          {day.toLocaleDateString("vi-VN", { weekday: "long", day: "2-digit", month: "2-digit", year: "numeric" })}
        </p>
        <Button variant="ghost" onClick={() => shift(1)} aria-label="Ngày sau"><ChevronRight className="size-4" /></Button>
        {!isToday && <Button variant="ghost" onClick={() => setDay(startOfDay(new Date()))}>Hôm nay</Button>}
      </div>

      {list.error && <ErrorNote error={list.error} onRetry={list.reload} />}
      {list.loading && <Skeleton rows={5} />}
      {list.data?.length === 0 && <Empty title="Không có lịch hẹn trong ngày">Tạo lịch từ hội thoại Messenger hoặc nhập tay.</Empty>}
      <ul className="divide-y divide-rule">
        {list.data?.map((b) => (
          <BookingRow key={b.id} b={b} onChanged={list.reload} />
        ))}
      </ul>
    </>
  );
}

function BookingRow({ b, onChanged }: { b: Booking; onChanged: () => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  async function move(status: BookingStatus) {
    let body: Record<string, unknown> = { status };
    if (status === "completed") {
      const input = prompt("Doanh thu thực tế (VNĐ)", String(b.expected_value ?? ""));
      if (input === null) return;
      const amount = Number(input.replace(/\D/g, ""));
      body = { status, actual_revenue: Number.isFinite(amount) ? amount : undefined };
    }
    setBusy(status);
    setError(null);
    try {
      await api(`/bookings/${b.id}`, { method: "PATCH", json: body });
      onChanged();
    } catch (e) {
      setError(e as ApiError);
    } finally {
      setBusy(null);
    }
  }

  return (
    <li className="flex flex-wrap items-center gap-x-4 gap-y-2 py-3">
      <span className="w-24 flex-none font-medium">{time(b.start_at)}–{time(b.end_at)}</span>
      <div className="min-w-48 flex-1">
        <Link href={`/app/customers?id=${b.customer_id}`} className="font-medium hover:underline">{b.customer_name}</Link>
        <p className="text-sm text-muted">{b.service_name}{b.source === "messenger" ? " · từ Messenger" : ""}</p>
      </div>
      <span className="w-28 text-right">{vnd(b.actual_revenue ?? b.expected_value)}</span>
      <Pill tone={TONE[b.status]}>{BOOKING[b.status]}</Pill>
      <div className="flex gap-1">
        {NEXT[b.status]?.map((s) => (
          <Button key={s} variant={s === "cancelled" || s === "no_show" ? "ghost" : "secondary"} className="h-8 text-xs" busy={busy === s} onClick={() => move(s)}>
            {BOOKING[s]}
          </Button>
        ))}
      </div>
      {error && <div className="w-full"><ErrorNote error={error} /></div>}
    </li>
  );
}

function CreateBooking({
  customerId,
  conversationId,
  onDone,
}: {
  customerId: string | null;
  conversationId: string | null;
  onDone: (b: Booking) => void;
}) {
  const customers = useApi<Customer[]>("/customers?limit=200");
  const branches = useApi<Branch[]>("/branches");
  const services = useApi<Service[]>("/services");
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.currentTarget)) as Record<string, string>;
    setBusy(true);
    setError(null);
    try {
      onDone(
        await api<Booking>("/bookings", {
          method: "POST",
          json: {
            customer_id: f.customer_id,
            branch_id: f.branch_id,
            service_id: f.service_id,
            start_at: f.start_at ? new Date(f.start_at).toISOString() : "",
            status: f.status,
            conversation_id: conversationId,
            notes: f.notes,
          },
        }),
      );
    } catch (err) {
      setError(err as ApiError);
      setBusy(false);
    }
  }

  const ready = customers.data && branches.data && services.data;
  const missing = ready && (!branches.data!.length || !services.data!.length);
  return (
    <Panel title="Lịch hẹn mới" className="mb-6">
      {!ready && <Skeleton rows={3} />}
      {missing && (
        <p className="text-sm">
          Cần ít nhất một chi nhánh và một dịch vụ.{" "}
          <Link href="/app/settings?tab=services" className="font-medium underline">Thêm trong Cài đặt</Link>
        </p>
      )}
      {ready && !missing && (
        <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" noValidate>
          <Select label="Khách" name="customer_id" defaultValue={customerId ?? ""} required>
            <option value="" disabled>Chọn khách</option>
            {customers.data!.map((c) => <option key={c.id} value={c.id}>{c.display_name}{c.phone ? ` · ${c.phone}` : ""}</option>)}
          </Select>
          <Select label="Dịch vụ" name="service_id" required>
            {services.data!.filter((s) => s.active).map((s) => (
              <option key={s.id} value={s.id}>{s.name} · {s.duration_minutes} phút</option>
            ))}
          </Select>
          <Select label="Chi nhánh" name="branch_id" required>
            {branches.data!.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </Select>
          <Field label="Thời gian bắt đầu" name="start_at" type="datetime-local" required error={error?.fields.start_at} />
          <Select label="Trạng thái" name="status" defaultValue="pending">
            <option value="pending">Chờ xác nhận</option>
            <option value="confirmed">Đã xác nhận với khách</option>
          </Select>
          <Field label="Ghi chú" name="notes" />
          <div className="flex flex-wrap items-center gap-3 sm:col-span-2 xl:col-span-3">
            <Button variant="primary" type="submit" busy={busy}>Lưu lịch hẹn</Button>
            {error && !Object.keys(error.fields).length && <ErrorNote error={error} />}
            {error && Object.keys(error.fields).length > 0 && !error.fields.start_at && <ErrorNote error={error} />}
          </div>
        </form>
      )}
    </Panel>
  );
}
