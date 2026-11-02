# %% [markdown]
# # GrowthPilot-Generative-Studio (Notebook 1)
#
# System design §2: **FLUX.2 [klein]** (studio image + thumbnail) → **MiniMax H3** I2VA
# (video + SFX/voice) → **ACE-Step 1.5** (BGM) → **FFmpeg** mix with BGM at 25%.
#
# Settings: Accelerator **GPU T4 x2**, Internet **On**, Secrets: `GP_API_URL`, `MEDIA_WORKER_TOKEN`,
# `HF_TOKEN`.
#
# VRAM plan (Phương án A): `cuda:0` → ComfyUI with FLUX.2 klein + ACE-Step 1.5;
# `cuda:1` → MiniMax H3 fl2va (I2VA) Q4_K + Turbo LoRA 8-step via stable-diffusion.cpp (`sd-cli`):
# the unsloth H3 GGUFs are sd.cpp files that ComfyUI-GGUF cannot load. Its Qwen3-VL-32B text encoder
# (Q4_K_M 17 GB) runs on the CPU and weights are memory-mapped, as the model card recommends.
# sd-cli is compiled for the T4 (sm_75) while the models download. Downloads are ~59 GB.
#
# Licences (checked on Hugging Face, Nov 2026): FLUX.2 klein **4B = Apache-2.0** (commercial OK);
# klein **9B = FLUX Non-Commercial** (needs a BFL commercial licence for a paid SaaS). MiniMax H3 =
# community licence: commercial OK under USD 20M/yr revenue, and the product UI must display
# "MiniMax H3". ACE-Step 1.5 = MIT / Apache-2.0.
#
# FLUX.2 and ACE-Step graphs live in ComfyUI workflow files (API format) under `workflows/`, built
# from the official ComfyUI templates with GGUF loaders, so swapping a model never needs a code change.

# %%
import json
import os
import random
import shutil
import subprocess
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

# Kaggle mounts the dataset at /kaggle/input/<slug> or /kaggle/input/datasets/<owner>/<slug>.
HERE = Path(os.environ.get("GP_NOTEBOOK_DIR") or next(Path("/kaggle/input").rglob("gp_worker.py")).parent)
sys.path.insert(0, str(HERE))
from gp_worker import Worker, ffmpeg, probe_duration, secret, video_codec  # noqa: E402

# DRY_RUN=1 renders placeholder media with FFmpeg only: tests the full API/R2 loop without GPUs.
DRY_RUN = os.environ.get("GP_DRY_RUN", "0") == "1"
WORKFLOWS = HERE / "workflows" if (HERE / "workflows").is_dir() else HERE  # the dataset is flat
# Kaggle defaults; Modal (notebooks/modal/growthpilot.py) bakes ComfyUI and sd-cli into its image.
ROOT = Path(os.environ.get("GP_ROOT", "/kaggle/working"))
HF_DIR = os.environ.get("GP_HF_DIR")  # plain files on a Modal Volume instead of the HF cache
# "split": Kaggle T4 x2, ComfyUI on cuda:0 and H3 on cuda:1 with its text encoder on the CPU.
# "single": one big GPU (Modal L40S 48 GB) runs everything; ComfyUI unloads before H3.
GPU_LAYOUT = os.environ.get("GP_GPU_LAYOUT", "split")
COMFY = ROOT / "ComfyUI"
GPU_SERVERS = {"image": "http://127.0.0.1:8188", "audio": "http://127.0.0.1:8188"}
SDCPP = ROOT / "stable-diffusion.cpp"
SDCPP_TAG = "master-1031-c6dfa9d"  # first release with MiniMax-H3 I2VA docs; bump deliberately
SD_CLI = SDCPP / "build/bin/sd-cli"

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

H3_MODEL = "minimax_h3_fl2va_pruned-Q4_K.gguf"
H3_TE = "qwen3vl_32b_minimax_h3-Q4_K_M.gguf"
H3_LORA = "loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"

# (hf repo, file in repo, ComfyUI models subfolder). Keep in sync with the loaders in workflows/*.json.
MODELS = [
    *FLUX,
    ("Comfy-Org/Flux-2-Klein-4B", "split_files/vae/flux2-vae.safetensors", "vae"),
    # MiniMax H3 fl2va = first/last-frame image-to-video+audio (the design's I2VA mode)
    ("unsloth/MiniMax-H3-GGUF", H3_MODEL, "diffusion_models"),  # 10.6 GiB
    ("unsloth/MiniMax-H3-GGUF", H3_TE, "text_encoders"),  # 17 GiB
    ("unsloth/MiniMax-H3-GGUF", "vae/minimax_h3_video_vae_fp16.safetensors", "vae"),
    ("unsloth/MiniMax-H3-GGUF", "vae/minimax_h3_audio_vae_fp32.safetensors", "vae"),
    ("Comfy-Org/MiniMax-H3", H3_LORA, "loras"),
    # ACE-Step 1.5 turbo, split files (~3.5 GB VRAM incl. the small text encoder)
    ("Comfy-Org/ACE-Step-1.5", "split_files/diffusion_models/acestep_v1.5_turbo.safetensors", "diffusion_models"),
    ("Comfy-Org/ACE-Step-1.5", "split_files/text_encoders/qwen_0.6b_ace15.safetensors", "text_encoders"),
    ("Comfy-Org/ACE-Step-1.5", "split_files/text_encoders/qwen_1.7b_ace15.safetensors", "text_encoders"),
    ("Comfy-Org/ACE-Step-1.5", "split_files/vae/ace_1.5_vae.safetensors", "vae"),
]

# %% [markdown]
# ## Setup: ComfyUI + GGUF loader, model download, one server per GPU

# %%
def build_sdcpp() -> None:
    """Compile sd-cli with CUDA for the T4 only (sm_75, no CUTLASS) to keep the build short.

    The build takes ~27 min, so a binary from an earlier run ships in the dataset when available
    (build.py picks up notebooks/kaggle/prebuilt/sd-cli) and is used if it starts."""
    prebuilt = HERE / "sd-cli"
    if prebuilt.exists() and not SD_CLI.exists():
        SD_CLI.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(prebuilt, SD_CLI)
        SD_CLI.chmod(0o755)
        res = subprocess.run([str(SD_CLI), "--help"], capture_output=True, text=True)
        if "error while loading shared libraries" in res.stdout + res.stderr:
            print("prebuilt sd-cli does not start here; building", flush=True)
            SD_CLI.unlink()
    if SD_CLI.exists():
        return
    log_path = ROOT / "sdcpp_build.log"
    log = log_path.open("w")

    def run(*cmd: str) -> None:
        if subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT).returncode:
            log.flush()
            tail = "\n".join(log_path.read_text(errors="replace").splitlines()[-40:])
            raise RuntimeError(f"sd.cpp build step failed: {' '.join(cmd[:3])}…\n--- last log lines ---\n{tail}")

    if not shutil.which("cmake"):
        run(sys.executable, "-m", "pip", "install", "-q", "cmake<4")
    cudas = sorted(Path("/usr/local").glob("cuda*/bin/nvcc"))
    nvcc = shutil.which("nvcc") or (str(cudas[-1]) if cudas else "/usr/local/cuda/bin/nvcc")
    # Kaggle's driver library sits outside FindCUDAToolkit's search paths (CUDA::cuda_driver not
    # found): link against the toolkit's stub, or the real libcuda, explicitly.
    cuda_root = Path(nvcc).resolve().parent.parent
    libcuda = next((str(f) for pattern in ("lib64/stubs/libcuda.so", "targets/*/lib/stubs/libcuda.so") for f in cuda_root.glob(pattern)), None) \
        or next((str(f) for d in ("/usr/lib/x86_64-linux-gnu", "/usr/local/nvidia/lib64", "/usr/lib64-nvidia", "/usr/lib64")
                 for f in sorted(Path(d).glob("libcuda.so*")) if f.is_file()), None)
    if not libcuda:
        raise RuntimeError("libcuda.so not found (no CUDA stub and no driver library); cannot build sd-cli")
    if not (SDCPP / ".git").exists():  # a re-run after a failed build reuses the checkout
        run("git", "clone", "--depth", "1", "--branch", SDCPP_TAG, "--recursive", "--shallow-submodules",
            "https://github.com/leejet/stable-diffusion.cpp", str(SDCPP))
    run("cmake", "-S", str(SDCPP), "-B", str(SDCPP / "build"), "-DCMAKE_BUILD_TYPE=Release", "-DSD_CUDA=ON",
        "-DCMAKE_CUDA_ARCHITECTURES=75", "-DGGML_CUDA_CUTLASS_PATH:PATH=",
        f"-DCMAKE_CUDA_COMPILER={nvcc}", f"-DCUDA_cuda_driver_LIBRARY={libcuda}")
    run("cmake", "--build", str(SDCPP / "build"), "--config", "Release", "-j", str(os.cpu_count()), "--target", "sd-cli")


def download_models() -> None:
    from huggingface_hub import hf_hub_download

    for repo, filename, folder in MODELS:
        target = COMFY / "models" / folder / Path(filename).name
        if not target.exists():
            print("downloading", repo, filename, flush=True)
            where = {"local_dir": f"{HF_DIR}/{repo}"} if HF_DIR else {"cache_dir": "/kaggle/tmp/hf"}
            path = hf_hub_download(repo, filename, token=secret("HF_TOKEN"), **where)
            target.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(path, target)


def setup() -> None:
    builder = ThreadPoolExecutor(1).submit(build_sdcpp)  # overlaps with the model downloads
    if not COMFY.exists():
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/comfyanonymous/ComfyUI", str(COMFY)], check=True)
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/city96/ComfyUI-GGUF",
                        str(COMFY / "custom_nodes/ComfyUI-GGUF")], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(COMFY / "requirements.txt"),
                        "-r", str(COMFY / "custom_nodes/ComfyUI-GGUF/requirements.txt"), "huggingface_hub"], check=True)
    download_models()
    subprocess.Popen([sys.executable, "main.py", "--listen", "127.0.0.1", "--port", "8188", "--disable-auto-launch"],
                     cwd=COMFY, env={**os.environ, "CUDA_VISIBLE_DEVICES": "0"},
                     stdout=open(ROOT / "comfy0.log", "w"), stderr=subprocess.STDOUT)
    for _ in range(180):
        try:
            if requests.get(f"{GPU_SERVERS['image']}/system_stats", timeout=2).ok:
                break
        except requests.RequestException:
            time.sleep(2)
    else:
        raise RuntimeError(f"ComfyUI did not start; see {ROOT / 'comfy0.log'}")
    builder.result()  # raises if the sd.cpp build failed; see sdcpp_build.log


# %% [markdown]
# ## ComfyUI client
# Each workflow `workflows/<name>.json` (exported with *Save (API Format)*) has a sibling
# `<name>.map.json` saying where to inject values, e.g.
# `{"prompt": [["7", "text"]], "seed": [["12", "noise_seed"]], "image": [["4", "image"]],
#   "width": [["14", "width"], ["15", "width"]], "height": [["14", "height"], ["15", "height"]]}`

# %%
def load_workflow(name: str) -> tuple[dict, dict]:
    wf = WORKFLOWS / f"{name}.json"
    mp = WORKFLOWS / f"{name}.map.json"
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
# MiniMax H3 size (multiples of 32); stage_mix scales to W x H. On a T4 480x864 took ~0.2 min per
# frame (a 6 s shot ~30 min), so Kaggle renders 384x672. The L40S did 384x672 in ~2 min per shot.
VIDEO_W, VIDEO_H = (480, 864) if GPU_LAYOUT == "single" else (384, 672)


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
    seed = random.randint(0, 2**31 - 1)
    flux_image(flux_wf(ref), p["studio_master"]["prompt"], ref, seed, master)
    w.progress("flux2:thumbnail", 0.2)
    flux_image(flux_wf(ref), p["thumbnail"]["prompt"], ref, seed + 1, thumb)
    if p["thumbnail"].get("headline"):  # jobs queued before this asked FLUX to paint the text
        draw_headline(thumb, p["thumbnail"]["headline"])
    return master, thumb


FONT_URL = "https://github.com/google/fonts/raw/main/ofl/bevietnampro/BeVietnamPro-Bold.ttf"


def _font(size: int):
    from PIL import ImageFont

    font_file = ROOT / "BeVietnamPro-Bold.ttf"
    if not font_file.exists():
        r = requests.get(FONT_URL, timeout=60)
        r.raise_for_status()
        font_file.write_bytes(r.content)
    return ImageFont.truetype(str(font_file), size)


def text_lines(text: str, size: int, top: float, highlight: str = "", accent: str = "#E9C77B") -> list:
    """One transparent W x H layer per wrapped line, centred from `top` (a share of H), in a real
    Vietnamese font (FLUX misspells diacritics: "Kiểh hagi lân da"). The `highlight` word is drawn
    in the accent colour. Separate layers let each line come in on its own beat."""
    from PIL import Image, ImageDraw

    font = _font(size)
    measure = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines = [""]
    for word in text.split():
        trial = f"{lines[-1]} {word}".strip()
        if lines[-1] and measure.textlength(trial, font=font) > W * 0.84:
            lines.append(word)
        else:
            lines[-1] = trial
    keys = {k.strip(".,!?:;") for k in highlight.lower().split()}  # "BLUE GREEN MASK" is three words
    layers, y = [], int(H * top)
    for line in lines:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        x = (W - draw.textlength(line, font=font)) / 2
        for word in line.split():
            hit = word.lower().strip(".,!?:;") in keys
            draw.text((x, y), word, font=font, fill=accent if hit else "white",
                      stroke_width=size // 22, stroke_fill=(60, 45, 35))
            x += draw.textlength(word + " ", font=font)
        layers.append(layer)
        y += int(size * 1.25)
    return layers


def text_layer(text: str, size: int):
    from PIL import Image

    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for layer in text_lines(text, size, 0.08):
        out.alpha_composite(layer)
    return out


def stat_card(text: str, accent: str):
    """Big number callout ("505nm", "10 phút") on a soft dark pill, centred a little below middle."""
    from PIL import Image, ImageDraw

    font = _font(170)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    tw = draw.textlength(text, font=font)
    box_w, box_h, cy = tw + 120, 250, int(H * 0.56)
    draw.rounded_rectangle(((W - box_w) / 2, cy - box_h / 2, (W + box_w) / 2, cy + box_h / 2), radius=60,
                           fill=(20, 16, 12, 150))
    draw.text(((W - tw) / 2, cy - 112), text, font=font, fill=accent)
    return layer


def draw_headline(path: Path, text: str) -> None:
    from PIL import Image

    img = Image.open(path).convert("RGBA")
    img.alpha_composite(text_layer(text, 88))
    img.convert("RGB").save(path)


def flux_wf(ref: Path | None) -> str:
    return "flux2_klein_ref" if ref else "flux2_klein_t2i"


def comfy_unload() -> None:
    """Free ComfyUI's VRAM so H3 fits next to it on a single GPU."""
    server = GPU_SERVERS["image"]
    requests.post(f"{server}/free", json={"unload_models": True, "free_memory": True}, timeout=30).raise_for_status()
    for _ in range(30):
        dev = requests.get(f"{server}/system_stats", timeout=10).json()["devices"][0]
        if dev["vram_free"] > 0.8 * dev["vram_total"]:
            return
        time.sleep(2)


def h3_clip(prompt: str, image: Path, frames: int, seed: int, out: Path) -> None:
    """MiniMax H3 I2VA with sd-cli (flags from sd.cpp docs/minimax_h3.md and the unsloth model card)."""
    m, avi = COMFY / "models", out.with_suffix(".avi")
    lora = Path(H3_LORA).stem
    # On the T4 the 17 GB text encoder runs on the CPU and weights page in and out of VRAM.
    low_vram = ["--backend", "te=cpu", "--offload-to-cpu"] if GPU_LAYOUT == "split" else []
    cmd = [str(SD_CLI), "-M", "vid_gen",
           "--diffusion-model", str(m / "diffusion_models" / H3_MODEL), "--llm", str(m / "text_encoders" / H3_TE),
           "--vae", str(m / "vae/minimax_h3_video_vae_fp16.safetensors"),
           "--audio-vae", str(m / "vae/minimax_h3_audio_vae_fp32.safetensors"),
           "--lora-model-dir", str(m / "loras"), "-p", f"{prompt}<lora:{lora}:1>", "-i", str(image),
           "-W", str(VIDEO_W), "-H", str(VIDEO_H), "--video-frames", str(frames), "--fps", "24",
           "--steps", "8", "--cfg-scale", "1.0", "-s", str(seed), "--rng", "cpu",
           *low_vram, "--mmap", "--diffusion-fa", "--vae-tiling", "-o", str(avi)]
    gpu = "1" if GPU_LAYOUT == "split" else "0"
    res = subprocess.run(cmd, env={**os.environ, "CUDA_VISIBLE_DEVICES": gpu}, capture_output=True, text=True)
    if res.returncode or not avi.exists():
        raise RuntimeError(f"sd-cli MiniMax H3 failed ({res.returncode}): {(res.stdout + res.stderr)[-1500:]}")
    ffmpeg("-i", str(avi), *video_codec(), "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "32000", str(out))


def stage_clips(w: Worker, job: dict, d: Path, master: Path) -> list[Path]:
    clips = []
    shots = job["payload"]["shots"]
    # Shots after the first start from their own frame (jobs queued before this have none), edited
    # from the studio master so the same product, person and room carry across shots. All frames
    # come first so a single GPU unloads FLUX only once.
    # Shots without the product are edited from a plate (the master with the product removed):
    # edited from the master, FLUX kept the mask and turned a hand mirror into a second one.
    plate = master
    if job["payload"].get("plate") and not DRY_RUN:
        w.progress("flux2:plate", 0.18)
        plate = d / "plate.png"
        flux_image("flux2_klein_ref", job["payload"]["plate"]["prompt"], master, random.randint(0, 2**31 - 1), plate)
    frames = []
    for i, shot in enumerate(shots):
        frame = master
        if shot.get("keyframe") and not DRY_RUN:
            w.progress(f"flux2:keyframe {i + 1}/{len(shots)}", 0.2)
            frame = d / f"frame_{i}.png"
            base = plate if shot["keyframe"].get("base") == "plate" else master
            flux_image("flux2_klein_ref", shot["keyframe"]["prompt"], base, random.randint(0, 2**31 - 1), frame)
        frames.append(frame)
    if GPU_LAYOUT == "single" and not DRY_RUN:
        comfy_unload()
    for i, (shot, frame) in enumerate(zip(shots, frames, strict=True)):
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
            h3_clip(prompt, frame, h3_frames(secs), random.randint(0, 2**31 - 1), out)
        clips.append(out)
    return clips


# Synthesised accents, no files to license: a soft two-tone chime under a stat card and a breathy
# whoosh where a flash or dissolve brings the shot in.
TING = "aevalsrc='0.22*sin(2*PI*1568*t)*exp(-5*t)+0.1*sin(2*PI*2349*t)*exp(-7*t)':s=32000:d=0.9"
WHOOSH = "anoisesrc=d=0.7:c=pink:a=0.6,highpass=f=500,lowpass=f=5000,afade=t=in:d=0.3,afade=t=out:st=0.35:d=0.35"
LOWER = ("macro", "close_up", "top_down")  # the subject fills the top: text goes to the lower third


# Transitions are baked into each shot as fades and the shots are then simply concatenated:
# overlapping xfade chains ended the video early on FFmpeg 4.4 (Modal and Kaggle images), dropping
# shot 5. flash = a quick white dip, dissolve = a soft dip to dark.
FADE = {"flash": ("white", 0.2, 0.25), "dissolve": ("black", 0.35, 0.35)}  # colour, out, in


def finish_shot(w: Worker, i: int, shot: dict, clip: Path, d: Path, accent: str, came_in: str = "cut",
                goes_out: str = "cut") -> Path:
    """Animate the shot's on-screen text in line by line with the voice, pop the stat card with a
    chime, and mix the Vietnamese voiceover (Gemini TTS, made by the API) over the H3 sound, which
    drops to 35% under the voice."""
    text, stat, voice = shot.get("on_screen_text", "").strip(), shot.get("stat", "").strip(), shot.get("voice_url")
    whoosh = came_in in FADE
    if not (text or stat or voice or whoosh or goes_out in FADE):
        return clip
    dur = probe_duration(clip)
    inputs = ["-i", str(clip)]
    graph = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=24,setsar=1[base0]"]
    layers = []  # (png, start)
    voice_wav = w.download(voice, d / f"voice_{i}.wav") if voice else None
    spoken = probe_duration(voice_wav) if voice_wav else dur * 0.6
    if text:
        lines = text_lines(text, 72, 0.64 if shot.get("framing") in LOWER else 0.08, shot.get("highlight", ""), accent)
        step = min(0.6, spoken * 0.7 / len(lines))
        for k, layer in enumerate(lines):
            png = d / f"text_{i}_{k}.png"
            layer.save(png)
            layers.append((png, 0.3 + k * step))
    stat_at = min(dur * 0.45, dur - 1.2)
    if stat:
        png = d / f"stat_{i}.png"
        stat_card(stat, accent).save(png)
        layers.append((png, stat_at))
    cur = "base0"
    for n, (png, at) in enumerate(layers, 1):
        inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", str(png)]
        graph.append(f"[{n}:v]format=rgba,fade=in:st={at:.2f}:d=0.35:alpha=1[l{n}]")
        # slides up 30 px while it fades in
        graph.append(f"[{cur}][l{n}]overlay=0:'if(lt(t,{at:.2f}),30,max(0,30-(t-{at:.2f})*90))'[base{n}]")
        cur = f"base{n}"
    fades = []
    if came_in in FADE:
        color, _, t = FADE[came_in]
        fades.append(f"fade=t=in:st=0:d={t}:color={color}")
    if goes_out in FADE:
        color, t, _ = FADE[goes_out]
        fades.append(f"fade=t=out:st={dur - t:.2f}:d={t}:color={color}")
    graph.append(f"[{cur}]{','.join(fades) or 'null'}[v]")
    sounds = [f"[0:a]aresample=32000,aformat=channel_layouts=stereo{',volume=0.35' if voice_wav else ''}[sfx]"]
    mix = ["[sfx]"]
    if voice_wav:
        n = 1 + len(layers)  # input index after the clip and the text/stat stills
        inputs += ["-i", str(voice_wav)]
        sounds.append(f"[{n}:a]aresample=32000,aformat=channel_layouts=stereo,adelay=300:all=1[vo]")
        mix.append("[vo]")
    if stat:
        sounds.append(f"{TING},aformat=channel_layouts=stereo,adelay={int(stat_at * 1000)}:all=1[ting]")
        mix.append("[ting]")
    if whoosh:
        sounds.append(f"{WHOOSH},aformat=sample_rates=32000:channel_layouts=stereo,volume=0.4[whoosh]")
        mix.append("[whoosh]")
    sounds.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0[a]")
    out = d / f"shot_{i}.mp4"
    ffmpeg(*inputs, "-filter_complex", ";".join(graph + sounds), "-map", "[v]", "-map", "[a]", "-t", f"{dur:.2f}",
           *video_codec(), "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "32000", str(out))
    return out


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


def stage_mix(w: Worker, job: dict, d: Path, clips: list[Path], bgm: Path, name: str = "final_commercial.mp4") -> Path:
    """Concat shots (keeping their SFX/voice and baked-in transitions), then mix the BGM with fades
    (system design §2)."""
    w.progress("ffmpeg:mix", 0.85)
    raw = d / f"raw_{name}"
    inputs = [x for c in clips for x in ("-i", str(c))]
    norm = "".join(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=24,setsar=1[v{i}];"
                   f"[{i}:a]aresample=32000,aformat=channel_layouts=stereo[a{i}];" for i in range(len(clips)))
    pairs = "".join(f"[v{i}][a{i}]" for i in range(len(clips)))
    ffmpeg(*inputs, "-filter_complex", f"{norm}{pairs}concat=n={len(clips)}:v=1:a=1[v][a]",
           "-map", "[v]", "-map", "[a]", *video_codec(), "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "32000", str(raw))
    dur = probe_duration(raw)
    vol = job["payload"]["mix"]["bgm_volume"]
    final = d / name
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
    shots = job["payload"]["shots"]
    accent = job["payload"]["mix"].get("accent", "#E9C77B")
    joins = [s.get("transition", "cut") for s in shots[:-1]]
    came_in, goes_out = ["cut", *joins], [*joins, "cut"]
    clips = [finish_shot(w, i, shot, clip, d, accent, came_in[i], goes_out[i])
             for i, (shot, clip) in enumerate(zip(shots, clips, strict=True))]
    bgm = stage_bgm(w, job, d)
    final = stage_mix(w, job, d, clips, bgm)
    w.progress("upload", 0.95)
    w.upload("bgm", bgm)
    w.upload("final_video", final)
    meta = {"width": W, "height": H, "dry_run": DRY_RUN}
    outputs = {
        "studio_master": meta,
        "thumbnail": meta,
        "bgm": {"duration": probe_duration(bgm)},
        "final_video": {**meta, "duration": round(probe_duration(final), 2), "fps": 24, "audio_sample_rate": 32000},
    }
    # Shorts reuse the finished shots (voice and text already in): opening + one benefit + CTA
    for k, plan in enumerate(job["payload"].get("shorts", []), 1):
        short = stage_mix(w, job, d, [clips[i] for i in plan["shots"]], bgm, f"short_{k}.mp4")
        w.upload(f"short_{k}", short)
        outputs[f"short_{k}"] = {**meta, "duration": round(probe_duration(short), 2), "shots": plan["shots"]}
    return outputs


# %% [markdown]
# ## Run (stops after 60 idle minutes to save the 30 h/week GPU quota)

# %%
if __name__ == "__main__" or "ipykernel" in sys.modules:
    worker = Worker(["studio"])  # checks secrets before the long model download
    if not DRY_RUN:
        setup()
    worker.run(handle, max_idle_minutes=float(os.environ.get("GP_MAX_IDLE_MIN", 60)))
