"use client";

import type { Today } from "@/lib/types";

/** Customer messages per local hour today, with the quiet-hours band where the AI is off. */
export function HourChart({ today, nowHour }: { today: Today; nowHour: number }) {
  const W = 720;
  const H = 240;
  const pad = { l: 28, r: 8, t: 26, b: 22 };
  const pw = W - pad.l - pad.r;
  const ph = H - pad.t - pad.b;
  const max = Math.max(...today.inbound_by_hour);
  const step = max <= 4 ? 1 : Math.ceil(max / 4);
  const top = Math.max(4, step * 4);
  const ticks = Array.from({ length: 5 }, (_, i) => (top / 4) * i);
  const bw = pw / 24;
  const start = Number(today.active_start.slice(0, 2));
  const end = Number(today.active_end.slice(0, 2));
  const quiet = (h: number) => (start <= end ? h < start || h >= end : h >= end && h < start);
  const x = (h: number) => pad.l + h * bw;
  const y = (v: number) => pad.t + ph - (v / top) * ph;
  const total = today.inbound_by_hour.reduce((a, b) => a + b, 0);

  return (
    <figure className="-mx-1 overflow-x-auto px-1">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full min-w-[600px]"
        role="img"
        aria-label={`${total} tin nhắn của khách hôm nay; giờ yên lặng ${today.active_end}–${today.active_start}`}
      >
        {/* quiet hours band */}
        {Array.from({ length: 24 }, (_, h) =>
          quiet(h) ? <rect key={h} x={x(h)} y={pad.t} width={bw} height={ph} fill="var(--raised)" /> : null,
        )}
        <text x={x(0) + 4} y={pad.t - 8} fontSize="11" fill="var(--muted)">
          AI nghỉ · chỉ gửi tin mẫu
        </text>
        <text x={x(start) + 4} y={pad.t - 8} fontSize="11" fill="var(--text)">
          {today.active_start} gom tin đêm
          {today.queued_for_morning ? ` (${today.queued_for_morning} hội thoại chờ)` : ""}
        </text>
        <line x1={x(start)} x2={x(start)} y1={pad.t - 4} y2={pad.t + ph} stroke="var(--text)" strokeWidth="1" />
        {ticks.map((t) => (
          <g key={t}>
            <line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} stroke={t === 0 ? "var(--control)" : "var(--rule)"} />
            <text x={pad.l - 6} y={y(t) + 4} fontSize="11" textAnchor="end" fill="var(--muted)">
              {t}
            </text>
          </g>
        ))}
        {today.inbound_by_hour.map((v, h) =>
          v > 0 ? (
            <rect
              key={h}
              x={x(h) + 3}
              y={y(v)}
              width={bw - 6}
              height={y(0) - y(v)}
              fill={h > nowHour ? "var(--control)" : "var(--chart-1)"}
            >
              <title>{`${String(h).padStart(2, "0")}:00 — ${v} tin`}</title>
            </rect>
          ) : null,
        )}
        {[0, 3, 6, 9, 12, 15, 18, 21].map((h) => (
          <text key={h} x={x(h) + bw / 2} y={H - 6} fontSize="11" textAnchor="middle" fill="var(--muted)">
            {String(h).padStart(2, "0")}h
          </text>
        ))}
      </svg>
    </figure>
  );
}
