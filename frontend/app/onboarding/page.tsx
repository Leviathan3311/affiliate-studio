"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { AuthCard } from "@/components/auth-form";
import { Button, ErrorNote, Field } from "@/components/ui";
import { api, ApiError, session } from "@/lib/api";

export default function Onboarding() {
  const router = useRouter();
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
      router.replace("/app/settings?tab=brand");
    } catch (err) {
      setError(err as ApiError);
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Thông tin spa của bạn" sub="Mỗi spa có dữ liệu riêng; bạn có thể mời nhân viên sau.">
      <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
        {error && !error.fields.name && <ErrorNote error={error} />}
        <Field label="Tên spa" name="name" required placeholder="Ví dụ: Lotus Spa Quận 3" error={error?.fields.name} />
        <Button variant="primary" type="submit" busy={busy} className="h-10">
          Tạo workspace
        </Button>
      </form>
    </AuthCard>
  );
}
