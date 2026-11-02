"""GrowthPilot media worker client, shared by both Kaggle notebooks.

The notebook polls the API (exposed through Cloudflare Tunnel), receives a job with presigned R2
URLs, renders, uploads straight to R2 and reports back. It never holds DB or R2 credentials.

Config (Kaggle → Add-ons → Secrets, or environment variables when run locally):
  GP_API_URL            e.g. https://api.your-domain.vn
  MEDIA_WORKER_TOKEN    same value as the backend's MEDIA_WORKER_TOKEN
"""

import os
import shutil
import socket
import subprocess
import threading
import time
import traceback
from pathlib import Path

import requests


SECRET_ERRORS: dict[str, str] = {}  # why a secret could not be read (never its value)


def secret(name: str, default: str | None = None) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    try:  # Kaggle secrets are only available inside a Kaggle session
        from kaggle_secrets import UserSecretsClient

        return UserSecretsClient().get_secret(name)
    except Exception as e:
        SECRET_ERRORS[name] = f"{type(e).__name__}: {str(e)[:160]}"
        return default


class Cancelled(Exception):
    pass


# The GPU itself broke (Modal log: "Xid 79, GPU has fallen off the bus"): every later job on this
# machine fails the same way, so give the job back and stop instead of burning its retries.
GPU_LOST = ("cudaErrorUnknown", "CUDA error: unknown error", "fallen off the bus", "illegal memory access")


class Worker:
    def __init__(self, kinds: list[str], workdir: str = "/kaggle/working/gp"):
        api_url, token = secret("GP_API_URL"), secret("MEDIA_WORKER_TOKEN")
        if not api_url or not token:
            # Fail fast: without these the notebook would download ~60 GB and idle on GPU quota.
            missing = [n for n, v in (("GP_API_URL", api_url), ("MEDIA_WORKER_TOKEN", token)) if not v]
            why = "; ".join(f"{n} -> {SECRET_ERRORS.get(n, 'empty')}" for n in missing)
            raise SystemExit(
                f"Kaggle secrets not readable: {why}. In the editor open Add-ons -> Secrets and tick "
                "'Attached' next to each secret for THIS notebook, then Run All again."
            )
        self.api = api_url.rstrip("/") + "/api/v1/worker"
        self.headers = {"Authorization": f"Bearer {token}"}
        self.kinds = kinds
        self.worker_id = f"{socket.gethostname()}-{'-'.join(kinds)}"
        self.workdir = Path(os.environ.get("GP_WORKDIR", workdir))
        self.job: dict | None = None
        self._stage = ("claimed", 0.0)
        self._cancelled = False

    # --- API ---
    def _post(self, path: str, body: dict, tries: int = 1) -> dict:
        """tries > 1 for results: a tunnel blip (HTTP 530) once threw away a finished video."""
        for attempt in range(tries):
            try:
                r = requests.post(f"{self.api}{path}", json=body, headers=self.headers, timeout=60)
                r.raise_for_status()
                return r.json()
            except requests.RequestException as e:
                if attempt == tries - 1:
                    raise
                print(f"{path} failed ({e}); retrying", flush=True)
                time.sleep(min(60, 5 * 2**attempt))
        raise AssertionError("unreachable")

    def claim(self) -> dict | None:
        return self._post("/jobs/claim", {"worker_id": self.worker_id, "kinds": self.kinds})["job"]

    def progress(self, stage: str, value: float) -> None:
        """Called by the pipeline; raises Cancelled when the user cancelled the job."""
        self._stage = (stage, value)
        print(f"[{self.job['id'][:8]}] {stage} {value:.0%}", flush=True)
        if self._cancelled:
            raise Cancelled()

    def _heartbeat(self, stop: threading.Event) -> None:
        while not stop.wait(30):
            try:
                res = self._post(f"/jobs/{self.job['id']}/progress",
                                 {"stage": self._stage[0], "progress": self._stage[1]})
                self._cancelled = res.get("cancel", False)
            except requests.RequestException as e:
                print("heartbeat failed:", e, flush=True)

    # --- files ---
    def download(self, url: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True, timeout=600) as r:
            r.raise_for_status()
            with dest.open("wb") as f:
                shutil.copyfileobj(r.raw, f, 1 << 20)
        return dest

    def upload(self, name: str, path: Path) -> None:
        up = self.job["uploads"][name]
        with path.open("rb") as f:
            r = requests.put(up["url"], data=f, headers={"Content-Type": up["content_type"]}, timeout=1800)
        r.raise_for_status()

    # --- loop ---
    def run(self, handler, poll_seconds: int = 20, max_idle_minutes: float = 60) -> str:
        """handler(worker, job, workdir) -> {output name: metadata}. Uploads happen inside it.
        Returns "idle", or "gpu_lost" after a GPU fault so the host can start a fresh machine."""
        idle_since = time.time()
        while True:
            try:
                self.job = self.claim()
            except requests.RequestException as e:
                print("claim failed:", e, flush=True)
                self.job = None
            if self.job is None:
                if time.time() - idle_since > max_idle_minutes * 60:
                    print("idle, stopping to save GPU quota", flush=True)
                    return "idle"
                time.sleep(poll_seconds)
                continue
            idle_since = time.time()
            self._cancelled = False
            jobdir = self.workdir / self.job["id"]
            jobdir.mkdir(parents=True, exist_ok=True)
            stop = threading.Event()
            threading.Thread(target=self._heartbeat, args=(stop,), daemon=True).start()
            try:
                outputs = handler(self, self.job, jobdir)
                res = self._post(f"/jobs/{self.job['id']}/complete", {"outputs": outputs}, tries=8)  # ~6 min
                print("completed:", res, flush=True)
            except Cancelled:
                print("cancelled by user", flush=True)
            except Exception as e:
                traceback.print_exc()
                oom = "out of memory" in str(e).lower()
                # sd-cli only aborts (-6) with a backtrace, so its GPU fault shows up in ComfyUI next
                lost = any(m in str(e) for m in GPU_LOST) or "sd-cli MiniMax H3 failed (-6)" in str(e)
                try:
                    self._post(f"/jobs/{self.job['id']}/fail",
                               {"error": f"{type(e).__name__}: {e}"[:3900], "retryable": not oom}, tries=4)
                except requests.RequestException:
                    pass
                if lost:
                    print("GPU fault: giving the job back and stopping this machine", flush=True)
                    return "gpu_lost"
            finally:
                stop.set()
                shutil.rmtree(jobdir, ignore_errors=True)  # /kaggle/working is small


def ffmpeg(*args: str) -> None:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    subprocess.run(cmd, check=True)


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def has_nvenc() -> bool:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True)
    return "h264_nvenc" in out.stdout and shutil.which("nvidia-smi") is not None


def video_codec() -> list[str]:
    return ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "21"] if has_nvenc() else \
        ["-c:v", "libx264", "-preset", "medium", "-crf", "20"]
