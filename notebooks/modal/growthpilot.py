"""Notebook 1 (studio) as a Modal app: started by the backend when a job is queued, no Kaggle clicks.

One-time setup (from the repo root):
    uvx modal secret create growthpilot-worker GP_API_URL=... MEDIA_WORKER_TOKEN=... HF_TOKEN=...
    uvx modal deploy notebooks/modal/growthpilot.py
    uvx modal run notebooks/modal/growthpilot.py::download     # ~59 GB of models into a Volume, CPU only

Then set MODAL_APP=growthpilot in backend/.env. The worker code is notebooks/kaggle/ unchanged; this
file only bakes ComfyUI and sd-cli (built for the L40S, sm_89) into an image and runs the same loop
on one 48 GB GPU, stopping after 2 idle minutes so nothing is billed between jobs.
"""

import os
import sys
from pathlib import Path

import modal

SRC = Path(__file__).parent.parent / "kaggle"
ROOT = "/opt/gp"
SDCPP = f"{ROOT}/stable-diffusion.cpp"
SDCPP_TAG = "master-1031-c6dfa9d"  # keep in step with nb1_generative_studio.py

image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu22.04", add_python="3.12")
    .apt_install("git", "ffmpeg", "build-essential")
    .pip_install("cmake<4")
    .run_commands(
        f"git clone --depth 1 --branch {SDCPP_TAG} --recursive --shallow-submodules "
        f"https://github.com/leejet/stable-diffusion.cpp {SDCPP}",
        # No GPU while the image builds: link against the toolkit's libcuda stub.
        f"cmake -S {SDCPP} -B {SDCPP}/build -DCMAKE_BUILD_TYPE=Release -DSD_CUDA=ON "
        "-DCMAKE_CUDA_ARCHITECTURES=89 -DGGML_CUDA_CUTLASS_PATH:PATH= "
        "-DCUDA_cuda_driver_LIBRARY=/usr/local/cuda/lib64/stubs/libcuda.so",
        f"cmake --build {SDCPP}/build --config Release -j $(nproc) --target sd-cli",
    )
    .pip_install("torch", "torchvision", "torchaudio", index_url="https://download.pytorch.org/whl/cu128")
    .run_commands(
        f"git clone --depth 1 https://github.com/comfyanonymous/ComfyUI {ROOT}/ComfyUI",
        f"git clone --depth 1 https://github.com/city96/ComfyUI-GGUF {ROOT}/ComfyUI/custom_nodes/ComfyUI-GGUF",
        f"python -m pip install -r {ROOT}/ComfyUI/requirements.txt "
        f"-r {ROOT}/ComfyUI/custom_nodes/ComfyUI-GGUF/requirements.txt 'huggingface_hub[hf_xet]' requests",
    )
    .env({
        "GP_NOTEBOOK_DIR": "/opt/gp/src",
        "GP_ROOT": ROOT,
        "GP_HF_DIR": "/models",
        "GP_GPU_LAYOUT": "single",
        "GP_WORKDIR": "/tmp/gp",
    })
    .add_local_dir(SRC, "/opt/gp/src", ignore=["dist", "prebuilt", "__pycache__"])
)

app = modal.App("growthpilot")
models = modal.Volume.from_name("growthpilot-models", create_if_missing=True)
secrets = [modal.Secret.from_name("growthpilot-worker")]


def _nb1():
    sys.path.insert(0, "/opt/gp/src")
    import nb1_generative_studio

    return nb1_generative_studio


@app.function(image=image, volumes={"/models": models}, secrets=secrets, cpu=2, memory=4096, timeout=3 * 3600)
def download() -> None:
    _nb1().download_models()
    models.commit()


@app.function(image=image, gpu="L40S", volumes={"/models": models}, secrets=secrets, cpu=4, memory=32768,
              timeout=4 * 3600, max_containers=1)
def studio() -> None:
    nb1 = _nb1()
    worker = nb1.Worker(["studio"])
    nb1.setup()
    worker.run(nb1.handle, max_idle_minutes=float(os.environ.get("GP_MAX_IDLE_MIN", "2")))
