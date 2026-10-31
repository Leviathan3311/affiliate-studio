"use client";

import Link from "next/link";
import { HourChart } from "@/components/hour-chart";
import { Empty, ErrorNote, Initials, PageTitle, Panel, Pill, Skeleton } from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { useApi } from "@/lib/api";
import { ago, BOOKING, INTENT, pct, time, vnd } from "@/lib/format";
import type { Booking, Conversation, Overview, Today } from "@/lib/types";

function dayRange() {
  const s = new Date();
  s.setHours(0, 0, 0, 0);
  const e = new Date(s);
  e.setDate(e.getDate() + 1);
  return `start=${encodeURIComponent(s.toISOString())}&end=${encodeURIComponent(e.toISOString())}`;
}

export default function Dashboard() {
  const { can } = useWorkspace();
  const inbox = can("admin", "sales", "branch_manager");
  const ov = useApi<Overview>("/analytics/overview", 30000);
  const today = useApi<Today>("/analytics/today", 30000);
  const queue = useApi<Conversation[]>(inbox ? "/conversations?needs_human=true&status=open&limit=6" : null, 15000);
  const bookings = useApi<Booking[]>(inbox ? `/bookings?${dayRange()}` : null, 30000);

  const o = ov.data;
  const waiting = queue.data?.length ?? 0;
  const finding = o
    ? [
        o.unread_high_intent ? `${o.unread_high_intent} khách có nhu cầu cao chưa được xem` : null,
        o.needs_human ? `${o.needs_human} hội thoại cần nhân viên trả lời` : null,
        today.data?.queued_for_morning ? `${today.data.queued_for_morning} hội thoại chờ AI lúc ${today.data.active_start}` : null,
      ].filter(Boolean).join(" · ") || "Không có khách nào đang chờ. Mọi hội thoại đã được xử lý."
    : undefined;

  return (
    <>
      <PageTitle title="Tổng quan" sub={finding} />
      {ov.error && <ErrorNote error={ov.error} onRetry={ov.reload} />}

      <div className="grid gap-6 xl:grid-cols-3">
        {inbox && (
          <Panel
            className="xl:col-span-2"
            title={`Cần xử lý ngay${waiting ? ` · ${waiting}` : ""}`}
            action={<Link href="/app/inbox" className="text-sm font-medium hover:underline">Mở hộp thư</Link>}
          >
            {queue.loading && <Skeleton rows={4} />}
            {queue.error && <ErrorNote error={queue.error} onRetry={queue.reload} />}
            {queue.data && waiting === 0 && (
              <Empty title="Không có khách nào đang chờ">AI vẫn đang gợi ý câu trả lời cho các tin nhắn mới.</Empty>
            )}
            <ul className="-mx-2">
              {queue.data?.map((c) => (
                <li key={c.id}>
                  <Link href={`/app/inbox?c=${c.id}`} className="flex items-center gap-3 rounded-md px-2 py-3 hover:bg-raised">
                    <Initials name={c.customer_name} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-baseline justify-between gap-3">
                        <p className="truncate font-semibold">{c.customer_name}</p>
                        <span className="flex-none text-xs text-muted">{ago(c.last_customer_message_at)}</span>
                      </div>
                      <p className="truncate text-sm text-muted">{c.ai_summary || c.last_message_preview}</p>
                    </div>
                    {c.ai_intent && <Pill tone={c.ai_intent === "complaint" ? "negative" : "accent"}>{INTENT[c.ai_intent]}</Pill>}
                  </Link>
                </li>
              ))}
            </ul>
          </Panel>
        )}

        {inbox && (
          <Panel
            title="Lịch hẹn hôm nay"
            action={<Link href="/app/bookings" className="text-sm font-medium hover:underline">Xem lịch</Link>}
          >
            {bookings.loading && <Skeleton rows={4} />}
            {bookings.error && <ErrorNote error={bookings.error} onRetry={bookings.reload} />}
            {bookings.data?.length === 0 && <Empty title="Chưa có lịch hẹn hôm nay" />}
            <ul className="divide-y divide-rule">
              {bookings.data?.slice(0, 6).map((b) => (
                <li key={b.id} className="flex items-center gap-3 py-2.5">
                  <span className="w-12 flex-none font-medium">{time(b.start_at)}</span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate">{b.customer_name}</p>
                    <p className="truncate text-xs text-muted">{b.service_name}</p>
                  </div>
                  <span className="flex-none text-xs text-muted">{BOOKING[b.status]}</span>
                </li>
              ))}
            </ul>
          </Panel>
        )}

        <Panel className="xl:col-span-2" title="Tin nhắn của khách hôm nay">
          {today.data ? <HourChart today={today.data} nowHour={new Date().getHours()} /> : <Skeleton rows={5} />}
        </Panel>

        <Panel title="30 ngày qua">
          {!o ? (
            <Skeleton rows={6} />
          ) : (
            <dl className="divide-y divide-rule">
              {[
                ["Khách tiềm năng mới", o.leads_total.toLocaleString("vi-VN")],
                ["Tỷ lệ được phản hồi", pct(o.response_rate)],
                ["Phản hồi đầu tiên trung bình", o.avg_first_response_minutes == null ? "—" : `${o.avg_first_response_minutes.toLocaleString("vi-VN")} phút`],
                ["Lịch hẹn đã tạo", o.bookings_total.toLocaleString("vi-VN")],
                ["Tỷ lệ khách → lịch hẹn", pct(o.lead_to_booking_rate)],
                ["Doanh thu dự kiến", vnd(o.expected_revenue)],
                ["Doanh thu thực tế", vnd(o.actual_revenue)],
              ].map(([k, v]) => (
                <div key={k} className="flex items-baseline justify-between gap-3 py-2.5">
                  <dt className="text-sm text-muted">{k}</dt>
                  <dd className="text-right font-medium">{v}</dd>
                </div>
              ))}
            </dl>
          )}
        </Panel>
      </div>
    </>
  );
}
