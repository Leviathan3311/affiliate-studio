# %% [markdown]
# # GrowthPilot-Generative-Studio (Notebook 1)
#
# System design §2: **FLUX.2 [klein]** (studio image + thumbnail) → **MiniMax H3** I2VA
# (video + SFX/voice) → **ACE-Step 1.5** (BGM) → **FFmpeg** mix with BGM at 25%.
#
# Settings: Accelerator **GPU T4 x2**, Internet **On**, Secrets: `GP_API_URL`, `MEDIA_WORKER_TOKEN`,
# `HF_TOKEN`.
#
# VRAM plan (Phương án A): one ComfyUI server per GPU so nothing is reloaded between jobs.
# `cuda:0` → FLUX.2 klein + ACE-Step 1.5; `cuda:1` → MiniMax H3 fl2va (I2VA) Q4_K + Turbo LoRA 8-step.
# MiniMax H3 also needs its Qwen3-VL-32B text encoder (GGUF Q4_K_M 18.2 GB): it does not fit on a
# 16 GB T4 next to the 11.4 GB transformer, so ComfyUI encodes the prompt first and offloads it to the
# 29 GB system RAM. Total downloads are ~59 GB of the session's temporary disk.
#
# Licences (checked on Hugging Face, Nov 2026): FLUX.2 klein **4B = Apache-2.0** (commercial OK);
# klein **9B = FLUX Non-Commercial** (needs a BFL commercial licence for a paid SaaS). MiniMax H3 =
# community licence: commercial OK under USD 20M/yr revenue, and the product UI must display
# "MiniMax H3". ACE-Step 1.5 = MIT / Apache-2.0.
#
# The model graphs live in ComfyUI workflow files (API format) under `workflows/`, built from the
# official ComfyUI templates (FLUX.2 klein 9B distilled edit, MiniMax H3 I2V turbo, ACE-Step 1.5 split)
# with GGUF loaders, so swapping a model or quantization never needs a code change.

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

# Owner's decision (Nov 2026): non-commercial internal use, so the higher-quality 9B is the default.
# FLUX.2 klein 9B is FLUX Non-Commercial; set GP_FLUX_VARIANT=4b (Apache-2.0) before selling the service.
FLUX_VARIANT = os.environ.get("GP_FLUX_VARIANT", "9b")
FLUX = {
    "4b": [
        ("unsloth/FLUX.2-klein-4B-GGUF", "flux-2-klein-4b-Q8_0.gguf", "diffusion_models"),  # 4.3 GB
        ("Comfy-Org/Flux-2-Klein-4B", "split_files/text_encoders/qwen_3_4b.safetensors", "text_encoders"),
    ],
    "9b": [
        ("unsloth/FLUX.2-klein-9B-GGUF", "flux-2-klein-9b-Q8_0.gguf", "diffusion_models"),  # 10.3 GB
        ("Comfy-Org/Flux-2-Klein-9B", "split_files/text_encoders/qwen_3_8b_fp8mixed.safetensors", "text_encoders"),
    ],
}[FLUX_VARIANT]
# workflows/*.json name the 9B files; the 4B variant swaps them in at run time.
FILE_SWAP = {"4b": {"flux-2-klein-9b-Q8_0.gguf": "flux-2-klein-4b-Q8_0.gguf",
                    "qwen_3_8b_fp8mixed.safetensors": "qwen_3_4b.safetensors"}}.get(FLUX_VARIANT, {})

# (hf repo, file in repo, ComfyUI models subfolder). Keep in sync with the loaders in workflows/*.json.
MODELS = [
    *FLUX,
    ("Comfy-Org/Flux-2-Klein-4B", "split_files/vae/flux2-vae.safetensors", "vae"),
    # MiniMax H3 fl2va = first/last-frame image-to-video+audio (the design's I2VA mode)
    ("unsloth/MiniMax-H3-GGUF", "minimax_h3_fl2va_pruned-Q4_K.gguf", "diffusion_models"),  # 11.4 GB
    ("unsloth/MiniMax-H3-GGUF", "qwen3vl_32b_minimax_h3-Q4_K_M.gguf", "text_encoders"),  # 18.2 GB
    ("unsloth/MiniMax-H3-GGUF", "vae/minimax_h3_video_vae_fp16.safetensors", "vae"),
    ("unsloth/MiniMax-H3-GGUF", "vae/minimax_h3_audio_vae_fp32.safetensors", "vae"),
    ("Comfy-Org/MiniMax-H3", "loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors", "loras"),
    # ACE-Step 1.5 turbo, split files (~3.5 GB VRAM incl. the small text encoder)
    ("Comfy-Org/ACE-Step-1.5", "split_files/diffusion_models/acestep_v1.5_turbo.safetensors", "diffusion_models"),
    ("Comfy-Org/ACE-Step-1.5", "split_files/text_encoders/qwen_0.6b_ace15.safetensors", "text_encoders"),
    ("Comfy-Org/ACE-Step-1.5", "split_files/text_encoders/qwen_1.7b_ace15.safetensors", "text_encoders"),
    ("Comfy-Org/ACE-Step-1.5", "split_files/vae/ace_1.5_vae.safetensors", "vae"),
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
        target = COMFY / "models" / folder / Path(filename).name
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
# `{"prompt": [["7", "text"]], "seed": [["12", "noise_seed"]], "image": [["4", "image"]],
#   "width": [["14", "width"], ["15", "width"]], "height": [["14", "height"], ["15", "height"]]}`

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
    for node in graph.values():
        for key, value in node["inputs"].items():
            if isinstance(value, str) and value in FILE_SWAP:
                node["inputs"][key] = FILE_SWAP[value]
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
GEN_W = 1088  # FLUX.2 latents need multiples of 16; cropped back to W
VIDEO_W, VIDEO_H = 480, 864  # MiniMax H3 on a T4 (multiples of 32); stage_mix scales to W x H


def h3_frames(seconds: float) -> int:
    """MiniMax H3 frame count at 24 fps, snapped up to its 17k+5 grid (as in the ComfyUI template)."""
    n = max(5, round(seconds * 24))
    return n + (5 - n % 17) % 17


def flux_image(wf: str, prompt: str, ref: Path | None, seed: int, out: Path) -> None:
    raw = out.with_suffix(".raw.png")
    comfy_run(wf, "image", {"prompt": prompt, "image": ref, "seed": seed, "width": GEN_W, "height": H}, raw)
    ffmpeg("-i", str(raw), "-vf", f"crop={W}:{H}", str(out))


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
    flux_image(wf, p["studio_master"]["prompt"], ref, seed, master)
    w.progress("flux2:thumbnail", 0.2)
    flux_image(wf, p["thumbnail"]["prompt"], ref, seed + 1, thumb)
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
            # H3 has no negative-prompt input; the template writes constraints into the prompt instead.
            prompt = f"{shot['prompt']}\n\nAvoid: {shot['negative_prompt']}" if shot.get("negative_prompt") else shot["prompt"]
            comfy_run("minimax_h3_i2va", "video", {"prompt": prompt, "image": master, "length": h3_frames(secs),
                                                   "width": VIDEO_W, "height": VIDEO_H,
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
        flac = comfy_run("ace_step_bgm", "audio", {"prompt": job["payload"]["bgm"]["prompt"], "seconds": secs,
                                                    "seed": random.randint(0, 2**31 - 1)}, d / "bgm.flac")
        ffmpeg("-i", str(flac), "-ar", "32000", str(bgm))
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
    worker = Worker(["studio"])  # checks secrets before the long model download
    if not DRY_RUN:
        setup()
    worker.run(handle, max_idle_minutes=float(os.environ.get("GP_MAX_IDLE_MIN", 60)))
