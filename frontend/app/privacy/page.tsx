import type { Metadata } from "next";
import Link from "next/link";
import { LegalPage, Mail, OPERATOR } from "@/components/legal";

export const metadata: Metadata = { title: "Chính sách quyền riêng tư · GrowthPilot AI" };

export default function PrivacyPage() {
  return (
    <LegalPage title="Chính sách quyền riêng tư">
      <section>
        <p>
          GrowthPilot AI là phần mềm giúp cửa hàng trả lời tin nhắn Facebook Messenger, quản lý khách hàng, lịch hẹn và
          tạo nội dung quảng cáo. Trang này giải thích chúng tôi ({OPERATOR}) thu thập dữ liệu gì, dùng để làm gì và
          bạn có quyền gì với dữ liệu của mình.
        </p>
      </section>

      <section>
        <h2>1. Dữ liệu chúng tôi thu thập</h2>
        <p><strong>Khi bạn nhắn tin cho Fanpage của một cửa hàng dùng GrowthPilot:</strong></p>
        <ul>
          <li>Tên hiển thị và mã định danh Facebook mà Facebook cấp cho Page (không phải mật khẩu hay tài khoản của bạn).</li>
          <li>Nội dung tin nhắn bạn gửi cho Page và tin Page trả lời bạn.</li>
          <li>Số điện thoại, email chỉ khi bạn tự cung cấp trong tin nhắn hoặc cho nhân viên cửa hàng.</li>
          <li>Lịch hẹn bạn đặt với cửa hàng và ghi chú chăm sóc do nhân viên cửa hàng nhập.</li>
        </ul>
        <p><strong>Với nhân viên và chủ cửa hàng dùng GrowthPilot:</strong> họ tên, email đăng nhập, thông tin cửa hàng (dịch vụ, giá, chi nhánh) và tài liệu, hình ảnh, video họ tải lên.</p>
      </section>

      <section>
        <h2>2. Chúng tôi dùng dữ liệu để làm gì</h2>
        <ul>
          <li>Hiển thị tin nhắn của bạn cho nhân viên cửa hàng để họ trả lời.</li>
          <li>Dùng AI để hiểu nhu cầu (hỏi giá, đặt lịch…) và gợi ý câu trả lời dựa trên thông tin dịch vụ, giá mà cửa hàng đã nhập.</li>
          <li>Ghi nhận và nhắc lịch hẹn.</li>
          <li>Đăng bài lên Fanpage của cửa hàng khi cửa hàng chọn đăng.</li>
        </ul>
        <p>Chúng tôi không bán dữ liệu, không dùng dữ liệu của bạn để quảng cáo cho bên khác và không gửi tin quảng cáo nếu bạn chưa đồng ý.</p>
      </section>

      <section>
        <h2>3. Bên thứ ba xử lý dữ liệu</h2>
        <p>Để vận hành, một phần dữ liệu được xử lý bởi các nhà cung cấp sau, chỉ trong phạm vi cần thiết:</p>
        <ul>
          <li><strong>Meta (Facebook):</strong> nhận và gửi tin nhắn Messenger, đăng bài lên Fanpage.</li>
          <li><strong>Google (Gemini) và Groq:</strong> mô hình AI đọc nội dung hội thoại để gợi ý câu trả lời. Số điện thoại và email được che đi trước khi gửi cho AI.</li>
          <li><strong>Supabase:</strong> lưu cơ sở dữ liệu (máy chủ tại Nhật Bản).</li>
          <li><strong>Cloudflare:</strong> lưu tệp hình ảnh, video và bảo vệ kết nối.</li>
          <li><strong>Langfuse:</strong> ghi nhật ký kỹ thuật của các lần gọi AI để kiểm tra chất lượng.</li>
        </ul>
      </section>

      <section>
        <h2>4. Lưu trữ và bảo mật</h2>
        <p>
          Dữ liệu được truyền qua kết nối mã hoá (HTTPS). Mã truy cập Fanpage được mã hoá khi lưu. Mỗi cửa hàng chỉ xem được
          dữ liệu của chính cửa hàng đó, và quyền của từng nhân viên được giới hạn theo vai trò.
        </p>
        <p>
          Trang giới thiệu và trang đăng ký dùng Meta Pixel để đo hiệu quả quảng cáo của GrowthPilot (lượt xem trang,
          đăng ký, bắt đầu dùng thử); chúng tôi không gửi tin nhắn hay dữ liệu khách của cửa hàng cho Pixel.
        </p>
        <p>
          Chúng tôi giữ dữ liệu trong thời gian cửa hàng còn sử dụng dịch vụ. Dự án bị xoá được giữ trong thùng rác 30 ngày rồi xoá hẳn.
        </p>
      </section>

      <section>
        <h2>5. Quyền của bạn</h2>
        <ul>
          <li><strong>Ngừng nhận tin:</strong> nhắn “dừng nhắn” hoặc “không nhận tin” cho Page. Hệ thống sẽ ngừng mọi tin tự động gửi cho bạn.</li>
          <li><strong>Xem, sửa hoặc xoá dữ liệu:</strong> làm theo <Link href="/data-deletion" className="font-medium text-ink underline">hướng dẫn xoá dữ liệu</Link> hoặc gửi email tới <Mail />.</li>
        </ul>
      </section>

      <section>
        <h2>6. Liên hệ</h2>
        <p>Mọi câu hỏi về quyền riêng tư, vui lòng gửi email tới <Mail />. Chúng tôi phản hồi trong vòng 7 ngày làm việc.</p>
      </section>

      <section lang="en" className="rounded-[var(--radius-card)] bg-surface p-5 text-sm text-muted">
        <h2 className="text-ink">English summary</h2>
        <p>
          GrowthPilot AI helps spas answer Facebook Messenger messages and manage customers and bookings. When you message
          a business&apos;s Page we store your Facebook display name, page-scoped ID, the messages exchanged, and any phone number or
          email you choose to share. We use them only to let the business reply (with AI-suggested answers), manage your bookings and
          publish the business&apos;s own posts. Processors: Meta, Google Gemini, Groq (phone numbers and emails are masked before AI
          processing), Supabase, Cloudflare and Langfuse. We never sell data. Reply “stop” to the Page to stop automated
          messages. To access or delete your data, see <Link href="/data-deletion" className="underline">Data deletion</Link> or
          email <Mail />.
        </p>
      </section>
    </LegalPage>
  );
}
