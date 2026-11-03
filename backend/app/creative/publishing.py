"""Publishing scheduler (MOD-05): approved creative -> Facebook Page or Instagram on schedule."""

import io

from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import storage
from app.core.db import utcnow
from app.core.security import decrypt_secret
from app.models import ArtifactVersion, PublishingJob, SocialAccount, StorageObject
from app.social import meta

MAX_ATTEMPTS = 3


def run_job(db: Session, job: PublishingJob) -> None:
    account = db.get(SocialAccount, job.social_account_id)
    if account is None or account.status != "connected":
        job.status, job.last_error = (
            "failed",
            "Tài khoản đã ngắt kết nối; kết nối lại rồi lên lịch lại",
        )
        return
    version = db.get(ArtifactVersion, job.artifact_version_id)
    obj = db.get(StorageObject, version.storage_object_id) if version.storage_object_id else None
    if obj is None or obj.status != "ready":
        job.status, job.last_error = "failed", "Không tìm thấy tệp media của creative"
        return
    key = obj.key
    if (
        account.provider == "instagram"
        and job.media_type == "photo"
        and obj.mime_type != "image/jpeg"
    ):
        key = _jpeg_copy(obj.key)  # Instagram only takes JPEG photos
        if key is None:
            job.status, job.last_error = "failed", "Ảnh quá lớn để chuyển sang JPG cho Instagram"
            return
    job.status, job.attempts = "publishing", job.attempts + 1
    db.flush()  # mark before calling Meta: a crash now leaves "publishing", never a silent retry
    post = meta.publish_instagram if account.provider == "instagram" else meta.publish
    res = post(
        account.external_id,
        decrypt_secret(account.token_encrypted),
        job.media_type,
        storage.presign_get(key, seconds=3600),  # Meta fetches the file from R2 directly
        job.caption,
    )
    if res.ok:
        job.status, job.published_at = "published", utcnow()
        job.external_post_id = res.message_id or res.status
        job.last_error = None
    elif res.status == "unknown":
        job.status = "failed"
        job.last_error = (
            f"Không rõ kết quả, kiểm tra Page/Instagram trước khi đăng lại: {res.error}"
        )
    else:
        job.status = (
            "scheduled" if job.attempts < MAX_ATTEMPTS and _retryable(res.error) else "failed"
        )
        job.last_error = res.error


def _jpeg_copy(key: str) -> str | None:
    data = storage.read_bytes(key, 30 * 1024 * 1024)
    if data is None:
        return None
    out = io.BytesIO()
    Image.open(io.BytesIO(data)).convert("RGB").save(out, "JPEG", quality=92)
    jpeg = key.rsplit(".", 1)[0] + ".ig.jpg"
    storage.put_bytes(jpeg, out.getvalue(), "image/jpeg")
    return jpeg


def _retryable(error: str | None) -> bool:
    return bool(error) and any(
        w in error.lower() for w in ("temporar", "rate", "timeout", "try again")
    )


def due_jobs(db: Session, limit: int = 10) -> list[PublishingJob]:
    stmt = (
        select(PublishingJob)
        .where(PublishingJob.status == "scheduled", PublishingJob.scheduled_at <= utcnow())
        .order_by(PublishingJob.scheduled_at)
        .limit(limit)
    )
    if db.get_bind().dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)
    return db.scalars(stmt).all()
