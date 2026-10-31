"""Object storage: Cloudflare R2 (S3 API) in production, local disk in dev.

Browsers and Kaggle notebooks never get credentials: they receive short-lived presigned URLs and
move bytes directly to/from storage, so media never passes through PostgreSQL or the API process.
"""

import hashlib
import hmac
import time
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote, urlencode

from app.config import get_settings


def _r2_enabled() -> bool:
    s = get_settings()
    return bool(s.r2_account_id and s.r2_access_key_id and s.r2_secret_access_key)


@lru_cache
def _s3():
    import boto3
    from botocore.config import Config

    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=f"https://{s.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=s.r2_access_key_id,
        aws_secret_access_key=s.r2_secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


# --- local backend: HMAC-signed URLs served by app.api.files ---


def _sign(method: str, key: str, exp: int) -> str:
    msg = f"{method}\n{key}\n{exp}".encode()
    return hmac.new(get_settings().secret_key.encode(), msg, hashlib.sha256).hexdigest()


def verify_local(method: str, key: str, exp: int, sig: str) -> bool:
    return exp > time.time() and hmac.compare_digest(_sign(method, key, exp), sig)


def local_path(key: str) -> Path:
    root = Path(get_settings().local_media_dir).resolve()
    path = (root / key).resolve()
    if root not in path.parents:
        raise ValueError("key escapes media root")
    return path


def _local_url(method: str, key: str, seconds: int) -> str:
    exp = int(time.time()) + seconds
    q = urlencode({"exp": exp, "sig": _sign(method, key, exp)})
    return f"{get_settings().api_public_url}/api/v1/files/{quote(key)}?{q}"


# --- public interface ---


def presign_put(key: str, content_type: str, seconds: int | None = None) -> str:
    seconds = seconds or get_settings().presign_seconds
    if _r2_enabled():
        return _s3().generate_presigned_url(
            "put_object",
            Params={"Bucket": get_settings().r2_bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=seconds,
        )
    return _local_url("PUT", key, seconds)


def presign_get(key: str, seconds: int | None = None) -> str:
    seconds = seconds or get_settings().presign_seconds
    if _r2_enabled():
        return _s3().generate_presigned_url(
            "get_object", Params={"Bucket": get_settings().r2_bucket, "Key": key}, ExpiresIn=seconds
        )
    return _local_url("GET", key, seconds)


def size_of(key: str) -> int | None:
    """Bytes actually stored, or None when the object is missing (upload not finished)."""
    if _r2_enabled():
        from botocore.exceptions import ClientError

        try:
            return _s3().head_object(Bucket=get_settings().r2_bucket, Key=key)["ContentLength"]
        except ClientError:
            return None
    p = local_path(key)
    return p.stat().st_size if p.exists() else None


def delete(key: str) -> None:
    if _r2_enabled():
        _s3().delete_object(Bucket=get_settings().r2_bucket, Key=key)
    else:
        local_path(key).unlink(missing_ok=True)


def read_bytes(key: str, limit: int) -> bytes | None:
    """Small files only (briefs, reference images) for sending inline to Gemini."""
    if _r2_enabled():
        obj = _s3().get_object(Bucket=get_settings().r2_bucket, Key=key)
        return obj["Body"].read() if obj["ContentLength"] <= limit else None
    p = local_path(key)
    return p.read_bytes() if p.exists() and p.stat().st_size <= limit else None
