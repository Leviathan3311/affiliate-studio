"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";
import { AuthCard } from "@/components/auth-form";
import { Button, ErrorNote, Field } from "@/components/ui";
import { track } from "@/components/pixel";
import { api, ApiError, session } from "@/lib/api";

export default function OnboardingPage() {
  return (
    <Suspense>
      <Onboarding />
    </Suspense>
  );
}

function Onboarding() {
  const router = useRouter();
  const params = useSearchParams();
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    try {
      const ws = await api<{ id: string }>("/workspaces", {
        method: "POST",
        json: Object.fromEntries(new FormData(e.currentTarget)),
      });
      session.setWorkspace(ws.id);
      track("StartTrial", { value: 0, currency: "VND" });
      router.replace("/app/settings?tab=brand");
    } catch (err) {
      setError(err as ApiError);
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Thông tin cửa hàng của bạn" sub="Mỗi cửa hàng có dữ liệu riêng; bạn có thể mời nhân viên sau.">
      <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
        {error && !error.fields.name && <ErrorNote error={error} />}
        <Field label="Tên cửa hàng" name="name" required placeholder="Ví dụ: Mây Nail Quận 3"
          defaultValue={params.get("shop") ?? ""} error={error?.fields.name} />
        <Field
          label="Loại hình kinh doanh"
          name="industry"
          defaultValue={params.get("industry") ?? ""}
          placeholder="Spa, tiệm nail, quán cafe, shop thời trang…"
          hint="Để AI tư vấn và viết quảng cáo đúng ngành của bạn"
          error={error?.fields.industry}
        />
        <Button variant="primary" type="submit" busy={busy} className="h-10">
          Bắt đầu dùng thử 14 ngày
        </Button>
        <Link href="/app" className="text-center text-sm text-muted underline">
          Quay lại
        </Link>
      </form>
    </AuthCard>
  );
}
