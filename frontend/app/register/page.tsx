import { AuthCard, AuthForm } from "@/components/auth-form";

export default function RegisterPage() {
  return (
    <AuthCard title="Tạo tài khoản" sub="Bắt đầu với một spa, kết nối Facebook Page sau.">
      <AuthForm mode="register" />
    </AuthCard>
  );
}
