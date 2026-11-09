# Cài đặt dịch vụ miễn phí

Hướng dẫn đăng ký các dịch vụ GrowthPilot dùng khi chạy thật, theo đúng cách bộ cài hiện tại đang chạy. Tất cả đều có gói miễn phí; giới hạn của từng gói có thể thay đổi, nên kiểm tra lại trên trang của nhà cung cấp.

Mọi khoá lấy được ở đây đều điền vào **`backend/.env`** (copy từ [`backend/.env.example`](../backend/.env.example)). File này đã bị Git bỏ qua. **Không dán khoá vào mã nguồn, issue hay chat.**

Thứ tự nên làm:

1. [Cloudflare](#1-cloudflare-tên-miền-tunnel-r2-pages): tên miền, Tunnel, R2, Pages
2. [Supabase](#2-supabase-cơ-sở-dữ-liệu): cơ sở dữ liệu
3. [Google AI Studio](#3-google-ai-studio-gemini) và [Groq](#4-groq-qwen): AI
4. [Langfuse](#5-langfuse-theo-dõi-ai): theo dõi AI
5. [Meta for Developers](#6-meta-for-developers-fanpage-messenger-và-instagram): Fanpage, Messenger và Instagram
6. [Hugging Face](#7-hugging-face), [Modal](#8-modal-gpu-l40s-tự-bật-khi-có-việc) hoặc [Kaggle](#9-kaggle-gpu-miễn-phí-bật-tay): GPU tạo ảnh, video

Trước khi bắt đầu, tạo sẵn các khoá bí mật của riêng hệ thống:

```bash
cd backend && uv run python -c "import secrets;print('SECRET_KEY=' + secrets.token_urlsafe(48));print('META_VERIFY_TOKEN=' + secrets.token_urlsafe(24));print('MEDIA_WORKER_TOKEN=' + secrets.token_urlsafe(32))"
```

```bash
cd backend && uv run python -c "from cryptography.fernet import Fernet;print('TOKEN_ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

Dán các dòng in ra vào `backend/.env`. Giữ nguyên các khoá này sau khi đã có dữ liệu thật: đổi `TOKEN_ENCRYPTION_KEY` làm các Fanpage đã kết nối mất hiệu lực, đổi `SECRET_KEY` làm mọi người bị đăng xuất.

---

## 1. Cloudflare: tên miền, Tunnel, R2, Pages

**Đăng ký:** <https://dash.cloudflare.com/sign-up> (miễn phí).

### Tên miền

Mua tên miền ngay trong Cloudflare (Domain Registration), hoặc thêm tên miền đã có (Add a domain) rồi đổi nameserver ở nơi bạn mua sang hai nameserver Cloudflare đưa. Bộ cài hiện tại dùng `growthpilot-spa.online`:

- `api.<tên-miền>`: API (qua Tunnel)
- `<tên-miền>`: web (qua Pages)

### Tunnel: đưa API ra internet mà không mở cổng

Facebook và Kaggle cần gọi được API qua HTTPS. Tunnel làm việc này kể cả khi API chạy trên máy cá nhân.

1. **Zero Trust → Networks → Tunnels → Create a tunnel → Cloudflared**, đặt tên, ví dụ `growthpilot`.
2. Làm theo lệnh cài connector cho hệ điều hành của máy chạy API. Trên macOS:

   ```bash
   brew install cloudflared
   ```

   Sau đó chạy lệnh `sudo cloudflared service install <token>` mà Cloudflare hiển thị, để Tunnel tự chạy khi bật máy.
3. Tab **Public Hostname → Add**: subdomain `api`, domain `<tên-miền>`, service `HTTP` → `localhost:8000` (đúng cổng API đang chạy).
4. Trong `backend/.env`:

   ```
   API_PUBLIC_URL=https://api.<tên-miền>
   ```

5. Kiểm tra: mở `https://api.<tên-miền>/healthz` phải thấy `{"ok":true}`.

### R2: lưu ảnh, video, tài liệu

Gói miễn phí có 10 GB lưu trữ và không tính phí băng thông tải xuống.

1. **R2 Object Storage → Create bucket**, tên `growthpilot-media`. Lần đầu dùng R2, Cloudflare có thể yêu cầu thêm thẻ thanh toán dù vẫn trong gói miễn phí.
2. **R2 → Manage API tokens → Create API token**, quyền **Object Read & Write**, chỉ cho bucket `growthpilot-media`. Ghi lại *Access Key ID* và *Secret Access Key* (chỉ hiện một lần).
3. **Account ID** nằm ở trang tổng quan R2.
4. **Bucket → Settings → CORS policy**: dán đoạn dưới đây (sửa tên miền cho đúng) để trình duyệt tải tệp thẳng lên R2:

   ```json
   [
     {
       "AllowedOrigins": ["http://localhost:3000", "https://<tên-miền>"],
       "AllowedMethods": ["GET", "PUT", "HEAD"],
       "AllowedHeaders": ["*"],
       "ExposeHeaders": ["ETag"],
       "MaxAgeSeconds": 3600
     }
   ]
   ```

5. Trong `backend/.env`:

   ```
   R2_ACCOUNT_ID=...
   R2_ACCESS_KEY_ID=...
   R2_SECRET_ACCESS_KEY=...
   R2_BUCKET=growthpilot-media
   ```

### Pages: đưa web lên

Web là trang tĩnh (static export), nên Cloudflare Pages phục vụ miễn phí.

1. Đăng nhập Wrangler một lần (mở trình duyệt để xác nhận):

   ```bash
   cd frontend && npx wrangler login
   ```

2. Sửa `routes` trong `frontend/wrangler.jsonc` thành tên miền của web (ví dụ `app.<tên-miền>`), rồi build với địa chỉ API thật và đẩy lên. Wrangler tự tạo bản ghi DNS và chứng chỉ cho tên miền đó:

   ```bash
   cd frontend && NEXT_PUBLIC_API_URL=https://api.<tên-miền> npm run build && npx wrangler deploy
   ```

3. Trong `backend/.env`, cho phép web gọi API:

   ```
   FRONTEND_URL=https://<tên-miền>
   CORS_ORIGINS=["https://<tên-miền>","http://localhost:3000"]
   ```

## 2. Supabase: cơ sở dữ liệu

**Đăng ký:** <https://supabase.com/dashboard> (đăng nhập bằng GitHub). Gói miễn phí có 500 MB cơ sở dữ liệu; dự án tự tạm dừng sau một tuần không có truy cập.

1. **New project**: đặt tên, tạo mật khẩu cơ sở dữ liệu mạnh (lưu vào trình quản lý mật khẩu), chọn vùng gần Việt Nam: **Northeast Asia (Tokyo)** hoặc **Southeast Asia (Singapore)**.
2. **Database → Extensions**: bật **vector** (kho kiến thức AI cần pgvector).
3. Nút **Connect** ở đầu trang → **Session pooler** → copy chuỗi kết nối. Đổi `postgresql://` ở đầu thành `postgresql+psycopg://` và thay `[YOUR-PASSWORD]` bằng mật khẩu ở bước 1:

   ```
   DATABASE_URL=postgresql+psycopg://postgres.<project-ref>:<mật-khẩu>@aws-0-<vùng>.pooler.supabase.com:5432/postgres
   ```

4. **Project Settings → Database → SSL Configuration → Download certificate**, lưu vào `backend/certs/` (thư mục đã bị Git bỏ qua):

   ```
   POSTGRES_SSL_ROOT_CERT=certs/prod-ca-2021.crt
   ```

5. Tạo bảng:

   ```bash
   cd backend && uv run alembic upgrade head
   ```

## 3. Google AI Studio: Gemini

Dùng cho nghiên cứu thị trường, viết kịch bản, đọc tài liệu và chọn đoạn hay khi cắt Shorts.

1. Vào <https://aistudio.google.com/apikey>, đăng nhập Google, **Create API key**.
2. Trong `backend/.env`:

   ```
   GEMINI_API_KEY=...
   ```

Gói miễn phí giới hạn số lượt gọi mỗi phút và mỗi ngày; khi hết, hệ thống tự thử các mô hình Gemini nhẹ hơn. Muốn AI tự tìm kiếm Google khi nghiên cứu, bật thanh toán cho dự án Google Cloud của khoá rồi đặt `GEMINI_SEARCH=true`. Lưu ý: ở gói miễn phí, Google có thể dùng nội dung gửi lên để cải thiện sản phẩm; GrowthPilot đã che số điện thoại và email trước khi gửi.

## 4. Groq: Qwen

Dùng để trả lời tin nhắn khách vì phản hồi rất nhanh. Khi Groq lỗi hoặc hết lượt, hệ thống tự chuyển sang Gemini.

1. Vào <https://console.groq.com/keys>, đăng nhập, **Create API Key**.
2. Trong `backend/.env`:

   ```
   GROQ_API_KEY=...
   ```

## 5. Langfuse: theo dõi AI

Ghi lại từng lần gọi AI (câu hỏi, câu trả lời, số token, thời gian, lỗi) để kiểm tra chất lượng. Không bắt buộc; để trống thì tắt.

1. Vào <https://cloud.langfuse.com>, tạo organization và project.
2. **Project Settings → API Keys → Create new API keys**.
3. Trong `backend/.env`:

   ```
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_BASE_URL=https://cloud.langfuse.com
   ```

## 6. Meta for Developers: Fanpage, Messenger và Instagram

Cần một tài khoản Facebook là **admin của Fanpage** spa.

1. Vào <https://developers.facebook.com/apps> → **Create app**. Chọn mục đích liên quan tới quản lý Page và nhắn tin cho doanh nghiệp, gắn với Business portfolio của spa nếu có.
2. **App settings → Basic**: ghi lại **App ID** và **App Secret**.
3. Thêm sản phẩm **Facebook Login** (app loại Business gọi là **Facebook Login for Business**). Trong phần cài đặt của nó, mục **Valid OAuth Redirect URIs** điền:

   ```
   https://api.<tên-miền>/api/v1/integrations/meta/callback
   ```

4. Thêm sản phẩm **Webhooks**, chọn đối tượng **Page**:
   - **Callback URL:** `https://api.<tên-miền>/api/v1/webhooks/meta`
   - **Verify token:** đúng giá trị `META_VERIFY_TOKEN` đã tạo ở đầu
   - Bấm **Verify and save** (API phải đang chạy), rồi **Subscribe** trường `messages`.
5. Trong `backend/.env`:

   ```
   META_APP_ID=...
   META_APP_SECRET=...
   META_VERIFY_TOKEN=...
   META_DRY_RUN=false
   ```

   Để `META_DRY_RUN=true` nếu chỉ muốn chạy thử: tin nhắn và bài đăng được ghi lại nhưng không gửi lên Facebook.
6. Khởi động lại API, vào web: **Cài đặt → Facebook & Instagram → Kết nối bằng Facebook**, chọn Page.

**Instagram (chỉ đăng bài):** GrowthPilot đăng ảnh và Reels lên Instagram của spa bằng chính lần kết nối Facebook ở trên.
- Chuyển Instagram sang **tài khoản chuyên nghiệp** (Business hoặc Creator) trong app Instagram: **Cài đặt → Loại tài khoản và công cụ**.
- Liên kết Instagram đó với Fanpage: trên Facebook, vào Page → **Cài đặt → Tài khoản đã liên kết → Instagram**.
- Trong app Meta, thêm use case **Manage messaging & content on Instagram** để có quyền `instagram_basic` và `instagram_content_publish`.
- Bấm **Kết nối bằng Facebook** lại; tài khoản `@tên` hiện thêm dưới Page. Khi đăng, chọn "· Instagram" ở ô **Đăng lên**.

Instagram chỉ nhận ảnh JPG (GrowthPilot tự đổi ảnh PNG) và nội dung tối đa 2.200 ký tự; video được đăng dạng Reels. Tin nhắn và bình luận Instagram chưa vào hộp thư: phần đó cần Meta duyệt quyền `instagram_manage_messages` và xác minh doanh nghiệp.

Khi app còn ở chế độ **Development**, chỉ tài khoản có vai trò trong app mới nhắn được tới GrowthPilot. Thêm nhân viên làm Tester ở **App Roles → Roles** để thử. Muốn phục vụ mọi khách, làm theo [docs/meta-app-review.md](meta-app-review.md).

## 7. Hugging Face

Notebook tải mô hình tạo ảnh, video, nhạc từ Hugging Face; có token thì tải nhanh và ổn định hơn.

1. Đăng ký <https://huggingface.co/join>.
2. **Settings → Access Tokens → Create new token**, loại **Read**.
3. Token này điền vào secret của Modal (bước 8) hoặc Kaggle (bước 9). Nếu dùng Modal, ghi thêm `HF_TOKEN=` vào `backend/.env` để lệnh tạo secret đọc được.

## 8. Modal: GPU L40S tự bật khi có việc

Nên dùng cách này. Khi bạn bấm **Tạo ảnh & video**, API tự bật một GPU L40S 48GB trên Modal; làm xong và rảnh 2 phút thì tự tắt nên không tốn tiền lúc chờ. Một video 3 cảnh mất khoảng 10–15 phút (Kaggle T4: khoảng 75 phút). Gói Starter có $30 miễn phí mỗi tháng, một video tốn khoảng $0.4–0.7; xem số thật ở mục **Usage** trên modal.com.

1. Đăng ký <https://modal.com/signup>, rồi đăng nhập trên máy chạy API:

   ```bash
   uvx modal token new
   ```

2. Tạo secret `growthpilot-worker` từ `backend/.env`, không hiện giá trị ra màn hình (chạy ở thư mục gốc của repo):

   ```bash
   f=$(mktemp) && chmod 600 "$f" && { echo "GP_API_URL=$(grep -E '^API_PUBLIC_URL=' backend/.env | cut -d= -f2-)"; grep -E '^(MEDIA_WORKER_TOKEN|HF_TOKEN)=' backend/.env; } > "$f" && uvx --with python-dotenv modal secret create growthpilot-worker --from-dotenv "$f" --force; rm -f "$f"
   ```

3. Deploy. Lần đầu mất khoảng 50 phút vì Modal biên dịch sd-cli cho L40S; các lần sau chỉ vài giây:

   ```bash
   uvx modal deploy notebooks/modal/growthpilot.py
   ```

4. Tải khoảng 70GB mô hình về ổ lưu của Modal (chạy bằng CPU, làm một lần):

   ```bash
   uvx modal run notebooks/modal/growthpilot.py::download
   ```

5. Thêm `MODAL_APP=growthpilot` vào `backend/.env`, rồi khởi động lại API và worker.

Mỗi lần sửa `notebooks/kaggle/*.py` thì chạy lại bước 3. Nếu Modal lỗi hoặc hết tiền, API chỉ ghi log; khi đó chạy Kaggle bằng tay như bước 9.

## 9. Kaggle: GPU miễn phí, bật tay

Kaggle cho dùng GPU miễn phí khoảng 30 giờ mỗi tuần. Notebook tự hỏi API xem có việc không, làm xong thì tải kết quả lên R2. Notebook không giữ khoá cơ sở dữ liệu hay R2.

1. Đăng ký <https://www.kaggle.com>, rồi **Settings → Phone verification**. Phải xác minh số điện thoại mới bật được GPU và Internet cho notebook.
2. **Settings → API → Create New Token** để dùng Kaggle CLI. Lưu file token vào `~/.kaggle/` trên máy, không đưa vào repo. Các lệnh dưới đây chạy CLI qua `uvx` nên không cần cài riêng.
3. Đóng gói và đẩy code lên (thay `<username>` bằng tên Kaggle của bạn):

   ```bash
   KAGGLE_USERNAME=<username> python notebooks/kaggle/build.py
   ```

   ```bash
   uvx --with six kaggle datasets create -p notebooks/kaggle/dist/dataset
   ```

   ```bash
   uvx --with six kaggle kernels push -p notebooks/kaggle/dist/nb1 --no-run --accelerator NvidiaTeslaT4
   ```

   Làm tương tự với `dist/nb2` cho Notebook 2. Lần cập nhật sau dùng `uvx --with six kaggle datasets version -p notebooks/kaggle/dist/dataset -m "update"` thay cho `create`.
4. Mở notebook trên Kaggle, ở thanh bên phải:
   - **Session options → Accelerator:** `GPU T4 x2` (Notebook 1) hoặc `GPU T4 x1` (Notebook 2)
   - **Internet:** On
   - **Add-ons → Secrets:** thêm 3 secret và **tick Attached** cho từng cái:

     | Tên | Giá trị |
     | --- | --- |
     | `GP_API_URL` | `https://api.<tên-miền>` |
     | `MEDIA_WORKER_TOKEN` | đúng giá trị `MEDIA_WORKER_TOKEN` trong `backend/.env` |
     | `HF_TOKEN` | token Hugging Face ở bước 7 |

5. **Save Version → Save & Run All**. Notebook chạy tối đa khoảng 12 giờ mỗi phiên và tự tắt sau 60 phút không có việc.

Luôn đẩy code với `--no-run` và chạy notebook từ giao diện Kaggle: lượt chạy do lệnh `push` khởi động không nhận được Secrets nên sẽ dừng ngay.

---

## Kiểm tra sau khi cài

```bash
cd backend && uv run pytest
```

- `https://api.<tên-miền>/healthz` mở được.
- Đăng nhập web, tải một tài liệu lên dự án: tệp phải hiện trong bucket R2.
- Nhắn vào Fanpage bằng một tài khoản Tester: tin hiện trong **Hộp thư** kèm gợi ý của AI.
- Trên Langfuse thấy các lượt gọi AI mới.
