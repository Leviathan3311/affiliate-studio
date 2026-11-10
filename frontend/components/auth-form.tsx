"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, type FormEvent } from "react";
import { api, ApiError, session } from "@/lib/api";
import { LegalLinks } from "./legal";
import { track } from "./pixel";
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
        <LegalLinks className="mt-6" />
      </div>
    </main>
  );
}

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [mfaToken, setMfaToken] = useState("");

  function signedIn() {
    session.clear();
    session.markSignedIn();
    if (mode === "register") track("CompleteRegistration");
    const next = new URLSearchParams(window.location.search).get("next");
    if (next?.startsWith("/invite")) return router.replace(next); // accept the invitation first
    // keep ?shop=&industry= from the landing page so onboarding is prefilled
    router.replace(mode === "register" ? `/onboarding${window.location.search}` : "/app");
  }

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = Object.fromEntries(new FormData(e.currentTarget));
    setBusy(true);
    setError(null);
    try {
      if (mfaToken) {
        await api("/auth/2fa/verify", { method: "POST", json: { mfa_token: mfaToken, code: form.code } });
        return signedIn();
      }
      const res = await api<{ mfa_required: boolean; mfa_token: string }>(`/auth/${mode}`, { method: "POST", json: form });
      if (res.mfa_required) {
        setMfaToken(res.mfa_token);
        setBusy(false);
        return;
      }
      signedIn();
    } catch (err) {
      setError(err as ApiError);
      setBusy(false);
    }
  }

  if (mfaToken)
    return (
      <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
        {error && <ErrorNote error={error} />}
        <Field
          label="Mã xác thực 6 số"
          name="code"
          inputMode="numeric"
          autoComplete="one-time-code"
          autoFocus
          hint="Mở app Google Authenticator hoặc app xác thực bạn đã cài"
        />
        <Button variant="primary" type="submit" busy={busy} className="mt-1 h-10">
          Xác nhận
        </Button>
      </form>
    );

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
      {mode === "login" && (
        <Link href="/forgot-password" className="-mt-2 self-end text-sm text-muted underline">
          Quên mật khẩu?
        </Link>
      )}
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

export function ForgotForm() {
  const [error, setError] = useState<ApiError | null>(null);
  const [sentTo, setSentTo] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const email = String(new FormData(e.currentTarget).get("email") ?? "");
    setBusy(true);
    setError(null);
    try {
      await api("/auth/forgot-password", { method: "POST", json: { email } });
      setSentTo(email);
    } catch (err) {
      setError(err as ApiError);
    }
    setBusy(false);
  }

  if (sentTo)
    return (
      <div className="flex flex-col gap-4 text-sm">
        <p>
          Nếu <b>{sentTo}</b> có tài khoản, chúng tôi vừa gửi liên kết đặt lại
          mật khẩu tới hộp thư đó. Liên kết hết hạn sau 30 phút; nhớ xem cả thư
          mục Spam.
        </p>
        <Link href="/login" className="font-medium text-ink underline">
          Quay lại đăng nhập
        </Link>
      </div>
    );

  const f = error?.fields ?? {};
  return (
    <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
      {error && !Object.keys(f).length && <ErrorNote error={error} />}
      <Field
        label="Email"
        name="email"
        type="email"
        autoComplete="email"
        required
        error={f.email}
      />
      <Button variant="primary" type="submit" busy={busy} className="mt-1 h-10">
        Gửi liên kết đặt lại
      </Button>
      <p className="text-center text-sm text-muted">
        Nhớ ra rồi?{" "}
        <Link href="/login" className="font-medium text-ink underline">
          Đăng nhập
        </Link>
      </p>
    </form>
  );
}

export function ResetForm() {
  const router = useRouter();
  const token = useSearchParams().get("token") ?? "";
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    if (form.get("password") !== form.get("confirm")) {
      setError(new ApiError(422, "", { confirm: "Hai mật khẩu chưa khớp" }));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api(
        "/auth/reset-password",
        {
          method: "POST",
          json: { token, password: form.get("password") },
        },
      );
      session.clear();
      session.markSignedIn();
      router.replace("/app");
    } catch (err) {
      setError(err as ApiError);
      setBusy(false);
    }
  }

  if (!token)
    return (
      <p className="text-sm">
        Liên kết không đầy đủ.{" "}
        <Link
          href="/forgot-password"
          className="font-medium text-ink underline"
        >
          Gửi lại yêu cầu
        </Link>
      </p>
    );

  const f = error?.fields ?? {};
  return (
    <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
      {error && !Object.keys(f).length && <ErrorNote error={error} />}
      <Field
        label="Mật khẩu mới"
        name="password"
        type="password"
        autoComplete="new-password"
        required
        hint="Tối thiểu 8 ký tự"
        error={f.password}
      />
      <Field
        label="Nhập lại mật khẩu"
        name="confirm"
        type="password"
        autoComplete="new-password"
        required
        error={f.confirm}
      />
      <Button variant="primary" type="submit" busy={busy} className="mt-1 h-10">
        Đặt mật khẩu mới
      </Button>
      {error?.status === 400 && (
        <Link href="/forgot-password" className="text-center text-sm font-medium text-ink underline">
          Gửi lại liên kết
        </Link>
      )}
    </form>
  );
}
