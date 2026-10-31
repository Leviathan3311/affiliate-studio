"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { api, ApiError, session } from "@/lib/api";
import { Mark } from "./shell";
import { Button, ErrorNote, Field } from "./ui";

export function AuthCard({ title, sub, children }: { title: string; sub: string; children: React.ReactNode }) {
  return (
    <main className="grid min-h-screen place-items-center bg-ground px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex items-center gap-2.5">
          <Mark size={28} />
          <span className="text-base font-semibold">GrowthPilot AI</span>
        </div>
        <div className="rounded-[var(--radius-sheet)] border border-border bg-surface p-6">
          <h1 className="text-[22px] font-semibold">{title}</h1>
          <p className="mb-5 mt-1 text-sm text-muted">{sub}</p>
          {children}
        </div>
      </div>
    </main>
  );
}

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = Object.fromEntries(new FormData(e.currentTarget));
    setBusy(true);
    setError(null);
    try {
      const { access_token } = await api<{ access_token: string }>(`/auth/${mode}`, {
        method: "POST",
        json: form,
      });
      session.clear();
      session.setToken(access_token);
      router.replace(mode === "register" ? "/onboarding" : "/app");
    } catch (err) {
      setError(err as ApiError);
      setBusy(false);
    }
  }

  const f = error?.fields ?? {};
  return (
    <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
      {error && !Object.keys(f).length && <ErrorNote error={error} />}
      {mode === "register" && <Field label="Họ tên" name="full_name" autoComplete="name" />}
      <Field label="Email" name="email" type="email" autoComplete="email" required error={f.email} />
      <Field
        label="Mật khẩu"
        name="password"
        type="password"
        required
        autoComplete={mode === "login" ? "current-password" : "new-password"}
        hint={mode === "register" ? "Tối thiểu 8 ký tự" : undefined}
        error={f.password}
      />
      <Button variant="primary" type="submit" busy={busy} className="mt-1 h-10">
        {mode === "login" ? "Đăng nhập" : "Tạo tài khoản"}
      </Button>
      <p className="text-center text-sm text-muted">
        {mode === "login" ? (
          <>
            Chưa có tài khoản?{" "}
            <Link href="/register" className="font-medium text-ink underline">
              Đăng ký
            </Link>
          </>
        ) : (
          <>
            Đã có tài khoản?{" "}
            <Link href="/login" className="font-medium text-ink underline">
              Đăng nhập
            </Link>
          </>
        )}
      </p>
    </form>
  );
}
