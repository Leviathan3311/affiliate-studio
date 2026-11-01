# %% [markdown]
# # GrowthPilot-Shorts-Repurposer (Notebook 2)
#
# System design §2 step 4, replacing the three cores of SamurAIGPT/AI-Youtube-Shorts-Generator:
# 1. **WhisperX large-v3-turbo** + wav2vec2 forced alignment → word-level timestamps (ms).
# 2. **Gemini 3.8 Flash** (structured JSON, 1M context) picks 2–5 viral 15–30 s segments.
# 3. **YOLOv8-face** tracks the speaker; EMA-smoothed 9:16 crop; FFmpeg burns karaoke `.ass`
#    subtitles and keeps the original audio untouched.
#
# Settings: GPU T4 x1 is enough (~5 GB VRAM). Secrets: `GP_API_URL`, `MEDIA_WORKER_TOKEN`,
# `GEMINI_API_KEY`.

# %%
import json
import os
import subprocess
import sys
from pathlib import Path

# Kaggle mounts the dataset at /kaggle/input/<slug> or /kaggle/input/datasets/<owner>/<slug>.
HERE = Path(os.environ.get("GP_NOTEBOOK_DIR") or next(Path("/kaggle/input").rglob("gp_worker.py")).parent)
sys.path.insert(0, str(HERE))
from gp_worker import Worker, ffmpeg, probe_duration, secret, video_codec  # noqa: E402

DRY_RUN = os.environ.get("GP_DRY_RUN", "0") == "1"
GEMINI_MODEL = os.environ.get("GP_GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_FALLBACK = "gemini-2.5-flash"
FACE_WEIGHTS = ("arnabdhar/YOLOv8-Face-Detection", "model.pt")  # CONFIRM or swap for your weights
OUT_W, OUT_H = 1080, 1920
EMA_ALPHA = 0.12  # lower = smoother "cameraman" pan

WORKER = Worker(["shorts"])  # checks secrets before installing anything
if not DRY_RUN:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "whisperx", "google-genai",
                    "ultralytics", "opencv-python-headless", "huggingface_hub"], check=True)

# %% [markdown]
# ## 4.1 Transcribe + align (word level)

# %%
_ASR = {}


def transcribe(audio: Path, language: str) -> list[dict]:
    """Returns [{word, start, end}] in seconds."""
    if DRY_RUN:
        words = "Vai gáy mỏi nhừ sau tám tiếng làm việc hãy thử massage đá nóng tại spa".split()
        return [{"word": w, "start": i * 0.45, "end": i * 0.45 + 0.4} for i, w in enumerate(words * 6)]
    import whisperx

    if "model" not in _ASR:
        _ASR["model"] = whisperx.load_model("large-v3-turbo", "cuda", compute_type="float16", language=language)
        _ASR["align"] = whisperx.load_align_model(language_code=language, device="cuda")
    audio_data = whisperx.load_audio(str(audio))
    result = _ASR["model"].transcribe(audio_data, batch_size=16, language=language)
    model_a, meta = _ASR["align"]
    aligned = whisperx.align(result["segments"], model_a, meta, audio_data, "cuda", return_char_alignments=False)
    return [{"word": w["word"], "start": w["start"], "end": w["end"]}
            for w in aligned["word_segments"] if "start" in w and "end" in w]


# %% [markdown]
# ## 4.2 Viral segment selection with Gemini (structured output)

# %%
SCHEMA = {
    "type": "object",
    "properties": {
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"}, "end": {"type": "number"},
                    "title": {"type": "string"}, "hook": {"type": "string"},
                    "reason": {"type": "string"}, "caption": {"type": "string"},
                },
                "required": ["start", "end", "title", "hook", "reason", "caption"],
            },
        }
    },
    "required": ["segments"],
}


def select_segments(words: list[dict], p: dict, duration: float) -> list[dict]:
    lo, hi, n = p["min_seconds"], p["max_seconds"], p["target_count"]
    if DRY_RUN:
        step = max(hi, duration / max(n, 1))
        return [{"start": i * step, "end": min(duration, i * step + lo), "title": f"Đoạn {i + 1}",
                 "hook": "Vai gáy mỏi?", "reason": "dry run", "caption": "Thử ngay"} for i in range(n)
                if i * step + 3 < duration]
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=secret("GEMINI_API_KEY"))
    transcript = " ".join(f"[{w['start']:.2f}]{w['word']}" for w in words)
    ctx = p["brand_context"]
    prompt = (
        f"Bạn chọn {n} đoạn video ngắn {lo}-{hi} giây gây chú ý nhất cho Facebook Reels của spa.\n"
        f"Dự án: {ctx['project']}. Dịch vụ: {ctx['service']}. Khách mục tiêu: {ctx['audience']}. "
        f"CTA: {ctx['cta'] or 'nhắn Page để được tư vấn'}. Dữ kiện cố định: {'; '.join(ctx['facts'])}.\n"
        "Mỗi đoạn phải có hook mạnh ở 3 giây đầu, giải quyết nỗi đau khách hàng, kết thúc trọn câu. "
        "start/end lấy đúng mốc thời gian (giây) trong transcript. Không bịa giá/ưu đãi/cam kết. "
        "title/hook/caption bằng tiếng Việt.\nTRANSCRIPT:\n" + transcript
    )
    for model in (GEMINI_MODEL, GEMINI_FALLBACK):
        try:
            res = client.models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=SCHEMA),
            )
            segs = json.loads(res.text)["segments"]
            break
        except Exception as e:  # quota / model not available -> fallback model
            print(model, "failed:", e, flush=True)
    else:
        raise RuntimeError("Gemini selection failed on all models")
    clean = []
    for s in segs:
        start, end = max(0.0, float(s["start"])), min(duration, float(s["end"]))
        if end - start >= max(5, lo * 0.6):
            clean.append({**s, "start": round(start, 2), "end": round(end, 2)})
    return clean[:n]


# %% [markdown]
# ## 4.3 Face tracking crop 9:16 + karaoke subtitles

# %%
def ass_time(t: float) -> str:
    h, rem = divmod(max(t, 0), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def karaoke_ass(words: list[dict], start: float, end: float, path: Path) -> None:
    """Lines of ≤5 words; each word highlighted with \\kf as it is spoken."""
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
        "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        "Style: Karaoke,Arial,74,&H0000E5FF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,5,0,2,80,80,360,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    seg = [w for w in words if w["start"] >= start and w["end"] <= end]
    lines = [seg[i:i + 5] for i in range(0, len(seg), 5)]
    events = []
    for line in lines:
        t0, t1 = line[0]["start"] - start, line[-1]["end"] - start
        text = "".join(f"{{\\kf{max(1, round((w['end'] - w['start']) * 100))}}}{w['word'].strip()} " for w in line)
        events.append(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},Karaoke,,0,0,0,,{text.strip()}")
    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


_FACE = {}


def face_centers(video: Path, start: float, end: float) -> tuple[list[float], float, int, int]:
    """Smoothed x-center per frame (pixels) for the speaker's face."""
    import cv2

    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    if not DRY_RUN and "model" not in _FACE:
        from huggingface_hub import hf_hub_download
        from ultralytics import YOLO

        _FACE["model"] = YOLO(hf_hub_download(*FACE_WEIGHTS))
    xs, x = [], w / 2
    frames = int((end - start) * fps)
    for i in range(frames):
        ok, frame = cap.read()
        if not ok:
            break
        if not DRY_RUN and i % 3 == 0:  # detect every 3rd frame, smooth in between
            boxes = _FACE["model"].predict(frame, verbose=False, device=0)[0].boxes
            if len(boxes):
                b = max(boxes.xyxy.tolist(), key=lambda bb: (bb[2] - bb[0]) * (bb[3] - bb[1]))  # largest face
                target = (b[0] + b[2]) / 2
                x = EMA_ALPHA * target + (1 - EMA_ALPHA) * x
        xs.append(x)
    cap.release()
    return xs, fps, w, h


def render_short(src: Path, words: list[dict], seg: dict, i: int, d: Path) -> tuple[Path, Path, Path]:
    import cv2

    start, end = seg["start"], seg["end"]
    xs, fps, w, h = face_centers(src, start, end)
    crop_w = min(w, int(h * 9 / 16))
    ass = d / f"short_{i}.ass"
    karaoke_ass(words, start, end, ass)
    silent = d / f"crop_{i}.mp4"
    enc = subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", f"{OUT_W}x{OUT_H}", "-r", f"{fps}", "-i", "-", *video_codec(), "-pix_fmt", "yuv420p", str(silent)],
        stdin=subprocess.PIPE,
    )
    cap = cv2.VideoCapture(str(src))
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    for x in xs:
        ok, frame = cap.read()
        if not ok:
            break
        left = int(min(max(x - crop_w / 2, 0), w - crop_w))
        enc.stdin.write(cv2.resize(frame[:, left:left + crop_w], (OUT_W, OUT_H)).tobytes())
    cap.release()
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("ffmpeg crop encode failed")
    out = d / f"short_{i}.mp4"
    ffmpeg("-i", str(silent), "-ss", f"{start}", "-to", f"{end}", "-i", str(src),
           "-map", "0:v", "-map", "1:a?", "-vf", f"ass={ass}", *video_codec(), "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out))
    cover = d / f"cover_{i}.jpg"
    ffmpeg("-ss", "1", "-i", str(out), "-frames:v", "1", "-q:v", "3", str(cover))
    return out, cover, ass


def handle(w: Worker, job: dict, d: Path) -> dict:
    p = job["payload"]
    w.progress("download", 0.02)
    src = w.download(p["source_url"], d / "source.mp4")
    duration = probe_duration(src)
    audio = d / "audio.wav"
    ffmpeg("-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(audio))
    w.progress("whisperx", 0.1)
    words = transcribe(audio, p["language"])
    w.progress("gemini:viral selection", 0.35)
    segments = select_segments(words, p, duration)
    if not segments:
        raise RuntimeError("Không tìm được đoạn phù hợp trong video")
    outputs = {}
    for i, seg in enumerate(segments, start=1):
        w.progress(f"render short {i}/{len(segments)}", 0.4 + 0.55 * (i - 1) / len(segments))
        video, cover, ass = render_short(src, words, seg, i, d)
        w.upload(f"short_{i}", video)
        w.upload(f"cover_{i}", cover)
        w.upload(f"subtitle_{i}", ass)
        outputs[f"short_{i}"] = {**seg, "duration": round(probe_duration(video), 2), "width": OUT_W,
                                 "height": OUT_H, "dry_run": DRY_RUN}
        outputs[f"cover_{i}"] = {}
        outputs[f"subtitle_{i}"] = {}
    return outputs


# %%
if __name__ == "__main__" or "ipykernel" in sys.modules:
    WORKER.run(handle, max_idle_minutes=float(os.environ.get("GP_MAX_IDLE_MIN", 60)))
