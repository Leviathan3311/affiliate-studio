"""GrowthPilot API + worker on Modal, so nothing depends on a laptop being on.

One small always-on container serves the FastAPI app and runs the worker loop in a thread (one
container only, so no job is processed twice). Media generation stays in notebooks/modal.

One-time setup (from the repo root):
    uvx modal secret create growthpilot-backend --from-dotenv backend/.env --force
    uvx modal deploy deploy/modal_backend.py
Then point api.<domain> at the printed *.modal.run URL (deploy/api-proxy) and stop the local
API and worker.
"""

import os
from pathlib import Path

import modal

BACKEND = Path(__file__).parent.parent / "backend"

image = (
    modal.Image.debian_slim(python_version="3.13")
    .pip_install_from_pyproject(str(BACKEND / "pyproject.toml"))
    .add_local_dir(BACKEND / "certs", "/srv/backend/certs")
    .add_local_dir(BACKEND / "app", "/srv/backend/app")
)
app = modal.App("growthpilot-backend")


def _env() -> None:
    # Secrets come from backend/.env; paths in it point at the laptop, so set the server ones here.
    os.environ.update(
        GP_ENV_FILE="",
        LOCAL_MEDIA_DIR="/tmp/media",
        POSTGRES_SSL_ROOT_CERT="/srv/backend/certs/supabase-ca.crt",
        FRONTEND_URL="https://app.growthpilot-spa.online",  # reset links and the Meta OAuth return
        API_PUBLIC_URL="https://api.growthpilot-spa.online",
    )
    import sys

    sys.path.insert(0, "/srv/backend")


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("growthpilot-backend")],
    cpu=0.25,
    memory=1024,
    min_containers=1,
    max_containers=1,
    timeout=600,
)
@modal.concurrent(max_inputs=64)
@modal.asgi_app()
def api():
    _env()
    import threading

    from app import worker
    from app.main import app as web

    threading.Thread(target=worker.main, name="worker", daemon=True).start()
    return web
