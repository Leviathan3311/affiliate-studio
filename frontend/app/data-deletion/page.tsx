import type { Metadata } from "next";
import { LegalPage, Mail } from "@/components/legal";

export const metadata: Metadata = { title: "Xoá dữ liệu · GrowthPilot AI" };

export default function DataDeletionPage() {
  return (
    <LegalPage title="Hướng dẫn xoá dữ liệu">
      <section>
        <p>
          Nếu bạn đã nhắn tin cho Fanpage của một spa dùng GrowthPilot AI, bạn có thể yêu cầu xoá toàn bộ dữ liệu của mình
          bất cứ lúc nào.
        </p>
      </section>

      <section>
        <h2>Cách yêu cầu</h2>
        <ul>
          <li>Gửi email tới <Mail /> với tiêu đề “Xoá dữ liệu”.</li>
          <li>Ghi tên Facebook bạn dùng để nhắn tin và tên Fanpage (spa) bạn đã nhắn.</li>
          <li>Nếu đã đặt lịch, ghi thêm số điện thoại đã dùng khi đặt để chúng tôi tìm đúng hồ sơ.</li>
        </ul>
      </section>

      <section>
        <h2>Chúng tôi sẽ xoá</h2>
        <ul>
          <li>Hồ sơ khách hàng: tên, số điện thoại, email, ghi chú.</li>
          <li>Toàn bộ tin nhắn giữa bạn và Fanpage được lưu trong GrowthPilot.</li>
          <li>Lịch hẹn và lịch sử chăm sóc gắn với bạn.</li>
        </ul>
        <p>
          Việc xoá hoàn tất trong vòng 30 ngày kể từ khi nhận yêu cầu và chúng tôi sẽ email xác nhận cho bạn. Tin nhắn vẫn
          còn trong ứng dụng Messenger của bạn và của Fanpage, vì phần đó do Facebook lưu; bạn có thể tự xoá trong Messenger.
        </p>
      </section>

      <section>
        <h2>Chỉ muốn ngừng nhận tin?</h2>
        <p>Nhắn “dừng nhắn” hoặc “không nhận tin” cho Fanpage. Hệ thống sẽ ngừng ngay mọi tin tự động gửi cho bạn.</p>
      </section>

      <section lang="en" className="rounded-[var(--radius-card)] bg-surface p-5 text-sm text-muted">
        <h2 className="text-ink">Data deletion (English)</h2>
        <p>
          To delete the data GrowthPilot AI holds about you, email <Mail /> with the subject “Data deletion”, your Facebook name
          and the Page you messaged. We delete your customer profile, stored messages and bookings within 30 days and confirm
          by email. To only stop automated messages, reply “stop” to the Page.
        </p>
      </section>
    </LegalPage>
  );
}
