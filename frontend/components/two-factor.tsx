"use client";

import { Check, Copy, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type ClipboardEvent, type KeyboardEvent, type ReactNode } from "react";
import { encode } from "uqr";
import { api, ApiError, session, useApi } from "@/lib/api";
import { LegalLinks } from "./legal";
import { Mark } from "./shell";
import { Button, ErrorNote, Skeleton } from "./ui";

const LENGTH = 6;

/** Full-screen gate: nothing of the app shows until the second factor is done. */
export function TwoFactorScreen({ title, sub, wide, footer, children }: {
  title: string;
  sub: string;
  wide?: boolean;
  footer?: ReactNode;
  children: ReactNode;
}) {
  return (
    <main className="fixed inset-0 z-50 overflow-y-auto bg-ground">
      <div className="mx-auto flex min-h-full w-full max-w-5xl flex-col px-4 py-8 sm:px-8">
        <div className="flex items-center gap-2.5">
          <Mark size={28} />
          <span className="text-base font-semibold">GrowthPilot AI</span>
        </div>
        <section className={`m-auto w-full py-12 ${wide ? "max-w-3xl" : "max-w-md"}`}>
          <div className="mb-6 grid size-14 place-items-center rounded-2xl bg-raised text-ink">
            <ShieldCheck className="size-7" aria-hidden />
          </div>
          <h1 className="text-[28px] font-semibold leading-tight sm:text-[32px]">{title}</h1>
          <p className="mt-2 max-w-xl text-[15px] text-muted">{sub}</p>
          <div className="mt-8">{children}</div>
        </section>
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-muted">
          {footer ?? <span />}
          <LegalLinks />
        </div>
      </div>
    </main>
  );
}

/** Six boxes for a one-time code: typing moves on, backspace moves back, pasting fills all. */
export function CodeInput({ value, onChange, onComplete, disabled, invalid, autoFocus = true }: {
  value: string;
  autoFocus?: boolean;
  onChange: (code: string) => void;
  onComplete?: (code: string) => void;
  disabled?: boolean;
  invalid?: boolean;
}) {
  const boxes = useRef<(HTMLInputElement | null)[]>([]);
  // Keys typed faster than React re-renders must build on each other, not on the last render.
  const current = useRef(value);
  useEffect(() => {
    current.current = value;
  }, [value]);
  // after a wrong code the boxes are cleared and re-enabled: start again from the first one
  const wasDisabled = useRef(disabled);
  useEffect(() => {
    if (wasDisabled.current && !disabled && !value) boxes.current[0]?.focus();
    wasDisabled.current = disabled;
  }, [disabled, value]);

  function set(next: string, focus: number) {
    const code = next.replace(/\D/g, "").slice(0, LENGTH);
    current.current = code;
    onChange(code);
    boxes.current[Math.min(focus, LENGTH - 1)]?.focus();
    if (code.length === LENGTH) onComplete?.(code);
  }

  function key(e: KeyboardEvent<HTMLInputElement>, i: number) {
    const v = current.current;
    if (e.key === "Backspace" && !v[i] && i > 0) {
      e.preventDefault();
      set(v.slice(0, i - 1) + v.slice(i), i - 1);
    } else if (e.key === "ArrowLeft") boxes.current[i - 1]?.focus();
    else if (e.key === "ArrowRight") boxes.current[i + 1]?.focus();
  }

  function paste(e: ClipboardEvent<HTMLInputElement>) {
    e.preventDefault();
    const digits = e.clipboardData.getData("text").replace(/\D/g, "");
    set(digits, digits.length);
  }

  return (
    <div className="flex gap-2 sm:gap-3" role="group" aria-label="Mã 6 số">
      {Array.from({ length: LENGTH }, (_, i) => (
        <input
          key={i}
          ref={(el) => {
            boxes.current[i] = el;
          }}
          value={value[i] ?? ""}
          onChange={(e) => {
            const v = current.current;
            let d = e.target.value.replace(/\D/g, "");
            if (!d) return set(v.slice(0, i) + v.slice(i + 1), i);
            // typed next to the digit already there: keep only the new one
            if (v[i] && d.length === 2) d = d.replace(v[i], "");
            // the phone's one-time-code autofill (or a quick insert) puts several digits into one box
            set(v.slice(0, i) + d + v.slice(i + d.length), i + d.length);
          }}
          onKeyDown={(e) => key(e, i)}
          onPaste={paste}
          onFocus={(e) => e.target.select()}
          inputMode="numeric"
          autoComplete={i === 0 ? "one-time-code" : "off"}
          autoFocus={autoFocus && i === 0}
          maxLength={LENGTH}
          disabled={disabled}
          aria-label={`Số thứ ${i + 1}`}
          aria-invalid={invalid || undefined}
          className={`h-14 w-full min-w-0 max-w-14 rounded-xl border bg-surface text-center text-2xl font-semibold tabular-nums text-ink transition-colors focus:border-ink focus:outline-none disabled:opacity-60 sm:h-16 sm:max-w-16 sm:text-[28px] ${
            invalid ? "border-negative" : value[i] ? "border-control" : "border-border"
          }`}
        />
      ))}
    </div>
  );
}

/** Sign-in step two: the password was right, now the code from the authenticator app. */
export function CodeStep({ mfaToken, onDone, onBack }: { mfaToken: string; onDone: () => void; onBack: () => void }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  async function verify(value = code) {
    if (value.length !== LENGTH || busy) return;
    setBusy(true);
    setError(null);
    try {
      await api("/auth/2fa/verify", { method: "POST", json: { mfa_token: mfaToken, code: value } });
      onDone();
    } catch (err) {
      setError(err as ApiError);
      setCode("");
      setBusy(false);
    }
  }

  return (
    <TwoFactorScreen
      title="Nhập mã xác thực"
      sub="Mở app xác thực trên điện thoại (Google Authenticator, Microsoft Authenticator…) và nhập mã 6 số của GrowthPilot."
      footer={
        <button type="button" onClick={onBack} className="cursor-pointer underline">
          Đăng nhập bằng tài khoản khác
        </button>
      }
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          verify();
        }}
        className="flex flex-col gap-5"
        noValidate
      >
        <CodeInput value={code} onChange={setCode} onComplete={verify} disabled={busy} invalid={!!error} />
        {error && <ErrorNote error={error} />}
        <Button variant="primary" type="submit" busy={busy} disabled={code.length !== LENGTH} className="h-11 w-full max-w-[26rem]">
          Xác nhận
        </Button>
        <p className="text-sm text-faint">Mã đổi sau mỗi 30 giây. Nếu báo sai, đợi mã mới rồi nhập lại.</p>
      </form>
    </TwoFactorScreen>
  );
}

function Qr({ text }: { text: string }) {
  const { data, size } = useMemo(() => encode(text, { border: 0 }), [text]);
  const path = data.flatMap((row, y) => row.map((on, x) => (on ? `M${x} ${y}h1v1h-1z` : ""))).join("");
  return (
    <svg viewBox={`-2 -2 ${size + 4} ${size + 4}`} className="size-48 rounded-xl bg-white sm:size-52" role="img" aria-label="Mã QR để thêm GrowthPilot vào app xác thực">
      <path d={path} fill="#0e0d0c" shapeRendering="crispEdges" />
    </svg>
  );
}

/** Platform admins extend any shop's plan, so the whole app waits until their second factor is on. */
export function EnrolScreen() {
  const setup = useApi<{ secret: string; otpauth_url: string }>("/auth/2fa/setup");
  const [code, setCode] = useState("");
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const key = setup.data?.secret.replace(/(.{4})/g, "$1 ").trim();

  async function enable(value = code) {
    if (!setup.data || value.length !== LENGTH || busy) return;
    setBusy(true);
    setError(null);
    try {
      await api("/auth/2fa/enable", { method: "POST", json: { secret: setup.data.secret, code: value } });
      window.location.reload();
    } catch (err) {
      setError(err as ApiError);
      setCode("");
      setBusy(false);
    }
  }

  async function logout() {
    await api("/auth/logout", { method: "POST" }).catch(() => {});
    session.clear();
    window.location.replace("/login");
  }

  return (
    <TwoFactorScreen
      wide
      title="Bật xác thực hai lớp để tiếp tục"
      sub="Tài khoản quản trị gia hạn được mọi cửa hàng, nên mỗi lần đăng nhập cần thêm mã 6 số từ điện thoại. Làm một lần, mất khoảng một phút."
      footer={
        <button type="button" onClick={logout} className="cursor-pointer underline">
          Đăng xuất
        </button>
      }
    >
      {setup.error ? (
        <ErrorNote error={setup.error} onRetry={setup.reload} />
      ) : !setup.data ? (
        <Skeleton rows={4} />
      ) : (
        <ol className="grid gap-4 md:grid-cols-[auto_1fr]">
          <li className="flex flex-col items-start gap-4 rounded-[var(--radius-sheet)] bg-surface p-6">
            <Step n={1} title="Quét mã bằng app xác thực" />
            <Qr text={setup.data.otpauth_url} />
            <a
              href={setup.data.otpauth_url}
              className="inline-flex h-10 items-center rounded-[var(--radius-control)] bg-raised px-4 text-sm font-medium md:hidden"
            >
              Đang dùng điện thoại? Mở thẳng app
            </a>
            <p className="max-w-52 text-sm text-muted">
              Chưa có app? Cài Google Authenticator hoặc Microsoft Authenticator trên điện thoại.
            </p>
          </li>
          <li className="flex flex-col gap-6 rounded-[var(--radius-sheet)] bg-surface p-6">
            <div className="flex flex-col gap-3">
              <Step n={2} title="Không quét được? Nhập khoá này" />
              <div className="flex items-center gap-2">
                <code className="min-w-0 flex-1 select-all rounded-[var(--radius-control)] bg-raised px-3 py-2.5 font-mono text-[15px] tracking-wider break-all">
                  {key}
                </code>
                <Button
                  type="button"
                  aria-label="Chép khoá"
                  className="h-11 shrink-0"
                  onClick={() => {
                    navigator.clipboard.writeText(setup.data!.secret).then(() => setCopied(true));
                  }}
                >
                  {copied ? <Check className="size-4" aria-hidden /> : <Copy className="size-4" aria-hidden />}
                  {copied ? "Đã chép" : "Chép"}
                </Button>
              </div>
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                enable();
              }}
              className="flex flex-col gap-4"
              noValidate
            >
              <Step n={3} title="Nhập mã 6 số app hiện ra" />
              <CodeInput value={code} onChange={setCode} onComplete={enable} disabled={busy} invalid={!!error} autoFocus={false} />
              {error && <ErrorNote error={error} />}
              <Button variant="primary" type="submit" busy={busy} disabled={code.length !== LENGTH} className="h-11 w-full">
                Bật xác thực hai lớp
              </Button>
            </form>
          </li>
        </ol>
      )}
    </TwoFactorScreen>
  );
}

function Step({ n, title }: { n: number; title: string }) {
  return (
    <h2 className="flex items-center gap-3 text-[15px] font-semibold">
      <span className="grid size-7 shrink-0 place-items-center rounded-full bg-raised text-sm tabular-nums">{n}</span>
      {title}
    </h2>
  );
}
