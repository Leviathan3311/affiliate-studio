# Bán GrowthPilot và chạy quảng cáo Facebook, Instagram

Kế hoạch là thử thị trường trước:
1. Trang giới thiệu cho dùng thử 14 ngày.
2. Hết hạn thì khách chuyển khoản 499.000đ/tháng.
3. Bạn gia hạn bằng tay.
4. Quảng cáo do chính GrowthPilot làm, bạn chạy trong Meta Ads Manager.

## 1. Thu tiền

Trong `backend/.env`, điền tài khoản nhận tiền rồi khởi động lại API:

```
BANK_BIN=970436            # mã NAPAS: 970436 Vietcombank, 970422 MB, 970407 Techcombank, 970418 BIDV, 970415 VietinBank, 970416 ACB
BANK_ACCOUNT=0123456789
BANK_ACCOUNT_NAME=NGUYEN VAN A
PLAN_PRICE_VND=499000
TRIAL_DAYS=14
PLATFORM_ADMIN_EMAILS=["email-dang-nhap-cua-ban@gmail.com"]
```

Trang **Gói & thanh toán** sẽ hiện mã VietQR, kèm nội dung chuyển khoản riêng cho từng cửa hàng (dạng `GP 1A2B3C4D`).

Khi tiền về:
1. Mở trang **Quản trị** trong app.
2. Tìm theo nội dung chuyển khoản.
3. Bấm **Gia hạn**, nhập số tháng và số tiền đã nhận.

Cửa hàng hết hạn vẫn đăng nhập và xem được trang thanh toán. Tin nhắn khách vẫn được lưu, chỉ AI tạm ngừng trả lời.

## 2. Meta Pixel

1. Vào **Meta Events Manager → Connect data sources → Web**, đặt tên `GrowthPilot` rồi chép **Pixel ID** (một dãy số).
2. Build web kèm Pixel và deploy:

   ```bash
   cd frontend && NEXT_PUBLIC_META_PIXEL_ID=<pixel-id> NEXT_PUBLIC_API_URL=https://api.growthpilot-spa.online npm run build && npx wrangler deploy && npm run build
   ```

Trang tự gửi ba sự kiện:
- `PageView` khi có người xem trang.
- `CompleteRegistration` khi tạo tài khoản xong.
- `StartTrial` khi tạo cửa hàng xong.

## 3. Làm quảng cáo bằng chính GrowthPilot

1. Tạo một cửa hàng mới tên **GrowthPilot**, loại hình kinh doanh "Phần mềm cho cửa hàng".
2. Trong **Sản phẩm, dịch vụ & giá**, thêm một dịch vụ "Gói hàng tháng", giá 499.000đ, ưu đãi "Dùng thử 14 ngày miễn phí".
3. Kết nối Fanpage GrowthPilot (và Instagram nếu có).
4. Tạo dự án quảng cáo. Ví dụ brief: *"Video 30 giây cho chủ quán cafe, shop quần áo, tiệm hoa: khách nhắn Facebook lúc nửa đêm vẫn được trả lời đúng giá; dùng thử 14 ngày miễn phí"*.
5. Chọn kịch bản, tạo ảnh và video, rồi đăng lên Fanpage và Instagram.

Ảnh dùng FLUX.2 klein 4B, có giấy phép Apache-2.0 nên được dùng để bán dịch vụ. Đừng dùng lại video cũ làm bằng bản 9B (giấy phép phi thương mại).

## 4. Chạy quảng cáo trong Ads Manager

- **Tài khoản quảng cáo:** vào business.facebook.com → Tài khoản quảng cáo → thêm phương thức thanh toán (thẻ hoặc ví MoMo). Tài khoản mới có hạn mức chi tiêu thấp lúc đầu.
- **Chiến dịch:** mục tiêu **Doanh số (Sales)** hoặc **Khách tiềm năng (Leads)**. Chuyển đổi chọn **Website**, sự kiện `CompleteRegistration`. Khi đã có khoảng 50 người đăng ký mỗi tuần, đổi sang `StartTrial`.
- **Đích đến:** `https://app.growthpilot-spa.online/?utm_source=facebook&utm_campaign=<tên>`.
- **Đối tượng thử nghiệm:**
  - Việt Nam, 22–50 tuổi.
  - Hành vi "Quản trị viên Trang Facebook" (Facebook Page admins).
  - Sở thích: kinh doanh nhỏ, bán hàng online, quán cafe, thời trang.
- **Ngân sách:** 100.000–200.000đ/ngày cho mỗi nhóm quảng cáo, chạy 5–7 ngày trước khi đánh giá.
- **Nội dung:** dùng video Reels 9:16 từ bước 3 và chạy 2–3 mẫu cùng lúc để so sánh.
- **Đo:** số người đăng ký, số cửa hàng tạo xong, và sau 14 ngày là bao nhiêu cửa hàng chuyển khoản. Chi phí mỗi khách trả tiền nên nhỏ hơn khoảng ba tháng phí (1,5 triệu).

## 5. Tên miền

`growthpilot-spa.online` có chữ "spa", trong khi sản phẩm giờ dành cho mọi cửa hàng. Nên mua một tên miền trung tính rồi trỏ web và API sang đó, trước khi chi nhiều tiền quảng cáo.
