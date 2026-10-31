# %% [markdown]
# # GrowthPilot-Generative-Studio (Notebook 1)
#
# System design §2: **FLUX.2 [klein] 9B** (studio image + thumbnail) → **MiniMax H3** I2VA
# (video + SFX/voice) → **ACE-Step 1.5** (BGM) → **FFmpeg** mix with BGM at 25%.
#
# Settings: Accelerator **GPU T4 x2**, Internet **On**, Secrets: `GP_API_URL`, `MEDIA_WORKER_TOKEN`,
# `HF_TOKEN` (gated FLUX weights).
#
# VRAM plan (Phương án A): one ComfyUI server per GPU so nothing is reloaded between jobs.
# `cuda:0` → FLUX.2 klein (~9.5 GB) + ACE-Step (~3.5 GB); `cuda:1` → MiniMax H3 Q4_K_M + Turbo LoRA
# (~12.5 GB). The exact model graphs live in ComfyUI workflow files (API format) under
# `workflows/`, so swapping a model or quantization never needs a code change.

# %%
import json
import os
import random
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

import requests

sys.path.insert(0, "/kaggle/input/growthpilot-worker")  # utility-script dataset; build.py inlines it
from gp_worker import Worker, ffmpeg, probe_duration, secret, video_codec  # noqa: E402

# DRY_RUN=1 renders placeholder media with FFmpeg only: tests the full API/R2 loop without GPUs.
DRY_RUN = os.environ.get("GP_DRY_RUN", "0") == "1"
HERE = Path(os.environ.get("GP_NOTEBOOK_DIR", "/kaggle/input/growthpilot-worker"))
COMFY = Path("/kaggle/working/ComfyUI")
GPU_SERVERS = {"image": "http://127.0.0.1:8188", "audio": "http://127.0.0.1:8188", "video": "http://127.0.0.1:8189"}

# Model files → ComfyUI model folders. CONFIRM the exact repos/files you use, then keep this list
# in sync with the loaders inside workflows/*.json.
MODELS = [
    # (hf repo, filename in repo, ComfyUI models subfolder)
    ("black-forest-labs/FLUX.2-klein-9B", "flux2-klein-9b-fp8.safetensors", "diffusion_models"),
    ("black-forest-labs/FLUX.2-klein-9B", "text_encoder.safetensors", "text_encoders"),
    ("black-forest-labs/FLUX.2-klein-9B", "ae.safetensors", "vae"),
    ("MiniMaxAI/MiniMax-H3-GGUF", "minimax-h3-Q4_K_M.gguf", "diffusion_models"),
    ("MiniMaxAI/MiniMax-H3-GGUF", "h3-turbo-lora-8step.safetensors", "loras"),
    ("ACE-Step/ACE-Step-v1-5", "ace_step_v1.5.safetensors", "checkpoints"),
]

# %% [markdown]
# ## Setup: ComfyUI + GGUF loader, model download, one server per GPU

# %%
def setup() -> None:
    if not COMFY.exists():
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/comfyanonymous/ComfyUI", str(COMFY)], check=True)
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/city96/ComfyUI-GGUF",
                        str(COMFY / "custom_nodes/ComfyUI-GGUF")], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(COMFY / "requirements.txt"),
                        "-r", str(COMFY / "custom_nodes/ComfyUI-GGUF/requirements.txt"), "huggingface_hub"], check=True)
    from huggingface_hub import hf_hub_download

    for repo, filename, folder in MODELS:
        target = COMFY / "models" / folder / filename
        if not target.exists():
            print("downloading", repo, filename, flush=True)
            path = hf_hub_download(repo, filename, token=secret("HF_TOKEN"), cache_dir="/kaggle/tmp/hf")
            target.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(path, target)
    for gpu, port in (("0", 8188), ("1", 8189)):
        env = {**os.environ, "CUDA_VISIBLE_DEVICES": gpu}
        subprocess.Popen([sys.executable, "main.py", "--listen", "127.0.0.1", "--port", str(port),
                          "--disable-auto-launch"], cwd=COMFY, env=env,
                         stdout=open(f"/kaggle/working/comfy{gpu}.log", "w"), stderr=subprocess.STDOUT)
    for url in {GPU_SERVERS["image"], GPU_SERVERS["video"]}:
        for _ in range(180):
            try:
                if requests.get(f"{url}/system_stats", timeout=2).ok:
                    break
            except requests.RequestException:
                time.sleep(2)
        else:
            raise RuntimeError(f"ComfyUI at {url} did not start; see /kaggle/working/comfy*.log")


# %% [markdown]
# ## ComfyUI client
# Each workflow `workflows/<name>.json` (exported with *Save (API Format)*) has a sibling
# `<name>.map.json` saying where to inject values, e.g.
# `{"prompt": [["6", "text"]], "negative": [["7", "text"]], "seed": [["3", "seed"]],
#   "image": [["12", "image"]], "width": [["5", "width"]], "height": [["5", "height"]],
#   "seconds": [["20", "length"]]}`

# %%
def load_workflow(name: str) -> tuple[dict, dict]:
    wf = HERE / "workflows" / f"{name}.json"
    mp = HERE / "workflows" / f"{name}.map.json"
    if not wf.exists() or not mp.exists():
        raise FileNotFoundError(f"Missing ComfyUI workflow {wf} / {mp}. See workflows/README.md")
    return json.loads(wf.read_text()), json.loads(mp.read_text())


def comfy_upload(server: str, path: Path) -> str:
    with path.open("rb") as f:
        r = requests.post(f"{server}/upload/image", files={"image": (path.name, f)}, data={"overwrite": "true"}, timeout=120)
    r.raise_for_status()
    return r.json()["name"]


def comfy_run(name: str, modality: str, values: dict, out: Path, timeout: int = 1800) -> Path:
    server = GPU_SERVERS[modality]
    graph, mapping = load_workflow(name)
    for field, value in values.items():
        if value is None:
            continue
        if field == "image":
            value = comfy_upload(server, value)
        for node, key in mapping.get(field, []):
            graph[node]["inputs"][key] = value
    r = requests.post(f"{server}/prompt", json={"prompt": graph}, timeout=60)
    r.raise_for_status()
    prompt_id = r.json()["prompt_id"]
    deadline = time.time() + timeout
    while time.time() < deadline:
        hist = requests.get(f"{server}/history/{prompt_id}", timeout=30).json().get(prompt_id)
        if hist:
            if hist.get("status", {}).get("status_str") == "error":
                raise RuntimeError(f"ComfyUI {name} failed: {hist['status']}")
            for node_out in hist["outputs"].values():
                for files in node_out.values():
                    if isinstance(files, list) and files and isinstance(files[0], dict) and "filename" in files[0]:
                        q = urllib.parse.urlencode({k: files[0][k] for k in ("filename", "subfolder", "type")})
                        data = requests.get(f"{server}/view?{q}", timeout=600)
                        data.raise_for_status()
                        out.write_bytes(data.content)
                        return out
            raise RuntimeError(f"ComfyUI {name} produced no file")
        time.sleep(3)
    raise TimeoutError(f"ComfyUI {name} timed out")


# %% [markdown]
# ## Stages

# %%
W, H = 1080, 1920


def stage_images(w: Worker, job: dict, d: Path) -> tuple[Path, Path]:
    p = job["payload"]
    refs = [r for r in p["references"] if r["role"] in ("product", "facility")]
    ref = w.download(refs[0]["url"], d / "reference.png") if refs else None
    master, thumb = d / "studio_master.png", d / "thumbnail.png"
    if DRY_RUN:
        for path, color in ((master, "0xE8DCCB"), (thumb, "0xA3315A")):
            ffmpeg("-f", "lavfi", "-i", f"color=c={color}:s={W}x{H}", "-frames:v", "1", str(path))
        return master, thumb
    wf = "flux2_klein_ref" if ref else "flux2_klein_t2i"
    seed = random.randint(0, 2**31 - 1)
    comfy_run(wf, "image", {"prompt": p["studio_master"]["prompt"], "image": ref, "seed": seed,
                            "width": W, "height": H}, master)
    w.progress("flux2:thumbnail", 0.2)
    comfy_run(wf, "image", {"prompt": p["thumbnail"]["prompt"], "image": ref, "seed": seed + 1,
                            "width": W, "height": H}, thumb)
    return master, thumb


def stage_clips(w: Worker, job: dict, d: Path, master: Path) -> list[Path]:
    clips = []
    shots = job["payload"]["shots"]
    for i, shot in enumerate(shots):
        w.progress(f"minimax-h3:shot {i + 1}/{len(shots)}", 0.25 + 0.45 * i / len(shots))
        out = d / f"clip_{i}.mp4"
        secs = max(2, min(10, round(shot["duration_seconds"])))
        if DRY_RUN:
            ffmpeg("-loop", "1", "-i", str(master), "-f", "lavfi", "-i", f"sine=frequency={300 + 100 * i}:duration={secs}",
                   "-t", str(secs), "-vf", f"scale={W}:{H},fps=24", *video_codec(), "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-ar", "32000", "-shortest", str(out))
        else:
            comfy_run("minimax_h3_i2va", "video", {"prompt": shot["prompt"], "negative": shot["negative_prompt"],
                                                   "image": master, "seconds": secs,
                                                   "seed": random.randint(0, 2**31 - 1)}, out)
        clips.append(out)
    return clips


def stage_bgm(w: Worker, job: dict, d: Path) -> Path:
    w.progress("ace-step:bgm", 0.75)
    bgm = d / "bgm_track.wav"
    secs = job["payload"]["bgm"]["duration_seconds"]
    if DRY_RUN:
        ffmpeg("-f", "lavfi", "-i", f"sine=frequency=220:duration={secs}", "-ar", "32000", str(bgm))
    else:
        comfy_run("ace_step_bgm", "audio", {"prompt": job["payload"]["bgm"]["prompt"], "seconds": secs,
                                             "seed": random.randint(0, 2**31 - 1)}, bgm)
    return bgm


def stage_mix(w: Worker, job: dict, d: Path, clips: list[Path], bgm: Path) -> Path:
    """Concat shots (keeping their SFX/voice), then mix BGM at 25% with fades (system design §2)."""
    w.progress("ffmpeg:mix", 0.85)
    raw = d / "raw_ad_with_sfx_voice.mp4"
    inputs = [x for c in clips for x in ("-i", str(c))]
    norm = "".join(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=24,setsar=1[v{i}];"
                   f"[{i}:a]aresample=32000,aformat=channel_layouts=stereo[a{i}];" for i in range(len(clips)))
    pairs = "".join(f"[v{i}][a{i}]" for i in range(len(clips)))
    ffmpeg(*inputs, "-filter_complex", f"{norm}{pairs}concat=n={len(clips)}:v=1:a=1[v][a]",
           "-map", "[v]", "-map", "[a]", *video_codec(), "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "32000", str(raw))
    dur = probe_duration(raw)
    vol = job["payload"]["mix"]["bgm_volume"]
    final = d / "final_commercial.mp4"
    ffmpeg("-i", str(raw), "-i", str(bgm), "-filter_complex",
           f"[1:a]volume={vol},afade=t=in:d=1,afade=t=out:st={max(0, dur - 1.5):.2f}:d=1.5[bgm];"
           "[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]",
           "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-ar", "32000",
           "-movflags", "+faststart", str(final))
    return final


def handle(w: Worker, job: dict, d: Path) -> dict:
    w.progress("flux2:studio master", 0.05)
    master, thumb = stage_images(w, job, d)
    w.upload("studio_master", master)
    w.upload("thumbnail", thumb)
    clips = stage_clips(w, job, d, master)
    bgm = stage_bgm(w, job, d)
    final = stage_mix(w, job, d, clips, bgm)
    w.progress("upload", 0.95)
    w.upload("bgm", bgm)
    w.upload("final_video", final)
    meta = {"width": W, "height": H, "dry_run": DRY_RUN}
    return {
        "studio_master": meta,
        "thumbnail": meta,
        "bgm": {"duration": probe_duration(bgm)},
        "final_video": {**meta, "duration": round(probe_duration(final), 2), "fps": 24, "audio_sample_rate": 32000},
    }


# %% [markdown]
# ## Run (stops after 60 idle minutes to save the 30 h/week GPU quota)

# %%
if __name__ == "__main__" or "ipykernel" in sys.modules:
    if not DRY_RUN:
        setup()
    Worker(["studio"]).run(handle, max_idle_minutes=float(os.environ.get("GP_MAX_IDLE_MIN", 60)))
