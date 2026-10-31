# GrowthPilot AI — Kiến trúc Hệ thống (System Design) & Chiến lược Hạ tầng Toàn diện

**Phiên bản:** 2.1 (Cập nhật LLM Routing: `Qwen3.8-27B` trực khách chính + `Gemini 3.8 Flash` dự phòng & chuyên trách Viral Shorts / Nghiên cứu thị trường / Viết kịch bản)
**Ngày lập:** 31/10/2026
**Ngành dọc mục tiêu:** Spa & Thẩm mỹ viện tại Việt Nam

## 1. Tổng quan Kiến trúc Hệ thống (End-to-End Architecture)

Hệ thống GrowthPilot AI được thiết kế theo mô hình **Hybrid Modular Monolith + Distributed GPU Workers (Kaggle)** nhằm giải quyết bài toán cốt lõi của BRD v1.6: vừa vận hành mượt mà **Project-based AI Creative Workspace** (tạo ảnh, video quảng cáo, BGM, cắt Shorts/Reels), vừa duy trì **Customer Engagement Agent** trực chiến từ sáng đến tối để phản hồi bình luận/tin nhắn Facebook Page, quản lý CRM và chốt lịch hẹn (Booking) với chi phí hạ tầng khởi đầu gần như bằng **0 VNĐ**.

Hệ thống được chia thành **4 tầng (Tiers)** độc lập để tách biệt tải xử lý nặng (GPU Media Generation) khỏi luồng phản hồi thời gian thực (Real-time Webhook & Chat):

```
+--------------------------------------------------------------------------------------------------+
|                                    TẦNG 1: CLIENT & KÊNH SOCIAL                                  |
|  [Chủ Spa / Nhân viên: Web UI (Next.js)]           [Khách hàng: Facebook Page / Messenger / IG]  |
+--------------------------------------------------------------------------------------------------+
                     | (HTTPS / REST / SSE)                               | (Meta Graph Webhooks)
                     v                                                    v
+--------------------------------------------------------------------------------------------------+
|                        TẦNG 2: CORE APPLICATION SERVER (MODULAR MONOLITH)                        |
|                                   FastAPI (Python) + Background Workers                          |
|                                                                                                  |
|  +-----------------------------+  +-----------------------------+  +--------------------------+  |
|  | Project Creative Workspace  |  | Unified AI Orchestrator     |  | Social & CRM Engine      |  |
|  | - Wizard & Context Manager  |  | - Research & Script Agents  |  | - Webhook Gateway        |  |
|  | - Style Pack & Prompt Comp. |  | - Conversational Editor     |  | - Messaging Policy Engine|  |
|  | - Artifact Version Graph    |  | - LLM Router & Fallback     |  | - Follow-up Scheduler    |  |
|  +-----------------------------+  +-----------------------------+  +--------------------------+  |
+--------------------------------------------------------------------------------------------------+
         | (SQL / Vector)                  | (LLM API Calls)              | (Job Queue / Tunnel)
         v                                 v                              v
+-------------------------+   +-----------------------------+   +----------------------------------+
| TẦNG 3: DATA & STORAGE  |   | TẦNG 4A: CLOUD LLM ROUTER   |   | TẦNG 4B: KAGGLE GPU MEDIA WORKER |
|                         |   |                             |   |      (2 Notebooks x 32GB VRAM)   |
| - PostgreSQL + pgvector |   | - Luồng 1 (CSKH 08h-22h):   |   |                                  |
|   (Supabase / Self-host)|   |   + Chính: Qwen3.8-27B(Groq)|   | - Notebook 1: Visual & Ad Video  |
| - Redis Queue & Cache   |   |   + Phụ: Gemini 3.8 Flash   |   |   + FLUX.2 [klein] 9B / [dev] 32B|
|   (Upstash / Local)     |   | - Luồng 2 (Chiến lược/Media)|   |   + MiniMax H3 (I2VA/Ref2VA)     |
| - Object Storage        |   |   + Research -> Kịch bản    |   |   + ACE-Step 1.5 + FFmpeg (25%)  |
|   (Cloudflare R2 - 10GB)|   |   + Chọn đoạn Viral Shorts  |   | - Notebook 2: Viral Shorts 9:16  |
|                         |   |   (Gemini 3.8 Flash / 2.5Pro|   |   + WhisperX (large-v3-turbo)    |
|                         |   | - Luồng 3 (22:00 - 08:00):  |   |   + Gemini 3.8 Flash (Viral Cut) |
|                         |   |   Quiet Hours Queue & Rule  |   |   + YOLOv8-face + FFmpeg Karaoke |
+-------------------------+   +-----------------------------+   +----------------------------------+
```

### Nguyên tắc Vận hành Cốt lõi
1. **Tách biệt Control Plane và Media Plane:** Server chính (FastAPI) chỉ xử lý logic nghiệp vụ, ghép prompt qua **Prompt Composer** (kèm **Reusable Generation Style Packs**), kiểm duyệt chính sách qua **Messaging Policy Engine** và lưu trữ metadata. Toàn bộ tác vụ nặng (vẽ ảnh, dựng video, sinh nhạc, cắt Shorts) được đẩy qua hàng đợi tới **2 Kaggle Notebooks** thông qua kết nối bảo mật [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) hoặc cơ chế Worker Polling từ [Upstash Redis](https://upstash.com/pricing/redis).
2. **Không bao giờ lưu file media vào Database:** Ảnh gốc sản phẩm, ảnh studio từ FLUX.2, video từ MiniMax H3 và các bản cắt Shorts 9:16 được tải trực tiếp từ Kaggle lên [Cloudflare R2](https://developers.cloudflare.com/r2/pricing/) (miễn phí 10 GB lưu trữ và miễn phí 100% băng thông tải ra - zero egress fee), chỉ trả URL và metadata (`storage_objects`, `project_artifact_versions`) về PostgreSQL.

## 2. Thiết kế Chi tiết AI Media Pipeline & Phân chia 2 Kaggle Notebooks

Mỗi tài khoản [Kaggle](https://www.kaggle.com/discussions/general/108481) cung cấp miễn phí định mức khoảng **30 giờ GPU/tuần** với cấu hình máy ảo chọn được **Accelerator: GPU T4 x2** (2 card NVIDIA Tesla T4 × 16 GB = **tổng cộng 32 GB VRAM**, kèm khoảng 29–30 GB System RAM).

Nếu nhồi nhét cả 4 bước (FLUX.2 + MiniMax H3 + ACE-Step 1.5 + WhisperX + YOLOv8-face) vào chung 1 Notebook, bạn sẽ lập tức gặp 3 nút thắt:
- **Tràn ổ cứng tạm (`/kaggle/working` & `/root/.cache`):** Tổng dung lượng weights của FLUX.2 (10–19 GB), MiniMax H3 (11.4 GB), ACE-Step 1.5 (~3–4 GB) và WhisperX (~3 GB) vượt ngưỡng lưu trữ an toàn của 1 phiên làm việc.
- **Xung đột thư viện (Dependency Hell):** ComfyUI/Diffusers đời mới cho FLUX.2 và MiniMax H3 thường xung đột phiên bản `torch`, `torchaudio`, `ctranslate2` và `onnxruntime-gpu` với `WhisperX` và `SamurAIGPT/AI-Youtube-Shorts-Generator`.
- **Xung đột luồng nghiệp vụ:** Bước 1–2–3 thuộc luồng **Tạo mới (Generative Studio)** chạy nối tiếp nhau (Ảnh → Video + SFX → Nhạc BGM), trong khi Bước 4 thuộc luồng **Tái sử dụng (Video Repurposing)** có thể nhận cả video từ Bước 3 lẫn video dài do chủ spa tự quay tải lên (theo `MOD-04` trong BRD).

Do đó, phương án chia thành **2 Kaggle Notebooks chuyên biệt** dưới đây tối ưu hóa toàn bộ 32 GB VRAM (2× T4) và tránh hoàn toàn lỗi tràn bộ nhớ (OOM).

### Bảng Phân bổ Tài nguyên & Nhiệm vụ giữa 2 Kaggle Notebooks

| Tiêu chí | Notebook 1: `GrowthPilot-Generative-Studio` (Bước 1 + Bước 2 + Bước 3) | Notebook 2: `GrowthPilot-Shorts-Repurposer` (Bước 4) |
| :--- | :--- | :--- |
| **Vai trò trong BRD** | Đảm nhận phần **Generative AI Creative Studio** (`MOD-04`): Từ ảnh chụp điện thoại + Style Pack → Ảnh Studio/Thumbnail → Video quảng cáo có tiếng động/lời thoại → Video hoàn chỉnh có nhạc nền BGM. | Đảm nhận phần **Short Video Repurposing** (`MOD-04`): Nhận video quảng cáo hoặc video dài của spa → Bóc băng mili-giây → Chọn đoạn viral → Bám mặt crop dọc 9:16 + đốt phụ đề Karaoke. |
| **Cấu hình phần cứng** | Kaggle **GPU T4 x2** (`cuda:0` = 16 GB VRAM, `cuda:1` = 16 GB VRAM). | Kaggle **GPU T4 x1** (16 GB VRAM) hoặc **GPU T4 x2** (chạy song song nhiều clip). |
| **Models & Dung lượng VRAM** | 1. **FLUX.2 [klein] 9B** (FP8 / GGUF Q8 ~9.5 GB) hoặc **FLUX.2 [dev] 32B** (GGUF Q4_K_M ~18.5 GB chia 2 GPU).<br>2. **MiniMax H3** (GGUF Q4_K_M 11.4 GB + H3-Turbo-LoRA 8-steps ~12.5 GB VRAM khi suy luận).<br>3. **ACE-Step 1.5** (`ace-step/ACE-Step` ~3.5 GB VRAM). | 1. **WhisperX** (`large-v3-turbo` ~3.2 GB VRAM + Wav2Vec2 alignment ~1 GB VRAM).<br>2. **Gemini 3.8 Flash API** (Gọi qua mạng 0 GB VRAM).<br>3. **YOLOv8-face** (~0.8 GB VRAM).<br>4. **FFmpeg NVENC** (`h264_nvenc` đốt phụ đề ASS). |
| **Cơ chế Quản trị VRAM (Anti-OOM)** | **Phương án A (Dùng FLUX.2 [klein] 9B - Khuyên dùng cho tốc độ cao):**<br>- Pin cố định **FLUX.2 [klein] 9B** (~9.5 GB) + **ACE-Step 1.5** (~3.5 GB) trên **`cuda:0`** (tổng ~13 GB / 16 GB).<br>- Pin cố định **MiniMax H3 GGUF Q4_K_M + Turbo LoRA** (~12.5 GB) trên **`cuda:1`** (12.5 GB / 16 GB).<br>→ *Không cần nạp/xóa model giữa chừng, tốc độ sinh ảnh + video + nhạc nhanh gấp 3 lần!*<br><br>**Phương án B (Dùng FLUX.2 [dev] 32B Q4_K_M khi cần độ chi tiết tối đa):**<br>- Dùng `device_map="balanced"` trải FLUX.2 32B qua cả `cuda:0` và `cuda:1` (~9.5 GB mỗi card). Sau khi xuất ảnh xong, gọi `torch.cuda.empty_cache()` và offload FLUX.2 xuống System RAM (29 GB) trước khi nạp MiniMax H3 lên `cuda:1`. | Tổng VRAM của cả WhisperX (`large-v3-turbo`) + YOLOv8-face chỉ chiếm khoảng **5 GB VRAM**, nằm gọn trong 1 card T4 16 GB mà không bao giờ bị tràn bộ nhớ, cho phép xử lý video dài từ 5–30 phút cực kỳ ổn định. |

### Luồng Xử lý Chi tiết trong Notebook 1 (`GrowthPilot-Generative-Studio`)

```
[Input: Ảnh sản phẩm chụp điện thoại + Composed Prompt (đã ghép Style Pack từ Backend)]
       |
       v
+-----------------------------------------------------------------------------------+
| GIAI ĐOẠN 1: TẠO ẢNH STUDIO & THUMBNAIL (Trên GPU 0 - cuda:0)                     |
| - Nếu có ảnh sản phẩm thật: Tách nền tự động -> Đưa vào FLUX.2 [klein] 9B (FP8/Q8)|
|   vẽ lại bối cảnh spa sang trọng (theo Style Pack) + giữ nguyên sản phẩm gốc.     |
| - Nếu làm Banner/Thumbnail: FLUX.2 trực tiếp vẽ ảnh + render chữ Slogan sắc nét.  |
| - Xuất file: `studio_master.png` & `thumbnail_banner.png` -> Upload Cloudflare R2.|
+-----------------------------------------------------------------------------------+
       | (Truyền `studio_master.png` sang GPU 1)
       v
+-----------------------------------------------------------------------------------+
| GIAI ĐOẠN 2: TẠO VIDEO QUẢNG CÁO + SFX + GIỌNG THOẠI (Trên GPU 1 - cuda:1)        |
| - Model: MiniMax H3 (GGUF Q4_K_M 11.4GB) + H3-Turbo-LoRA (chỉ cần 8-steps).       |
| - Chế độ I2VA (Image-to-Video-Audio) hoặc Ref2VA: Biến `studio_master.png` thành  |
|   video quảng cáo (có người mẫu hoặc cận cảnh sản phẩm).                          |
| - Tự động sinh đồng bộ kênh âm thanh Stereo 32kHz: tiếng động vật lý (tiếng rót   |
|   nước, bước chân, suối chảy spa) + giọng nói nhép môi khớp từng khung hình.      |
| - Xuất file tạm: `raw_ad_with_sfx_voice.mp4`.                                     |
+-----------------------------------------------------------------------------------+
       | (Kích hoạt song song hoặc nối tiếp trên GPU 0)
       v
+-----------------------------------------------------------------------------------+
| GIAI ĐOẠN 3: TẠO NHẠC NỀN (BGM) & HOÀN THIỆN AUDIO MIX (Trên GPU 0 + CPU FFmpeg)  |
| - Model: ACE-Step 1.5 (`ace-step/ACE-Step`) sinh bản nhạc thương mại (15-60s)     |
|   theo mood của Style Pack chỉ trong vài giây -> Xuất `bgm_track.wav`.            |
| - FFmpeg Audio Mixing Pipeline:                                                   |
|   Lấy audio gốc (SFX + Voice 100%) từ `raw_ad_with_sfx_voice.mp4` trộn với        |
|   `bgm_track.wav` được hạ âm lượng xuống đúng 25% (`volume=0.25`) kèm hiệu ứng    |
|   fade-in/fade-out mượt mà:                                                       |
|   `ffmpeg -i raw_ad.mp4 -i bgm.wav -filter_complex "[1:a]volume=0.25[bgm];        |
|    [0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"             |
|    -map 0:v -map "[aout]" -c:v copy -c:a aac -ar 32000 final_commercial.mp4`      |
| - Upload `final_commercial.mp4` lên Cloudflare R2 -> Báo hoàn tất về Backend.     |
+-----------------------------------------------------------------------------------+
```

### Luồng Xử lý Chi tiết trong Notebook 2 (`GrowthPilot-Shorts-Repurposer`)

Notebook 2 fork và nâng cấp trực tiếp từ bộ khung `SamurAIGPT/AI-Youtube-Shorts-Generator` với 3 lõi đã thay thế hoàn toàn theo yêu cầu của bạn:

1. **Bước 4.1 — Nghe & Căn chỉnh Phụ đề Mili-giây (`WhisperX large-v3-turbo`):**
   - Tách luồng âm thanh gốc từ video đầu vào (vẫn bảo toàn nguyên vẹn âm thanh Stereo/BGM để ghép lại ở bước cuối).
   - Chạy `WhisperX` với model `large-v3-turbo` để nhận diện tiếng Việt/tiếng Anh tốc độ cao, sau đó chạy mô hình **Forced Alignment (Wav2Vec2)** để lấy chính xác `start_ms` và `end_ms` của **từng từ (word-level timestamps)**.
   - Xuất ra cấu trúc JSON và tạo file phụ đề `.ass` (Advanced SubStation Alpha) có thẻ hiệu ứng Karaoke (`\k`, `\kf`) làm nổi bật từng chữ ngay khi người nói phát âm.
2. **Bước 4.2 — Chọn Đoạn Viral Thông minh (`Gemini 3.8 Flash API` thay thế OpenAI trong `LanguageTasks.py`):**
   - Sửa trực tiếp hàm gọi LLM trong `Components/LanguageTasks.py`: thay vì dùng thư viện `openai` tốn phí, chuyển sang gọi SDK `google-genai` với model `gemini-3.8-flash` (hoặc `gemini-2.5-flash` làm fallback, sử dụng API Key miễn phí từ [Google AI Studio](https://aistudio.google.com/docs/models)).
   - Nhờ cửa sổ ngữ cảnh **1.048.576 tokens (1M context)** và khả năng trả về **Structured Outputs (JSON Schema)** của `Gemini 3.8 Flash`, hệ thống gửi toàn bộ bản bóc băng có gắn mốc thời gian kèm thông tin dịch vụ spa (từ `MOD-02 Brand Profile`) để Gemini chọn ra **2–5 phân đoạn gay cấn/cuốn hút nhất (15–30 giây)** có chứa Hook mạnh, giải quyết nỗi đau khách hàng và CTA rõ ràng.
3. **Bước 4.3 — Bám Khuôn mặt/Vật thể & Crop Dọc 9:16 + Đốt Phụ đề (`YOLOv8-face` + `FFmpeg`):**
   - Thay thế bộ nhận diện mặt cổ điển trong `Components/FaceCrop.py` bằng **YOLOv8-face** chạy trên GPU T4.
   - Ở mỗi khung hình của đoạn clip đã cắt, YOLOv8-face xác định tọa độ hộp giới hạn `(x, y, w, h)` của khuôn mặt người đang nói (hoặc sản phẩm chính). Áp dụng **bộ lọc làm mượt chuyển động (Exponential Moving Average / Kalman Filter)** trên trục X để khung hình crop dọc `9:16` (ví dụ `1080x1920`) lia máy mượt như cameraman chuyên nghiệp, không bị giật cục giữa các frame.
   - Cuối cùng, gọi `FFmpeg` kết hợp khung hình dọc 9:16, đốt cứng (burn-in) lớp phụ đề Karaoke nhảy chữ `.ass` từ Bước 4.1 và ghép lại **nguyên vẹn luồng âm thanh gốc** (giữ nguyên giọng nói, SFX và nhạc nền).

## 3. Chiến lược Hosting LLM: Phân vai Chuyên biệt (`Qwen3.8-27B` + `Gemini 3.8 Flash`)

Theo yêu cầu phân vai của bạn, các tác vụ LLM trong GrowthPilot AI được chia thành **2 luồng chuyên biệt** giúp **không bị tranh chấp hạn mức (Quota/RPM)** giữa việc trả lời khách hàng và việc nghiên cứu/viết kịch bản/cắt video:

- **Luồng 1 — Trực chiến Trả lời Khách hàng từ Sáng đến Tối (08:00 – 22:00, tắt ban đêm 22:00 – 08:00):**
  - **Model Chính (Primary):** **`Qwen3.8-27B` (`qwen/qwen3.8-27b`)** chạy miễn phí trên **[Groq Cloud](https://www.betterclaw.io/blog/openclaw-best-free-model)** với tốc độ siêu thanh (~450 tokens/giây), hạn mức **30 RPM / 1.000 RPD / 200.000 tokens/ngày**.
  - **Model Dự phòng (Fallback):** **`Gemini 3.8 Flash` (`gemini-3.8-flash`)** trên **[Google AI Studio](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)**. Bất cứ khi nào khách nhắn dồn dập vượt ngưỡng 8.000 tokens/phút của Groq hoặc đạt trần 1.000 tin/ngày, Router tự động chuyển sang `Gemini 3.8 Flash` mà không làm gián đoạn cuộc trò chuyện.
- **Luồng 2 — Nghiên cứu Thị trường → Viết Kịch bản A/B/C & Chọn Đoạn Viral Shorts (Chạy On-Demand):**
  - **Model Chuyên trách:** **`Gemini 3.8 Flash` (`gemini-3.8-flash`)** (kèm **`Gemini 2.5 Pro`** miễn phí ở hạn mức thấp cho các bước cần suy luận chiến lược cực sâu).
  - **Lý do kỹ thuật:** Vì `Qwen3.8-27B` đã gánh toàn bộ tải trả lời inbox/comment hàng ngày trên Groq, toàn bộ quỹ hạn mức miễn phí và cửa sổ ngữ cảnh khổng lồ **1.048.576 tokens (1M context)** của `Gemini 3.8 Flash` trên Google AI Studio được dành trọn cho việc đọc tài liệu đối thủ, tổng hợp `Research Report` có trích dẫn (`MOD-03A`), sinh các phương án **Kịch bản A / B / C** (`MOD-02A`), ghép **Style Pack Prompt** và đọc toàn bộ bản bóc băng video dài để **chọn đoạn Viral (Bước 4)**.

### 3.1. Bảng Phân bổ Chi tiết trong LLM Router (100% Miễn phí)

| Vai trò trong Hệ thống | Model Chỉ định & Nhà cung cấp | Hạn mức Miễn phí (2026) | Lưu ý Cấu hình Kỹ thuật |
| :--- | :--- | :--- | :--- |
| **1. Trả lời Khách hàng Chính (08:00 – 22:00)**<br>*(Comment & Messenger `MOD-07A`)* | **[Groq Cloud](https://www.betterclaw.io/blog/openclaw-best-free-model) — `qwen/qwen3.8-27b`** | **30 RPM**<br>**1.000 RPD**<br>**8.000 TPM / 200K TPD** | - Tốc độ ~450 tokens/s giúp khách nhận phản hồi trong <0.8 giây.<br>- Thêm chỉ dẫn trong System Prompt: *"Trả lời 100% bằng tiếng Việt tự nhiên, lịch sự chuẩn chuyên viên tư vấn spa; tuyệt đối không dùng ký tự tiếng Trung"* để khóa chặt ngôn ngữ đầu ra. |
| **2. Trả lời Khách hàng Phụ (Fallback) + Lọc Spam Nhanh** | **[Google AI Studio](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash) — `gemini-3.8-flash`** (và `gemini-3.5-flash-lite`) | **Free of charge** trên AI Studio Free Tier (~1.500 RPD) | - Tự động kích hoạt khi Groq báo mã `HTTP 429` (vượt 8.000 TPM).<br>- Dùng `gemini-3.5-flash-lite` để phân loại nhanh bình luận spam trước khi đưa vào `Qwen3.8-27B`. |
| **3. Nghiên cứu Thị trường → Viết Kịch bản A/B/C & Chọn Viral Shorts (Bước 4)** | **[Google AI Studio](https://aistudio.google.com/docs/models) — `gemini-3.8-flash`** *(Kết hợp `gemini-2.5-pro` cho Deep Research)* | **1.048.576 tokens** input, **65.536 tokens** output, **Free of charge** | - **`Gemini 3.8 Flash` hiện là model tổng quát mạnh nhất và mới nhất được mở miễn phí hoàn toàn trên Google AI Studio** (trong khi `Gemini 4 Argon`/`Carbon` và `Gemini 3.1 Pro Preview` chỉ mở cho gói trả phí).<br>- Đảm nhận trọn vẹn `LanguageTasks.py` ở Notebook 2 và `Unified AI Orchestrator` ở Backend. |

#### Cơ chế Hoạt động "Sáng Bật – Tối Tắt" (08:00 – 22:00 Active / 22:00 – 08:00 Quiet Hours)
Thiết kế này khớp 100% với mục **Follow-up Scheduler & Contact Policy (`MOD-07A.C`)** trong BRD của bạn:
- **Khung giờ Hoạt động (08:00 – 22:00):** Khi khách bình luận hoặc nhắn tin vào Page, Webhook nhận sự kiện → **Messaging Policy Engine** kiểm tra cửa sổ 24h → gọi trực tiếp **`Qwen3.8-27B` (Groq)** (hoặc fallback sang **`Gemini 3.8 Flash`**) kèm dữ liệu RAG từ `Brand & Service Profile` để trả lời tư vấn ngay lập tức hoặc gợi ý cho nhân viên trực ca.
- **Khung giờ Tắt / Nghỉ đêm (22:00 – 08:00):** Hệ thống chuyển sang chế độ **Night/Quiet Hours Mode** để tiết kiệm tối đa quota (đặc biệt là trần 200K tokens/ngày của Groq) và tuân thủ chính sách không làm phiền đêm khuya:
  1. **Ngắt toàn bộ lệnh gọi LLM:** Mọi bình luận/tin nhắn đến trong khoảng 22:00–08:00 **không gọi LLM ngay**.
  2. **Phản hồi tĩnh tức thì (Zero-LLM Cost):** Nếu khách nhắn vào Messenger lần đầu trong đêm, hệ thống chỉ gửi 1 tin nhắn mẫu cố định (Rule-based Template): *"Cảm ơn chị đã nhắn tin cho [Tên Spa]! Hiện tại chuyên viên tư vấn đã nghỉ ca tối. Đầu giờ sáng mai (08:00) bên em sẽ gửi chi tiết liệu trình và ưu đãi ngay cho chị nhé ạ!"*
  3. **Xếp hàng xử lý sáng hôm sau (Morning Batch Queue):** Toàn bộ sự kiện phát sinh ban đêm được lưu vào bảng `webhook_events` / hàng đợi với lịch hẹn `scheduled_at = 08:00 AM`. Đúng 08:00 sáng, Worker thức dậy, gom (batch) toàn bộ tin nhắn nối tiếp của từng khách trong đêm thành **1 lần gọi LLM duy nhất** để tóm tắt nhu cầu, tạo câu trả lời tư vấn hoàn chỉnh và gửi thông báo `customer.intent.high` cho quản lý spa.

### 3.2. Phân tích Ưu/Nhược điểm & Phương án Trả phí (Paid LLM) khi Mở rộng

Mặc dù gói miễn phí của Groq (`Qwen3.8-27B`) + Google AI Studio (`Gemini 3.8 Flash`) hoàn toàn gánh tốt **1 Facebook Page đầu tiên**, bạn cần nắm rõ giới hạn pháp lý và kỹ thuật để quyết định khi nào chuyển sang gói trả phí:

| Phương án | Chi phí Ước tính | Ưu điểm | Nhược điểm & Rủi ro (Theo BRD Mục 14) | Khi nào nên áp dụng? |
| :--- | :--- | :--- | :--- | :--- |
| **1. Cloud API Miễn phí**<br>([Groq `Qwen3.8-27B`](https://www.betterclaw.io/blog/openclaw-best-free-model) + [AI Studio `Gemini 3.8 Flash`](https://aistudio.google.com/docs/pricing)) | **0 VNĐ / tháng** | - Không tốn tiền thuê GPU.<br>- Tách biệt hoàn toàn quota CSKH (Groq) và quota Sáng tạo/Chiến lược (Gemini 3.8 Flash).<br>- Đủ ~2.500 lượt phản hồi/ngày (gộp 2 nguồn), thừa sức chạy 1–3 Facebook Pages nhỏ. | - **Quyền riêng tư dữ liệu:** Trên gói Free Tier của Google AI Studio, dữ liệu prompt có thể được Google dùng để cải thiện sản phẩm ([chi tiết](https://felloai.com/free-ai-models/)). Cần ẩn danh SĐT/tên thật (PII Masking) trước khi gửi prompt.<br>- `Qwen3.8-27B` trên Groq Free giới hạn 8.000 TPM / 200K TPD nên cần truyền đoạn RAG gọn gàng (~500–800 tokens/lượt). | **Khuyên dùng ngay cho Giai đoạn MVP / Pilot 1 Facebook Page đầu tiên.** (Kết hợp bộ lọc Regex che SĐT trước khi gửi lên LLM). |
| **2. Cloud API Pay-As-You-Go**<br>([Gemini 3.8 Flash Paid](https://aistudio.google.com/docs/pricing) / OpenRouter `Qwen3.8-27B`) | **~50.000 – 150.000 VNĐ / tháng / Page** ($2 – $6/tháng) | - **Bảo mật tuyệt đối (Tuân thủ Luật BVDLCN 91/2025/QH15):** Ở Paid Tier, nhà cung cấp cam kết **không** dùng dữ liệu khách hàng để huấn luyện model.<br>- Giá `Qwen3.8-27B` trả phí chỉ $0.035/1M input tokens ([OpenRouter](https://openrouter.ai/qwen/qwen3.8-27b)), cực kỳ rẻ khi chạy Ads lớn. | - Tốn chi phí biến đổi theo lưu lượng tin nhắn (nhưng chỉ vài chục ngàn đồng mỗi tháng). | Khi spa bắt đầu chạy quảng cáo trả phí (Meta Ads) đổ lượng inbox lớn hoặc khi ký hợp đồng thương mại chính thức với khách hàng trả phí. |
| **3. Tự Host LLM theo Giờ (08:00–22:00)**<br>(Thuê GPU L4/RTX 4090 trên RunPod / Vast.ai chạy `vLLM` + `Qwen3.8-27B`) | **~1.100.000 – 1.800.000 VNĐ / tháng**<br>(14 giờ/ngày × $0.12–$0.20/giờ) | - Dữ liệu nằm 100% trên server riêng, không phụ thuộc hạn mức RPM của bên thứ ba.<br>- Có thể tắt hoàn toàn máy chủ từ 22:00 đến 08:00 qua API để tiết kiệm 42% tiền thuê. | - Chi phí cố định theo giờ quá cao nếu chỉ phục vụ 1–5 Facebook Pages.<br>- Tốn công vận hành, quản lý cold-start (mất 2–3 phút khởi động lúc 08:00 sáng). | Chỉ hiệu quả kinh tế khi nền tảng đạt quy mô **>50–100 Spa (Multi-tenant)** hoạt động đồng thời. |

## 4. Chiến lược Hosting Database, Storage & App Server: Miễn phí vs. Trả phí

Với mục tiêu triển khai **Self-host cho 1 Facebook Page đầu tiên**, câu trả lời là: **Hoàn toàn có thể vận hành 100% Miễn phí với độ ổn định rất cao** nếu kết hợp đúng các mảnh ghép hạ tầng dưới đây.

### 4.1. So sánh các Phương án Lưu trữ Database (PostgreSQL + `pgvector`) & Queue

Hệ thống cần **PostgreSQL** (lưu 14 nhóm bảng trong BRD Mục 11 + extension `pgvector` để tìm kiếm RAG cho bảng giá/dịch vụ spa), **Redis** (quản lý hàng đợi Webhook, Follow-up Scheduler và Kaggle Jobs) và **Object Storage** (lưu ảnh/video).

| Thành phần | Phương án Miễn phí (0 VNĐ) — Khuyên dùng cho 1 Page đầu tiên | Giới hạn & Điểm cần lưu ý của Gói Miễn phí | Phương án Trả phí (Paid Upgrade) — Ưu/Nhược điểm khi mở rộng |
| :--- | :--- | :--- | :--- |
| **PostgreSQL + `pgvector`**<br>*(Database chính)* | **Lựa chọn A (Managed Cloud): [Supabase Free Tier](https://supabase.com/pricing)**<br>- 500 MB dung lượng Database thực.<br>- Hỗ trợ sẵn `pgvector`, Auth và REST API.<br><br>**Lựa chọn B (Dự phòng): [Neon Free Tier](https://neon.com/pricing)**<br>- 500 MB lưu trữ, 100 CU-hours/tháng.<br><br>**Lựa chọn C (Self-host trên VPS Free):** Cài Docker PostgreSQL + `pgvector` trực tiếp trên [Oracle Cloud Always Free](https://www.infoq.com/news/2026/07/oracle-cloud-free-tier-limits/) (có 200 GB ổ cứng Block Volume miễn phí). | - **Supabase Free:** Tự động tạm dừng (pause) sau **7 ngày không có truy vấn** ([chi tiết](https://mykavo.app/blog/supabase-free-tier-limits)), nhưng vì worker của bạn chạy hàng ngày từ 08:00–22:00 nên **không bao giờ bị pause**. Với 1 Facebook Page, 500 MB văn bản lưu được hơn **200.000–300.000 tin nhắn và hồ sơ CRM**.<br>- **Neon Free:** Có độ trễ khởi động lại (cold-start ~0.5–1s) khi nghỉ đêm và giới hạn 100 CU-hours/tháng (chạy liên tục 14h/ngày × 30 ngày ở mức 0.25 CU sẽ tiêu tốn ~105 CU-hours, sát ngưỡng giới hạn). **Do đó Supabase hoặc tự cài trên Oracle Cloud tốt hơn Neon cho bài toán chạy 14h/ngày.** | **1. [Supabase Pro](https://supabase.com/pricing) ($25/tháng ~ 630.000đ):**<br>- *Ưu điểm:* 8 GB DB, tự động backup hàng ngày, không bao giờ pause.<br>- *Nhược điểm:* Tốn phí cố định $25/tháng hơi dư thừa khi mới chạy 1 Page.<br><br>**2. Tự cài PostgreSQL trên VPS trả phí (Hetzner / Vietnix / Vultr ~ 120.000đ – 180.000đ/tháng):**<br>- *Ưu điểm:* Rẻ gấp 4 lần Supabase Pro, dung lượng ổ cứng 40–80 GB thoải mái lưu trữ.<br>- *Nhược điểm:* Phải tự cấu hình cronjob backup dữ liệu hàng ngày lên Cloudflare R2. |
| **Redis Queue & Scheduler**<br>*(Hàng đợi & Lịch hẹn)* | **[Upstash Redis Free Tier](https://upstash.com/pricing/redis)** (hoặc cài Redis container trên cùng VPS/Home Server). | Upstash miễn phí 256 MB và 500.000 lệnh/tháng, cực kỳ tiện lợi để làm cầu nối giao tiếp giữa App Server và 2 Kaggle Notebooks. | **Upstash Pay-As-You-Go ($0.20 / 100k lệnh)** hoặc chạy trực tiếp Redis trong Docker trên VPS (0đ phát sinh). |
| **Object Storage**<br>*(Lưu Ảnh & Video)* | **[Cloudflare R2 Free Tier](https://developers.cloudflare.com/r2/pricing/)** | - **Miễn phí 10 GB lưu trữ/tháng**.<br>- **Miễn phí 100% băng thông tải ra (Zero Egress Fee)**.<br>- Kết hợp với tính năng `Storage Management & Retention Cleanup` (`MOD-02A` & `MOD-07A.F`) trong BRD để xóa các bản nháp video cũ, 10 GB lưu được hàng trăm video quảng cáo MP4 cho 1 Page. | **Cloudflare R2 Paid ($0.015 / GB / tháng):**<br>- Ngay cả khi vượt 10 GB và lưu tới **100 GB video**, bạn chỉ tốn khoảng **$1.35/tháng (~35.000 VNĐ)** và vẫn miễn phí băng thông tải video sang Facebook! |

### 4.2. So sánh các Phương án Host App Server (FastAPI Backend + Next.js Frontend)

Vì Meta Messenger Webhook (`MOD-06`) yêu cầu server phải phản hồi (ACK) gói tin `HTTP 200 OK` nhanh chóng (thường dưới 1–3 giây, nếu server đang "ngủ" mất 30–50 giây để thức dậy như Render Free Tier thì Facebook sẽ đánh dấu lỗi và ngắt kết nối Webhook của Page), bạn có **2 kiến trúc Self-Host 0 VNĐ** chuẩn chỉnh nhất để bắt đầu với Facebook Page đầu tiên:

#### Phương án Miễn phí A (Khuyên dùng số 1 nếu có thẻ Visa/Mastercard đăng ký): Cloud VPS Always-Free + Managed DB
- **Web Frontend (Next.js):** Host miễn phí trên **Vercel** hoặc **Cloudflare Pages** (tốc độ tải trang cực nhanh tại Việt Nam).
- **Backend API & Workers (FastAPI + Celery/APScheduler + Redis):** Đặt trên máy chủ ảo **[Oracle Cloud Always Free Tier](https://www.infoq.com/news/2026/07/oracle-cloud-free-tier-limits/)** (cấu hình ARM Ampere A1 cung cấp 2–4 OCPU và 12–24 GB RAM miễn phí trọn đời, chạy 24/7 không bao giờ ngủ).
- **Database:** Dùng **[Supabase Free Tier](https://supabase.com/pricing)** (500 MB) hoặc chạy luôn container PostgreSQL + `pgvector` ngay trong 200 GB ổ cứng của máy ảo Oracle Cloud.
- **Đánh giá:** Chạy ổn định 24/7 như một hệ thống trả phí chuyên nghiệp, nhận Webhook Facebook tức thì, tự động bật/tắt luồng AI theo lịch 08:00–22:00.

#### Phương án Miễn phí B (Self-Host trên Máy cá nhân / Mini PC sẵn có): Local Docker + Cloudflare Tunnel
Nếu bạn muốn **tự host ngay trên máy tính cá nhân / máy chủ nhỏ tại nhà hoặc văn phòng** (mở máy từ sáng đến tối hoặc 24/7):
- Chạy toàn bộ `FastAPI + PostgreSQL (pgvector) + Redis + Next.js` bằng một file `docker-compose.yml` duy nhất.
- Sử dụng **[Cloudflare Tunnel (`cloudflared`)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)** hoàn toàn miễn phí để nối máy local ra tên miền HTTPS chuẩn (ví dụ `https://api.growthpilot.vn/api/v1/webhooks/meta`) mà không cần mở port modem hay thuê IP tĩnh.
- **Mẹo kỹ thuật xử lý khi tắt máy ban đêm (22:00 – 08:00):** Nếu bạn tắt máy tính local vào ban đêm, để Facebook không ngắt Webhook khi có khách nhắn lúc 01:00 sáng, hãy đặt một **Cloudflare Worker (Miễn phí 100.000 requests/ngày)** đứng làm cổng nhận Webhook (`Webhook Edge Gateway`):
  - Khi Facebook bắn sự kiện lúc nửa đêm, Cloudflare Worker lập tức xác thực chữ ký (`X-Hub-Signature-256`), đẩy gói tin JSON vào **[Upstash Redis](https://upstash.com/pricing/redis)** (hoặc Cloudflare Queue) và trả về `200 OK` cho Facebook trong 10ms!
  - Sáng 08:00 khi bạn bật máy (hoặc Worker thức dậy), FastAPI đọc hàng đợi từ Upstash Redis và xử lý toàn bộ tin nhắn đêm qua mà không mất một khách hàng nào.

#### Phương án Trả phí Tiết kiệm (Low-Cost Production — Khi muốn nhàn hạ 100%)
Nếu không đăng ký được Oracle Cloud Free Tier và không muốn bật máy tính cá nhân:
- Thuê **1 VPS Linux (2 vCPU, 4 GB RAM, 60 GB NVMe)** tại Việt Nam hoặc Singapore (như Hetzner, Vultr, Vietnix, GreenCloud) với chi phí chỉ **~120.000 – 160.000 VNĐ/tháng ($4.5 – $6/tháng)**.
- Cài đặt **Coolify** hoặc **Docker Compose** chạy trọn bộ: `FastAPI + PostgreSQL (pgvector) + Redis + Worker` trên cùng 1 VPS, kết hợp với **Cloudflare R2 (Free)** và **Groq `Qwen3.8-27B` / `Gemini 3.8 Flash` (Free)**.
- **Tổng chi phí vận hành toàn hệ thống:** Chỉ ~150.000 VNĐ/tháng nhưng chịu tải thoải mái cho **5–10 Spa (Facebook Pages)** đầu tiên trước khi bạn thu phí thuê bao từ khách hàng (299.000đ – 1.990.000đ/spa/tháng theo `MOD-12` của BRD).

## 5. Sơ đồ Luồng Hoạt động Tích hợp (Sequence Workflows)

### 5.1. Luồng 1: Project-based Creative Studio (`Gemini 3.8 Flash`) → 2 Kaggle Notebooks → Xuất bản lên Facebook Page

```
[Chủ Spa / Marketing]              [FastAPI + Gemini 3.8 Flash]          [Kaggle NB1: Studio]          [Kaggle NB2: Shorts]          [Cloudflare R2 & FB API]
        |                                       |                                 |                             |                               |
        |-- 1. Tạo Project, tải ảnh SP thật --->|                                 |                             |                               |
        |-- 2. Gemini 3.8 Flash nghiên cứu TT,  |                                 |                             |                               |
        |      viết Kịch bản A/B/C -> User chọn |                                 |                             |                               |
        |                                       |-- 3. Lấy Style Pack mặc định,   |                             |                               |
        |                                       |      ghép Composed Prompt +     |                             |                               |
        |                                       |      lưu Style Snapshot vào DB  |                             |                               |
        |                                       |-- 4. Đẩy Job tạo Ảnh & Video -->|                             |                               |
        |                                       |                                 |-- 5. Chạy FLUX.2 (GPU 0)    |                               |
        |                                       |                                 |      tách nền & vẽ Studio   |                               |
        |                                       |                                 |-- 6. Chạy MiniMax H3 (GPU 1)|                               |
        |                                       |                                 |      sinh Video + SFX + Thoại                               |
        |                                       |                                 |-- 7. Chạy ACE-Step 1.5 (BGM)|                               |
        |                                       |                                 |      + FFmpeg mix 25% audio |                               |
        |                                       |                                 |-- 8. Upload Video gốc MP4 --------------------------------->|
        |                                       |<-- 9. Báo hoàn tất + URL R2 ----|                             |                               |
        |-- 10. Yêu cầu cắt thành Reels 9:16 -->|                                 |                             |                               |
        |                                       |-- 11. Đẩy Job cắt Shorts ------------------------------------>|                               |
        |                                       |                                 |                             |-- 12. WhisperX bóc băng ms    |
        |                                       |                                 |                             |-- 13. Gemini 3.8 Flash chọn   |
        |                                       |                                 |                             |       đoạn Viral              |
        |                                       |                                 |                             |-- 14. YOLOv8-face crop 9:16 + |
        |                                       |                                 |                             |       FFmpeg đốt sub Karaoke  |
        |                                       |                                 |                             |-- 15. Upload Reels 9:16 ----->|
        |<-- 16. Hiển thị Preview & Duyệt ------|<-- 17. Trả danh sách Shorts ----|                             |                               |
        |-- 18. Bấm "Approve & Schedule" ------>|                                 |                             |                               |
        |                                       |-- 19. Đúng giờ hẹn: Đăng bài lên Facebook Page + (Tùy chọn) Gửi Messenger Outreach ---------->|
```

### 5.2. Luồng 2: Facebook Comment & Messenger Automation (`Qwen3.8-27B` Chính + `Gemini 3.8 Flash` Phụ)

```
[Khách hàng trên FB Page]         [Webhook Gateway (Cloudflare/FastAPI)]         [Messaging Policy & Scheduler]         [LLM Router: Qwen3.8-27B -> Gemini 3.8]
           |                                        |                                           |                                       |
           |-- 1. Bình luận / Nhắn tin ------------>|                                           |                                       |
           |<-- 2. Trả HTTP 200 OK (<50ms) ---------|                                           |                                       |
           |                                        |-- 3. Chuẩn hóa Event + Chống trùng lặp -->|                                       |
           |                                        |                                           |-- 4. Kiểm tra Giờ hiện tại (UTC+7):   |
           |                                        |                                           |                                       |
           |                                        |      [TRƯỜNG HỢP A: Trong khung 08:00 - 22:00]                                    |
           |                                        |                                           |-- 5A. Truy vấn RAG (Giá/Dịch vụ Spa)  |
           |                                        |                                           |       + Gọi Qwen3.8-27B (Groq) chính  |
           |                                        |                                           |       (Fallback sang Gemini 3.8 Flash)|
           |                                        |                                           |<-- 6A. Trả JSON (Intent, Score, Reply)|
           |                                        |                                           |-- 7A. Kiểm tra cửa sổ 24h, Consent,   |
           |                                        |                                           |       Frequency Cap (ALLOW / HOLD)    |
           |<-- 8A. Gửi câu trả lời (hoặc Gợi ý cho Admin + Báo Notification nếu Intent Cao) ---|                                       |
           |                                        |                                           |                                       |
           |                                        |      [TRƯỜNG HỢP B: Ngoài giờ / Ban đêm 22:00 - 08:00]                            |
           |                                        |                                           |-- 5B. KHÔNG gọi LLM (Tiết kiệm 100%)  |
           |<-- 6B. Gửi mẫu tin tĩnh hẹn 08:00 sáng (nếu khách mới inbox lần đầu) --------------|                                       |
           |                                        |                                           |-- 7B. Đưa vào hàng đợi hẹn 08:00 sáng |
           |                                        |                                           |-- 8B. Đúng 08:00: Gom tin nhắn đêm -> |
           |                                        |                                           |       Gọi LLM 1 lần duy nhất -------->|
```

## 6. Lộ trình Triển khai Thực tế (Action Plan cho Facebook Page Đầu tiên)

Để đưa hệ thống vào chạy thực tế ngay cho **Facebook Page đầu tiên** với chi phí **0 VNĐ**, bạn nên triển khai theo 4 bước tuần tự sau:

1. **Tuần 1 — Dựng Core Backend, Database & Kết nối Facebook Page đầu tiên (0 VNĐ):**
   - Khởi tạo project PostgreSQL + `pgvector` trên [Supabase Free Tier](https://supabase.com/pricing), tạo bucket `growthpilot-media` trên [Cloudflare R2](https://developers.cloudflare.com/r2/pricing/) và tạo hàng đợi trên [Upstash Redis](https://upstash.com/pricing/redis).
   - Triển khai FastAPI Backend (trên Oracle Cloud Free Tier hoặc Docker local nối qua Cloudflare Tunnel), tích hợp **Meta Graph API Webhook** (`pages_messaging`, `pages_manage_engagement`) cho Facebook Page đầu tiên.
2. **Tuần 2 — Kích hoạt Customer Engagement Agent (`Qwen3.8-27B` Chính + `Gemini 3.8 Flash` Phụ) & CRM/Booking (0 VNĐ):**
   - Tích hợp API Key miễn phí của **Groq (`qwen/qwen3.8-27b`)** làm luồng trả lời khách hàng chính từ 08:00–22:00 và **Google AI Studio (`gemini-3.8-flash`)** làm luồng dự phòng + chuyên trách Nghiên cứu thị trường / Viết kịch bản A-B-C.
   - Nạp dữ liệu bảng giá, liệu trình, FAQ của spa vào bảng `services` / `knowledge_documents` và bật bộ lập lịch **08:00–22:00 Active / 22:00–08:00 Quiet Hours** kèm **Messaging Policy Engine** kiểm soát cửa sổ 24 giờ của Meta.
3. **Tuần 3 — Đóng gói Kaggle Notebook 1 (`GrowthPilot-Generative-Studio`):**
   - Cấu hình Notebook 1 ở chế độ **GPU T4 x2 (32 GB VRAM)**: đặt **FLUX.2 [klein] 9B (FP8/Q8)** + **ACE-Step 1.5** trên `cuda:0` và **MiniMax H3 (Q4_K_M + Turbo LoRA)** trên `cuda:1`.
   - Nối kết quả đầu ra qua script `FFmpeg` (trộn BGM ở mức 25% âm lượng) và tự động đẩy file MP4/PNG lên Cloudflare R2, trả link về **Project Creative Workspace** (`MOD-02A` & `MOD-04`).
4. **Tuần 4 — Đóng gói Kaggle Notebook 2 (`GrowthPilot-Shorts-Repurposer`) & Lịch Đăng bài (`MOD-05`):**
   - Cấu hình Notebook 2 tích hợp `SamurAIGPT/AI-Youtube-Shorts-Generator` đã nâng cấp 3 lõi: `WhisperX large-v3-turbo` (phụ đề nhảy chữ mili-giây) + `Gemini 3.8 Flash API` (sửa `LanguageTasks.py`) + `YOLOv8-face` (bám mặt crop dọc 9:16).
   - Kết nối đầu ra của cả 2 Notebook vào bảng lịch đăng bài (`publishing_jobs`) để tự động đăng Reels/Post lên Facebook Page và kích hoạt chiến dịch chăm sóc lại khách hàng đủ điều kiện (`MOD-07A.D`).
