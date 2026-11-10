"use client";

import { Bell, CalendarClock, CalendarDays, Check, ChevronsUpDown, CreditCard, FolderKanban, Inbox, LayoutGrid, LogOut, Menu, Plus, Settings, Shield, Users, X } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";
import { api, session, useApi, useNow } from "@/lib/api";
import { ROLE } from "@/lib/format";
import type { Billing, Notification, Overview } from "@/lib/types";
import { Initials } from "./ui";
import { useWorkspace } from "./workspace";

export function Mark({ size = 22 }: { size?: number }) {
  // Lotus bud: three petals opening from one stem, the product's mark.
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      <rect width="24" height="24" rx="6" fill="var(--accent)" />
      <path d="M12 5c2.2 2.2 2.2 6.8 0 9-2.2-2.2-2.2-6.8 0-9Z" fill="#fff" />
      <path d="M6 9.5c3 .3 5.4 2.6 6 5.5-3-.3-5.4-2.6-6-5.5Z" fill="#fff" opacity=".85" />
      <path d="M18 9.5c-3 .3-5.4 2.6-6 5.5 3-.3 5.4-2.6 6-5.5Z" fill="#fff" opacity=".85" />
      <path d="M12 15v4" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

const NAV = [
  { href: "/app", label: "Tổng quan", icon: LayoutGrid, roles: [] as string[] },
  { href: "/app/projects", label: "Dự án quảng cáo", icon: FolderKanban, roles: ["admin", "marketing"] },
  { href: "/app/publishing", label: "Lịch đăng", icon: CalendarClock, roles: ["admin", "marketing"] },
  { href: "/app/inbox", label: "Hộp thư", icon: Inbox, roles: ["admin", "sales", "branch_manager"] },
  { href: "/app/customers", label: "Khách hàng", icon: Users, roles: ["admin", "sales", "branch_manager"] },
  { href: "/app/bookings", label: "Lịch hẹn", icon: CalendarDays, roles: ["admin", "sales", "branch_manager"] },
];

function NavLink({
  href,
  label,
  icon: Icon,
  count,
  onNavigate,
}: {
  href: string;
  label: string;
  icon: typeof Inbox;
  count?: number;
  onNavigate?: () => void;
}) {
  const path = usePathname();
  const active = href === "/app" ? path === "/app" : path.startsWith(href) || (href === "/app/projects" && path.startsWith("/app/project"));
  return (
    <Link
      href={href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={`flex h-[34px] items-center gap-2.5 rounded-lg px-2.5 text-sm transition-colors duration-150 ${
        active ? "font-medium text-ink" : "text-faint hover:text-ink"
      }`}
    >
      <Icon className="size-4" strokeWidth={1.6} aria-hidden />
      <span className="flex-1">{label}</span>
      {count ? (
        <span className="text-xs font-medium text-ink" aria-label={`${count} cần xử lý`}>
          {count}
        </span>
      ) : null}
    </Link>
  );
}

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { me, workspace, can } = useWorkspace();
  const router = useRouter();
  const { data: ov } = useApi<Overview>(can("admin", "sales", "branch_manager") ? "/analytics/overview" : null, 30000);
  return (
    <nav aria-label="Điều hướng chính" className="flex h-full flex-col gap-6 px-3 py-3">
      <details className="relative">
        <summary className="flex cursor-pointer list-none items-center gap-2.5 rounded-lg px-1.5 py-1 hover:bg-raised [&::-webkit-details-marker]:hidden">
          <Mark />
          <div className="min-w-0 flex-1 leading-tight">
            <p className="truncate text-sm font-semibold">{workspace.name}</p>
            <p className="text-xs text-muted">GrowthPilot AI</p>
          </div>
          <ChevronsUpDown className="size-4 flex-none text-muted" strokeWidth={1.6} aria-label="Đổi cửa hàng" />
        </summary>
        <div className="absolute inset-x-0 top-full z-30 mt-1 rounded-[var(--radius-control)] border border-border bg-surface p-1 shadow-lg shadow-black/40">
          {me.workspaces.map((w) => (
            <button
              key={w.id}
              onClick={() => {
                session.setWorkspace(w.id);
                // Full reload on purpose: no screen keeps the old workspace's cached data.
                // eslint-disable-next-line @next/next/no-location-assign-relative-destination
                window.location.href = "/app";
              }}
              aria-current={w.id === workspace.id || undefined}
              className="flex w-full cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-raised"
            >
              <span className="min-w-0 flex-1 truncate">{w.name}</span>
              {w.id === workspace.id && <Check className="size-4 text-muted" strokeWidth={1.6} />}
            </button>
          ))}
          <Link
            href="/onboarding"
            onClick={onNavigate}
            className="mt-1 flex items-center gap-2 border-t border-border px-2 pb-1.5 pt-2.5 text-sm text-muted hover:text-ink"
          >
            <Plus className="size-4" strokeWidth={1.6} /> Tạo cửa hàng mới
          </Link>
        </div>
      </details>
      <div className="flex flex-col gap-0.5">
        {NAV.filter((n) => can(...n.roles) || n.roles.length === 0).map((n) => (
          <NavLink
            key={n.href}
            {...n}
            count={n.href === "/app/inbox" ? ov?.needs_human : undefined}
            onNavigate={onNavigate}
          />
        ))}
      </div>
      <div className="mt-auto flex flex-col gap-0.5">
        {me.is_platform_admin && <NavLink href="/app/admin" label="Quản trị" icon={Shield} onNavigate={onNavigate} />}
        {can("admin") && <NavLink href="/app/billing" label="Gói & thanh toán" icon={CreditCard} onNavigate={onNavigate} />}
        <NavLink href="/app/settings" label="Cài đặt" icon={Settings} onNavigate={onNavigate} />
        <div className="mt-3 flex items-center gap-2.5 px-1.5">
          <Initials name={me.full_name || me.email} size={28} />
          <div className="min-w-0 flex-1 leading-tight">
            <p className="truncate text-sm">{me.full_name || me.email}</p>
            <p className="text-xs text-muted">{ROLE[workspace.role]}</p>
          </div>
          <button
            onClick={() => {
              api("/auth/logout", { method: "POST" }).catch(() => undefined);
              session.clear();
              router.replace("/login");
            }}
            className="grid size-9 cursor-pointer place-items-center rounded-lg text-muted hover:bg-raised hover:text-ink"
            aria-label="Đăng xuất"
          >
            <LogOut className="size-4" strokeWidth={1.6} />
          </button>
        </div>
      </div>
    </nav>
  );
}

/** Days left in the trial or paid period; only shown when it matters (trial, or under a week). */
function PlanPill() {
  const { data } = useApi<Billing>("/billing");
  const now = useNow(60000);
  if (!data) return null;
  const days = Math.ceil((new Date(data.access_until).getTime() - now) / 86400000);
  if (data.status === "active" && days > 7) return null;
  const text = data.status === "expired" ? "Đã hết hạn" : `${data.status === "trial" ? "Dùng thử" : "Còn"}: ${days} ngày`;
  return (
    <Link
      href="/app/billing"
      className={`rounded-full px-2.5 py-1 text-xs font-medium ${
        data.status === "expired" || days <= 3 ? "bg-[var(--pill-negative-bg)] text-[var(--pill-negative-ink)]" : "bg-raised text-ink"
      }`}
    >
      {text}
    </Link>
  );
}

function Notifications() {
  const [open, setOpen] = useState(false);
  const { data, reload } = useApi<Notification[]>("/notifications?unread=true&limit=8", 20000);
  const n = data?.length ?? 0;
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-label={n ? `Thông báo, ${n} chưa đọc` : "Thông báo"}
        className="relative grid size-9 cursor-pointer place-items-center rounded-lg text-muted hover:bg-raised hover:text-ink"
      >
        <Bell className="size-4" strokeWidth={1.6} />
        {n > 0 && <span className="absolute right-2 top-2 size-2 rounded-full bg-accent" aria-hidden />}
      </button>
      {open && (
        <div className="absolute right-0 top-11 z-30 w-80 rounded-[var(--radius-card)] border border-border bg-surface p-2 shadow-lg">
          <p className="px-2 py-1.5 text-sm font-semibold">Khách tiềm năng cần xử lý</p>
          {n === 0 && <p className="px-2 pb-2 text-sm text-muted">Không có thông báo mới.</p>}
          {data?.map((item) => (
            <Link
              key={item.id}
              href={item.conversation_id ? `/app/inbox?c=${item.conversation_id}` : "/app"}
              onClick={async () => {
                setOpen(false);
                await api(`/notifications/${item.id}/acknowledge`, { method: "POST" }).catch(() => undefined);
                reload();
              }}
              className="block rounded-md px-2 py-2 hover:bg-raised"
            >
              <p className="text-sm font-medium">{item.title}</p>
              <p className="line-clamp-2 text-xs text-muted">{item.body}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export function Shell({ children }: { children: ReactNode }) {
  const [menu, setMenu] = useState(false);
  const { workspace } = useWorkspace();
  return (
    <div className="min-h-screen bg-ground lg:grid lg:grid-cols-[228px_1fr]">
      <aside className="sticky top-0 hidden h-screen lg:block">
        <Sidebar />
      </aside>
      {menu && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal aria-label="Menu">
          <button className="absolute inset-0 bg-black/60" aria-label="Đóng menu" onClick={() => setMenu(false)} />
          <div className="absolute inset-y-0 left-0 w-72 bg-ground">
            <button
              onClick={() => setMenu(false)}
              className="absolute right-2 top-3 grid size-9 place-items-center rounded-lg text-muted"
              aria-label="Đóng menu"
            >
              <X className="size-4" />
            </button>
            <Sidebar onNavigate={() => setMenu(false)} />
          </div>
        </div>
      )}
      <div className="flex min-h-screen min-w-0 flex-col lg:pr-2 lg:pb-2">
        <header className="flex h-12 flex-none items-center justify-between gap-3 px-3 lg:px-1">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMenu(true)}
              className="grid size-9 place-items-center rounded-lg text-muted lg:hidden"
              aria-label="Mở menu"
            >
              <Menu className="size-4" />
            </button>
            <span className="text-sm text-muted">
              Giờ AI trực: {workspace.active_start}–{workspace.active_end}
              <span className="hidden sm:inline"> · {workspace.reply_mode === "auto" ? "Tự trả lời" : "Chỉ gợi ý"}</span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <PlanPill />
            <Notifications />
          </div>
        </header>
        <main className="min-w-0 flex-1 p-4 sm:p-6 lg:border-l lg:border-t lg:border-rule lg:rounded-tl-[var(--radius-sheet)]">
          {children}
        </main>
      </div>
    </div>
  );
}
