"""Publishing scheduler (MOD-05): approved creative -> Facebook Page at the scheduled time."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import meta, storage
from app.db import utcnow
from app.models import ArtifactVersion, PublishingJob, SocialAccount, StorageObject
from app.security import decrypt_secret

MAX_ATTEMPTS = 3


def run_job(db: Session, job: PublishingJob) -> None:
    account = db.get(SocialAccount, job.social_account_id)
    if account is None or account.status != "connected":
        job.status, job.last_error = "failed", "Page đã ngắt kết nối; kết nối lại rồi lên lịch lại"
        return
    version = db.get(ArtifactVersion, job.artifact_version_id)
    obj = db.get(StorageObject, version.storage_object_id) if version.storage_object_id else None
    if obj is None or obj.status != "ready":
        job.status, job.last_error = "failed", "Không tìm thấy tệp media của creative"
        return
    job.status, job.attempts = "publishing", job.attempts + 1
    db.flush()  # mark before calling Meta: a crash now leaves "publishing", never a silent retry
    res = meta.publish(
        account.external_id,
        decrypt_secret(account.token_encrypted),
        job.media_type,
        storage.presign_get(obj.key, seconds=3600),  # Meta fetches the file from R2 directly
        job.caption,
    )
    if res.ok:
        job.status, job.published_at = "published", utcnow()
        job.external_post_id = res.message_id or res.status
        job.last_error = None
    elif res.status == "unknown":
        job.status = "failed"
        job.last_error = f"Không rõ kết quả, kiểm tra Page trước khi đăng lại: {res.error}"
    else:
        job.status = (
            "scheduled" if job.attempts < MAX_ATTEMPTS and _retryable(res.error) else "failed"
        )
        job.last_error = res.error


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
