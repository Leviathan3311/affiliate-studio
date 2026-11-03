# Đưa app Meta lên Live để GrowthPilot trả lời mọi khách

Khi app Meta còn ở chế độ Development, chỉ những tài khoản có vai trò trong app (Admin, Developer, Tester) mới nhắn được tới GrowthPilot. Muốn nhận và trả lời tin của mọi khách, cần làm đủ các bước dưới đây theo thứ tự.

## 0. Điều kiện trước khi nộp

| Việc | Ai làm | Trạng thái |
|---|---|---|
| Web chạy công khai tại `https://growthpilot-spa.online` (để Meta mở được 2 trang chính sách) | Dev | Chưa: tên miền chưa có DNS |
| API và worker chạy 24/7, không phụ thuộc máy Mac | Dev | Chưa: đang chạy trên Mac qua tunnel |
| Email liên hệ có người đọc (mặc định `privacy@growthpilot-spa.online`, đổi bằng `NEXT_PUBLIC_CONTACT_EMAIL`) | Chủ app | Chưa |
| Page đã kết nối trong GrowthPilot (Cài đặt → Facebook Page) | Chủ spa | Chưa |
| `META_DRY_RUN=false` trong `backend/.env` | Dev | Xong |

## 1. Điền thông tin app

Meta for Developers → app → **App settings → Basic**:

- **Privacy Policy URL:** `https://growthpilot-spa.online/privacy`
- **User data deletion:** chọn *Data deletion instructions URL*, điền `https://growthpilot-spa.online/data-deletion`
- **App icon** 1024×1024, **Category:** Business and pages
- **App domains:** `growthpilot-spa.online`

## 2. Xác minh doanh nghiệp (Business Verification)

Meta Business Suite → **Settings → Business info → Business verification**. Cần giấy phép kinh doanh (hoặc giấy tờ đăng ký hộ kinh doanh), địa chỉ, số điện thoại và tên miền hoặc email theo tên miền để nhận mã xác nhận. Tên doanh nghiệp phải khớp với "Đơn vị vận hành" trên trang chính sách (`NEXT_PUBLIC_OPERATOR_NAME`).

## 3. Xin quyền nâng cao (Advanced Access)

**App Review → Permissions and Features**, bấm *Request advanced access* cho từng quyền dưới đây. Phần mô tả có thể dán nguyên văn (Meta đọc tiếng Anh):

| Quyền | Mô tả để dán |
|---|---|
| `pages_messaging` | GrowthPilot AI is an inbox for spas. When a customer messages the spa's Facebook Page, the message appears in GrowthPilot; staff read an AI-suggested reply, edit it if needed and send it back through the Send API. Messages are only sent within the 24-hour standard messaging window, in reply to the customer. |
| `pages_manage_metadata` | Used once when the spa connects its Page, to subscribe the Page to the `messages` webhook so customer messages reach the spa's GrowthPilot inbox. |
| `pages_show_list` | Lets the spa owner pick which of the Pages they manage to connect to GrowthPilot. |
| `pages_read_engagement` | Reads the connected Page's name and basic information to label the inbox and the publishing calendar. |
| `pages_manage_posts` | The spa approves an image or video created in GrowthPilot and publishes it to its own Page, now or at a scheduled time. Nothing is posted without the spa's approval. |
| `instagram_basic` | Reads the username of the Instagram professional account linked to the spa's Page, so the spa can choose it as a publishing destination. |
| `instagram_content_publish` | The spa approves an image or video created in GrowthPilot and publishes it to its own Instagram account as a photo or Reel, now or at a scheduled time. Nothing is posted without the spa's approval. |

## 4. Quay video minh hoạ (một video cho mỗi quyền, hoặc một video dài đủ các bước)

Quay màn hình, có thể nói hoặc chèn chữ tiếng Anh:

1. Đăng nhập GrowthPilot → **Cài đặt → Facebook & Instagram → Kết nối bằng Facebook**, chọn Page, đồng ý các quyền. Page hiện "Đang kết nối". *(pages_show_list, pages_manage_metadata, pages_read_engagement)*
2. Dùng một tài khoản Facebook khác nhắn vào Page: "Cho em hỏi giá massage body". Tin hiện trong **Hộp thư** của GrowthPilot, kèm gợi ý của AI.
3. Bấm **Dùng gợi ý này** → **Gửi**. Mở Messenger của khách: câu trả lời đã tới. *(pages_messaging)*
4. Mở một dự án → **Đăng bài**, chọn ảnh đã duyệt → **Đăng ngay**. Mở Page: bài đã lên. *(pages_manage_posts)*
5. Chọn video đã duyệt, ô **Đăng lên** chọn tài khoản "· Instagram" → **Đăng ngay**. Mở Instagram: Reel đã lên. *(instagram_basic, instagram_content_publish)*

Trong lúc quay, tài khoản khách phải được thêm làm **Tester** (App Roles → Roles), vì app vẫn đang ở Development.

## 5. Gửi duyệt và chuyển Live

- Bấm **Submit for review**. Meta thường trả lời trong vài ngày đến vài tuần; nếu bị từ chối, họ ghi lý do để sửa rồi nộp lại.
- Khi các quyền đã được duyệt: trên thanh trên cùng của app, chuyển **App Mode** từ *Development* sang **Live**.
- Kết nối lại Page trong GrowthPilot nếu được yêu cầu, rồi nhắn thử bằng một tài khoản không có vai trò trong app.

## 6. Sau khi Live

- Giữ **Chỉ gợi ý** (Cài đặt → Giờ trực AI) trong 1–2 tuần đầu, rồi chuyển sang **Tự trả lời khi AI chắc chắn**.
- Yêu cầu xoá dữ liệu gửi tới email liên hệ phải được xử lý trong 30 ngày, như đã cam kết trên trang `/data-deletion`.
