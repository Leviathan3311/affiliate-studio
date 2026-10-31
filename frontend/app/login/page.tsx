import { AuthCard, AuthForm } from "@/components/auth-form";

export default function LoginPage() {
  return (
    <AuthCard title="Đăng nhập" sub="Vào hộp thư, khách hàng và lịch hẹn của spa.">
      <AuthForm mode="login" />
    </AuthCard>
  );
}
