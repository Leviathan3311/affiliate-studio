"use client";

import { ErrorNote, PageTitle, Panel, Pill, Skeleton } from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { useApi } from "@/lib/api";
import { vnd } from "@/lib/format";
import type { Billing } from "@/lib/types";

const STATUS = {
  trial: ["Đang dùng thử", "neutral"],
  active: ["Đang hoạt động", "positive"],
  expired: ["Đã hết hạn", "negative"],
} as const;

export default function BillingPage() {
  const { workspace } = useWorkspace();
  const { data, error, reload } = useApi<Billing>("/billing");
  if (error) return <ErrorNote error={error} onRetry={reload} />;
  if (!data) return <Skeleton rows={6} />;
  const [label, tone] = STATUS[data.status];
  const until = new Date(data.access_until).toLocaleDateString("vi-VN");
  const t = data.transfer;
  return (
    <>
      <PageTitle title="Gói & thanh toán" sub={`Cửa hàng ${workspace.name}`} />
      <div className="grid max-w-4xl gap-6 lg:grid-cols-2">
        <Panel title="Gói hiện tại" action={<Pill tone={tone}>{label}</Pill>}>
          <p className="text-3xl font-semibold">
            {vnd(data.price_vnd)}
            <span className="text-base font-normal text-muted"> / tháng</span>
          </p>
          <p className="mt-2 text-sm">
            {data.status === "expired" ? "Hết hạn từ" : "Dùng được đến hết"} <b>{until}</b>.
          </p>
          <ul className="mt-4 flex flex-col gap-1.5 text-sm text-muted">
            <li>AI trả lời tin nhắn Facebook Messenger theo bảng giá của bạn</li>
            <li>Quản lý khách hàng, lịch hẹn, nhiều chi nhánh và nhân viên</li>
            <li>AI nghiên cứu, viết kịch bản, làm ảnh và video quảng cáo</li>
            <li>Đăng bài lên Facebook và Instagram theo lịch</li>
          </ul>
          {data.status === "expired" && (
            <p className="mt-4 text-sm">
              Trong lúc hết hạn, tin nhắn của khách vẫn được lưu nhưng AI tạm ngừng trả lời. Gia hạn xong là dùng
              tiếp ngay, không mất dữ liệu.
            </p>
          )}
        </Panel>
        <Panel title="Gia hạn bằng chuyển khoản">
          {t.account ? (
            <div className="flex flex-col gap-4 sm:flex-row lg:flex-col xl:flex-row">
              {t.qr_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={t.qr_url}
                  alt={`Mã VietQR chuyển ${vnd(data.price_vnd)} với nội dung ${t.content}`}
                  className="w-48 flex-none rounded-lg bg-white p-2"
                />
              )}
              <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5 text-sm">
                <dt className="text-muted">Số tài khoản</dt>
                <dd className="font-medium">{t.account}</dd>
                <dt className="text-muted">Chủ tài khoản</dt>
                <dd>{t.account_name}</dd>
                <dt className="text-muted">Số tiền</dt>
                <dd>{vnd(data.price_vnd)} / tháng</dd>
                <dt className="text-muted">Nội dung</dt>
                <dd className="font-mono font-semibold">{t.content}</dd>
              </dl>
            </div>
          ) : (
            <p className="text-sm text-muted">Thông tin chuyển khoản chưa được thiết lập. Vui lòng liên hệ GrowthPilot.</p>
          )}
          <p className="mt-4 text-sm text-muted">
            Ghi đúng nội dung <b className="text-ink">{t.content}</b> để chúng tôi nhận ra cửa hàng của bạn. Muốn trả
            nhiều tháng thì nhân số tiền lên. Gói được gia hạn trong vòng vài giờ làm việc sau khi tiền về.
          </p>
        </Panel>
      </div>
    </>
  );
}
