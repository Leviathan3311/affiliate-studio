# GrowthPilot AI (affiliate-studio)

Nền tảng giúp spa trả lời khách Facebook Messenger bằng AI, quản lý khách hàng và lịch hẹn.
Tài liệu gốc: [BRD v1.6](GrowthPilot_AI_BRD_v1.6.md) · [System design v2.1](growthpilot_ai_system_design_v2_0.md).

## Đã có (lát cắt P0 — Tuần 1–2 của system design)

| Phần | Nội dung | Mã nguồn |
| --- | --- | --- |
| Tài khoản & RBAC | Đăng ký/đăng nhập JWT, workspace, 5 vai trò, audit log | `backend/app/api/auth.py`, `workspaces.py`, `deps.py` |
| Brand & dịch vụ | Thương hiệu, chi nhánh (sức chứa), dịch vụ & giá, FAQ — nguồn duy nhất AI được trích | `backend/app/api/brand.py` |
| Meta | OAuth kết nối Page, kết nối thủ công bằng Page token (pilot), webhook xác thực `X-Hub-Signature-256`, chống trùng | `backend/app/meta.py`, `api/integrations.py` |
| Hàng đợi & worker | Postgres làm queue (`SKIP LOCKED`), ingest → khách/lead/hội thoại, retry + dead-letter | `backend/app/worker.py`, `engagement.py` |
| LLM Router | Groq `qwen/qwen3.8-27b` chính → fallback Gemini 3.8 Flash; che SĐT/email trước khi gửi; log model/latency/token | `backend/app/ai/llm.py` |
| Customer Engagement Agent | Chế độ gợi ý (mặc định) hoặc tự trả lời theo ngưỡng; chặn giá không có trong bảng giá; phát hiện intent cao → thông báo | `backend/app/ai/engagement.py` |
| Messaging Policy Engine | Cửa sổ 24h, giờ yên lặng 22:00–08:00, opt-out, tạm dừng tự động — mọi tin gửi đi đều qua đây | `backend/app/policy.py` |
| Chế độ đêm | Không gọi LLM, gửi 1 tin mẫu/đêm, gom toàn bộ tin đêm thành 1 lần gọi LLM lúc 08:00 | `engagement.ingest_event` |
| CRM, Booking, Analytics | Hồ sơ 360, lead, chặn chăm sóc; lịch hẹn kiểm tra trùng slot & chuyển trạng thái; dashboard | `api/crm.py`, `bookings.py`, `dashboard.py` |
| Web | Next.js 16: Tổng quan, Hộp thư (gợi ý AI + quyết định chính sách), Khách hàng, Lịch hẹn, Cài đặt | `frontend/` |

**Chưa làm (đợt sau):** Kaggle Notebook 1/2 (FLUX.2, MiniMax H3, ACE-Step, WhisperX…), Project Creative Workspace & Style Packs, bình luận Facebook, đăng bài/lịch đăng, Messenger outreach theo tệp, retention policy, mời thành viên qua email, quên mật khẩu, RAG bằng pgvector (hiện dùng so khớp từ khoá).

## Chạy local

Yêu cầu: Python 3.13 + [uv](https://docs.astral.sh/uv/), Node 22+.

```bash
cd backend && cp .env.example .env && uv sync && uv run alembic upgrade head
```

```bash
cd backend && uv run python -m scripts.seed_demo
```

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
```

```bash
cd backend && uv run python -m app.worker
```

```bash
cd frontend && npm install && npm run dev
```

Mở http://localhost:3000, đăng nhập `demo@growthpilot.vn` / `demo12345` (dữ liệu mẫu từ `seed_demo`; khi chưa có API key LLM, câu trả lời AI trong seed là dữ liệu mẫu cố định).

Hoặc toàn bộ bằng Docker (Postgres + pgvector):

```bash
docker compose up --build
```

## Kết nối Facebook Page đầu tiên

1. Tạo app trên developers.facebook.com, điền `META_APP_ID`, `META_APP_SECRET` vào `backend/.env`.
2. Webhook callback: `{API_PUBLIC_URL}/api/v1/webhooks/meta`, verify token = `META_VERIFY_TOKEN`, subscribe `messages`. API phải có HTTPS công khai (Cloudflare Tunnel như system design §4.2).
3. Cài đặt → Facebook Page → "Kết nối bằng Facebook" (hoặc dán Page token khi app chưa qua App Review).
4. Giữ `META_DRY_RUN=true` cho tới khi kiểm thử xong: tin gửi đi chỉ được ghi lại, không gọi Send API.

## Kiểm thử

```bash
cd backend && uv run pytest
```

```bash
cd frontend && npx tsc --noEmit && npm run lint && npm run build
```
