"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { AuthCard } from "@/components/auth-form";
import { Button, ErrorNote, Skeleton } from "@/components/ui";
import { api, ApiError, session } from "@/lib/api";
import { ROLE } from "@/lib/format";
import type { Role } from "@/lib/types";

export default function InvitePage() {
  return (
    <Suspense>
      <Invite />
    </Suspense>
  );
}

function Invite() {
  const router = useRouter();
  const token = useSearchParams().get("token") ?? "";
  const [info, setInfo] = useState<{ shop: string; email: string; role: Role } | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
  const here = `/invite?token=${encodeURIComponent(token)}`;

  useEffect(() => {
    setSignedIn(!!session.token()); // after hydration: the static page is rendered signed out
    api<{ shop: string; email: string; role: Role }>(`/auth/invites/${encodeURIComponent(token)}`)
      .then(setInfo)
      .catch((e) => setError(e as ApiError));
  }, [token]);

  async function accept() {
    setBusy(true);
    setError(null);
    try {
      const { workspace_id } = await api<{ workspace_id: string }>("/auth/invites/accept", { method: "POST", json: { token } });
      session.setWorkspace(workspace_id);
      router.replace("/app");
    } catch (e) {
      setError(e as ApiError);
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Lời mời tham gia" sub="Cùng quản lý một cửa hàng trên GrowthPilot.">
      {error && <ErrorNote error={error} />}
      {!info && !error && <Skeleton rows={2} />}
      {info && (
        <div className="flex flex-col gap-4 text-sm">
          <p>
            Bạn được mời vào <b>{info.shop}</b> với vai trò <b>{ROLE[info.role]}</b>. Lời mời dành cho <b>{info.email}</b>.
          </p>
          {signedIn ? (
            <Button variant="primary" className="h-10" busy={busy} onClick={accept}>
              Nhận lời mời
            </Button>
          ) : (
            <>
              <Link href={`/register?next=${encodeURIComponent(here)}`} className="inline-flex h-10 items-center justify-center rounded-[var(--radius-control)] bg-ink font-medium text-ground">
                Tạo tài khoản bằng {info.email}
              </Link>
              <Link href={`/login?next=${encodeURIComponent(here)}`} className="text-center text-muted underline">
                Đã có tài khoản? Đăng nhập
              </Link>
            </>
          )}
        </div>
      )}
    </AuthCard>
  );
}
