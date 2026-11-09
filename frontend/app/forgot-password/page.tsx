import { AuthCard, ForgotForm } from "@/components/auth-form";

export default function ForgotPasswordPage() {
  return (
    <AuthCard title="Quên mật khẩu" sub="Nhập email đã đăng ký, chúng tôi gửi liên kết đặt mật khẩu mới.">
      <ForgotForm />
    </AuthCard>
  );
}
