"use client";

import Link from "next/link";
import { useState } from "react";
import { Button, ErrorNote, Field, PageTitle, Panel, Pill } from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { api, ApiError } from "@/lib/api";
import { ROLE } from "@/lib/format";

export default function AccountPage() {
  const { me, reload } = useWorkspace();
  const [name, setName] = useState(me.full_name);
  const [saved, setSaved] = useState("");
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState("");

  async function run(what: string, fn: () => Promise<unknown>, done: string) {
    setBusy(what);
    setError(null);
    setSaved("");
    try {
      await fn();
      setSaved(done);
      await reload();
    } catch (e) {
      setError(e as ApiError);
    }
    setBusy("");
  }

  return (
    <>
      <PageTitle title="Tài khoản của tôi" sub={me.email} />
      <div className="grid max-w-4xl gap-6 lg:grid-cols-2">
        <Panel title="Thông tin">
          <form
            className="flex flex-col gap-4"
            onSubmit={(e) => {
              e.preventDefault();
              run("name", () => api("/auth/me", { method: "PATCH", json: { full_name: name } }), "Đã lưu họ tên.");
            }}
          >
            <Field label="Họ tên" name="full_name" value={name} onChange={(e) => setName(e.target.value)} />
            <Field label="Email đăng nhập" name="email" value={me.email} disabled hint="Email dùng để đăng nhập, không đổi được" />
            <div>
              <Button variant="primary" type="submit" busy={busy === "name"}>Lưu</Button>
            </div>
          </form>
        </Panel>

        <Panel title="Đổi mật khẩu">
          <form
            className="flex flex-col gap-4"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              const target = e.currentTarget;
              if (f.get("new_password") !== f.get("confirm")) {
                setError(new ApiError(422, "Hai mật khẩu mới chưa khớp"));
                return;
              }
              run(
                "pw",
                async () => {
                  await api("/auth/change-password", {
                    method: "POST",
                    json: { current_password: f.get("current_password"), new_password: f.get("new_password") },
                  });
                  target.reset();
                },
                "Đã đổi mật khẩu. Các thiết bị khác đã được đăng xuất.",
              );
            }}
          >
            <Field label="Mật khẩu hiện tại" name="current_password" type="password" autoComplete="current-password" />
            <Field label="Mật khẩu mới" name="new_password" type="password" autoComplete="new-password" hint="Tối thiểu 8 ký tự" />
            <Field label="Nhập lại mật khẩu mới" name="confirm" type="password" autoComplete="new-password" />
            <div>
              <Button variant="primary" type="submit" busy={busy === "pw"}>Đổi mật khẩu</Button>
            </div>
          </form>
        </Panel>

        <Panel title="Bảo mật" action={me.mfa_enabled ? <Pill tone="positive">Đã bật</Pill> : <Pill tone="neutral">Chưa bật</Pill>}>
          <p className="text-sm">
            {me.mfa_enabled
              ? "Mỗi lần đăng nhập cần thêm mã 6 số từ app xác thực trên điện thoại."
              : me.is_platform_admin
                ? "Tài khoản quản trị bắt buộc bật xác thực hai lớp."
                : "Bạn có thể bật xác thực hai lớp để tài khoản an toàn hơn."}
          </p>
          {!me.mfa_enabled && me.is_platform_admin && (
            <Link href="/app/admin" className="mt-3 inline-block text-sm font-medium underline">Bật ngay</Link>
          )}
        </Panel>

        <Panel title="Cửa hàng của tôi" action={me.is_platform_admin ? <Pill tone="accent">Quản trị GrowthPilot</Pill> : undefined}>
          <ul className="flex flex-col divide-y divide-rule text-sm">
            {me.workspaces.map((w) => (
              <li key={w.id} className="flex justify-between gap-3 py-2">
                <span className="min-w-0 truncate">{w.name}</span>
                <span className="text-muted">{ROLE[w.role]}</span>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
      {error && <div className="mt-4 max-w-4xl"><ErrorNote error={error} /></div>}
      {saved && <p role="status" className="mt-4 text-sm text-positive">{saved}</p>}
    </>
  );
}
