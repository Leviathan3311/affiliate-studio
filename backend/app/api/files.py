"""Local-disk stand-in for R2 presigned URLs (dev only; R2 serves these directly in production)."""

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.config import get_settings
from app.storage import local_path, verify_local

router = APIRouter(prefix="/files", tags=["files"])


def _check(method: str, key: str, exp: int, sig: str):
    if not verify_local(method, key, exp, sig):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "expired or invalid signature")
    try:
        return local_path(key)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "bad key") from None


@router.put("/{key:path}", status_code=200)
async def put_file(key: str, exp: int, sig: str, request: Request):
    path = _check("PUT", key, exp, sig)
    path.parent.mkdir(parents=True, exist_ok=True)
    limit = get_settings().max_upload_mb * 1024 * 1024
    written = 0
    with path.open("wb") as f:
        async for chunk in request.stream():
            written += len(chunk)
            if written > limit:
                f.close()
                path.unlink(missing_ok=True)
                raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "file too large")
            f.write(chunk)
    return {"ok": True, "bytes": written}


@router.get("/{key:path}")
def get_file(key: str, exp: int, sig: str):
    path = _check("GET", key, exp, sig)
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
    return FileResponse(path)
