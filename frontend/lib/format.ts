import type { BookingStatus, Intent, LeadStatus, Role } from "./types";

export const vnd = (n: number | null | undefined) =>
  n == null ? "—" : `${n.toLocaleString("vi-VN")}đ`;

export const pct = (r: number | null | undefined) =>
  r == null ? "—" : `${(r * 100).toLocaleString("vi-VN", { maximumFractionDigits: 1 })}%`;

export function ago(iso: string | null | undefined): string {
  if (!iso) return "—";
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 1) return "Vừa xong";
  if (mins < 60) return `${mins} phút`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours} giờ`;
  const days = Math.round(hours / 24);
  return days === 1 ? "Hôm qua" : `${days} ngày`;
}

export const time = (iso: string) =>
  new Date(iso).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });

export const dateTime = (iso: string) =>
  new Date(iso).toLocaleString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "2-digit",
  });

export const INTENT: Record<Intent, string> = {
  price_inquiry: "Hỏi giá",
  service_inquiry: "Hỏi dịch vụ",
  booking_request: "Muốn đặt lịch",
  promotion_inquiry: "Hỏi ưu đãi",
  location_inquiry: "Hỏi địa chỉ",
  complaint: "Khiếu nại",
  other: "Khác",
  spam: "Spam",
};

export const LEAD: Record<LeadStatus, string> = {
  new: "Mới",
  engaged: "Đang trao đổi",
  interested: "Quan tâm",
  qualified: "Tiềm năng cao",
  booking_pending: "Chờ chốt lịch",
  booked: "Đã đặt lịch",
  not_interested: "Không quan tâm",
  opted_out: "Từ chối nhận tin",
};

export const BOOKING: Record<BookingStatus, string> = {
  pending: "Chờ xác nhận",
  confirmed: "Đã xác nhận",
  arrived: "Đã đến",
  completed: "Hoàn tất",
  cancelled: "Đã huỷ",
  no_show: "Không đến",
};

export const ROLE: Record<Role, string> = {
  owner: "Chủ spa",
  admin: "Quản trị",
  marketing: "Marketing",
  sales: "Tư vấn / Sales",
  branch_manager: "Quản lý chi nhánh",
};

export const FLAG: Record<string, string> = {
  unverified_price: "AI nhắc tới giá không có trong bảng giá",
  non_vietnamese_output: "Câu trả lời có ký tự ngoài tiếng Việt",
  llm_unavailable: "AI tạm thời không phản hồi (hết hạn mức hoặc lỗi mạng)",
  invalid_ai_output: "AI trả lời chưa trọn vẹn",
  agent_error: "Lỗi khi phân tích hội thoại",
};

export const POLICY_REASON: Record<string, string> = {
  ok: "Được phép gửi",
  customer_opted_out: "Khách đã yêu cầu dừng nhận tin",
  automation_paused: "Tự động hoá đang tạm dừng cho khách này",
  outside_24h_window: "Đã quá 24 giờ kể từ tin nhắn cuối của khách (quy định của Facebook)",
  marketing_opt_in_required: "Cần khách đồng ý nhận tin marketing",
  quiet_hours: "Ngoài giờ hoạt động — sẽ xử lý vào đầu ca",
  unknown_purpose: "Mục đích gửi không hợp lệ",
};

export const OBJECTIVE: Record<string, string> = {
  promote_service: "Quảng bá dịch vụ",
  opening: "Khai trương",
  seasonal_offer: "Ưu đãi theo mùa",
  new_customers: "Thu hút khách mới",
  retention: "Kéo khách cũ quay lại",
};

export const ARTIFACT_STATUS: Record<string, string> = {
  generating: "Đang tạo",
  ready: "Sẵn sàng xem",
  selected: "Đã chọn",
  approved: "Đã duyệt",
  failed: "Lỗi",
  archived: "Đã lưu trữ",
};

export const INPUT_ROLE: Record<string, string> = {
  brief: "Brief / tài liệu",
  logo: "Logo",
  product: "Ảnh sản phẩm",
  facility: "Ảnh cơ sở",
  staff: "Nhân viên / người mẫu",
  reference: "Ảnh tham chiếu",
  source_video: "Video nguồn",
  other: "Khác",
};

export const LEAD_SOURCE: Record<string, string> = {
  messenger: "Messenger",
  manual: "Nhập tay",
};

export const PUBLISH_STATUS: Record<string, string> = {
  scheduled: "Đã lên lịch",
  publishing: "Đang đăng",
  published: "Đã đăng",
  failed: "Lỗi",
  cancelled: "Đã huỷ",
};

export const bytes = (n: number) =>
  n < 1024 ** 2 ? `${Math.max(1, Math.round(n / 1024))} KB` : n < 1024 ** 3 ? `${(n / 1024 ** 2).toFixed(1)} MB` : `${(n / 1024 ** 3).toFixed(2)} GB`;
