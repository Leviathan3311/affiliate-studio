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


def secret(name: str, default: str | None = None) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    try:  # Kaggle secrets are only available inside a Kaggle session
        from kaggle_secrets import UserSecretsClient

        return UserSecretsClient().get_secret(name)
    except Exception:
        return default


class Cancelled(Exception):
    pass


class Worker:
    def __init__(self, kinds: list[str], workdir: str = "/kaggle/working/gp"):
        api_url, token = secret("GP_API_URL"), secret("MEDIA_WORKER_TOKEN")
        if not api_url or not token:
            # Fail fast: without these the notebook would download ~60 GB and idle on GPU quota.
            raise SystemExit("Missing Kaggle secrets GP_API_URL / MEDIA_WORKER_TOKEN (Add-ons -> Secrets).")
        self.api = api_url.rstrip("/") + "/api/v1/worker"
        self.headers = {"Authorization": f"Bearer {token}"}
        self.kinds = kinds
        self.worker_id = f"{socket.gethostname()}-{'-'.join(kinds)}"
        self.workdir = Path(os.environ.get("GP_WORKDIR", workdir))
        self.job: dict | None = None
        self._stage = ("claimed", 0.0)
        self._cancelled = False

    # --- API ---
    def _post(self, path: str, body: dict) -> dict:
        r = requests.post(f"{self.api}{path}", json=body, headers=self.headers, timeout=60)
        r.raise_for_status()
        return r.json()

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
    def run(self, handler, poll_seconds: int = 20, max_idle_minutes: float = 60) -> None:
        """handler(worker, job, workdir) -> {output name: metadata}. Uploads happen inside it."""
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
                    return
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
                res = self._post(f"/jobs/{self.job['id']}/complete", {"outputs": outputs})
                print("completed:", res, flush=True)
            except Cancelled:
                print("cancelled by user", flush=True)
            except Exception as e:
                traceback.print_exc()
                oom = "out of memory" in str(e).lower()
                try:
                    self._post(f"/jobs/{self.job['id']}/fail",
                               {"error": f"{type(e).__name__}: {e}"[:3900], "retryable": not oom})
                except requests.RequestException:
                    pass
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
