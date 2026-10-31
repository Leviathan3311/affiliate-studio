# GrowthPilot AI --- Business Requirements Document (BRD)

**Phiên bản:** 1.6\
**Ngày cập nhật:** 31/10/2026\
**Trạng thái:** Product discovery / MVP planning (bổ sung Project-based AI Creative Workspace, Reusable Generation Style Packs, Dedicated Customer Engagement Agent, Facebook comment/Messenger automation, campaign audience outreach và customer data lifecycle)\
**Thị trường khởi đầu:** Việt Nam\
**Ngành dọc:** Spa và cơ sở chăm sóc sắc đẹp\
**Định vị:** All-in-One AI Marketing & Customer Conversion Automation
for Spas

------------------------------------------------------------------------

## 1. Tóm tắt điều hành

**Trải nghiệm sản phẩm trung tâm:** GrowthPilot vận hành theo mô hình **Project-based AI Creative Workspace**. Người dùng tạo một project cho từng chiến dịch/đợt quảng bá, tải brief, tài liệu, hình ảnh/video tham chiếu và thông tin dịch vụ vào project. AI nghiên cứu, đề xuất nhiều phương án kịch bản; mỗi phương án được lưu thành một item/version có tên dễ nhận biết (ví dụ “Kịch bản A”, “Kịch bản B”, “Kịch bản C”) trong một panel thư viện bên cạnh khu vực chat. Người dùng xem, so sánh, trao đổi và chọn một phương án để chuyển sang tạo ảnh/video. Các creative đầu ra cũng được lưu thành phiên bản riêng trong project. Mọi yêu cầu gửi tới model sinh ảnh/video đều đi qua Prompt Composer để tự động ghép các đoạn mô tả style (Reusable Generation Style Packs) theo cấu hình mặc định của workspace/project/model, trước khi gửi prompt cuối cùng tới model. Sau khi duyệt, người dùng chọn nội dung để xuất bản/đặt lịch. Tất cả tài sản, hội thoại, phiên bản, trạng thái và lịch sử thao tác được giữ trong project cho đến khi người dùng chủ động xóa.

GrowthPilot AI là nền tảng SaaS giúp spa vận hành quy trình marketing và
chuyển đổi khách hàng trên một hệ thống thống nhất. Sản phẩm kết hợp AI
tạo nội dung, quản lý kênh social, hợp nhất hội thoại, CRM, tư vấn khách
hàng, tự động hóa chăm sóc và đặt lịch.

Sản phẩm không nên định vị đơn thuần là một công cụ viết content hoặc
chatbot. Giá trị cốt lõi là kết nối toàn bộ hành trình:

**Dịch vụ spa → Nghiên cứu thị trường/khách hàng/đối thủ/social → Chiến lược marketing → Ý tưởng chiến dịch → Tạo nội dung/creative → Xuất bản + chọn tệp khách đủ điều kiện để outreach → Trả lời comment/Messenger và chăm sóc theo lịch → Thu lead/inbox → Đặt lịch → Ghi nhận doanh thu → Đo lường, tối ưu và quản trị retention dữ liệu.**

### 1.1 Vấn đề kinh doanh

Nhiều spa vừa và nhỏ đang sử dụng nhiều công cụ rời rạc để: - Lên ý
tưởng và sản xuất nội dung. - Đăng bài trên Facebook/Instagram. - Chạy
quảng cáo và thu lead. - Trả lời Messenger, Instagram Direct và bình
luận. - Theo dõi khách hàng bằng Excel hoặc phần mềm CRM/spa riêng. -
Nhắc lịch, chăm sóc lại khách cũ. - Đo hiệu quả marketing và doanh thu.

Dữ liệu bị phân mảnh khiến chủ spa khó biết chiến dịch nào tạo ra khách
hàng và doanh thu. Nhân viên có thể phản hồi chậm, bỏ sót khách tiềm
năng hoặc tư vấn không nhất quán.

### 1.2 Giải pháp

GrowthPilot AI cung cấp một workspace theo từng spa/doanh nghiệp, trong đó: 1. Thu thập thông tin dịch vụ, thương hiệu và mục tiêu. 2. AI nghiên cứu khách hàng, đối thủ, nội dung social và cơ hội thị trường dựa trên nguồn dữ liệu được phép truy cập. 3. AI tổng hợp insight thành chiến lược và ý tưởng chiến dịch. 4. AI tạo nội dung, hình ảnh, video và biến thể. 5. Người dùng duyệt và lên lịch xuất bản. 6. Kết nối social, hợp nhất hội thoại và lead. 7. AI hỗ trợ tư vấn, CRM, follow-up và booking. 8. Đo lường lead, booking, doanh thu để cải thiện chiến dịch tiếp theo.

### 1.3 North Star Metric

**Qualified Bookings Attributed to GrowthPilot AI** --- số lượt đặt lịch
đủ điều kiện có thể quy nguồn về hoạt động được vận hành hoặc hỗ trợ bởi
GrowthPilot AI.

Các chỉ số bổ trợ: - Research-to-approved-campaign conversion; tỷ lệ claim có evidence; usefulness score của report; cost và latency mỗi research run. - Thời gian phản hồi lead đầu tiên. - Tỷ lệ lead được
phản hồi. - Tỷ lệ lead chuyển thành booking. - Tỷ lệ booking đến spa. -
Doanh thu được ghi nhận theo nguồn. - Tỷ lệ workflow automation chạy
thành công. - Số khách hàng trả phí và tỷ lệ duy trì thuê bao.

------------------------------------------------------------------------

## 2. Mục tiêu và phạm vi

### 2.1 Mục tiêu sản phẩm

-   Giảm thời gian tạo và vận hành chiến dịch marketing.
-   Giảm thời gian phản hồi khách hàng trên social.
-   Hạn chế bỏ sót lead và lịch hẹn.
-   Chuẩn hóa chất lượng tư vấn giữa các nhân viên.
-   Giúp chủ spa nhìn thấy mối liên hệ giữa marketing, lead, booking và
    doanh thu.
-   Tạo một sản phẩm SaaS có khả năng thu phí định kỳ tại thị trường
    Việt Nam.

### 2.2 Mục tiêu MVP

MVP phải chứng minh được một vòng lặp giá trị hoàn chỉnh:

1.  Spa tạo workspace và khai báo thương hiệu/dịch vụ.
2.  Kết nối Facebook Page.
3.  Nhận hội thoại hoặc lead từ kênh được Meta cấp quyền.
4.  AI phân loại nhu cầu và hỗ trợ tư vấn.
5.  Lưu thông tin khách vào CRM.
6.  Nhân viên tạo/xác nhận booking.
7.  Chủ spa xem được hiệu quả cơ bản.

Instagram được đưa vào MVP nếu quyền API và tiến độ tích hợp cho phép;
nếu không, triển khai ngay sau khi Facebook flow ổn định.

### 2.3 Ngoài phạm vi MVP

-   Phần mềm kế toán đầy đủ.
-   Quản lý kho, nguyên vật liệu, chấm công và tính lương.
-   POS và quản lý bán lẻ toàn diện.
-   Tự huấn luyện foundation model.
-   Tự động tạo và chạy quảng cáo trả phí hoặc tự tăng ngân sách mà không có phê duyệt của người dùng.
-   Ứng dụng mobile native.
-   White-label đa thương hiệu.
-   Tối ưu ngân sách quảng cáo tự động hoặc tự động tăng ngân sách.
-   Tích hợp toàn diện Google Ads, TikTok và Zalo ngay từ phiên bản đầu.
-   Quản lý hồ sơ điều trị y khoa hoặc đưa ra chẩn đoán.

------------------------------------------------------------------------

## 3. Khách hàng mục tiêu và người dùng

### 3.1 ICP --- Ideal Customer Profile

**Nhóm ưu tiên:** spa nhỏ và vừa tại Việt Nam, có hoạt động marketing
trên Facebook/Instagram, nhận nhiều inbox hoặc lead và cần tăng tỷ lệ
chuyển đổi.

Đặc điểm có thể phù hợp: - Có 1--5 chi nhánh. - Có chủ spa hoặc quản lý
trực tiếp theo dõi marketing. - Có nhân viên tư vấn/chốt lịch. - Đang
chạy quảng cáo hoặc đăng nội dung thường xuyên. - Đang dùng Excel,
Messenger, phần mềm quản lý spa hoặc nhiều công cụ riêng lẻ.

Nhóm mở rộng: - Chuỗi spa. - Beauty clinic/cơ sở thẩm mỹ (cần quy trình
tuân thủ nội dung và phạm vi dịch vụ chặt chẽ hơn). - Agency marketing
chuyên phục vụ spa.

### 3.2 Personas

  -----------------------------------------------------------------------
  Persona                 Nhu cầu                 Khó khăn
  ----------------------- ----------------------- -----------------------
  Chủ spa                 Theo dõi lead, booking, Thiếu dữ liệu tập
                          doanh thu và hiệu quả   trung, phụ thuộc nhân
                          marketing               viên

  Marketing manager       Lên kế hoạch, tạo nội   Tốn thời gian sản xuất
                          dung, quản lý chiến     và báo cáo
                          dịch                    

  Nhân viên tư vấn        Trả lời nhanh, tư vấn   Inbox nhiều, thiếu ngữ
                          đúng dịch vụ, chốt lịch cảnh khách hàng

  Quản lý chi nhánh       Theo dõi lịch hẹn và    Dữ liệu giữa chi nhánh
                          hiệu suất nhân viên     không đồng nhất

  Agency                  Quản lý nhiều spa/khách Khó chuẩn hóa quy trình
                          hàng                    và báo cáo
  -----------------------------------------------------------------------

### 3.3 Jobs To Be Done

-   Khi có chiến dịch mới, tôi muốn tạo nội dung nhanh nhưng đúng thương
    hiệu và dịch vụ.
-   Khi khách nhắn tin, tôi muốn phản hồi nhanh và không bỏ sót khách
    tiềm năng.
-   Khi khách đã quan tâm nhưng chưa đặt lịch, tôi muốn có quy trình
    follow-up phù hợp.
-   Khi khách đặt lịch, tôi muốn đội ngũ nhìn thấy lịch và trạng thái rõ
    ràng.
-   Khi kết thúc chiến dịch, tôi muốn biết chiến dịch tạo ra bao nhiêu
    lead, booking và doanh thu.

------------------------------------------------------------------------

## 4. Định vị và lợi thế cạnh tranh

### 4.1 Định vị

**GrowthPilot AI --- AI Marketing & Sales Automation Platform dành cho
spa Việt Nam.**

Không cạnh tranh bằng một tính năng AI đơn lẻ. Sản phẩm kết hợp: -
Workflow đặc thù ngành spa. - Customer intelligence và CRM. - AI hỗ trợ
tư vấn/chuyển đổi. - Tự động hóa theo sự kiện. - Đo lường từ chiến dịch
đến doanh thu.

### 4.2 Nhóm đối thủ/thay thế

  -----------------------------------------------------------------------
  Nhóm              Ví dụ tham khảo   Thế mạnh          Khoảng trống
                                                        GrowthPilot có
                                                        thể khai thác
  ----------------- ----------------- ----------------- -----------------
  Social            Pancake, Fchat,   Quản lý hội       Nối sâu nội dung
  inbox/chatbot     Harasocial        thoại, phân công, marketing với
                                      chatbot           booking và doanh
                                                        thu

  Phần mềm quản lý  Myspa, KiotViet   Lịch hẹn, khách   Marketing
  spa               Spa, PosApp Spa,  hàng, vận hành    automation và AI
                    TimeSpa, Nano Spa spa               sales xuyên kênh

  Công cụ AI sáng   ChatGPT, Gemini,  Tạo nội dung      Workflow chuyên
  tạo               Canva, CapCut,    nhanh             ngành, dữ liệu
                    công cụ tạo                         khách và
                    ảnh/video                           attribution

  Nền tảng quảng    Meta Ads Manager, Phân phối quảng   Kết nối lead với
  cáo               TikTok Ads        cáo và đo lường   tư vấn, booking
                                      nền tảng          và doanh thu
  -----------------------------------------------------------------------

**Nguyên tắc chiến lược:** không cố thay thế toàn bộ phần mềm quản lý
spa hiện có ở MVP. Tập trung làm lớp marketing, hội thoại, CRM lead và
automation; tích hợp với phần mềm spa khi có nhu cầu và API phù hợp.

### 4.3 Điểm khác biệt cốt lõi

**Campaign-to-Booking Automation:** biến một dịch vụ spa thành chiến
dịch, nội dung, lead, hội thoại tư vấn và booking có thể đo lường.

------------------------------------------------------------------------

## 5. Phạm vi chức năng

### MOD-01 --- Workspace, tài khoản và phân quyền

**Mục tiêu:** mỗi spa/doanh nghiệp có không gian dữ liệu riêng.

Yêu cầu: - Đăng ký, đăng nhập, quên mật khẩu. - Tạo workspace. - Mời
thành viên qua email. - Phân quyền theo vai trò. - Quản lý chi nhánh. -
Tenant isolation: người dùng workspace A không truy cập dữ liệu
workspace B. - Audit log cho thao tác quan trọng.

Vai trò: - Owner: toàn quyền, billing và tích hợp. - Admin: cấu hình
workspace và thành viên. - Marketing Manager/Staff: nội dung, chiến
dịch, báo cáo marketing. - Sales Manager/Staff: hội thoại, lead, CRM,
booking. - Branch Manager: dữ liệu và hoạt động chi nhánh được phân
công.

### MOD-02 --- Brand & Service Profile

Thông tin cấu hình: - Tên thương hiệu, logo, màu sắc, giọng điệu. - Địa
chỉ, hotline, giờ hoạt động, chi nhánh. - Danh mục dịch vụ. - Mô tả,
thời lượng, giá hoặc khoảng giá. - Điều kiện áp dụng khuyến mãi. - FAQ
và chính sách. - Nội dung được phép/không được phép tư vấn.

AI phải sử dụng dữ liệu cấu hình làm nguồn thông tin. Không tự bịa giá,
ưu đãi, thời gian hoặc cam kết kết quả.

### MOD-02A --- Campaign Project Workspace & Asset Library

**Mục tiêu:** biến project thành đơn vị làm việc và lưu trữ trung tâm cho toàn bộ quá trình tạo chiến dịch. Mỗi project là một không gian độc lập, có context, tài liệu đầu vào, research, hội thoại, phương án kịch bản, ảnh/video, version, approval và publishing handoff riêng.

**Tạo project và thu thập input:**
- Người dùng tạo project từ nút “Tạo project mới”; nhập tên, mục tiêu (ví dụ quảng bá dịch vụ, khai trương, ưu đãi theo mùa), dịch vụ, chi nhánh/khu vực, audience, kênh dự kiến và thời gian chiến dịch. Có thể tạo từ template hoặc bắt đầu trống.
- Project wizard chia thành các bước ngắn, có progress indicator và autosave; không bắt buộc người dùng phải điền hết mọi trường mới được tiếp tục.
- Cho phép upload brief, PDF/DOCX, bảng giá, FAQ, hình ảnh sản phẩm/cơ sở/nhân viên/model, logo, video nguồn, ảnh tham chiếu và brand assets. Cho phép kéo-thả nhiều file, xem preview, đổi tên, thêm mô tả/tag và đánh dấu vai trò của asset (logo, reference, product, staff, source video, inspiration…).
- Người dùng xác nhận quyền sử dụng hình ảnh/video đã upload, đặc biệt ảnh khách hàng, nhân viên hoặc người mẫu. Hỗ trợ đánh dấu “không được AI thay đổi” cho logo, mặt/người, sản phẩm hoặc yếu tố nhận diện quan trọng; giới hạn bảo toàn phụ thuộc năng lực model và phải hiển thị cảnh báo khi không thể đảm bảo.
- AI đọc tài liệu và ảnh để tạo Project Context (tóm tắt dịch vụ, thông điệp, brand voice, key facts, constraints, missing information). Người dùng xem và chỉnh sửa context trước khi research/generate. Mọi dữ kiện nhạy cảm như giá, khuyến mãi, thời hạn và cam kết phải truy về nguồn trong project/brand profile.

**Project workspace UI/UX:**
- Desktop bố cục ba vùng: (1) sidebar project navigation; (2) canvas/work area chính; (3) panel “Project Library / Các phương án” bên phải. Chat composer có thể dock ở đáy hoặc mở thành panel tùy bước. Trên tablet/mobile, các panel chuyển thành tab/drawer, ưu tiên canvas và preview.
- Header project hiển thị tên, trạng thái, dung lượng đã dùng/tổng quota, menu quản lý và nút “Xuất bản/Đặt lịch” khi có creative Approved.
- Project navigation gồm Overview, Input & Assets, Research, Scripts, Images, Videos, Publishing và Activity/History. Không hiển thị tất cả mục nếu chưa có dữ liệu; dùng trạng thái empty-state hướng dẫn hành động tiếp theo.
- Panel phương án dùng card/thumbnail gọn, có tên do AI đặt và người dùng đổi được, loại nội dung, ngày tạo, trạng thái (Draft / Ready to review / Selected / Generating / Approved / Archived), version, thời lượng hoặc tỷ lệ khung hình khi phù hợp. Ví dụ: “Kịch bản A — Giải quyết nỗi lo”, “Kịch bản B — Ưu đãi lần đầu”.
- Cho phép pin/favorite, rename, duplicate, compare side-by-side, chọn làm phương án chính, archive và delete. Phương án được chọn có highlight rõ ràng và CTA “Dùng kịch bản này” / “Generate ảnh & video”. Không tự động chọn hoặc generate khi người dùng chưa xác nhận.
- Khi người dùng chọn một phương án, canvas hiển thị nội dung đầy đủ, evidence/insight liên quan, audience, hook, key message, CTA, shot list/storyboard và assets tham chiếu. Có thể trao đổi ngay trên phương án đó; hội thoại được gắn đúng script/version để tránh nhầm lẫn giữa A/B/C.
- Mọi output được lưu tự động vào project; hiển thị toast/indicator “Đã lưu” và trạng thái save. Không để chat response là nơi lưu duy nhất.

**Project lifecycle và quản lý dung lượng:**
- Mỗi workspace có storage quota theo plan; hiển thị usage tổng, mức dùng theo project và loại asset (original uploads, generated images, video renders, documents, versions). Cảnh báo theo ngưỡng cấu hình, ví dụ 70%, 85%, 95% và khi đầy; các ngưỡng có thể thay đổi theo plan.
- Có trang Storage Management cho phép sort theo dung lượng, ngày hoạt động, project; lọc loại asset; xem file lớn và phiên bản cũ.
- Người dùng có thể xóa riêng script, image, video render, upload hoặc version; xóa một nhóm đã chọn; hoặc xóa toàn bộ project. Xóa project phải hiển thị rõ phạm vi ảnh hưởng và tổng dung lượng dự kiến giải phóng, yêu cầu xác nhận lần cuối.
- Khi xóa project, xóa/đánh dấu xóa tất cả dữ liệu thuộc project: project context, uploads, scripts, research reports/sources liên kết, chat sessions/messages, edit plans, generated assets, renders, versions, thumbnails, embeddings, jobs chưa chạy và liên kết publishing chưa phát sinh. Với nội dung đã publish lên nền tảng ngoài, GrowthPilot không thể mặc định xóa bài bên ngoài; cần thông báo rõ và cung cấp link/quy trình xử lý riêng nếu API cho phép.
- Xóa asset không được âm thầm phá vỡ asset đang được dùng ở project khác. MVP nên cấm cross-project reference mặc định hoặc tạo bản tham chiếu có ownership rõ ràng; trước khi xóa phải liệt kê dependency.
- Đề xuất Trash/Recently Deleted với thời gian khôi phục cấu hình được (ví dụ 30 ngày) trước hard delete; cho phép Restore trong thời hạn. Hết hạn hoặc khi user yêu cầu xóa vĩnh viễn, xóa object storage, DB metadata, vector embeddings, cache và derivative files theo deletion workflow. Phải thể hiện rõ trạng thái “đang xóa” cho tác vụ lớn.
- Billing/storage meter tính theo dung lượng thực tế lưu trữ; cần định nghĩa rõ có tính original, generated output, versions, thumbnail và trash hay không. Không tự xóa tài sản của người dùng khi vượt quota; chặn upload/generation mới hoặc yêu cầu nâng gói/dọn dẹp, nhưng vẫn cho phép tải xuống và xóa dữ liệu.

### MOD-03 --- AI Marketing Planner

Đầu vào: - Dịch vụ muốn quảng bá. - Mục tiêu: nhận diện, tương tác, lead, booking, khách quay lại. - Nhóm khách hàng mục tiêu. - Khu vực. - Ngân sách dự kiến (nếu có). - Thời gian chiến dịch. - Research Report đã duyệt (nếu có), insight, evidence và confidence. Cho phép chạy Planner không có report nhưng phải đánh dấu giả định và không giả vờ đã nghiên cứu thị trường.

Đầu ra: - Campaign brief có mục tiêu, audience, positioning, core message. - Ý tưởng và thông điệp chiến dịch. - Content pillars và content angles có liên kết về insight/evidence. - Lịch nội dung gợi ý. - CTA. - Đề xuất kênh và định dạng. - KPI tham khảo và giả định.

Người dùng có thể chỉnh sửa và phê duyệt kế hoạch.

### MOD-03A --- AI Marketing Intelligence & Research Engine

**Mục tiêu:** nghiên cứu trước khi đề xuất chiến dịch hoặc tạo creative. Biến GrowthPilot từ công cụ “nhập dịch vụ → sinh caption/ảnh” thành hệ thống “hiểu thị trường → tìm cơ hội → đề xuất chiến lược → sản xuất → đo lường”. Đây là lớp Intelligence đứng trước AI Marketing Planner và Creative Studio.

**Đầu vào:** Brand & Service Profile; dịch vụ/địa điểm/chi nhánh; mục tiêu chiến dịch; nhóm khách hàng giả định; đối thủ do người dùng cung cấp hoặc hệ thống phát hiện từ nguồn công khai; kênh/nền tảng; thời gian nghiên cứu; dữ liệu social/page insights mà workspace đã cấp quyền.

**Nhóm nghiên cứu:**
- Audience Research: phân khúc khách hàng, nhu cầu, pain points, câu hỏi thường gặp, rào cản/objection, động lực mua và tín hiệu ý định.
- Competitor Research: đối thủ tại khu vực, định vị, dịch vụ/offer công khai, content pillars, format, CTA, điểm mạnh/yếu và khoảng trống nội dung.
- Social Listening: tổng hợp chủ đề/câu hỏi/lời phàn nàn lặp lại từ bài đăng, bình luận và thảo luận công khai hoặc dữ liệu được cấp quyền; phân biệt quan sát với suy luận.
- Trend Research: phát hiện chủ đề, format, hook và nhu cầu đang tăng; phải ghi rõ thời điểm quan sát, phạm vi nguồn và độ tin cậy, không gọi một tín hiệu nhỏ là xu hướng thị trường.
- Content Opportunity: tìm content gap, góc tiếp cận, hook, proof point, format, CTA và câu hỏi cần giải đáp.
- Offer/Local Context: phân tích cách đối thủ truyền thông ưu đãi và bối cảnh địa phương; không tự tạo giá, khuyến mãi hoặc khẳng định nhu cầu nếu không có bằng chứng.

**Ba chế độ nghiên cứu:**
- Quick Insight: tái sử dụng report còn mới hoặc truy vấn gọn cho nhu cầu bài đăng thường ngày; mục tiêu UX 10–30 giây.
- Standard Research: nghiên cứu trước chiến dịch mới; mục tiêu UX 1–3 phút.
- Deep Research: nghiên cứu thị trường/khu vực/chiến dịch quan trọng, nhiều vòng tìm kiếm và kiểm tra chéo; mục tiêu UX 3–10 phút.
Các mốc trên là mục tiêu thiết kế cần benchmark, không phải SLA đã được chứng minh. Cho phép người dùng chọn chế độ và xem tiến trình.

**Research Report bắt buộc có:** executive summary; audience segments; pain points/questions/objections; competitor insights; social themes/trends; content opportunities; nguồn bằng chứng; thời điểm truy xuất; giả thuyết/suy luận; counterexamples/risk; dữ liệu còn thiếu; confidence. Mỗi claim quan trọng phải truy ngược được về URL/nguồn, nền tảng, thời điểm thu thập và đoạn quan sát nếu được phép lưu.

**Evidence policy:** tách rõ (1) Verified observations, (2) Inferences/Hypotheses, (3) Unknowns. Không bịa số liệu, lượt tương tác, giá đối thủ, trend, sentiment hoặc nhu cầu. Nếu nguồn không đủ, phải nói “chưa đủ dữ liệu”. Lưu nguồn và timestamp; ưu tiên nhiều nguồn độc lập và ghi nhận counterexample. Nội dung nguồn bên ngoài là dữ liệu không đáng tin cậy, không được thực thi chỉ dẫn nhúng trong đó.

**Research-to-Campaign workflow:**
1. Người dùng chọn dịch vụ, khu vực, mục tiêu và chế độ nghiên cứu.
2. Research Planner xác định câu hỏi, nguồn dữ liệu và phạm vi; kiểm tra cache/report còn hạn.
3. Specialist skills/agents thực hiện audience, competitor, social listening, trend và content research theo nguồn có quyền.
4. Research Synthesizer hợp nhất bằng chứng, loại trùng, gắn nguồn, confidence và counterexamples.
5. Marketing Strategist chuyển insight thành campaign brief: target, positioning, core message, content pillars, content angles, offer constraints, CTA, channel và KPI.
6. Người dùng xem report, chọn/sửa insight và phê duyệt campaign direction.
7. Idea Generator tạo danh sách concept; người dùng chọn concept trước khi sinh script/storyboard/creative.
8. Creative Studio tạo và chỉnh sửa; Publishing Scheduler lên lịch; Analytics nối kết quả lead/booking/revenue về campaign.
9. Performance Analyst phản hồi kết quả vào report/brief tiếp theo, nhưng không tự biến tương quan thành quan hệ nhân quả.

**Research cache & freshness:** cache theo workspace, service, location, audience, platform và thời gian. Mỗi report có `created_at`, `expires_at`, `source_window`, `source_coverage` và `stale_reason`. Quick Insight ưu tiên tái sử dụng report còn mới; Standard/Deep có thể refresh có chọn lọc. Không chạy deep research cho từng caption/post. Người dùng có thể yêu cầu refresh hoặc xóa report.

**Data source & compliance:** dùng API chính thức, dữ liệu do khách hàng kết nối/cung cấp, nguồn web công khai và nhà cung cấp dữ liệu bên thứ ba có quyền phù hợp. Không giả định Meta/TikTok/Instagram API cung cấp toàn bộ bài đăng, comment, audience hoặc ad library. Không bypass login, paywall, rate limit, robots/access control hoặc điều khoản nền tảng. Tôn trọng privacy, consent, retention và yêu cầu xóa dữ liệu. Nếu không có quyền truy cập, chuyển sang nhập URL/tệp/danh sách đối thủ do người dùng cung cấp hoặc nêu rõ giới hạn.

**MVP scope:** report dựa trên brand/service profile, khu vực, đối thủ do người dùng nhập, nguồn web công khai được phép và dữ liệu social/page mà workspace có quyền; sinh research report có citation/source ledger; tạo campaign brief và content angles. Social listening sâu, competitor monitoring định kỳ và cross-platform trend intelligence đưa vào P2 sau khi xác minh nguồn dữ liệu hợp pháp/ổn định.

### MOD-04 --- AI Creative Studio & Short Video Repurposing

**Mục tiêu:** tạo bộ nội dung quảng bá đa định dạng từ brief chiến dịch và tái sử dụng video quảng cáo đã được tạo/được người dùng tải lên thành các short video phù hợp Facebook Reels và các placement được hỗ trợ.

**Reusable Generation Style Packs (hệ thống style mặc định cho model ảnh/video):**

**Mục tiêu:** người dùng cấu hình một lần các đoạn văn mô tả phong cách (giống reusable skill/instruction), sau đó GrowthPilot tự động đính kèm đúng các đoạn mô tả này vào mọi prompt gửi tới model sinh ảnh hoặc video. Người dùng không phải lặp lại yêu cầu như “cinematic”, “soft lighting”, “beige luxury spa”, “minimalist composition” trong từng lần generate.

- **Style Pack** là một bộ hướng dẫn dạng văn bản có cấu trúc, gồm nhiều `Style Blocks` độc lập và có thứ tự. Ví dụ một pack “Luxury Beige Spa” có thể gồm: (1) Art Direction: luxury, calm, premium spa; (2) Color Palette: warm beige, ivory, muted gold; (3) Lighting: soft diffused natural light; (4) Composition: clean editorial composition, generous negative space; (5) Materials/Texture: natural stone, linen, wood; (6) Typography/Layout guidance cho poster; (7) Negative Constraints: tránh màu neon, bố cục rối, da nhựa, watermark giả.
- Style Block chỉ là chỉ dẫn nội dung/prompt declarative; không phải code, không có quyền gọi tool, không được thực thi như agent skill. Tool skills và style packs là hai lớp riêng: skill quyết định *làm gì/bằng công cụ nào*; style pack quyết định *đầu ra nên trông như thế nào*.
- Mỗi block có `name`, `description`, `content`, `category`, `priority`, `enabled`, `applies_to` (image/video/both), `tags` và optional `model_compatibility`. Cho phép bật/tắt, sửa, đổi thứ tự, nhân bản, lưu version và preview prompt sau khi ghép.
- Hỗ trợ nhiều pack theo mục đích: Brand Default, Luxury Spa, Clinical/Clean, Natural/Organic, Editorial, Minimalist, Festive/Seasonal, UGC/Authentic và custom pack do workspace tự tạo. Đây là ví dụ preset; không ép mọi spa dùng cùng một style.
- **Phạm vi áp dụng và kế thừa:** platform preset (nếu có) → workspace default → project override → campaign/creative override → model adapter constraints. Mặc định workspace style được áp dụng cho mọi project; project có thể kế thừa hoặc override; từng creative có thể tạm thời bỏ qua hoặc chọn pack khác. Cần hiển thị rõ pack nào đang active.
- **Phân tách theo modality:** một pack có thể chứa block dùng chung và block riêng cho image/video. Ví dụ hướng dẫn bố cục poster không được tự động đưa vào video prompt; video-specific blocks có thể quy định camera movement, shot pacing, motion intensity, frame continuity, transitions và temporal consistency.
- **Phân tách theo model:** cho phép khai báo model-specific adaptation/compatibility. Prompt Composer chuyển style blocks thành cách diễn đạt phù hợp model/provider, nhưng không tự ý bỏ các yêu cầu cốt lõi. Nếu model không hỗ trợ một đặc tính (ví dụ reference image, negative prompt, camera control), phải đánh dấu unsupported/approximate thay vì giả vờ đã áp dụng.
- **Prompt composition order:** (1) system/model safety constraints; (2) task instruction và nội dung người dùng; (3) project/brand facts và reference assets; (4) active style blocks theo thứ tự/priority; (5) modality/model-specific parameters; (6) negative constraints và output requirements. Prompt cuối cùng phải loại trùng lặp, giải quyết mâu thuẫn theo precedence đã công bố và giữ nguyên thông tin factual như giá/CTA/brand assets.
- Người dùng có thể nhập yêu cầu bổ sung trong chat, ví dụ “lần này chuyển sang phong cách watercolor”; orchestrator tạo **temporary override** cho creative hiện tại, không tự sửa workspace default. Chỉ khi user bấm “Lưu thành style mặc định” mới cập nhật pack/assignment.
- Cho phép chọn nhiều block/pack để ghép, nhưng phải cảnh báo khi có chỉ dẫn mâu thuẫn. Có nút “Xem prompt đã ghép” (advanced view), “Preview style”, “Reset về mặc định”, “Tắt style cho lần này” và “Lưu style này làm mặc định”.
- Mỗi generation job lưu snapshot bất biến của style pack/version, block IDs/content, inheritance/override resolution, final composed prompt, negative prompt, model/provider/version, parameters, reference assets và user instruction. Chỉnh sửa style về sau không làm thay đổi lịch sử hoặc kết quả đã tạo.
- Conversational Creative Editor có thể đề xuất thay đổi style blocks từ feedback như “ảnh đang quá vàng, giảm tone ấm”; trước khi lưu thành default phải cho user xem diff và xác nhận. Một chỉnh sửa chỉ áp dụng cho một output không được âm thầm làm thay đổi toàn bộ workspace.
- Style packs phải hỗ trợ tiếng Việt và tiếng Anh. Có thể lưu nội dung đa ngôn ngữ hoặc dùng canonical description + localized label; Prompt Composer chọn ngôn ngữ phù hợp model nhưng không được làm thay đổi ý nghĩa.
- Không bảo đảm mọi model tuân thủ style tuyệt đối. UI phải phân biệt “style instructions attached” với “style adherence verified”; cung cấp benchmark theo model và loại tác vụ.

**UX cấu hình Style Library:**
- Workspace Settings → AI Generation Styles: chọn default image pack, default video pack và optional shared pack; tạo/sửa/duplicate/archive pack.
- Trong project, mục “Generation Style” hiển thị inherited style, cho phép override theo project mà không ảnh hưởng workspace.
- Trong màn hình generate, hiển thị các style chips đang áp dụng và cho phép tắt/đổi pack cho lần chạy hiện tại.
- Mỗi style block có thể được preview bằng ví dụ prompt; người dùng có thể test một brief mẫu trước khi đặt làm default.
- Admin/Owner quản lý style dùng chung; thành viên có quyền phù hợp được dùng style nhưng không nhất thiết được sửa workspace defaults. Audit log ghi nhận ai thay đổi style và khi nào.

Chức năng tạo nội dung:
- Tạo caption, nội dung quảng cáo, hook, CTA và nhiều biến thể theo dịch vụ, mục tiêu, brand voice.
- Tạo ảnh theo brief và brand profile.
- Tạo video quảng cáo gốc bằng template hoặc tích hợp dịch vụ/model video bên ngoài; không tự huấn luyện foundation video model trong MVP.
- Lưu phiên bản, prompt, model/provider, chi phí và lịch sử chỉnh sửa.
- Có thư viện creative dùng lại theo workspace/campaign.

**Conversational AI Creative Editor (LLM điều khiển chỉnh sửa ảnh/video):**
- Cung cấp giao diện chat ngay trong Creative Studio; người dùng tương tác bằng tiếng Việt tự nhiên, không cần tự viết prompt hoặc hiểu thông số model.
- Hỗ trợ hội thoại nhiều lượt có ngữ cảnh: LLM hiểu creative đang mở, version hiện tại, brand profile, dịch vụ, mục tiêu chiến dịch, tỷ lệ khung hình và các chỉnh sửa trước đó.
- Ví dụ: “đổi nền thành spa sang trọng tông be”, “giữ nguyên khuôn mặt và sản phẩm, chỉ thay background”, “làm giá 499.000đ nổi bật hơn”, “rút video còn 15 giây”, “thêm subtitle tiếng Việt và logo ở cuối”, “tạo thêm 3 phiên bản CTA khác nhau”.
- LLM là creative copilot/orchestrator: phân tích ý định, hỏi lại khi mơ hồ, chuyển yêu cầu thành Edit Plan có cấu trúc (asset, vùng/đối tượng, thao tác, tham số, tool/model, credit ước tính và rủi ro), rồi gọi image/video tools phù hợp.
- Với ảnh: hỗ trợ instruction editing, inpainting/outpainting, thay nền, xóa/thêm vật thể, đổi màu/tông, bố cục, tỷ lệ, thêm/sửa text, logo và tạo biến thể. Cần mask/brush hoặc chọn vùng để chỉ định khu vực chỉnh sửa; hỗ trợ ảnh tham chiếu và bảo toàn các yếu tố được yêu cầu giữ nguyên trong giới hạn model.
- Với video: hỗ trợ chọn/trim đoạn theo mô tả tự nhiên hoặc timecode, rút gọn, đổi thứ tự clip, crop/reframe, thêm/xóa subtitle, thay hook/CTA/cover, thêm logo/overlay, điều chỉnh âm lượng/nhạc trong phạm vi quyền sử dụng và tạo biến thể. Thao tác timeline chính xác ưu tiên tool xác định (FFmpeg/editor engine), không tái sinh toàn bộ video bằng video model nếu không cần.
- Người dùng có thể chọn một phần ảnh hoặc frame cụ thể rồi chat “chỉ sửa cảnh này, giữ phần còn lại”; hệ thống ánh xạ yêu cầu vào vùng/timecode tương ứng.
- Trước tác vụ tốn credit hoặc thay đổi lớn, hiển thị tóm tắt thao tác, số lượng output và credit ước tính; yêu cầu xác nhận. Có thể bật auto-run cho thao tác nhỏ trong workspace settings.
- Mỗi lần chỉnh sửa tạo version/branch mới, không ghi đè file gốc; có preview Before/After, chấp nhận, yêu cầu sửa tiếp, undo/revert và duplicate thành biến thể.
- Lưu chat history, Edit Plan, tool calls, model/provider, input/output asset, chi phí, trạng thái job và người xác nhận để audit/tái lập.
- Nếu model không thể chỉnh cục bộ hoặc không bảo toàn chính xác yếu tố được yêu cầu, AI phải nói rõ giới hạn; không được tuyên bố đã giữ nguyên mặt/logo/chữ khi chưa kiểm chứng.
- Người dùng có thể sửa Edit Plan trước khi chạy; hội thoại không tự publish hoặc thay đổi lịch đăng nếu chưa có xác nhận riêng.

**Short Video Generator / Video Repurposing:**
- Đầu vào: video quảng cáo dài do GrowthPilot tạo hoặc video do người dùng tải lên và có quyền sử dụng; có thể chọn mục tiêu, dịch vụ, CTA, thời lượng mong muốn và nền tảng đích.
- AI phân tích nội dung, transcript, cảnh/shot và các đoạn có thông điệp rõ; đề xuất các đoạn clip độc lập.
- Tạo nhiều phiên bản ngắn, mặc định đề xuất 15–30 giây; cho phép cấu hình thời lượng theo giới hạn kỹ thuật và yêu cầu nền tảng.
- Tạo phiên bản dọc 9:16 ưu tiên Reels, đồng thời hỗ trợ 1:1 hoặc 4:5 khi phù hợp; crop/reframe chủ thể, tránh cắt mất nội dung quan trọng.
- Tạo subtitle tiếng Việt tự động, cho phép sửa transcript, kiểu chữ, vị trí, màu, logo/watermark và CTA overlay.
- Đề xuất hook mở đầu, tiêu đề/cover, caption và hashtag; người dùng có thể sửa từng thành phần.
- Có timeline/editor tối giản: trim đầu/cuối, chọn đoạn, đổi thứ tự clip, thay cover, bật/tắt subtitle, chỉnh CTA và preview trước khi export.
- Xuất file MP4 với codec, độ phân giải, frame rate, bitrate và audio phù hợp theo preset được kiểm thử; lưu file gốc và các bản render.
- Cho phép tạo nhiều biến thể A/B từ cùng video gốc (hook, CTA, độ dài, subtitle/layout); mỗi biến thể có creative ID riêng.
- Có thể đưa short video đã duyệt thẳng sang Publishing Calendar để đăng hoặc lên lịch.

Pipeline kỹ thuật gợi ý:
1. Upload/import video → kiểm tra định dạng, dung lượng, quyền sử dụng và malware.
2. Probe metadata, tách audio, speech-to-text, scene/shot detection.
3. AI đề xuất highlight/timecode và clip candidates; người dùng chọn hoặc chỉnh sửa.
4. FFmpeg thực hiện trim, crop/reframe, resize, subtitle, overlay và encode.
5. Quality checks: thời lượng, aspect ratio, audio/video sync, subtitle overflow, black frame, logo/CTA safe area.
6. Preview → approval → export/publish.

Yêu cầu governance:
- Trạng thái: Draft, Processing, Generated, In Review, Approved, Scheduled, Published, Failed, Rejected.
- Người dùng phải duyệt trước khi xuất bản; không tự động đăng creative chưa Approved.
- Không dùng ảnh/video khách hàng nếu chưa có quyền hợp lệ; kiểm tra quyền nhạc, stock footage, font và asset bên thứ ba.
- Không tạo before/after giả, chỉnh sửa làm sai lệch kết quả hoặc cam kết điều trị.
- Nội dung liên quan dịch vụ y tế/thẩm mỹ phải qua kiểm tra chính sách chuyên biệt.
- Lưu nguồn video, quyền sử dụng, consent, version và audit trail.

### MOD-05 --- Campaign & Publishing Manager / Smart Scheduler

**Mục tiêu:** quản lý lịch xuất bản đa kênh và đưa nội dung đã duyệt đến đúng Page/tài khoản vào thời điểm đã chọn.

Chức năng cơ bản:
- Tạo chiến dịch, gắn dịch vụ, mục tiêu, kênh, nội dung, creative và CTA.
- Đăng ngay hoặc đặt lịch thủ công cho từng bài; cho phép đặt trước nhiều ngày, tuần hoặc tháng. Không hard-code giới hạn lịch đăng theo số ngày; giới hạn thương mại (nếu có) nên dựa trên gói, số lượng job chờ, số Page và usage.
- Calendar theo ngày/tuần/tháng; lọc theo Page, nền tảng, chiến dịch, trạng thái và người phụ trách.
- Hỗ trợ lịch cho post ảnh, video/Reels và các loại media khác chỉ khi endpoint, tài khoản, quyền và API hiện hành hỗ trợ.
- Chỉnh sửa/hủy lịch khi job chưa bắt đầu publish; duplicate lịch; publish now; bulk scheduling.
- Trạng thái: Draft, Awaiting Approval, Approved, Scheduled, Publishing, Published, Failed, Cancelled.
- Hiển thị scheduled time, timezone, Page đích, preview, external post ID, thời điểm publish thực tế và lỗi trả về.
- Lưu lỗi, retry có kiểm soát, cảnh báo token hết hạn/quyền bị thu hồi/Page mất kết nối; không retry mù gây đăng trùng.
- Có lịch sử hoạt động và thông báo trong app/email khi đăng thành công/thất bại.

**AI Smart Scheduling:**
- Với Page mới/chưa có dữ liệu, dùng lịch khởi điểm theo ngành, định dạng và mục tiêu; giải thích đây là benchmark/giả thuyết chứ không phải giờ vàng bảo đảm.
- Khi có dữ liệu, phân tích hiệu suất theo Page, ngày trong tuần, giờ, định dạng, content pillar và mục tiêu.
- Tối ưu không chỉ theo like/reach mà theo inbox, qualified lead, booking và doanh thu nếu có dữ liệu attribution.
- Đề xuất lịch và giải thích lý do; người dùng phê duyệt. Không tự thay đổi lịch đã duyệt nếu chưa bật tùy chọn cho phép.
- Tránh đăng dồn, trùng nội dung, xung đột lịch chiến dịch và giờ không có nhân viên trực inbox; hỗ trợ quiet hours và posting frequency cap.
- Thu thập đủ mẫu trước khi kết luận; hiển thị độ tin cậy/cỡ mẫu và tránh khẳng định một khung giờ tối ưu từ một vài bài.

**Organic vs Paid:**
- Phân biệt rõ lịch đăng organic với lịch chạy quảng cáo. Lên lịch đăng bài không yêu cầu mua quảng cáo.
- Không cam kết bài đăng Page mới sẽ có reach/follower; organic distribution phụ thuộc follower, chia sẻ, nội dung và hệ thống đề xuất của nền tảng.
- Quảng cáo trả phí là workflow riêng, cần tài khoản/quyền Meta Marketing API phù hợp, ngân sách do khách hàng cấp và phê duyệt rõ ràng. Không tự tạo hoặc tăng ngân sách quảng cáo.

**MVP:**
- Ưu tiên Facebook Page publishing cho loại bài/media được API hỗ trợ.
- Có lịch thủ công, calendar, job queue, publish now, trạng thái, retry an toàn và thông báo lỗi.
- Short video generation có thể phát hành bản MVP giới hạn: nhận video, chọn/trim clip, crop 9:16, subtitle và export; nâng cấp AI highlight selection/A-B variants ở Phase 2.
- Instagram publishing triển khai theo loại tài khoản, loại media và quyền API được hỗ trợ.
- Không mặc định mọi định dạng hoặc tính năng đều được API hỗ trợ; cần xác minh Meta API trước khi cam kết.

### MOD-06 --- Social Integration & Omnichannel Inbox

Kênh khởi đầu: - Facebook Page / Messenger. - Instagram Professional /
Instagram Messaging.

Chức năng: - OAuth kết nối tài khoản. - Chọn Page/tài khoản được cấp
quyền. - Nhận webhook. - Đồng bộ hội thoại và tin nhắn theo khả năng
API. - Gán hội thoại cho nhân viên. - Trạng thái Open, Pending,
Resolved. - Gắn nhãn và ghi chú. - Hiển thị lịch sử khách hàng. - Trả
lời thủ công. - Đề xuất câu trả lời bằng AI. - Cho phép bật tự động trả
lời trong phạm vi chính sách.

Lưu ý: - Không được giả định có thể đọc mọi tin nhắn cá nhân hoặc mọi dữ
liệu trên nền tảng. - Quyền truy cập phụ thuộc loại tài khoản,
permission, App Review và chính sách Meta. - Phải xử lý webhook trùng
lặp, sự kiện đến sai thứ tự và retry. - Lưu nguồn, external ID và
timestamp để đối soát.

### MOD-07 --- AI Lead & Sales Automation

Chức năng: - Nhận lead từ inbox, comment hoặc Lead Ads khi được cấp
quyền. - Chuẩn hóa thông tin khách. - Phân loại intent: hỏi giá, hỏi
dịch vụ, đặt lịch, khiếu nại, hỏi địa chỉ, hỏi khuyến mãi, khác. - Lead
scoring theo tiêu chí cấu hình. - Tóm tắt hội thoại. - Đề xuất câu trả
lời dựa trên Brand & Service Profile. - Chuyển nhân viên khi cần. -
Follow-up khách chưa hoàn tất booking theo consent và chính sách kênh. -
Dừng automation khi khách yêu cầu dừng hoặc nhân viên tiếp quản.

AI Sales Agent không được: - Tự bịa thông tin dịch vụ/giá. - Đưa ra chẩn
đoán y khoa. - Cam kết hiệu quả điều trị. - Tự xác nhận booking nếu chưa
kiểm tra lịch. - Gửi thông điệp ngoài phạm vi quyền và chính sách nền
tảng.

### MOD-07A --- Dedicated Customer Engagement Agent & Facebook Outreach

**Mục tiêu:** một AI agent chuyên trách tương tác với khách hàng trên Facebook Page: xử lý comment, hỗ trợ Messenger, phân loại nhu cầu, chăm sóc lead theo lịch và triển khai chiến dịch nhắn tin tới tệp khách đủ điều kiện. Agent này tách biệt về system prompt, knowledge scope, model configuration, tools, evaluation và audit với Marketing/Creative agents. Có thể dùng model/provider riêng hoặc cùng provider nhưng phải có cấu hình và ranh giới nghiệp vụ riêng.

**A. Facebook Comment Assistant**
- Nhận comment/reply event từ Page webhook theo permission được Meta duyệt.
- Phân loại: hỏi giá, hỏi dịch vụ, quan tâm/đăng ký, xin tư vấn, phản hồi tích cực, khiếu nại, spam/không liên quan.
- Tạo câu trả lời công khai phù hợp ngữ cảnh post/campaign, brand voice, FAQ và bảng giá đã xác minh.
- Chế độ vận hành: Suggest only (nhân viên duyệt), Auto-reply theo confidence/allowlist, hoặc Escalate to human.
- Có rule riêng cho comment nhạy cảm/khiếu nại: không tranh luận công khai, không yêu cầu khách đăng thông tin cá nhân; chuyển sang kênh riêng chỉ khi cơ chế private reply được API/policy cho phép.
- Lưu comment gốc, post/campaign liên quan, câu trả lời, actor (AI/admin), trạng thái và kết quả API.

**B. Messenger Customer Engagement Agent**
- Xử lý inbound Messenger: hiểu nhu cầu, trả lời FAQ, tư vấn dịch vụ, thu thập thông tin tự nguyện, đánh giá intent/lead score và đề xuất booking.
- Theo dõi trạng thái hội thoại/lead: New, Engaged, Interested, Qualified, Booking Pending, Booked, Not Interested, Opted Out, Suppressed.
- Phân biệt inbound support/follow-up trong cửa sổ được phép với marketing outreach. Không coi mọi customer đã từng nhắn Page là đối tượng có thể nhắn quảng cáo vô thời hạn.
- Agent tạo đề xuất nội dung và next action; Policy Engine kiểm tra consent, cửa sổ nhắn tin, tần suất, quiet hours, suppression, campaign eligibility và quyền Page trước khi gửi.

**C. Follow-up Scheduler & Contact Policy**
- Workspace admin cấu hình lịch chăm sóc: thời điểm bắt đầu sau tương tác/lead, khoảng cách giữa các lần nhắn, khung giờ được phép, timezone, ngày trong tuần, quiet hours, giới hạn số tin/ngày/tuần và số lần thử tối đa.
- Cấu hình theo từng workflow/campaign và có thể đặt default toàn workspace. Ví dụ: follow-up lần 1 sau 2 giờ; lần 2 sau 24 giờ; lần 3 sau 3 ngày — chỉ là ví dụ cấu hình, không phải lịch mặc định bắt buộc.
- Stop/suppression rules cấu hình được: không phản hồi sau N lần gửi; không có tương tác trong X ngày; khách nói không quan tâm; khách yêu cầu dừng; đã opt-out; đã booking; nhân viên takeover; hội thoại khiếu nại; Page token/permission mất; hoặc policy window không còn hợp lệ.
- Không tự gửi dồn tin khi scheduler bị trễ; có per-customer cooldown, per-campaign frequency cap, deduplication và global Page rate guard.
- Admin có thể pause/resume một sequence, một campaign, một customer hoặc toàn bộ outreach của Page.

**D. Campaign Audience Outreach (từ luồng tạo campaign)**
- Sau khi người dùng hoàn thành research → strategy → script → image/video → approval, bước Publish hiển thị hai hành động riêng: (1) Publish/Schedule post; (2) Messenger Campaign/Customer Outreach nếu Page và API đủ điều kiện.
- Người dùng chọn Page, campaign/topic, message template/content, tệp khách và lịch gửi. Không tự động nhắn chỉ vì người dùng đã bấm đăng bài.
- Audience builder hỗ trợ điều kiện CRM: Page identity, tag, dịch vụ quan tâm, nguồn lead, trạng thái lead, lần tương tác cuối, booking history, chi nhánh, campaign source, consent/marketing opt-in và suppression status.
- Có thể chọn segment đã lưu hoặc tạo segment mới; loại trừ khách đã booking, khách đã nhận campaign gần đây, khách opt-out, khách bị suppression và khách không đủ điều kiện API.
- Preview trước khi gửi: total selected, eligible, excluded và lý do loại trừ; dự kiến số tin/credit/chi phí (nếu có); sample message; lịch gửi; giới hạn tần suất. Admin phải xác nhận trước khi enqueue.
- Hỗ trợ batch/throttling, pause/resume/cancel, idempotency và theo dõi trạng thái từng recipient. Không dùng chức năng này để gửi cold message hàng loạt tới người chưa có entrypoint/consent hợp lệ.
- Organic post publishing và Messenger outreach là hai job độc lập, hai permission/policy path và hai trạng thái; có thể liên kết cùng campaign_id để đo lường.

**E. High-intent notification & dashboard**
- Khi AI nhận diện khách có nhu cầu cao (ví dụ hỏi giá cụ thể, yêu cầu tư vấn, muốn đặt lịch, để lại số liên hệ tự nguyện, đồng ý nhận tư vấn), tạo event `customer.intent.high`.
- Gửi notification trong app tới Owner/Admin/nhân viên được phân công; optional email/push nếu workspace bật. Notification có Page, tên hiển thị theo dữ liệu được phép, intent, confidence, lý do, tóm tắt hội thoại và deep link mở đúng conversation/CRM profile.
- Dashboard/Trang chủ có widget: Khách tiềm năng mới, Cần gọi lại ngay, Đang chờ phản hồi, Lịch follow-up hôm nay, Khách đã quan tâm, Booking từ Messenger, Outreach đang chạy và cảnh báo campaign.
- Cho phép admin nhận lead, assign nhân viên, đánh dấu đã xử lý, tạo booking/task hoặc tắt automation cho khách.
- Tránh gửi notification lặp: gộp theo customer/conversation/intent trong một khoảng cooldown; vẫn giữ event history.

**F. Customer inactivity & data lifecycle**
- Admin cấu hình retention theo loại dữ liệu: CRM profile, social identity, conversation/message content, raw webhook payload, AI summaries, campaign recipient logs, analytics aggregates và attachments.
- Có hai chính sách độc lập: (1) Inactivity suppression — ngừng mời/chăm sóc sau X ngày không tương tác; (2) Data retention cleanup — archive/anonymize/delete sau thời gian lưu trữ được cấu hình và phù hợp nghĩa vụ pháp lý/nghiệp vụ. Không dùng một điều kiện để thay thế điều kiện còn lại.
- Hỗ trợ các hành động theo từng nhóm: mark inactive, suppress from outreach, archive, anonymize PII hoặc hard delete. Có preview số customer/record/bytes bị ảnh hưởng, exclude list và xác nhận admin trước khi bật policy.
- Không tự động xóa chỉ vì khách không tương tác trong thời gian ngắn hoặc chỉ để giảm tải server. Ưu tiên retention theo data type, archive/cold storage, TTL cho raw webhook/log và xóa/anonymize PII khi hết mục đích lưu trữ.
- Loại trừ hoặc giữ theo chính sách riêng các hồ sơ đang có booking, tranh chấp/khiếu nại, yêu cầu hỗ trợ chưa đóng, giao dịch cần lưu, legal hold hoặc nghĩa vụ lưu trữ khác.
- Có Trash/restore trong thời gian cấu hình; hard delete phải cascade tới PII, social identity, conversation content, attachments, embeddings, caches và derivatives theo policy. Giữ audit tối thiểu cần thiết, không giữ nội dung đã xóa trái với yêu cầu xóa.
- Opt-out/suppression phải được áp dụng ngay cho mọi campaign/workflow. Nếu dữ liệu customer bị xóa, hệ thống vẫn cần cơ chế tối thiểu, hợp pháp để không vô tình tái-import và tiếp tục gửi cho người đã yêu cầu dừng; thiết kế cụ thể phải được legal/privacy review.

**Meta policy guardrails bắt buộc:**
- Cửa sổ Standard Messaging thường là 24 giờ kể từ tương tác gần nhất của người dùng; mọi scheduled send phải kiểm tra lại eligibility tại thời điểm thực thi, không chỉ lúc tạo lịch.
- Tin quảng cáo ngoài cửa sổ tiêu chuẩn chỉ được gửi qua cơ chế marketing messaging/sponsored messaging phù hợp khi Page/app đủ điều kiện và người nhận đã opt-in theo yêu cầu tương ứng. Marketing Messages opt-in request cũng có điều kiện về entrypoint/cửa sổ; không giả định mọi Page được bật.
- Message Tags/utility/human-agent không được dùng làm đường vòng để gửi khuyến mãi hoặc solicitation. Human Agent là ngoại lệ phục vụ hỗ trợ con người trong phạm vi được phép, không phải kênh blast marketing.
- Comment event không đồng nghĩa có quyền gửi Messenger marketing vô thời hạn. Private reply từ comment chỉ triển khai nếu endpoint/use case hiện hành cho phép, đúng giới hạn và mục đích; không tự suy diễn quyền gửi follow-up nhiều lần.
- Nếu không đủ điều kiện gửi, hệ thống phải block/hold và giải thích lý do; có thể đề xuất kênh khác chỉ khi workspace có consent và quyền hợp lệ.
- Phải kiểm tra lại Meta Messenger Platform Policy/Send API và permission hiện hành trước mỗi lần release; policy/eligibility có thể thay đổi.

### MOD-08 --- CRM & Customer 360

Thông tin khách: - Tên hiển thị. - Số điện thoại/email nếu khách tự cung
cấp và có căn cứ xử lý. - Social identities. - Nguồn lead. - Dịch vụ
quan tâm. - Tags. - Lịch sử hội thoại. - Lịch sử booking. - Consent và
trạng thái liên hệ. - Ghi chú nội bộ.

Chức năng: - Tìm kiếm khách. - Hợp nhất profile theo quy tắc an toàn. -
Timeline hoạt động. - Phân nhóm khách. - Xuất dữ liệu theo quyền. - Yêu
cầu chỉnh sửa/xóa dữ liệu theo quy định.

Không tự động hợp nhất hai profile chỉ vì tên hiển thị giống nhau.

### MOD-09 --- Booking & Appointment

Chức năng MVP: - Tạo booking thủ công từ hội thoại. - Chọn chi nhánh,
dịch vụ, nhân viên (nếu có), ngày giờ. - Trạng thái: Pending, Confirmed,
Arrived, Completed, Cancelled, No-show. - Gửi nhắc lịch qua kênh được
phép. - Lưu nguồn lead/campaign. - Ghi nhận giá trị booking/doanh thu
thủ công.

Quy tắc: - Kiểm tra lịch trước khi xác nhận. - Không để hai booking
trùng slot nếu spa bật quản lý sức chứa. - Phân biệt booking dự kiến và
doanh thu thực tế. - MVP không thay thế hệ thống POS/kế toán.

### MOD-10 --- Automation Workflow Builder

Mô hình ECA: Event → Condition → Action.

Trigger ví dụ: - Có tin nhắn mới. - Có lead mới. - Lead chưa được phản
hồi trong khoảng thời gian cấu hình. - Lead chuyển trạng thái. - Booking
được tạo/đổi/hủy. - Khách đến ngày cần chăm sóc lại.

Condition: - Kênh. - Dịch vụ quan tâm. - Chi nhánh. - Trạng thái lead. -
Giờ hoạt động. - Consent. - Nhãn khách.

Action: - Gán nhân viên. - Thêm tag. - Tạo task. - Gửi câu trả lời được
duyệt. - Tạo booking nháp. - Gửi thông báo nội bộ. - Đưa vào workflow
follow-up.

Yêu cầu: - Có bật/tắt workflow. - Có lịch sử execution. - Retry có giới
hạn và exponential backoff. - Idempotency. - Stop condition. - Human
handoff. - Kiểm tra consent và giới hạn kênh trước khi gửi.

### MOD-11 --- Analytics & Reporting

Dashboard MVP: - Tổng lead theo nguồn. - Lead theo chiến dịch. - Thời
gian phản hồi trung bình. - Tỷ lệ phản hồi. - Tỷ lệ lead → booking. -
Booking theo chi nhánh/dịch vụ. - Booking đến hẹn/no-show. - Doanh thu
được ghi nhận. - Hiệu quả workflow. - Khách có intent cao/cần xử lý ngay. - Follow-up đến hạn hôm nay. - Outreach đang chạy và recipient bị loại trừ. - No-response/suppression counts. - Customer inactivity/retention jobs và dung lượng dự kiến giải phóng.

Phân biệt: - Platform metrics: số liệu Meta/TikTok/Google trả về. -
GrowthPilot metrics: lead, booking và doanh thu do hệ thống ghi nhận. -
Attribution: nguồn gốc có thể không đầy đủ; cần lưu attribution model và
mức độ tin cậy.

Không tuyên bố doanh thu được quy nguồn chính xác tuyệt đối nếu dữ liệu
offline hoặc tracking không đầy đủ.

### MOD-12 --- Subscription, Credits & Billing

Gói giá giả thuyết để kiểm chứng: - Starter: 299.000 VND/tháng. -
Growth: 799.000 VND/tháng. - Business: 1.990.000 VND/tháng. -
Enterprise: báo giá riêng.

Có thể giới hạn theo: - Số workspace/chi nhánh. - Số tài khoản social. -
Số thành viên. - Số hội thoại/lead. - Số lượt tạo ảnh/video AI. - Số
workflow đang chạy.

Giá trên chỉ là giả thuyết ban đầu, chưa được xác nhận bằng
willingness-to-pay. Cần tính riêng chi phí model AI, lưu trữ, hạ tầng và
hỗ trợ.

------------------------------------------------------------------------

## 6. User journeys

### 6.1 Onboarding spa

1.  Người dùng đăng ký.
2.  Tạo workspace.
3.  Khai báo thương hiệu, dịch vụ và bảng giá.
4.  Thêm chi nhánh/nhân viên.
5.  Kết nối Facebook Page.
6.  Cấu hình quyền AI và quy tắc chuyển nhân viên.
7.  Kiểm tra thử một hội thoại.
8.  Bật workflow sau khi kiểm thử.

### 6.2 Project-based campaign creation (primary journey)

1. Người dùng nhấn “Tạo project mới”, đặt tên và chọn mục tiêu chiến dịch; wizard cho phép nhập thông tin từng bước và autosave.
2. Upload brief/tài liệu/hình ảnh/video tham chiếu; chọn dịch vụ, khu vực, audience, kênh và thời gian. AI phân tích file, tạo Project Context và hỏi lại các thông tin còn thiếu.
3. Người dùng xác nhận context và chọn Quick Insight / Standard Research / Deep Research.
4. LLM Orchestrator nghiên cứu thị trường/khách hàng/đối thủ, tổng hợp evidence và tạo research report trong project.
5. AI đề xuất campaign direction và nhiều kịch bản/concept. Mỗi phương án được lưu thành item riêng trong panel bên cạnh, tên mặc định “Kịch bản A/B/C…”; người dùng có thể đổi tên, xem, so sánh, trao đổi, duplicate, archive hoặc xóa.
6. Người dùng mở một phương án, chat để yêu cầu chỉnh sửa nội dung; mỗi lần chỉnh sửa được lưu thành version mới, giữ lịch sử và không ghi đè bản gốc. Người dùng chọn một phương án và bấm “Dùng kịch bản này / Generate”.
7. Hệ thống tạo shot list/storyboard, sau đó sinh ảnh/video theo từng shot hoặc asset yêu cầu. Mọi ảnh/video và render được lưu trong project, hiển thị thành các output cards có version và trạng thái.
8. Người dùng chat với Creative Assistant để chỉnh sửa ảnh/video. LLM phân tích yêu cầu, chọn tool/model phù hợp, tạo Edit Plan, hiển thị preview/credit và xin xác nhận khi cần; tool worker thực thi và lưu output thành version mới.
9. Người dùng so sánh các output, chọn creative cuối cùng, đánh dấu Approved và chọn “Tiến hành xuất bản/Đặt lịch”.
10. Chọn kênh/Page, caption, ngày giờ, timezone và tùy chọn publish; xác nhận. Publishing job liên kết ngược project, script và creative đã chọn.
11. Sau xuất bản, metrics/lead/booking/revenue được liên kết về campaign/project để phân tích hiệu quả. Project tiếp tục lưu đầy đủ lịch sử và tài sản.

### 6.2.1 Project variant selection UX

- Dùng vertical card list trong panel phải, có thumbnail/preview, tên, mô tả một dòng và metadata. Không dùng bảng dày đặc làm trải nghiệm mặc định.
- Có nhóm “Kịch bản”, “Ảnh”, “Video” với count và filter; tab “Đã chọn” để người dùng luôn biết phương án hiện hành.
- Cho phép compare 2–3 phương án trong một view: hook, insight, message, CTA, duration, visual preview và điểm khác biệt. Tránh chấm điểm AI như sự thật khách quan; nếu có score phải giải thích tiêu chí.
- Mỗi item có menu context: Rename, Duplicate, Compare, Set as selected, Move to archive, Delete. Delete có undo nếu còn trong Trash.
- CTA chính thay đổi theo trạng thái: “Xem kịch bản”, “Tiếp tục trao đổi”, “Dùng kịch bản này”, “Generate ảnh/video”, “Review output”, “Approve & schedule”.
- Autosave hội thoại và phiên bản; badge “Unsaved changes” chỉ xuất hiện khi thực sự có thay đổi chưa lưu. Tránh tạo quá nhiều card cho từng token/partial response; chỉ tạo version/item khi LLM hoàn tất một deliverable hoặc người dùng chủ động Save as version.

### 6.2A Short video và lịch đăng

1. Marketing chọn một video quảng cáo đã tạo trong GrowthPilot hoặc upload video của spa.
2. Chọn mục tiêu (awareness, engagement, inbox/lead, booking), nền tảng, thời lượng và CTA.
3. AI phân tích transcript/cảnh, đề xuất 2–5 clip candidate kèm timecode và lý do chọn.
4. Người dùng chọn clip, sửa trim, subtitle, hook, cover và CTA.
5. Hệ thống render các phiên bản, kiểm tra chất lượng và hiển thị preview.
6. Người dùng duyệt nội dung và chọn Page/tài khoản đích.
7. Chọn Publish now, Schedule manually hoặc Use AI recommended time.
8. Hệ thống kiểm tra account connection, media eligibility, permission và thời điểm; tạo publishing job.
9. Worker publish, lưu external ID/status; gửi thông báo và đưa metrics vào dashboard khi có dữ liệu.

### 6.3 Lead đến booking

1.  Khách nhắn tin hoặc để lại lead.
2.  Webhook ghi nhận sự kiện.
3.  Hệ thống tìm/khởi tạo customer profile.
4.  AI phân loại intent và tóm tắt.
5.  AI đề xuất câu trả lời hoặc tự trả lời nếu được bật.
6.  Thu thập thông tin cần thiết.
7.  Nhân viên kiểm tra và xác nhận booking.
8.  CRM cập nhật trạng thái.
9.  Dashboard ghi nhận kết quả.

### 6.4 Follow-up và Customer Engagement Agent

1. Khách comment hoặc nhắn Page; webhook tạo event và gắn Page/post/campaign context.
2. Customer Engagement Agent phân loại intent, sentiment, mức độ cần hỗ trợ và confidence.
3. Với comment, tạo public reply suggestion hoặc auto-reply theo policy; trường hợp nhạy cảm chuyển nhân viên.
4. Với Messenger, trả lời inbound trong phạm vi API/policy; tạo hoặc cập nhật customer/lead profile.
5. Nếu lead chưa booking, Follow-up Planner đề xuất sequence; Policy Engine kiểm tra consent, 24-hour window, opt-in, cooldown, quiet hours và suppression.
6. Scheduler gửi đúng thời điểm được phép; sau mỗi lần gửi, cập nhật attempt count và next_action_at.
7. Nếu khách trả lời/tương tác, cập nhật trạng thái và hủy các job follow-up không còn phù hợp; AI đánh giá lại nhu cầu.
8. Nếu khách có intent cao, tạo notification cho Admin/nhân viên và hiển thị trên Dashboard/Trang chủ.
9. Nếu khách không trả lời đủ N lần hoặc không tương tác X ngày, áp dụng stop/suppression rule; không tiếp tục mời gọi.
10. Retention service chạy độc lập theo data retention policy để archive/anonymize/delete khi đủ điều kiện và đã qua approval/hold checks.

### 6.5 Tạo chiến dịch và chọn tệp Messenger Outreach

1. Người dùng tạo campaign project, cung cấp thông tin và tài liệu tham chiếu.
2. AI nghiên cứu, đề xuất chiến lược, script; người dùng chọn và duyệt nội dung.
3. Người dùng tạo ảnh/video, chỉnh sửa và duyệt creative.
4. Tại bước Publish, người dùng chọn Page và cấu hình bài đăng organic: caption, media, publish now/schedule.
5. Nếu muốn tiếp cận khách cũ/lead, người dùng bật riêng “Messenger Outreach”, chọn segment có sẵn hoặc tạo tệp khách bằng điều kiện CRM.
6. Hệ thống preview audience: selected/eligible/excluded, consent/opt-in, lý do loại trừ, số lượng tin và frequency cap.
7. Người dùng chọn nội dung tin nhắn, lịch gửi, khung giờ, giới hạn batch và stop conditions; xem preview theo customer sample.
8. Admin xác nhận. Publishing job và Messenger campaign job được tạo riêng nhưng liên kết campaign_id.
9. Scheduler chỉ gửi recipient đủ điều kiện tại thời điểm chạy; recipient không hợp lệ bị skip/hold với lý do rõ ràng.
10. Dashboard theo dõi sent/delivered/read (nếu API cung cấp), replies, interested leads, bookings, opt-outs, errors và attribution.

------------------------------------------------------------------------

## 7. Meta Integration --- Facebook & Instagram

### 7.1 Chiến lược tích hợp

Meta là nền tảng tích hợp đầu tiên. Ưu tiên Facebook và Instagram trước
khi mở rộng TikTok, Zalo OA và Google Ads.

Không cần mua một gói API Meta riêng. Developer đăng ký Meta App và sử
dụng các API/permission phù hợp. Tuy nhiên, để phục vụ khách hàng ngoài
nhóm vai trò của app, sản phẩm có thể cần Advanced Access, App Review và
Business Verification tùy quyền và trường hợp sử dụng.

Tài liệu chính thức: - Meta for Developers:
https://developers.facebook.com/ - Graph API:
https://developers.facebook.com/docs/graph-api/ - Messenger Platform:
https://developers.facebook.com/docs/messenger-platform/ - Instagram
Platform: https://developers.facebook.com/docs/instagram-platform/ - App
Review: https://developers.facebook.com/docs/app-review/ - Meta
Business: https://business.facebook.com/

### 7.2 Thành phần cần chuẩn bị

  -----------------------------------------------------------------------
  Thành phần              Mục đích                Chi phí API
  ----------------------- ----------------------- -----------------------
  Meta Developer Account  Quản lý ứng dụng        Không có phí mua API
                          developer               riêng

  Meta Business Portfolio Quản lý tài sản doanh   Không có phí mua API
                          nghiệp/xác minh         riêng

  Meta App                Định danh ứng dụng      Không có phí tạo app
                          GrowthPilot             

  Facebook Page thử       Kiểm thử Page/Messenger Không có phí API
  nghiệm                                          

  Instagram Professional  Kiểm thử Instagram API  Không có phí API

  HTTPS backend           OAuth callback và       Hạ tầng có thể tính phí
                          webhook                 

  Privacy Policy/Terms    Minh bạch dữ liệu và    Chi phí vận hành/pháp
                          phục vụ xét duyệt       lý nếu thuê ngoài
  -----------------------------------------------------------------------

### 7.3 Luồng triển khai

1.  Tạo Meta Developer Account.
2.  Tạo Meta App phù hợp với use case Business.
3.  Cấu hình app domains, redirect URI và URL chính sách.
4.  Thêm sản phẩm/API cần thiết.
5.  Thiết lập Facebook Login/OAuth theo mô hình được chọn.
6.  Xây dựng luồng chọn Page/tài sản mà người dùng có quyền quản trị.
7.  Lưu token an toàn và metadata kết nối.
8.  Cấu hình webhook callback HTTPS và verify token.
9.  Subscribe đúng Page/app events và webhook fields.
10. Xử lý message/comment events.
11. Kiểm thử gửi/nhận trong Development Mode với tài khoản có vai trò.
12. Hoàn thiện Privacy Policy, Terms, hướng dẫn xóa dữ liệu và video
    review.
13. Hoàn thiện Business Verification và xin Advanced Access/App Review
    khi cần.
14. Theo dõi trạng thái permission, token và lỗi API sau khi production.

### 7.4 Nhóm permission cần khảo sát

Các permission dưới đây là ví dụ thường gặp, không phải danh sách bắt
buộc cho mọi kiến trúc. Tên và điều kiện có thể thay đổi theo Instagram
Login hay Facebook Login, API version và use case. Trước khi triển khai
phải đối chiếu tài liệu endpoint chính thức.

  -----------------------------------------------------------------------
  Use case                            Permission thường liên quan
  ----------------------------------- -----------------------------------
  Liệt kê Page người dùng quản lý     `pages_show_list`

  Đọc nội dung/engagement Page        `pages_read_engagement`

  Quản lý webhook subscription của    `pages_manage_metadata`
  Page                                

  Gửi/nhận Messenger                  `pages_messaging`

  Đọc nội dung do người dùng đăng     `pages_read_user_content`
  trên Page                           

  Quản lý bình luận Page              `pages_manage_engagement`

  Instagram basic (Facebook Login     `instagram_basic`
  flow)                               

  Instagram messaging                 `instagram_manage_messages`

  Instagram comments                  `instagram_manage_comments`

  Instagram content publishing        `instagram_content_publish`

  Lead Ads                            Các permission/feature liên quan
                                      Lead Ads, ví dụ `leads_retrieval`
  -----------------------------------------------------------------------

Không xin quyền không dùng. Mỗi permission cần có lý do kinh doanh, mô
tả use case và video chứng minh trong App Review nếu được yêu cầu.

### 7.5 Giới hạn và điều kiện quan trọng

-   Instagram API thường yêu cầu tài khoản Professional (Business hoặc
    Creator); tài khoản cá nhân thông thường không đáp ứng một số use
    case API.
-   Quan hệ liên kết tài khoản, phương thức đăng nhập và permission phụ
    thuộc API flow đang dùng.
-   Không phải mọi loại nội dung, tính năng inbox hay dữ liệu đều được
    API hỗ trợ.
-   Messenger/Instagram có chính sách cửa sổ nhắn tin, loại tin nhắn, opt-in và giới hạn gửi; standard messaging thường có cửa sổ 24 giờ từ tương tác gần nhất. Marketing Messages/sponsored messaging chỉ dùng khi Page/app và recipient đủ điều kiện. Không coi API là công cụ gửi quảng cáo tùy ý.
-   App ở Development Mode bị giới hạn người dùng/tài khoản có vai trò
    phù hợp.
-   Advanced Access, App Review và Business Verification có thể cần
    thiết để mở rộng ra khách hàng bên ngoài.
-   API rate limits, token expiration, permission revocation và webhook
    retries phải được xử lý.
-   Không lưu access token dạng plaintext; mã hóa token và giới hạn
    quyền truy cập.

### 7.5.1 Messaging eligibility & outreach policy engine

Mọi outbound Messenger message phải qua một policy decision trước khi gửi. Tối thiểu đánh giá:
- `last_user_interaction_at` và thời điểm hiện tại theo UTC để xác định standard messaging window.
- Message purpose: customer support, response to inbound, marketing/promotional, approved marketing notification hoặc sponsored message.
- Recipient eligibility: valid Page-scoped identity, active opt-in/topic token nếu cơ chế được cấp, opt-out/block status và Page/app capability.
- Permission/token status, Page subscription, rate limits, per-recipient cooldown, per-campaign cap và quiet hours.
- `decision`: ALLOW, HOLD, SKIP hoặc REQUIRE_HUMAN; lưu policy version và reason codes.

Không được dùng `HUMAN_AGENT` hoặc utility/message tags để gửi quảng cáo/khuyến mãi. Comment private reply và marketing outreach là hai use case riêng, cần permission/eligibility và policy validation riêng. Nếu Meta không cho phép gửi tại thời điểm worker thực thi, skip/hold recipient; không retry vòng lặp để lách giới hạn.

### 7.5.2 Marketing outreach ngoài cửa sổ 24 giờ

- Chỉ bật nếu use case/API được Meta cấp quyền và recipient đã thực hiện opt-in phù hợp; kiểm tra topic, notification token và frequency rules mà API hiện hành yêu cầu.
- Sponsored Messages/paid messaging là một phương án khác, phụ thuộc Marketing API, ad account và eligibility; phải hiển thị phí media riêng, không gộp với organic publishing.
- Nếu Page không đủ điều kiện Marketing Messages hoặc user chưa opt-in, GrowthPilot không gửi marketing DM. Có thể tạo task cho nhân viên, chờ khách chủ động nhắn lại hoặc đề xuất email/SMS/Zalo chỉ khi spa có consent và tích hợp hợp lệ.

### 7.6 Kiến trúc tích hợp đề xuất

Dùng một Integration Layer có adapter riêng:

``` text
GrowthPilot Backend
    |
    +-- Social Integration Layer
          |
          +-- Meta OAuth Manager
          |
          +-- Facebook Page Adapter
          |      +-- Page Publishing
          |      +-- Messenger
          |      +-- Page Comments
          |      +-- Lead Ads (phase sau)
          |
          +-- Instagram Adapter
          |      +-- Content Publishing
          |      +-- Instagram Messaging
          |      +-- Comments
          |
          +-- Webhook Gateway
                 +-- Signature/Verification
                 +-- Event Normalization
                 +-- Idempotency
                 +-- Queue
```

Chuẩn hóa sự kiện về internal event schema, ví dụ: -
`social.message.received` - `social.message.sent` -
`social.comment.created` - `social.lead.created` -
`social.account.disconnected`

Mỗi event phải giữ `provider`, `provider_account_id`,
`external_event_id`, `occurred_at`, `payload_reference` và trạng thái xử
lý.

### 7.7 Phân kỳ Meta

**MVP-A** - Facebook OAuth. - Chọn Page. - Token lifecycle. - Messenger
webhook. - Inbox cơ bản. - Trả lời thủ công. - CRM contact/lead
creation.

**MVP-B** - AI intent classification. - AI reply suggestion. - Human
handoff. - Facebook comments nếu permission được duyệt. - Dedicated Customer Engagement Agent ở chế độ suggest/human approval. - Comment classification/reply workflow. - Instagram
Professional connection. - Instagram DM/comments theo khả năng API và
quyền được duyệt.

**MVP-Publishing** - Facebook Page publishing cho media được API hỗ trợ. - Lịch thủ công, calendar, queue, retry và thông báo. - Short video basic (trim, 9:16, subtitle, export) và nối vào lịch đăng.

**Phase 2** - Messenger campaign outreach theo audience segment và Marketing Messages/sponsored messaging eligibility. - Follow-up Scheduler nâng cao, stop rules, high-intent notifications và customer inactivity/data retention automation. - Instagram publishing theo eligibility. - AI highlight/clip selection nâng cao, batch short-video variants và A/B creative. - Smart Scheduling dựa trên dữ liệu Insights. - Meta Lead Ads. - Meta Marketing API campaign insights/ads management. - Attribution nâng cao.

Không nên để tiến độ toàn bộ MVP phụ thuộc vào App Review. Hãy xây
adapter và mock provider để tiếp tục phát triển trong lúc chờ xét duyệt.

------------------------------------------------------------------------

## 8. Tích hợp nền tảng khác

  -----------------------------------------------------------------------
  Nền tảng                Vai trò                 Thứ tự
  ----------------------- ----------------------- -----------------------
  Facebook/Messenger      Kênh social và hội      MVP
                          thoại                   

  Instagram               Kênh social và hội      MVP-B
                          thoại                   

  TikTok                  Nội dung, quảng cáo,    Phase 2
                          lead/messaging tùy      
                          quyền                   

  Zalo OA                 Chăm sóc khách hàng nội Phase 2
                          địa                     

  Google Ads              Quảng cáo tìm kiếm và   Phase 3
                          đo lường                

  Phần mềm spa/POS        Đồng bộ booking, khách  Theo nhu cầu khách hàng
                          và doanh thu            
  -----------------------------------------------------------------------

Mọi tích hợp cần kiểm tra điều kiện tài khoản, API access, app review,
quota, phí dịch vụ và chính sách hiện hành trước khi cam kết tính năng.

------------------------------------------------------------------------

## 9. AI Architecture & Workflows

### 9.1 Nguyên tắc

-   Model/provider abstraction để thay đổi nhà cung cấp.
-   RAG từ dữ liệu thương hiệu, dịch vụ, FAQ và chính sách.
-   Structured output cho intent, lead score và action.
-   Customer Engagement Agent là agent chuyên trách, tách system prompt/model config/knowledge/tools/evaluation khỏi Marketing/Creative; mọi send action phải qua deterministic Channel Policy Engine và Scheduler.
-   LLM không tự quyết định gửi ngoài giờ, vượt tần suất, bypass consent hoặc gửi recipient không eligible; LLM chỉ phân tích, soạn nội dung và đề xuất action.
-   Có confidence threshold.
-   Có human handoff.
-   Log prompt/version/model/cost/latency.
-   Không cho LLM tự quyết định các hành động có tác động tài chính hoặc
    cam kết dịch vụ nếu chưa qua rule engine.
-   Tách LLM planner khỏi media execution: LLM chỉ tạo Edit Plan theo JSON schema và allowlisted tools; backend validate quyền, tham số, asset, credit và policy trước khi enqueue worker.
-   Giới hạn conversation context theo creative/session; không gửi toàn bộ lịch sử workspace hoặc dữ liệu khách hàng không liên quan sang model.
-   Tool execution có idempotency theo job/action ID; hỗ trợ retry, timeout, cancel, progress events và dead-letter queue.
-   Mỗi lần chỉnh sửa tạo immutable asset/version mới; version graph lưu parent version, operation summary và nguồn asset.
-   Ưu tiên deterministic editing (FFmpeg, image processing, mask/overlay/text layers) cho thao tác xác định; chỉ gọi generative model khi cần sinh/sửa nội dung hình ảnh hoặc chuyển động.
-   Project là context boundary mặc định: orchestrator chỉ lấy project context, assets, selected script/version và knowledge được cấp quyền; không trộn dữ liệu giữa project/workspace.
-   Tách conversation message khỏi deliverable: câu trả lời chat thông thường không tự tạo artifact; script, research report, image, video, storyboard hoặc campaign brief hoàn chỉnh phải được lưu thành artifact/version có ID và metadata.
-   LLM Orchestrator điều phối Research, Script, Creative và Publishing tools theo state machine; không phải mỗi tác vụ là một chatbot độc lập. Agent chuyên môn có thể là prompt/skill/tool route dùng chung model/provider.
-   Tất cả generated outputs phải có provenance: project_id, parent artifact/version, source assets, prompt/model/provider, tool calls, created_by, cost/credits, approval state và timestamps.

### 9.2 AI agents/workers

  ------------------------------------------------------------------------
  Agent                   Input                   Output
  ----------------------- ----------------------- ------------------------
  Project Context Agent   Uploads, brand/service     Project Context + missing fields
                          profile, user brief

  Unified AI Orchestrator Project state, chat,       Intent route + tool plan + next step
                          selected artifact

  Script/Concept Agent    Research + project brief  Script variants A/B/C + storyboard

  Research Planner        Brief, phạm vi, mode    Research plan + nguồn cần tìm

  Audience Researcher      Nguồn/đối tượng        Segments, pain points, objections

  Competitor Analyst       Đối thủ/nguồn công khai Competitor insights

  Social Listening Agent   Posts/comments hợp lệ  Social themes + evidence

  Trend Researcher         Nguồn theo thời gian   Trend signals + confidence

  Research Synthesizer     Evidence từ agents     Research Report + citations

  Marketing Strategist     Report + mục tiêu       Campaign brief/positioning

  Content Ideation Agent   Campaign brief         Content angles/concepts

  Campaign Planner        Dịch vụ, mục tiêu,      Campaign brief
                          audience                

  Copywriting Agent       Brand profile, brief    Caption/ad copy

  Style Profile Manager   Workspace/project       Active Style Pack + version resolution
                          settings
  Prompt Composer         User brief, project,    Final model-ready prompt + style snapshot
                          style blocks, model
  Creative Agent          Prompt, brand assets    Image/video job

  Conversational Creative Lịch sử chat, creative  Edit Plan có cấu trúc;
  Agent                  hiện tại, brand profile  tool selection/clarification

  Creative Tool Executor  Edit Plan, asset,        Image/video edit job;
                          policy, user approval    version mới + metadata

  Project Asset Manager   Artifact/version events  Persist, index, quota and lifecycle

  Creative Reviewer       Creative, policy        Pass/reject/warnings
                          checklist               

  Intent Classifier       Message/context         Intent + confidence

  Lead Scoring            Customer/activity       Score + reasons

  Sales Assistant         FAQ, service data,      Suggested reply
                          conversation            

  Customer Engagement    Comment, inbox, CRM,     Reply draft/intent/next action
  Agent                   campaign context

  Outreach Planner        Segment, campaign,       Audience plan + message sequence
                          eligibility

  Messaging Policy Engine Consent, 24h window,     ALLOW/HOLD/SKIP + reason code
                          opt-in, caps, quiet hours

  Follow-up Scheduler     Sequence rules, events,  Scheduled send jobs/stop decisions
                          next_action_at

  High-intent Detector    Conversation, booking,   Intent event + confidence/reason
                          customer history

  Customer Retention      Retention policy,        Archive/anonymize/delete job plan
  Manager                 inactivity, legal holds

  Follow-up Planner       Lead state, consent,    Next action
                          channel rules           

  Analytics Assistant     Campaign/lead/booking   Insight/recommendation
                          metrics                 
  ------------------------------------------------------------------------

### 9.3 Research orchestration, skills và report schema

Dùng một orchestrator LLM điều phối các specialist skills/tools; không cần triển khai một model riêng cho mỗi agent. Skills nên là các đơn vị nhỏ, có input/output schema và kiểm thử độc lập: `brand-profile`, `audience-research`, `competitor-analysis`, `social-listening`, `trend-research`, `evidence-check`, `marketing-strategy`, `content-ideation`, `scriptwriting`, `creative-direction`, `performance-analysis`. Agent chỉ được gọi connector/source đã được allowlist.

Research Report nên lưu dạng JSON có cấu trúc, ví dụ:

```json
{
  "research_summary": "...",
  "target_audience": [],
  "customer_pain_points": [],
  "customer_questions": [],
  "competitor_insights": [],
  "social_trends": [],
  "content_opportunities": [],
  "evidence": [{"claim":"...", "source_url":"...", "platform":"...", "observed_at":"...", "excerpt":"..."}],
  "assumptions": [],
  "counterexamples": [],
  "risks": [],
  "unknowns": [],
  "confidence": "low|medium|high"
}
```

Mỗi evidence item cần source URL hoặc source reference nội bộ, retrieved_at/observed_at, source type, claim được hỗ trợ và provenance. Không dùng output dạng văn bản dài làm nguồn dữ liệu duy nhất cho bước Campaign Planner.

#### 9.3.1 Reusable Style Packs và Prompt Composer

Style Packs là một loại reusable instruction/skill dành riêng cho visual direction, không phải agent có quyền thực thi. Cấu trúc khuyến nghị:

```json
{
  "style_pack_id": "style_luxury_beige_spa",
  "name": "Luxury Beige Spa",
  "version": 3,
  "scope": "workspace",
  "applies_to": ["image", "video"],
  "blocks": [
    {
      "block_id": "art_direction",
      "category": "art_direction",
      "priority": 100,
      "content": "Premium, calm, refined luxury spa visual direction...",
      "applies_to": ["image", "video"],
      "enabled": true
    },
    {
      "block_id": "palette",
      "category": "color_palette",
      "priority": 90,
      "content": "Warm beige, ivory, muted champagne gold; avoid oversaturated colors...",
      "applies_to": ["image", "video"],
      "enabled": true
    },
    {
      "block_id": "lighting",
      "category": "lighting",
      "priority": 80,
      "content": "Soft diffused light, natural skin tones, controlled highlights...",
      "applies_to": ["image", "video"],
      "enabled": true
    },
    {
      "block_id": "negative",
      "category": "negative_constraints",
      "priority": 10,
      "content": "Avoid clutter, plastic skin, distorted hands, fake logos and watermarks...",
      "applies_to": ["image", "video"],
      "enabled": true
    }
  ]
}
```

**Prompt Composer flow:**
1. Nhận user instruction, selected script/storyboard, project context, reference assets, modality và target model.
2. Resolve style assignment theo thứ tự kế thừa platform → workspace → project → campaign/creative; xác định block nào enabled và phù hợp modality.
3. Kiểm tra compatibility, token/context budget, duplicate và conflict giữa user instruction/style blocks/model constraints.
4. Áp dụng precedence: safety/platform constraints không thể bị override; factual project/brand data và user instruction cụ thể cho lần chạy thắng style mặc định khi có xung đột; project/campaign override thắng workspace default; model adapter chỉ chuyển đổi cú pháp/format, không được đổi ý nghĩa.
5. Build prompt sections có nhãn rõ ràng (task, subject/content, reference preservation, visual style, camera/motion, composition, text/layout, negative constraints, output spec). Với API hỗ trợ negative prompt/structured fields thì map riêng; nếu không, serialize phù hợp model.
6. Gửi prompt và parameters qua Model Router; lưu resolved prompt và Style Snapshot cùng generation job.
7. Trả UI thông tin pack/block nào đã áp dụng và cảnh báo phần không hỗ trợ.

**Yêu cầu vận hành:** Prompt Composer phải deterministic với cùng input/config/model adapter version; có prompt preview/debug view cho admin; giới hạn độ dài block; sanitize nội dung; không cho style block ghi đè safety, quyền sử dụng asset, consent, giá/offer đã xác minh hoặc approval gate. Style pack có versioning, rollback và audit log.

### 9.4 Kiến trúc model gợi ý

MVP nên dùng API model thương mại hoặc model open-source được triển khai
có kiểm soát: - LLM: provider abstraction (OpenAI/Gemini/Anthropic hoặc
model tương thích). - Embedding: multilingual embedding model phù hợp
tiếng Việt. - Vector search: pgvector. - Image: API tạo ảnh hoặc ComfyUI
với model có license phù hợp. - Video: ưu tiên template/API ngoài; chưa
tự huấn luyện video model.

Chọn model dựa trên benchmark tiếng Việt, độ chính xác, latency, chi
phí, khả năng structured output và điều khoản thương mại. Không khóa
kiến trúc vào một model duy nhất.

### 9.5 AI safety & policy

-   Không bịa giá, khuyến mãi, thành phần hoặc liệu trình.
-   Không chẩn đoán bệnh hoặc thay thế chuyên gia y tế.
-   Không cam kết kết quả điều trị.
-   Không tạo quảng cáo before/after giả hoặc gây hiểu lầm.
-   Không dùng hình ảnh khách hàng khi thiếu quyền hợp lệ.
-   Không gửi tin nhắn khi thiếu consent hoặc vượt chính sách nền tảng.
-   Không tự tăng ngân sách quảng cáo.
-   Không tự xác nhận lịch khi chưa kiểm tra slot.
-   Chuyển nhân viên khi confidence thấp, khiếu nại, yêu cầu hoàn tiền
    hoặc tình huống nhạy cảm.

------------------------------------------------------------------------

## 10. Kiến trúc kỹ thuật đề xuất

### 10.1 MVP architecture

Khuyến nghị **Modular Monolith + Background Workers**, chưa cần
microservices ngay từ đầu.

``` text
Web App (Next.js)
       |
API Backend (FastAPI)
       |
       +-- Auth & Workspace
       +-- Brand & Services
       +-- Marketing Intelligence / Research
       +-- Campaign & Creative
       +-- Video Processing / Rendering
       +-- Publishing Scheduler
       +-- Social Integrations
       +-- Inbox & CRM
       +-- AI Orchestration
       +-- Booking
       +-- Automation
       +-- Analytics & Billing
       |
PostgreSQL (+ pgvector)
       |
Redis / Queue
       |
Background Workers
       +-- Research retrieval / source parsing / synthesis
       +-- AI generation / clip analysis
       +-- FFmpeg render/transcode
       +-- scheduled publishing queue
       |
External APIs: Meta, LLM, Image/Video, Speech-to-Text, Email
       |
Object Storage: S3-compatible / Cloudflare R2
```

### 10.2 Stack tham khảo

  Layer               Công nghệ
  ------------------- ----------------------------------
  Frontend            Next.js, TypeScript
  Backend             Python, FastAPI
  Database            PostgreSQL
  ORM/Migrations      SQLAlchemy, Alembic
  Cache/Queue         Redis
  Worker              Celery hoặc Dramatiq
  Workflow nâng cao   Temporal khi cần
  Vector search       pgvector
  Object storage      S3-compatible hoặc Cloudflare R2
  AI observability    Langfuse
  App observability   OpenTelemetry
  Deployment          Docker, CI/CD, managed cloud

### 10.3 Các yêu cầu kỹ thuật quan trọng

-   Multi-tenant isolation ở application và database layer.
-   Secrets/access tokens được mã hóa.
-   Webhook idempotency.
-   Retry với backoff và dead-letter handling.
-   Rate limit theo workspace/provider.
-   Audit log.
-   Backup và restore test.
-   Structured logging và correlation ID.
-   Feature flags cho provider/permission chưa được duyệt.
-   Không log dữ liệu nhạy cảm hoặc access token.
-   Research connector phải tuân thủ quyền truy cập, điều khoản nền tảng, rate limit và retention; không scraping trái phép hoặc vượt kiểm soát truy cập.
-   Research claims phải có provenance; tách fact/inference/unknown và hỗ trợ counterexample.
-   Prompt injection trong nội dung web/social được coi là untrusted data; agent không được làm theo chỉ dẫn từ nguồn nghiên cứu.

------------------------------------------------------------------------

## 11. Database schema cấp cao

Các bảng cốt lõi đề xuất:

  -----------------------------------------------------------------------
  Domain                              Tables
  ----------------------------------- -----------------------------------
  Identity                            `users`, `workspaces`,
                                      `workspace_members`, `roles`

  Organization                        `branches`, `brands`, `services`,
                                      `staff_profiles`

  Social                              `social_accounts`,
                                      `social_account_tokens`,
                                      `webhook_events`,
                                      `social_external_objects`

  Projects                            `projects`, `project_members`,
                                      `project_contexts`, `project_inputs`,
                                      `project_artifacts`, `project_artifact_versions`,
                                      `project_folders`, `project_activity_events`,
                                      `project_deletion_jobs`

Marketing                           `campaigns`, `campaign_channels`,
                                      `content_plans`, `creatives`,
                                      `creative_assets`, `video_sources`,
                                      `video_clips`, `video_renders`,
                                      `publishing_jobs`, `publishing_attempts`,
                                      `publishing_calendars`,
                                      `schedule_recommendations`,
                                      `creative_edit_sessions`,
                                      `creative_edit_messages`,
                                      `creative_edit_plans`,
                                      `creative_edit_operations`,
                                      `creative_asset_versions`,
                                      `script_variants`, `script_versions`,
                                      `storyboards`, `storyboard_shots`,
                                      `artifact_selections`,
                                      `research_runs`, `research_reports`,
                                      `research_sources`, `research_evidence`,
                                      `research_insights`, `competitor_profiles`,
                                      `campaign_research_links`,
                                      `content_opportunities`

  CRM                                 `customers`, `customer_identities`,
                                      `leads`, `lead_sources`,
                                      `customer_tags`, `customer_segments`,
                                      `customer_activity_events`,
                                      `customer_retention_policies`,
                                      `customer_lifecycle_jobs`

  Inbox                               `conversations`,
                                      `conversation_assignments`,
                                      `messages`, `message_attachments`,
                                      `social_comments`, `comment_replies`

  Customer Engagement                `engagement_campaigns`,
                                      `engagement_audiences`,
                                      `engagement_recipients`,
                                      `engagement_sequences`,
                                      `engagement_sequence_steps`,
                                      `engagement_send_jobs`,
                                      `engagement_send_attempts`,
                                      `engagement_suppressions`,
                                      `engagement_policy_decisions`,
                                      `customer_intent_events`,
                                      `admin_notifications`

  Booking                             `bookings`, `booking_services`,
                                      `booking_status_history`,
                                      `availability_slots`

  Automation                          `automation_workflows`,
                                      `automation_versions`,
                                      `automation_executions`,
                                      `automation_steps`

  AI                                  `ai_generation_jobs`,
                                      `ai_prompt_templates`,
                                      `ai_usage_records`,
                                      `knowledge_documents`, `agent_runs`,
                                      `agent_skill_versions`, `research_cache_entries`

  Analytics                           `campaign_metrics`, `lead_events`,
                                      `booking_attributions`,
                                      `revenue_records`

  Billing                             `plans`, `subscriptions`,
                                      `invoices`, `credit_wallets`,
                                      `credit_transactions`

  Storage                             `storage_usage_snapshots`,
                                      `storage_objects`, `storage_deletion_jobs`,
                                      `trash_items`, `quota_events`

Governance                          `consent_records`,
                                      `suppression_lists`, `audit_logs`,
                                      `data_deletion_requests`
  -----------------------------------------------------------------------

Các bảng bổ sung cho Style Library và prompt lineage:

- `style_packs`: `id`, `workspace_id` (nullable cho system presets), `name`, `description`, `scope`, `status`, `created_by`, `created_at`, `updated_at`.
- `style_pack_versions`: `id`, `style_pack_id`, `version_number`, `is_published`, `created_by`, `created_at`, `change_summary`; version đã được dùng trong generation không được mutate.
- `style_blocks`: `id`, `style_pack_version_id`, `name`, `category`, `content`, `priority`, `applies_to`, `enabled`, `model_compatibility`, `sort_order`.
- `style_assignments`: `id`, `workspace_id`, `project_id` (nullable), `campaign_id` (nullable), `creative_id` (nullable), `modality`, `style_pack_version_id`, `is_default`, `override_mode`, `created_at`; ràng buộc đảm bảo chỉ có một default hợp lệ cho từng scope/modality.
- `model_style_adapters`: `id`, `provider`, `model_id`, `adapter_version`, `supported_features`, `prompt_format`, `negative_prompt_support`, `reference_support`, `limitations`.
- `generation_prompt_snapshots`: `id`, `generation_job_id`, `user_instruction`, `resolved_style_snapshot` (JSON), `composed_prompt`, `negative_prompt`, `model_parameters`, `adapter_version`, `unsupported_style_features`, `created_at`.
- `style_audit_events`: actor, workspace, style pack/version, action, before/after metadata, timestamp.

`generation_jobs` phải tham chiếu `generation_prompt_snapshots` hoặc lưu snapshot bất biến tương đương. Không chỉ lưu prompt người dùng nhập; phải lưu prompt cuối cùng thực sự gửi tới provider và style configuration đã resolve.

Các bảng bổ sung cho Customer Engagement, outreach và retention:

- `social_comments`: `workspace_id`, `social_account_id`, `external_comment_id`, `external_post_id`, `customer_identity_id`, `parent_comment_id`, `content_reference`, `created_at`, `status`, `provider_payload_ref`; unique theo provider/account/external_comment_id.
- `comment_replies`: `comment_id`, `reply_type` (public/private), `body`, `actor_type` (AI/admin), `approval_status`, `provider_message_id`, `sent_at`, `delivery_status`, `policy_decision_id`.
- `customer_segments`: điều kiện filter có version, owner, saved query và scope Page/workspace; query phải được validate và không cho truy cập cross-tenant.
- `customer_activity_events`: customer_id, Page, event_type, source, occurred_at, metadata tối thiểu; dùng để tính last_interaction_at và engagement state.
- `engagement_campaigns`: campaign_id, Page, purpose, message template/content version, schedule, timezone, status, created_by, approval metadata, policy version.
- `engagement_audiences`: segment snapshot/query version, selected_count, eligible_count, excluded_count, preview timestamp; không chỉ lưu query động mà không có snapshot tại thời điểm xác nhận.
- `engagement_recipients`: campaign_id, customer_identity_id, eligibility_status, exclusion_reason, consent/opt-in reference, scheduled_at, status, attempt_count, last_attempt_at, next_attempt_at.
- `engagement_sequences` / `engagement_sequence_steps`: trigger, delay, send window, max attempts, cooldown, quiet hours, timezone, stop conditions, content/template reference, approval mode.
- `engagement_send_jobs` / `engagement_send_attempts`: idempotency_key, recipient, Page, message purpose, policy decision, provider request/response reference, sent/delivered/read status where available, error and retry metadata.
- `engagement_suppressions`: customer identity, Page, reason (opt-out, no response threshold, inactive threshold, complaint, admin block, policy ineligible), created_at, expires_at, source; opt-out/suppression precedence over all segments.
- `engagement_policy_decisions`: decision, reason codes, channel window, opt-in evidence reference, policy version, evaluated_at; immutable audit.
- `customer_intent_events`: customer/conversation, intent, confidence, reason, detected_at, notification_status, dedupe_key.
- `admin_notifications`: workspace, recipient user/role, customer/conversation/campaign references, type, priority, read_at, actioned_at, dedupe_key.
- `customer_retention_policies`: workspace, data_category, inactivity_days, retention_days, action (archive/anonymize/delete), exclusions, grace_period, legal_basis/policy reference, enabled, updated_by.
- `customer_lifecycle_jobs`: subject/category, planned_action, eligibility_snapshot, hold_reason, status, executed_at, restore_until, audit metadata.

`last_interaction_at` must be computed from clearly defined customer-originated events; automated outbound messages alone do not count as customer engagement. `no_response_attempts` counts only successfully accepted/sent messages according to the chosen provider status definition, not failed attempts. Keep `inactive_for_outreach` separate from `eligible_for_data_deletion`.

### 11.1 Một số quy tắc dữ liệu

-   Bảng nghiệp vụ phải có `workspace_id`.
-   Dùng UUID/ULID làm internal primary key.
-   External IDs phải có unique constraint theo provider/account.
-   Token lưu mã hóa; không trả token về frontend.
-   Lưu timestamp UTC; hiển thị theo timezone workspace/branch.
-   Soft delete chỉ dùng khi phù hợp; có quy trình xóa dữ liệu thực tế
    theo yêu cầu pháp lý.
-   `webhook_events` cần unique key chống xử lý trùng.
-   `messages` phải phân biệt inbound/outbound, provider status và
    actor.
-   `booking_attributions` lưu nguồn và phương pháp quy nguồn, không chỉ
    lưu một campaign ID.
-   `research_sources` lưu provider/source URL, retrieved_at, observed_at, content hash, permission/provenance metadata và retention policy; tránh lưu raw personal data không cần thiết.
-   `research_evidence` liên kết claim với nguồn, excerpt được phép lưu, source locator, confidence và report version.
-   `research_reports` lưu mode, scope, source window, created_at, expires_at, status, structured output, model/prompt version và usage cost.
-   `campaign_research_links` nối campaign/creative với report/insight để truy xuất lý do tạo nội dung.
-   Mọi project-scoped table phải có `workspace_id` và `project_id` (nếu thuộc project); enforce tenant/project ownership ở service layer và DB constraints/RLS nếu phù hợp.
-   `project_artifacts` là registry chung cho deliverables (research report, campaign brief, script, storyboard, image, video, export); `project_artifact_versions` lưu immutable version, parent_version_id, status, metadata và storage object references. Domain tables chuyên biệt vẫn giữ dữ liệu cấu trúc riêng và liên kết artifact_id.
-   `script_variants` có `display_name`, `variant_key`, `status`, `selected_at`, `selected_by`; tên mặc định Kịch bản A/B/C nhưng người dùng được đổi. `artifact_selections` lưu lựa chọn hiện hành theo stage (script/image/video) và lịch sử lựa chọn.
-   `storage_objects` lưu object key, mime type, byte_size, checksum, category, lifecycle state, retention_until, source/derivative relationship; không lưu binary trong PostgreSQL.
-   `storage_usage_snapshots` tổng hợp bytes theo workspace/project/category; cập nhật qua event sau upload, generation, deletion và reconciliation định kỳ để tránh sai lệch.
-   `trash_items` hỗ trợ restore trước hard delete; `project_deletion_jobs` và `storage_deletion_jobs` chạy bất đồng bộ, idempotent, có tiến trình và audit.
-   Xóa project phải enqueue cascade deletion cho object storage, thumbnails, embeddings, caches và derivatives; không chỉ xóa DB row. Publishing external IDs được giữ trong audit tối thiểu cần thiết hoặc xử lý theo retention/legal policy.
-   `publishing_jobs` lưu `scheduled_at` UTC, `timezone`, `status`, `social_account_id`, `creative_id`, `media_type`, `external_post_id`, `published_at`, `last_error`, `retry_count`, `idempotency_key` và approval metadata.
-   Video source/clip/render phải liên kết workspace, quyền sử dụng, source file, timecode, output preset, duration, aspect ratio, subtitle version và checksum.
-   Recommendation phải lưu feature window, sample size, objective metric, model/version, confidence và lý do; không ghi đè lịch đã duyệt.
-   Tách scheduled organic publishing job khỏi paid ad campaign/ad spend entity.


------------------------------------------------------------------------

## 12. API specification cấp cao

API nội bộ có thể theo REST, version prefix `/api/v1`.

  POST       `/social/comments/{id}/reply`             Trả lời comment (public/private nếu đủ điều kiện)
  GET        `/workspaces/{id}/customer-segments`      Danh sách tệp khách đã lưu
  POST       `/workspaces/{id}/customer-segments`      Tạo segment theo điều kiện CRM
  POST       `/campaigns/{id}/engagement-preview`      Preview eligible/excluded audience
  POST       `/campaigns/{id}/engagement`              Tạo Messenger outreach campaign
  POST       `/engagement-campaigns/{id}/approve`      Admin duyệt gửi
  POST       `/engagement-campaigns/{id}/pause`        Tạm dừng campaign
  POST       `/engagement-campaigns/{id}/resume`       Tiếp tục campaign
  POST       `/engagement-campaigns/{id}/cancel`       Hủy campaign
  GET        `/engagement-campaigns/{id}/recipients`   Trạng thái từng recipient
  GET/PUT    `/workspaces/{id}/engagement-settings`    Lịch, quiet hours, caps, stop rules
  POST       `/customers/{id}/suppressions`            Ngừng mời/chăm sóc khách
  GET/PUT    `/workspaces/{id}/retention-policies`    Cấu hình vòng đời dữ liệu khách
  POST       `/workspaces/{id}/retention-preview`     Preview archive/anonymize/delete
  POST       `/retention-jobs/{id}/approve`             Duyệt thực thi retention job
  GET        `/workspaces/{id}/notifications`          Notification cho admin
  POST       `/notifications/{id}/acknowledge`         Đánh dấu đã tiếp nhận
  Method     Endpoint                               Mục đích
  ---------- -------------------------------------- -------------------------
  POST       `/auth/register`                       Đăng ký
  POST       `/auth/login`                          Đăng nhập
  POST       `/workspaces`                          Tạo workspace
  GET/POST   `/workspaces/{id}/members`             Quản lý thành viên
  GET/POST   `/projects`                            Danh sách/tạo project
  GET/PATCH  `/projects/{id}`                       Chi tiết/cập nhật project
  POST       `/projects/{id}/inputs`                Upload tài liệu/ảnh/video/brief
  GET        `/projects/{id}/context`                Project Context và missing fields
  PATCH      `/projects/{id}/context`               Xác nhận/chỉnh sửa Project Context
  GET        `/projects/{id}/artifacts`              Danh sách deliverables/variants
  POST       `/projects/{id}/artifacts`              Lưu artifact/deliverable
  POST       `/artifacts/{id}/versions`              Tạo version mới
  POST       `/artifacts/{id}/select`                Chọn phương án hiện hành
  POST       `/artifacts/compare`                    So sánh 2–3 artifacts
  POST       `/projects/{id}/archive`                Archive project
  DELETE     `/projects/{id}`                        Xóa project (soft delete + deletion job)
  POST       `/projects/{id}/restore`                Khôi phục project trong retention window
  GET        `/storage/usage`                         Dung lượng workspace/project/category
  GET        `/storage/objects`                       Tìm/lọc asset theo dung lượng/loại
  DELETE     `/storage/objects/{id}`                  Xóa asset/version cụ thể
  GET        `/trash`                                 Danh sách dữ liệu đã xóa mềm
  POST       `/trash/{id}/restore`                    Khôi phục item
  DELETE     `/trash/{id}/purge`                      Xóa vĩnh viễn item
  POST       `/projects/{id}/chat/messages`            Gửi chat vào Unified AI Orchestrator
  GET        `/projects/{id}/chat/sessions`            Danh sách hội thoại project
  GET        `/workspaces/{id}/style-packs`             Danh sách Style Packs/presets
  POST       `/workspaces/{id}/style-packs`             Tạo Style Pack
  GET/PATCH  `/style-packs/{id}`                        Xem/cập nhật metadata Style Pack
  POST       `/style-packs/{id}/versions`               Tạo version mới, giữ version cũ bất biến
  GET/POST   `/style-packs/{id}/blocks`                 Quản lý các đoạn mô tả style
  PATCH      `/style-blocks/{id}`                       Sửa/bật/tắt/sắp xếp một Style Block
  GET/PUT    `/workspaces/{id}/style-assignments`       Cấu hình default image/video style
  PUT        `/projects/{id}/style-assignment`          Override style ở cấp project
  POST       `/style-packs/{id}/preview`                Preview prompt/style với brief mẫu
  GET        `/generation-jobs/{id}/prompt-snapshot`    Xem prompt đã ghép và style snapshot
  GET/POST   `/services`                            Quản lý dịch vụ
  POST       `/integrations/meta/connect`           Khởi tạo OAuth
  GET        `/integrations/meta/callback`          OAuth callback
  GET        `/integrations/social-accounts`        Danh sách kết nối
  DELETE     `/integrations/social-accounts/{id}`   Ngắt kết nối
  GET/POST   `/conversations`                       Danh sách/tạo hội thoại
  POST       `/conversations/{id}/messages`         Gửi tin nhắn
  POST       `/webhooks/meta`                       Nhận webhook Meta
  GET/POST   `/campaigns`                           Quản lý chiến dịch
  POST       `/research-runs`                       Khởi chạy nghiên cứu thị trường/social theo scope và mode
  GET        `/research-runs/{id}`                  Trạng thái, tiến trình và lỗi research
  GET/POST   `/research-reports`                    Danh sách/tạo report; filter theo dịch vụ/khu vực/thời gian
  GET        `/research-reports/{id}`               Report, evidence, assumptions và confidence
  POST       `/research-reports/{id}/refresh`       Refresh report hoặc một research category
  POST       `/research-reports/{id}/campaign-brief` Tạo campaign brief từ report đã chọn
  POST       `/campaigns/{id}/generate`             Tạo nội dung bằng AI
  POST       `/creatives/{id}/approve`              Duyệt creative
  POST       `/videos/{id}/analyze`                 Phân tích video và đề xuất clip
  POST       `/videos/{id}/clips`                   Tạo/chọn clip candidate
  POST       `/creatives/{id}/edit-sessions`         Tạo phiên chat chỉnh sửa creative
  GET        `/creative-edit-sessions/{id}`          Lấy lịch sử hội thoại và trạng thái
  POST       `/creative-edit-sessions/{id}/messages` Gửi yêu cầu chỉnh sửa bằng ngôn ngữ tự nhiên
  POST       `/creative-edit-plans/{id}/confirm`     Xác nhận Edit Plan/credit trước khi chạy
  POST       `/creative-edit-plans/{id}/cancel`      Hủy edit job chưa thực thi
  POST       `/creative-asset-versions/{id}/revert`  Tạo version mới từ version trước
  POST       `/video-renders`                       Tạo short-video render job
  GET        `/video-renders/{id}`                  Trạng thái render/preview
  GET/POST   `/publishing-jobs`                     Lịch đăng và danh sách job
  PATCH      `/publishing-jobs/{id}`                Sửa lịch/job chưa publish
  POST       `/publishing-jobs/{id}/publish-now`    Đăng ngay
  POST       `/publishing-jobs/{id}/cancel`         Hủy lịch
  GET        `/publishing-calendar`                 Calendar theo Page/kênh
  POST       `/scheduling/recommendations`          Đề xuất khung giờ đăng
  GET/POST   `/customers`                           CRM
  GET/POST   `/leads`                               Lead management
  GET/POST   `/bookings`                            Booking
  GET/POST   `/automation/workflows`                Workflow
  GET        `/analytics/overview`                  Dashboard

Yêu cầu chung: - Authentication và authorization. - Workspace scope bắt
buộc. - Pagination/filter/sort. - Idempotency key cho thao tác tạo/gửi
có thể retry. - Rate limiting. - Validation và error schema nhất quán. -
API versioning. - Audit các thao tác quan trọng.

------------------------------------------------------------------------

## 13. Non-functional requirements (NFR)

  -----------------------------------------------------------------------
  Nhóm                                Yêu cầu mục tiêu MVP
  ----------------------------------- -----------------------------------
  Availability                        Mục tiêu 99,5% theo tháng sau pilot
                                      ổn định

  API latency                         P95 dưới 500 ms cho API nội bộ
                                      không phụ thuộc external provider

  Webhook ACK                         Phản hồi nhanh sau khi xác thực và
                                      enqueue; không chạy AI đồng bộ
                                      trong request

  Queue                               Retry, dead-letter và dashboard
                                      theo dõi

  Publishing                         Job chạy theo timezone workspace;
                                      không đăng trùng khi retry

  Video processing                   Render bất đồng bộ; progress, cancel,
                                      quota và giới hạn file rõ ràng

  Security                            TLS, encryption at rest cho
                                      secrets, RBAC

  Isolation                           Không truy cập chéo tenant

  Observability                       Logs, metrics, traces, alerting

  Backup                              Backup tự động và kiểm tra khôi
                                      phục

  Scalability                         Worker scale độc lập theo queue

  Reliability                         Idempotency cho webhook và outbound
                                      action

  Privacy                             Consent, retention, export và
                                      deletion workflow

  Project persistence                Deliverable đã hoàn tất phải được lưu bền vững;
                                      refresh/re-login không làm mất artifact

  Storage metering                    Usage hiển thị theo workspace/project/category;
                                      reconciliation định kỳ

  Deletion                            Xóa project/asset bất đồng bộ, idempotent;
                                      hiển thị tiến trình và kết quả

  Artifact lineage                    Mọi version truy được parent, source assets,
                                      model/tool và approval history
  -----------------------------------------------------------------------

Các con số trên là mục tiêu thiết kế ban đầu, cần điều chỉnh theo pilot
và SLO thực tế.

------------------------------------------------------------------------

## 14. Bảo mật, quyền riêng tư và tuân thủ

GrowthPilot AI xử lý thông tin khách hàng, hội thoại và dữ liệu
marketing. Cần thiết kế privacy-by-design.

Yêu cầu: - Thông báo rõ mục đích xử lý dữ liệu. - Chỉ thu thập dữ liệu
cần thiết. - Quản lý consent và căn cứ xử lý phù hợp. - Có cơ chế rút
consent/opt-out. - Quy định retention theo loại dữ liệu. - Có luồng yêu
cầu truy cập, chỉnh sửa, xuất và xóa dữ liệu. - Phân quyền nhân viên. -
Mã hóa token và dữ liệu nhạy cảm. - Có hợp đồng xử lý dữ liệu với nhà
cung cấp liên quan khi cần. - Kiểm tra yêu cầu chuyển dữ liệu ra nước
ngoài nếu dùng cloud/model quốc tế. - Không sử dụng dữ liệu khách hàng
để huấn luyện model nếu chưa có căn cứ và thông báo phù hợp.

Các văn bản cần bộ phận pháp lý rà soát trước khi thương mại hóa: - Luật
Bảo vệ dữ liệu cá nhân 91/2025/QH15 (hiệu lực từ 01/01/2026). - Luật sửa
đổi, bổ sung một số điều của Luật Quảng cáo 75/2025/QH15 (hiệu lực từ
01/01/2026). - Nghị định 342/2025/NĐ-CP quy định chi tiết một số điều và
biện pháp thi hành Luật Quảng cáo (hiệu lực từ 15/02/2026). - Quy định
liên quan bảo vệ người tiêu dùng, thương mại điện tử, tin nhắn/quảng cáo
và quy định chuyên ngành y tế/thẩm mỹ nếu áp dụng.

**Lưu ý:** Phạm vi hoạt động của spa chăm sóc sắc đẹp và cơ sở khám chữa
bệnh/thẩm mỹ có thể khác nhau. Không dùng một bộ nội dung quảng cáo
chung cho mọi loại hình dịch vụ. Đây là định hướng yêu cầu sản phẩm,
không thay thế ý kiến tư vấn pháp lý.

------------------------------------------------------------------------

## 15. MVP backlog và tiêu chí nghiệm thu

### P0 --- Bắt buộc

  -----------------------------------------------------------------------
  Epic                    Story/Deliverable       Acceptance criteria
  ----------------------- ----------------------- -----------------------
  Auth                    Đăng ký/đăng nhập       Người dùng truy cập
                                                  đúng workspace

  Workspace               Tạo workspace và mời    RBAC hoạt động
                          thành viên              

  Brand                   Cấu hình                AI truy xuất đúng dữ
                          brand/service/FAQ       liệu đã cấu hình

  Meta                    Facebook OAuth/Page     Kết nối, lưu trạng
                          connection              thái, ngắt kết nối được

  Webhook                 Nhận Messenger event    Verify, enqueue, chống
                                                  duplicate

  Inbox                   Danh sách hội thoại và  Tin nhắn được gửi/ghi
                          trả lời thủ công        nhận theo API response

  CRM                     Tạo customer/lead từ    Không tạo duplicate
                          hội thoại               theo external identity

  AI                      Intent classification   Trả structured output
                                                  và confidence

  AI Sales                Đề xuất câu trả lời     Có nguồn từ knowledge;
                                                  không tự bịa giá

  Customer Engagement    Agent suggest-only       Có intent/confidence; mọi
                                                  outbound qua policy engine

  Booking                 Tạo booking thủ công    Kiểm tra slot và trạng
                                                  thái

  Automation              Gán lead/tạo task/thông Có execution log và
                          báo                     retry

  Analytics               Dashboard lead/booking  Số liệu đối soát được
                          cơ bản                  với dữ liệu nội bộ

  Governance              Audit/consent/token     Có log và kiểm soát
                          security                truy cập
  -----------------------------------------------------------------------

### P1 --- Sau khi P0 ổn định

-   Project Workspace MVP: tạo project, wizard input/autosave, upload tài liệu/ảnh/video, Project Context, project navigation và project asset library.
-   Reusable Generation Style Packs MVP: Style Library, style blocks dạng mô tả, workspace default cho image/video, project override, Prompt Composer tự động ghép style vào mọi generation request, prompt preview và immutable style snapshot.
-   Persistent Script Variants: lưu Kịch bản A/B/C thành artifacts có tên, version, preview, compare, select, rename, duplicate, archive và delete.
-   Unified AI Orchestrator MVP: chat theo project, gọi Research/Script/Creative tools, hỏi lại khi thiếu thông tin, hiển thị tiến trình và tách chat messages khỏi deliverables.
-   Project-based generation: chỉ generate khi người dùng chọn script và bấm CTA; lưu storyboard, image/video outputs, versions và approvals vào project.
-   Storage Management MVP: quota meter, usage theo project/category, cảnh báo quota, xóa asset riêng và xóa project có xác nhận; deletion worker.
-   AI Marketing Intelligence MVP: Quick/Standard research từ brand/service, khu vực, đối thủ do người dùng nhập và nguồn web công khai được phép; report có source ledger, timestamp, assumptions và confidence.
-   Research-to-Campaign: chuyển report đã duyệt thành campaign brief, content pillars và content angles; người dùng chọn concept trước khi tạo creative.

-   Instagram Professional connection.
-   Instagram DM/comments theo quyền API.
-   Facebook comments.
-   AI reply có chế độ human approval.
-   Content calendar và Facebook publishing scheduler (publish now, lịch thủ công, calendar, retry/notification).
-   Short video basic: trim/crop 9:16/subtitle/export từ video gốc đã được cấp quyền.
-   Conversational AI Creative Editor MVP: chat tiếng Việt nhiều lượt; nhóm thao tác ảnh/video có kiểm soát; Edit Plan preview/confirm; version history, undo/revert; không tự publish.
-   Lead Ads.
-   Automation follow-up có consent.
-   Dashboard campaign-to-booking.
-   Dedicated Customer Engagement Agent MVP: comment classification/reply suggestion, Messenger inbound reply, high-intent notification cho admin.
-   Follow-up Scheduler cơ bản: configurable delay/time window, max attempts, cooldown, stop on reply/opt-out/booking và suppression list.
-   Customer segment builder + audience preview cho Messenger campaign; chỉ gửi trong cửa sổ/opt-in được Meta cho phép.

### P2 --- Mở rộng

-   Project Workspace nâng cao: template project, project sharing/roles chi tiết, cross-project asset library có reference ownership, advanced compare/branching.
-   Storage lifecycle nâng cao: trash/restore theo retention, bulk cleanup, duplicate detection, archive-to-cold-storage, quota add-ons và usage analytics.
-   Deep Research nhiều vòng, social listening/competitor monitoring định kỳ và trend radar đa nền tảng khi có nguồn dữ liệu hợp pháp, ổn định.
-   Research personalization theo chi nhánh, phân khúc khách hàng và hiệu suất lịch sử; tự refresh insight theo tín hiệu thay đổi.

-   Meta Marketing API sâu hơn.
-   TikTok.
-   Zalo OA.
-   Google Ads.
-   Đồng bộ phần mềm spa/POS.
-   Video AI nâng cao: highlight selection, auto-hook, batch variants, A/B creative.
-   Conversational Creative Editor nâng cao: mask/brush editing, frame-level video editing, multi-reference consistency, voice input, template-aware editing và multi-step workflows.
-   AI Smart Scheduling học từ Page Insights và mục tiêu inbox/lead/booking.
-   Messenger Marketing Messages/sponsored outreach nâng cao khi Page/app được cấp quyền; batch delivery, per-recipient eligibility và campaign analytics.
-   Advanced customer lifecycle automation: retention policy theo data category, preview, archive/anonymize/hard-delete jobs, restore window và legal hold.
-   Multi-branch analytics.
-   Agency workspace.

### 15.0A Acceptance criteria bổ sung: video và publishing

**Short video:**
- Người dùng có thể upload/chọn video nguồn và khai báo quyền sử dụng.
- Hệ thống tạo được ít nhất một clip preview có timecode nguồn, crop 9:16, subtitle tiếng Việt có thể sửa và CTA có thể sửa.
- Người dùng có thể trim lại clip và render MP4; UI hiển thị trạng thái Processing/Ready/Failed.
- Không publish nếu chưa Approved; file render gắn với đúng workspace và creative.
- Bộ kiểm thử xác nhận audio/video sync, aspect ratio, subtitle safe area, duration và khả năng phát file.

**Conversational AI Creative Editor:**
- Người dùng gửi yêu cầu chỉnh ảnh/video bằng tiếng Việt tự nhiên và tiếp tục ít nhất 3 lượt hội thoại mà hệ thống vẫn giữ đúng creative/version/context.
- Bộ test intent phân loại đúng thao tác, asset đích, vùng/timecode và tham số; yêu cầu mơ hồ phải được hỏi lại.
- LLM sinh Edit Plan đúng schema; backend chỉ thực thi tool trong allowlist, validate workspace ownership, permission, credit và policy.
- Người dùng xem tóm tắt thao tác và credit dự kiến trước khi xác nhận tác vụ tốn credit; retry không charge hai lần.
- Mỗi lần chỉnh sửa tạo version mới, giữ source version; có preview Before/After và revert/undo không phá hủy dữ liệu.
- Ảnh MVP: đổi nền, chỉnh màu/tông, thêm text/logo/CTA, resize/crop và tạo biến thể; generative edit trả về asset mới, không tự nhận bảo toàn chi tiết nếu chưa kiểm chứng.
- Video MVP: trim theo yêu cầu, crop 9:16, thêm/sửa subtitle, thêm logo/CTA overlay và rút gọn clip; thao tác timeline chính xác ưu tiên media tools deterministic.
- Người dùng hủy được job đang chờ; UI hiển thị queued/processing/succeeded/failed/cancelled và lỗi có thể hành động.
- Hội thoại không tự publish, gửi tin nhắn khách hàng hoặc thay đổi lịch đã duyệt nếu không có xác nhận riêng và quyền tương ứng.
- Audit log gồm user, session, message, Edit Plan, tool, model/provider, asset version, credit, approval và kết quả.

**AI Marketing Intelligence & Research:**
- Người dùng có thể tạo research run bằng cách chọn dịch vụ, mục tiêu, khu vực và Quick/Standard mode; UI hiển thị trạng thái và lỗi có thể hành động.
- Research Report trả về đúng schema, có summary, audience, pain points, competitor/social insights, content opportunities, evidence, assumptions, risks, unknowns và confidence.
- Mỗi claim được trình bày như dữ kiện phải có nguồn/URL và timestamp; nếu không có nguồn phù hợp, hệ thống gắn nhãn inference/unknown thay vì bịa.
- Report phân biệt observation, inference và hypothesis; có counterexample hoặc ghi rõ chưa tìm thấy counterexample.
- Research Planner kiểm tra cache freshness; Quick Insight không gọi deep research khi report còn hạn nếu không có yêu cầu refresh.
- Người dùng có thể mở nguồn, refresh report, xóa report và xem phạm vi nguồn đã khảo sát.
- Campaign brief được tạo từ report phải tham chiếu report/insight IDs; người dùng có thể sửa và phê duyệt trước khi Creative Studio chạy.
- Research connector chỉ truy cập nguồn được phép; test xác nhận rate limit, permission denial, token revocation, timeout và prompt injection từ nội dung nguồn được xử lý an toàn.
- Bộ benchmark tối thiểu gồm 20 brief spa (dịch vụ, khu vực và mục tiêu khác nhau); đo source correctness, claim support rate, hallucination rate, usefulness rating, latency và cost/run. Không đưa vào production nếu claim không có nguồn vượt ngưỡng đã định.

**Reusable Generation Style Packs và Prompt Composer:**
- Workspace Owner/Admin tạo được Style Pack gồm nhiều Style Blocks; có thể đặt tên, mô tả, bật/tắt, đổi thứ tự, sửa, duplicate và tạo version mới.
- Có thể cấu hình default riêng cho image và video; generation job không có explicit override phải tự động nhận đúng default của workspace hoặc project đã resolve.
- Project override chỉ ảnh hưởng project đó; temporary override trong chat chỉ ảnh hưởng generation hiện tại, không sửa default nếu chưa có xác nhận “Lưu thành mặc định”.
- Mỗi block được lọc theo modality; block bố cục poster không được tự động đưa vào video prompt nếu không được khai báo áp dụng cho video.
- Prompt Composer ghép task instruction, project/brand context, reference assets, style blocks, model-specific constraints và output requirements; xử lý duplicate/conflict theo precedence đã quy định.
- Người dùng xem được style chips đang active và có thể preview prompt đã ghép; không bắt buộc người dùng phải xem prompt kỹ thuật mới generate được.
- Generation job lưu prompt cuối cùng đã gửi, negative prompt (nếu có), Style Pack/version/block snapshot, adapter/model version, parameters và reference asset IDs; chỉnh style sau này không làm thay đổi snapshot cũ.
- Nếu model không hỗ trợ một style feature, UI/API ghi nhận unsupported hoặc approximate; không tuyên bố đã áp dụng thành công.
- Style block không thể override safety policy, asset consent, factual price/offer, quyền truy cập hoặc approval gate.
- Test xác nhận cùng một cấu hình/input/model adapter version cho kết quả prompt composition deterministic; test conflict, override, rollback, tenant isolation và audit log.
- Benchmark style adherence trên từng model/modality bằng bộ brief chuẩn; báo cáo riêng prompt attachment correctness và visual style adherence, không đánh đồng hai chỉ số.

**Dedicated Customer Engagement Agent, Facebook comments và Messenger outreach:**
- Có agent chuyên trách với system prompt, model/provider config, knowledge scope, tool allowlist, versioning và evaluation riêng; agent không được trực tiếp gọi Send API mà phải qua Messaging Policy Engine.
- Comment webhook được nhận idempotently; hệ thống lưu đúng Page/post/comment/customer identity và phân loại intent; public reply có suggest-only và auto-reply mode theo confidence/allowlist.
- Private reply chỉ hiển thị/cho phép khi endpoint và policy hiện hành xác nhận đủ điều kiện; comment không tự động tạo quyền nhắn marketing nhiều lần.
- Agent trả lời inbound Messenger dựa trên FAQ/service/price được xác minh; câu hỏi thiếu dữ liệu, khiếu nại, medical claim hoặc confidence thấp phải chuyển nhân viên.
- Admin cấu hình được follow-up delay, khung giờ, timezone, quiet hours, max attempts, cooldown, daily/weekly cap và stop conditions.
- Stop rules hỗ trợ: khách trả lời, booking thành công, khách opt-out/không quan tâm, admin takeover, không phản hồi sau N lần, không tương tác trong X ngày hoặc channel eligibility bị mất.
- Automated outbound không được tính là customer-originated interaction để reset inactivity timer.
- Tại bước Publish của campaign, user có thể chọn riêng Publish Post và Messenger Outreach; hai job độc lập, có chung campaign reference nhưng không tự động bật cùng nhau.
- Audience builder hỗ trợ saved segments và điều kiện CRM; preview hiển thị selected/eligible/excluded và reason code trước khi admin approve.
- Recipient list được snapshot tại thời điểm approve; trước mỗi send, worker re-check opt-in, 24-hour window, suppression, Page permission/token, quiet hours và frequency cap.
- Nếu recipient không eligible, hệ thống skip/hold và ghi lý do; không retry nhằm vượt policy. Không gửi promotional message ngoài cửa sổ bằng HUMAN_AGENT/utility tags.
- High-intent event tạo admin notification có deduplication, priority, reason/confidence và deep link tới đúng conversation/customer; Dashboard có widget lead nóng và follow-up cần xử lý.
- Dashboard phân biệt sent/accepted/delivered/read (chỉ khi provider cung cấp), reply, interested, booking, opt-out, failure và attribution; không hiển thị read/delivery như dữ liệu chắc chắn nếu API không trả.
- Có audit cho agent response, prompt/model version, policy decision, recipient, approval, provider response và admin action.

**Customer inactivity, suppression và data retention:**
- Admin cấu hình độc lập inactivity suppression (ngừng outreach) và data retention (archive/anonymize/delete) theo từng data category.
- Preview trước khi bật policy phải hiển thị số profile/record/attachment, hành động, thời gian grace, exclusions và ước lượng dung lượng giải phóng.
- Có thể cấu hình no-response sau N lần và inactivity X ngày; suppression được áp dụng ngay cho tất cả segment/campaign đang chạy.
- Retention job loại trừ legal hold, booking/giao dịch/khiếu nại chưa đóng và hồ sơ cần lưu theo nghĩa vụ hợp pháp; mọi ngoại lệ phải có reason.
- Có archive/anonymize/hard-delete; cascade theo data map tới PII, identity, message content, attachments, embeddings, caches và derivatives. Backup expiry được quản lý theo backup policy và pháp luật.
- Có Trash/restore/grace period nếu phù hợp; hard delete không được để record có thể khôi phục từ index/cache ngoài quy trình backup hợp lệ.
- Test xác nhận xóa/suppression theo đúng tenant, không gửi nhầm sau opt-out, idempotent jobs, retry sau partial failure và audit trail.

**Project Workspace, artifacts và storage:**
- Người dùng tạo project mới, đặt tên/mục tiêu và hoàn thành wizard từng phần; autosave không làm mất input khi reload hoặc mất kết nối ngắn.
- Người dùng upload tối thiểu các loại file được hỗ trợ (PDF/DOCX/JPG/PNG/MP4 theo giới hạn cấu hình); file có preview/metadata, project_id và ownership đúng tenant.
- Project Context được AI trích xuất từ input; người dùng có thể sửa/confirm; dữ kiện giá/offer phải có nguồn hoặc được đánh dấu chưa xác minh.
- Research run, script variants, storyboard, image/video outputs và chat sessions đều gắn với project; mở lại project thấy đủ lịch sử và artifacts.
- Mỗi script variant có tên riêng (mặc định Kịch bản A/B/C), preview, status, created_at và version; người dùng rename, duplicate, compare tối đa 3 bản, chọn một bản và chuyển sang generate.
- Không tạo image/video generation job khi chưa có lựa chọn/confirmation rõ ràng; thao tác generate phải tham chiếu script_id/version_id đã chọn.
- Chat chỉnh sửa một variant phải giữ đúng project và artifact context; khi tạo deliverable mới, lưu thành version/artifact mới, không ghi đè bản gốc.
- Project Library hiển thị rõ nhóm Scripts/Images/Videos/Research, trạng thái, thumbnail, version và selected badge; user có thể xem lại và mở lại bất kỳ bản nào.
- Storage UI hiển thị usage workspace, project và category; số liệu đối chiếu được với object storage qua reconciliation. Có cảnh báo ở các ngưỡng quota đã cấu hình.
- Người dùng xóa được một asset/version và xóa toàn bộ project; confirmation dialog nêu số lượng asset và dung lượng dự kiến giải phóng. Xóa project không để sót object, thumbnail, embedding, cache hoặc derivative sau khi deletion job hoàn tất.
- Xóa mềm/Trash cho phép restore trong retention window nếu plan/policy bật; hard delete xóa vĩnh viễn và cập nhật quota. Không tự động xóa dữ liệu chỉ vì quota đầy.
- Nếu project có content đã publish hoặc asset được tham chiếu ở nơi khác, UI phải cảnh báo và yêu cầu xử lý dependency; không giả định xóa bài trên social bên ngoài.
- Test xác nhận tenant isolation, authorization, deletion retry/idempotency, partial failure recovery và không thể truy cập asset sau khi project đã bị xóa vĩnh viễn.

**Publishing scheduler:**
- Người dùng chọn Page đã kết nối, media/creative Approved, ngày giờ và timezone; hệ thống hiển thị lại giờ địa phương trước khi xác nhận.
- Có thể tạo, sửa hoặc hủy job khi chưa vào trạng thái Publishing.
- Worker chỉ lấy job đến hạn; lưu attempt và response của provider; chống publish duplicate bằng idempotency và reconciliation.
- Khi token/permission/account/media không hợp lệ, job chuyển Failed/Needs Attention, thông báo người dùng và không retry vô hạn.
- Calendar hiển thị chính xác trạng thái và cho phép lọc theo Page, channel, campaign.
- Lịch dài hạn không bị hard-code giới hạn ngày; quota thương mại có thể áp dụng theo plan.
- Job được lưu UTC và chạy theo timezone workspace/Page đã cấu hình; xử lý daylight saving nếu timezone có áp dụng.

**Smart Scheduling:**
- Khi dữ liệu ít, hiển thị rõ là benchmark/low confidence; không gọi là giờ vàng chắc chắn.
- Khi có dữ liệu, recommendation có sample size, khoảng thời gian phân tích, metric mục tiêu và lý do.
- Không tự đổi lịch đã được duyệt; có tùy chọn chấp thuận từng đề xuất.
- Không tối ưu chỉ bằng likes; hỗ trợ reach/engagement/inbox/leads/bookings/revenue tùy dữ liệu được cấp.

### 15.1 Benchmark AI

  -----------------------------------------------------------------------
  Hạng mục                            Chỉ số đề xuất
  ----------------------------------- -----------------------------------
  Intent classification               Macro F1 mục tiêu ≥ 0,85 trên bộ
                                      test tiếng Việt nội bộ

  Hallucination giá/chính sách        0 lỗi nghiêm trọng trong bộ test
                                      nghiệm thu

  Human handoff                       100% tình huống thuộc rule
                                      escalation được chuyển người

  Response latency                    Đặt mục tiêu P95 theo
                                      model/provider và trải nghiệm thực
                                      tế

  Lead extraction                     Đo precision/recall cho tên, số
                                      điện thoại, dịch vụ, thời gian

  Workflow reliability                ≥ 99% execution thành công với các
                                      workflow P0 trong test ổn định

  Cost                                Theo dõi cost trên mỗi
                                      conversation/lead/booking
  -----------------------------------------------------------------------

Các ngưỡng là tiêu chí mục tiêu ban đầu, phải được xác nhận bằng dữ liệu
pilot.

Bổ sung benchmark cho Style Packs:
- Prompt composition correctness: 100% generation jobs trong test có đúng style snapshot theo workspace/project/modality/override.
- Style conflict resolution: không có trường hợp style default ghi đè yêu cầu cụ thể của người dùng hoặc dữ kiện thương hiệu đã xác minh.
- Style adherence: đánh giá mù theo rubric (palette, lighting, composition, texture, camera/motion, brand consistency) trên từng model; đặt ngưỡng theo modality/model sau vòng benchmark baseline.
- Cross-run consistency: đo độ ổn định phong cách giữa tối thiểu 4 output từ cùng pack/brief; đánh giá riêng image và video.
- Cost/latency overhead của Prompt Composer phải được đo; mục tiêu là nhỏ so với thời gian inference model.
- Model compatibility coverage: tỷ lệ style features supported/approximate/unsupported cho từng model adapter.

### 15.2 Bộ test cần xây

-   Khách hỏi giá nhưng bảng giá thiếu dữ liệu.
-   Khách hỏi dịch vụ không có trong danh mục.
-   Khách yêu cầu tư vấn y tế/chẩn đoán.
-   Khách khiếu nại hoặc đòi hoàn tiền.
-   Khách gửi nhiều tin liên tiếp.
-   Webhook trùng lặp hoặc đến sai thứ tự.
-   Token hết hạn hoặc bị thu hồi.
-   Nhân viên tiếp quản giữa workflow.
-   Khách yêu cầu ngừng nhận tin.
-   Comment công khai, private reply không đủ điều kiện, comment khiếu nại/spam.
-   Messenger standard window còn/mất hiệu lực tại thời điểm scheduled send.
-   Marketing Messages opt-in thiếu/sai topic hoặc recipient opt-out.
-   Segment audience có khách đã booking, khách suppression và khách trùng.
-   Không phản hồi sau N lần gửi và không tương tác X ngày; xác nhận scheduler dừng đúng.
-   High-intent notification deduplication và admin takeover.
-   Retention preview, legal hold, archive/anonymize/delete, restore và partial failure.
-   Booking trùng lịch.
-   Khách có nhiều social identity.

------------------------------------------------------------------------

## 16. Roadmap đề xuất

  -----------------------------------------------------------------------
  Giai đoạn               Thời lượng dự kiến      Deliverables
  ----------------------- ----------------------- -----------------------
  Discovery               2 tuần                  Interview, workflow map, prototype, pricing hypothesis, xác minh nguồn research/data access

  MVP Core                Tuần 3--6               Auth, workspace,
                                                  brand/service, Facebook
                                                  connection, webhook,
                                                  inbox

  MVP Conversion          Tuần 7--9               CRM, AI
                                                  classification/reply
                                                  assist, booking,
                                                  automation

  Pilot                   Tháng 3                 3--5 spa thử nghiệm, đo
                                                  KPI và
                                                  willingness-to-pay

  Growth                  Tháng 4--5              Project Workspace, persistent variants, Unified AI Orchestrator, AI Marketing Intelligence MVP, Instagram, publishing, analytics, onboarding/billing

  Scale                   Tháng 6+                Deep Research, social listening mở rộng, TikTok/Zalo, integrations, advanced attribution
  -----------------------------------------------------------------------

Thời gian Meta App Review/Business Verification là dependency bên ngoài,
không thể cam kết chính xác. Cần chạy song song prototype, mock
integration và kiểm thử nội bộ.

------------------------------------------------------------------------

## 17. Kế hoạch kiểm chứng thị trường và doanh thu

### 17.1 Discovery

Phỏng vấn tối thiểu 20 chủ spa/quản lý tại TP.HCM và Hà Nội.

Câu hỏi: - Hiện đang có bao nhiêu lead/inbox mỗi ngày? - Kênh nào tạo
nhiều khách nhất? - Ai trả lời inbox và thời gian phản hồi? - Bao nhiêu
lead không được follow-up? - Hiện đang dùng phần mềm nào? - Làm sao biết
quảng cáo nào tạo booking/doanh thu? - Sẵn sàng trả tiền cho kết quả
nào? - Có sẵn sàng kết nối Page/Instagram cho một SaaS mới không?

Không chỉ hỏi "có thích sản phẩm không"; cần quan sát quy trình thật và
hỏi về ngân sách đang chi.

### 17.2 Prototype test

-   Thiết kế prototype luồng connect Facebook → inbox → AI reply → CRM →
    booking.
-   Cho 5--8 người dùng mục tiêu thao tác.
-   Đo completion rate, lỗi hiểu UI và mức độ sẵn sàng dùng hàng ngày.

### 17.3 Paid pilot

-   Tuyển 3--5 spa.
-   Chọn một use case rõ: giảm thời gian phản hồi và tăng
    lead-to-booking.
-   Cài đặt dữ liệu dịch vụ/FAQ.
-   Theo dõi baseline trước khi dùng.
-   Thu phí pilot hoặc đặt cọc để kiểm chứng willingness-to-pay.
-   Phỏng vấn sau 2--4 tuần.

### 17.4 KPI pilot đề xuất

  KPI                           Mục tiêu giả thuyết
  ----------------------------- --------------------------------------------
  Thời gian phản hồi đầu tiên   Giảm ít nhất 30%
  Lead được ghi nhận vào CRM    ≥ 90% lead từ nguồn đã tích hợp
  Intent classification         Macro F1 ≥ 0,85 trên test set
  Workflow success              ≥ 95% trong pilot, tiến tới ≥ 99%
  Người dùng hoạt động          Owner hoặc nhân viên sử dụng hàng tuần
  Paid conversion               Có ít nhất 2 khách hàng trả tiền sau pilot

Không coi các mục tiêu này là cam kết hiệu quả; cần đo baseline và đánh
giá theo từng spa.

------------------------------------------------------------------------

## 18. Pricing hypothesis và unit economics

### 18.1 Giá thử nghiệm

  Gói                 Giá giả thuyết Khách hàng
  ------------ --------------------- ----------------------------------------
  Starter          299.000 VND/tháng Spa nhỏ, ít nhân viên
  Growth           799.000 VND/tháng Spa có marketing và inbox thường xuyên
  Business       1.990.000 VND/tháng Spa nhiều nhân viên/chi nhánh
  Enterprise                 Báo giá Chuỗi/agency

Có thể tính thêm credit cho tạo ảnh/video hoặc usage AI cao.

### 18.2 Ví dụ doanh thu định kỳ

Giả sử: - 50 khách Starter. - 50 khách Growth. - 15 khách Business.

MRR minh họa = 50 × 299.000 + 50 × 799.000 + 15 × 1.990.000 =
**84.750.000 VND/tháng**.

Đây chỉ là kịch bản số học, chưa trừ chi phí AI, hạ tầng, bán hàng, hỗ
trợ, thuế và churn; không phải dự báo doanh thu.

### 18.3 Unit economics cần theo dõi

-   AI cost/workspace/month.
-   AI cost/conversation.
-   Storage cost/workspace.
-   Cost of support/onboarding.
-   CAC.
-   Gross margin.
-   MRR/ARR.
-   Churn và retention.
-   Expansion revenue.
-   Payback period.

------------------------------------------------------------------------

## 19. Go-to-market

### Kênh khởi đầu

1.  Founder-led sales: tiếp cận trực tiếp chủ spa.
2.  Đối tác agency marketing chuyên ngành spa.
3.  Đối tác đào tạo/chuyên gia vận hành spa.
4.  Nội dung hướng dẫn tối ưu inbox, lead và booking.
5.  Referral từ spa đang sử dụng.

### Thông điệp bán hàng

Không bán "AI rất thông minh". Bán kết quả vận hành: - Không bỏ sót
khách nhắn tin. - Phản hồi nhanh hơn. - Nhân viên tư vấn nhất quán. -
Theo dõi lead đến booking. - Biết chiến dịch nào tạo khách.

### Onboarding

-   Import dịch vụ/giá/FAQ.
-   Kết nối Page.
-   Cấu hình quy tắc AI.
-   Kiểm tra 10--20 tình huống mẫu.
-   Bật AI ở chế độ gợi ý trước.
-   Chỉ bật tự động trả lời khi chủ spa phê duyệt.

------------------------------------------------------------------------

## 20. Rủi ro và phương án giảm thiểu

- Project UX quá nhiều bước: dùng wizard ngắn, progressive disclosure, autosave và template; cho phép bắt đầu với input tối thiểu.
- Quá nhiều variants gây rối: nhóm theo loại, trạng thái, stage; giới hạn compare 2–3 bản, hỗ trợ rename/favorite/archive và chỉ tạo artifact khi deliverable hoàn tất.
- Chat và artifact lệch context: mọi message/tool run phải mang project_id + artifact/version scope; UI luôn hiển thị “đang chỉnh sửa bản nào”.
- Storage tăng nhanh do video/version: quota meter, output resolution controls, cleanup riêng lẻ, archive/cold storage và cảnh báo trước khi generate.
- Xóa nhầm project/tài sản: soft delete, Trash/restore, confirmation, dependency check, audit log và deletion job có thể retry.
- Model/tool lỗi giữa workflow: state machine, idempotency, retry/cancel, giữ nguyên input và các artifact đã hoàn tất; không xóa output cũ khi job mới thất bại.

  -----------------------------------------------------------------------
  Rủi ro                  Tác động                Giảm thiểu
  ----------------------- ----------------------- -----------------------
  Meta App Review         Trễ tích hợp production Mock adapter, xin đúng
  chậm/không duyệt                                quyền, chuẩn bị video
                                                  và privacy docs sớm

  API/permission thay đổi Gián đoạn chức năng     Versioned adapter,
                                                  contract tests, theo
                                                  dõi changelog

  AI tư vấn sai           Mất uy tín/rủi ro pháp  RAG, rule engine,
                          lý                      confidence threshold,
                                                  human handoff

  Khách không muốn kết    Khó onboarding          Giải thích quyền tối
  nối tài khoản                                   thiểu, minh bạch dữ
                                                  liệu, demo trước

  Spa không nhập đủ dữ    AI trả lời thiếu chính  Onboarding checklist,
  liệu                    xác                     import template, bắt
                                                  buộc trường cốt lõi

  Chi phí AI tăng         Giảm gross margin       Usage limits, model
                                                  routing, caching,
                                                  credit system

  Cạnh tranh phần mềm     Khó khác biệt           Tập trung
  hiện hữu                                        campaign-to-booking và
                                                  automation chuyên ngành

  Attribution không chính Báo cáo gây hiểu lầm    Lưu nguồn và độ tin
  xác                                             cậy, phân biệt
                                                  attributed/unknown

  Spam/vi phạm chính sách Khóa quyền hoặc ảnh     Consent, channel policy
  kênh                    hưởng tài khoản         engine, rate limit,
                                                  opt-out
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 21. Quyết định sản phẩm cần chốt

- Customer Engagement Agent là agent riêng về nghiệp vụ/config/evaluation; không nhất thiết phải host một foundation model riêng ở giai đoạn MVP.
- Chỉ triển khai proactive Messenger outreach theo entrypoint, opt-in, marketing messaging hoặc sponsored messaging mà Meta cho phép; không cam kết cold DM toàn bộ người comment/đã từng nhắn Page.
- Chốt retention mặc định theo từng loại dữ liệu sau privacy/legal review; không xóa customer profile chỉ vì inactivity ngắn hạn.

Trước khi bắt đầu build, Product Owner cần chốt: 1. ICP đầu tiên: spa
đơn chi nhánh hay chuỗi nhỏ? 2. Facebook inbox là use case đầu tiên hay
AI content? 3. MVP có bao gồm Instagram DM ngay từ đầu không? 4. AI ở
chế độ gợi ý hay tự động trả lời? 5. Booking chỉ là lịch hẹn cơ bản hay
tích hợp phần mềm spa hiện hữu? 6. Giá theo workspace, số nhân viên, số
hội thoại hay AI credits? 7. Có hỗ trợ agency quản lý nhiều spa trong
MVP không?

**Đề xuất mặc định:** bắt đầu với spa 1--3 chi nhánh, Facebook Messenger
làm luồng chuyển đổi đầu tiên, AI reply ở chế độ gợi ý, CRM lead và
booking cơ bản. Mở rộng Instagram sau khi Facebook flow ổn định và quyền
API được xác nhận.

------------------------------------------------------------------------

## 22. Kết luận và ưu tiên thực thi

**Product principle mới:** project là “single source of truth” cho một chiến dịch; chat là cách người dùng điều khiển công việc, còn Project Library là nơi lưu deliverables. Không coi lịch sử chat là kho tài sản. Mọi script/creative/research quan trọng phải thành artifact có thể mở lại, version, so sánh, chọn và đưa qua bước tiếp theo.

Ưu tiên triển khai theo vertical slice: (1) tạo project + upload/context; (2) chat orchestrator + research; (3) script variant cards + compare/select; (4) generate ảnh/video có versioning; (5) creative chat/tool execution; (6) approve + publishing handoff; (7) storage meter + selective/project deletion. Hoàn thành luồng xuyên suốt với một dịch vụ spa mẫu trước khi mở rộng nhiều agent/model.

GrowthPilot AI nên được xây dựng như một hệ thống **Marketing-to-Revenue
Automation dành cho spa**, không phải một bộ công cụ AI rời rạc.

Thứ tự ưu tiên: 1. Workspace, Brand & Service Profile. 2. Facebook
integration: OAuth, Page, Messenger webhook. 3. Unified Inbox và CRM. 4.
AI intent classification + reply assist. 5. Booking. 6. Automation và
human handoff. 7. Analytics lead-to-booking. 8. Instagram integration.
9. AI Marketing Intelligence phải nghiên cứu trước khi đề xuất chiến dịch; Research Report có evidence, timestamp và confidence. 10. AI Creative Studio, short-video repurposing, Reusable Generation Style Packs/Prompt Composer và Facebook publishing scheduler. 11. Instagram publishing, Smart Scheduling dựa trên dữ liệu, sau đó mới mở rộng Deep Research, social listening đa nền tảng, TikTok, Zalo OA, Google Ads và tích hợp phần mềm spa.

**Nguyên tắc phát triển:** chứng minh một quy trình tạo ra booking và
giá trị kinh doanh trước; sau đó mới mở rộng số lượng kênh, model AI và
tính năng quản trị.

**Phạm vi marketing cần làm rõ:** GrowthPilot hỗ trợ organic publishing miễn phí về phía nền tảng (không cần ngân sách quảng cáo để đăng bài), nhưng không đảm bảo reach cho Page mới. Paid Ads là sản phẩm/workflow riêng; ngân sách do spa thanh toán trực tiếp cho Meta và phải có phê duyệt của người có thẩm quyền. Short video và lịch đăng giúp tăng năng lực sản xuất/phân phối nội dung, không thay thế chiến lược tạo follower, cộng đồng hoặc quảng cáo khi cần tìm khách mới.

------------------------------------------------------------------------

## Phụ lục A --- Tài liệu tham khảo

Các liên kết dưới đây là nguồn tham khảo ban đầu; cần kiểm tra lại phiên
bản, điều kiện truy cập và hiệu lực trước khi triển khai.

### Meta và tích hợp social

-   Meta for Developers: https://developers.facebook.com/
-   Graph API: https://developers.facebook.com/docs/graph-api/
-   Messenger Platform:
    https://developers.facebook.com/docs/messenger-platform/
-   Instagram Platform:
    https://developers.facebook.com/docs/instagram-platform/
-   App Review: https://developers.facebook.com/docs/app-review/
-   Meta Business: https://business.facebook.com/

### Đối thủ và thị trường

-   Sapo --- Tổng hợp phần mềm quản lý spa:
    https://www.sapo.vn/blog/phan-mem-quan-ly-spa
-   Fchat --- Bảng giá: https://fchat.vn/price
-   Haravan --- Bảng giá và tính năng:
    https://www.haravan.com/pages/pricing
-   GlobalData --- Spa in Vietnam:
    https://www.marketresearch.com/GlobalData-v3648/Spa-Vietnam-46332886/
-   Euromonitor --- Beauty and Personal Care in Vietnam:
    https://www.euromonitor.com/beauty-and-personal-care-in-vietnam/report?id=421249

### Nền tảng mở rộng

-   Zalo OA documentation: https://docs.zaloplatforms.com/docs/OA
-   TikTok Business API: https://business-api.tiktok.com/portal

### Pháp lý Việt Nam --- cần rà soát với tư vấn pháp lý

-   Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15:
    https://vanban.chinhphu.vn/?classid=1&docid=214590
-   Luật sửa đổi, bổ sung một số điều của Luật Quảng cáo 75/2025/QH15:
    https://vanban.chinhphu.vn/?classid=1&docid=214561
-   Nghị định 342/2025/NĐ-CP:
    https://chinhphu.vn/?docid=216403&pageid=27160

------------------------------------------------------------------------

**Tài liệu này là BRD định hướng sản phẩm ở cấp business/product.**
Trước khi phát triển production, cần chuyển các yêu cầu thành SRS,
Technical Design Document, ERD chi tiết, API contract, test plan và
backlog có estimate. Các permission/API của bên thứ ba và nội dung pháp
lý phải được xác minh lại tại thời điểm triển khai.


### Research/Agent workflow tham khảo (không phải dependency bắt buộc)
- OpenCreator (KrillinAI): https://github.com/krillinai/OpenCreator — tham khảo orchestration, skills, workspace và versioned creative workflow; không phải engine nghiên cứu thị trường chuyên biệt.
- Social Media Skills: https://github.com/social-media-skills/skills — tham khảo cách chia nhỏ skill cho audience research, social strategy, idea generation, publishing và analytics.
- Local Deep Researcher: https://github.com/langchain-ai/local-deep-researcher — tham khảo vòng lặp query → retrieve → summarize → identify gaps → research further → cited report.
- Social Media Research Skills: https://github.com/ScrapeCreators/social-media-research-skills — tham khảo các tác vụ research social; phải kiểm tra kỹ quyền truy cập, terms và độ sẵn có của từng provider trước khi dùng.
- Trend Opportunity Radar: https://github.com/datou202307-design/trend-opportunity-radar — tham khảo evidence-first trend research, source triangulation và counterexamples; không coi repo nhỏ này là production dependency.

Các repository trên chỉ là tài liệu tham khảo kiến trúc/skill. GrowthPilot phải tự xây permission-aware connectors, evidence ledger, quality benchmark và compliance controls. Kiểm tra license của repo, model, skill, custom node và dữ liệu trước khi triển khai thương mại.
