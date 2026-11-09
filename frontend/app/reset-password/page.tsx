import { Suspense } from "react";
import { AuthCard, ResetForm } from "@/components/auth-form";

export const metadata = { referrer: "no-referrer" };

export default function ResetPasswordPage() {
  return (
    <AuthCard title="Đặt mật khẩu mới" sub="Chọn mật khẩu mới cho tài khoản của bạn.">
      <Suspense>
        <ResetForm />
      </Suspense>
    </AuthCard>
  );
}
