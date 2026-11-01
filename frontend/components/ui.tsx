"use client";

import { Loader2 } from "lucide-react";
import { useId, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

const variants: Record<Variant, string> = {
  primary: "bg-ink text-ground hover:bg-ink/85",
  secondary: "bg-raised text-ink hover:bg-active",
  ghost: "text-muted hover:bg-raised hover:text-ink",
  danger: "text-negative hover:bg-[var(--pill-negative-bg)]",
};

export function Button({
  variant = "secondary",
  busy,
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; busy?: boolean }) {
  return (
    <button
      {...props}
      disabled={props.disabled || busy}
      aria-busy={busy || undefined}
      className={`inline-flex h-9 min-w-9 cursor-pointer items-center justify-center gap-1.5 rounded-[var(--radius-control)] px-4 text-sm font-medium transition-colors duration-150 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`}
    >
      {busy && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

const inputCls =
  "w-full rounded-[var(--radius-input)] border border-control bg-ground px-3 text-sm text-ink placeholder:text-faint focus:border-ink focus:outline-none aria-[invalid=true]:border-negative";

export function Field({
  label,
  error,
  hint,
  textarea,
  rows = 3,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
  hint?: string;
  textarea?: boolean;
  rows?: number;
}) {
  const id = useId();
  const describedBy = [error && `${id}-err`, hint && `${id}-hint`].filter(Boolean).join(" ");
  const common = {
    id,
    "aria-invalid": error ? true : undefined,
    "aria-describedby": describedBy || undefined,
  };
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      {textarea ? (
        <textarea
          {...(props as unknown as InputHTMLAttributes<HTMLTextAreaElement>)}
          {...common}
          rows={rows}
          className={`${inputCls} py-2 leading-relaxed`}
        />
      ) : (
        <input {...props} {...common} className={`${inputCls} h-9`} />
      )}
      {hint && !error && (
        <p id={`${id}-hint`} className="text-xs text-muted">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-err`} className="text-xs text-negative">
          {error}
        </p>
      )}
    </div>
  );
}

export function Select({
  label,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      <select {...props} id={id} className={`${inputCls} h-9`}>
        {children}
      </select>
    </div>
  );
}

const pillTones = {
  neutral: "bg-[var(--pill-neutral-bg)] text-[var(--pill-neutral-ink)]",
  positive: "bg-[var(--pill-positive-bg)] text-[var(--pill-positive-ink)]",
  negative: "bg-[var(--pill-negative-bg)] text-[var(--pill-negative-ink)]",
  warning: "bg-[var(--pill-warning-bg)] text-[var(--pill-warning-ink)]",
  accent: "bg-[var(--pill-accent-bg)] text-[var(--pill-accent-ink)]",
};

export function Pill({ tone = "neutral", children }: { tone?: keyof typeof pillTones; children: ReactNode }) {
  return (
    <span
      className={`inline-flex h-5 flex-none items-center whitespace-nowrap rounded-full px-2 text-xs font-medium ${pillTones[tone]}`}
    >
      {children}
    </span>
  );
}

export function Panel({
  title,
  action,
  children,
  className = "",
}: {
  title?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`min-w-0 rounded-[var(--radius-card)] bg-surface ${className}`}>
      {(title || action) && (
        <header className="flex min-h-14 flex-wrap items-center justify-between gap-3 px-[22px] pt-4">
          {title && <h2 className="text-base font-semibold">{title}</h2>}
          {action}
        </header>
      )}
      <div className="px-[22px] pb-[22px] pt-2">{children}</div>
    </section>
  );
}

export function PageTitle({ title, sub, actions }: { title: string; sub?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-[22px] font-semibold leading-tight">{title}</h1>
        {sub && <p className="mt-1 text-sm text-muted">{sub}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="py-8 text-center">
      <p className="font-medium">{title}</p>
      {children && <div className="mx-auto mt-1 max-w-sm text-sm text-muted">{children}</div>}
    </div>
  );
}

export function ErrorNote({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex items-center justify-between gap-3 rounded-[var(--radius-control)] bg-[var(--pill-negative-bg)] px-3 py-2 text-sm text-[var(--pill-negative-ink)]">
      <span>{error.message}</span>
      {onRetry && (
        <button onClick={onRetry} className="cursor-pointer font-medium underline">
          Thử lại
        </button>
      )}
    </div>
  );
}

export function Skeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3" aria-hidden>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="h-4 animate-pulse rounded-full bg-raised" style={{ width: `${90 - i * 12}%` }} />
      ))}
    </div>
  );
}

export function Initials({ name, size = 32 }: { name: string; size?: number }) {
  // Stable pale tint per person (identity, not data).
  const hue = [...name].reduce((h, c) => (h * 31 + c.charCodeAt(0)) % 360, 7);
  const letters = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(-2)
    .map((w) => w[0]?.toUpperCase())
    .join("");
  return (
    <span
      aria-hidden
      className="inline-flex flex-none items-center justify-center rounded-full text-xs font-semibold"
      style={{
        width: size,
        height: size,
        background: `oklch(0.93 0.035 ${hue})`,
        color: `oklch(0.35 0.06 ${hue})`,
      }}
    >
      {letters || "?"}
    </span>
  );
}

/** Modal sheet: the one surface allowed a shadow, since it truly floats. Esc and the backdrop close it. */
export function Dialog({ title, onClose, children, footer }: { title: string; onClose: () => void; children: ReactNode; footer?: ReactNode }) {
  const id = useId();
  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4" role="dialog" aria-modal aria-labelledby={id}
      onKeyDown={(e) => e.key === "Escape" && onClose()}>
      <button className="absolute inset-0 cursor-default bg-black/70" aria-label="Đóng" onClick={onClose} tabIndex={-1} />
      <div className="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-[var(--radius-sheet)] bg-surface p-6 shadow-2xl shadow-black/60">
        <h2 id={id} className="text-lg font-semibold">{title}</h2>
        <div className="mt-2">{children}</div>
        {footer && <div className="mt-6 flex justify-end gap-2">{footer}</div>}
      </div>
    </div>
  );
}

/** Thin progress bar in the data hue. */
export function Progress({ value, label }: { value: number; label: string }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <span role="progressbar" aria-label={label} aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}
      className="block h-1.5 w-full overflow-hidden rounded-full bg-raised">
      <span className="block h-full rounded-full bg-accent transition-[width] duration-700" style={{ width: `${Math.max(pct, 3)}%` }} />
    </span>
  );
}
