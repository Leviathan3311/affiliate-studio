"""Publishing calendar (MOD-05): approved creative -> Facebook Page, now or scheduled."""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.db import utcnow
from app.deps import Marketing
from app.models import Artifact, ArtifactVersion, PublishingJob, SocialAccount, StorageObject

router = APIRouter(prefix="/publishing-jobs", tags=["publishing"])


class PublishIn(BaseModel):
    artifact_id: uuid.UUID
    social_account_id: uuid.UUID
    caption: str = Field(default="", max_length=5000)
    scheduled_at: AwareDatetime | None = None  # None = publish now


class PublishPatch(BaseModel):
    caption: str | None = Field(default=None, max_length=5000)
    scheduled_at: AwareDatetime | None = None


class PublishOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID | None
    social_account_id: uuid.UUID
    artifact_version_id: uuid.UUID
    media_type: str
    caption: str
    scheduled_at: datetime
    timezone: str
    status: str
    external_post_id: str | None
    published_at: datetime | None
    attempts: int
    last_error: str | None
    created_at: datetime
    page_name: str = ""
    artifact_name: str = ""


def _out(db, j: PublishingJob) -> PublishOut:
    v = db.get(ArtifactVersion, j.artifact_version_id)
    art = db.get(Artifact, v.artifact_id)
    page = db.get(SocialAccount, j.social_account_id)
    return PublishOut.model_validate(j).model_copy(
        update={
            "page_name": page.name if page else "",
            "artifact_name": art.display_name if art else "",
        }
    )


@router.get("", response_model=list[PublishOut])
def list_jobs(
    ctx: Marketing,
    start: AwareDatetime | None = None,
    end: AwareDatetime | None = None,
    project_id: uuid.UUID | None = None,
    status_: Annotated[
        Literal["scheduled", "publishing", "published", "failed", "cancelled"] | None,
        Query(alias="status"),
    ] = None,
):
    stmt = select(PublishingJob).where(PublishingJob.workspace_id == ctx.ws_id)
    if start:
        stmt = stmt.where(PublishingJob.scheduled_at >= start)
    if end:
        stmt = stmt.where(PublishingJob.scheduled_at < end)
    if project_id:
        stmt = stmt.where(PublishingJob.project_id == project_id)
    if status_:
        stmt = stmt.where(PublishingJob.status == status_)
    return [
        _out(ctx.db, j)
        for j in ctx.db.scalars(stmt.order_by(PublishingJob.scheduled_at).limit(500))
    ]


@router.post("", response_model=PublishOut, status_code=201)
def create_job(body: PublishIn, ctx: Marketing):
    art = ctx.get(Artifact, body.artifact_id)
    if art.status != "approved":
        raise HTTPException(status.HTTP_409_CONFLICT, "Chỉ đăng creative đã được duyệt (Approved)")
    page = ctx.get(SocialAccount, body.social_account_id)
    if page.status != "connected":
        raise HTTPException(status.HTTP_409_CONFLICT, "Page chưa kết nối")
    v = ctx.db.get(ArtifactVersion, art.current_version_id)
    obj = ctx.db.get(StorageObject, v.storage_object_id) if v.storage_object_id else None
    if obj is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Creative chưa có tệp media")
    when = body.scheduled_at or utcnow()
    job = PublishingJob(
        workspace_id=ctx.ws_id,
        project_id=art.project_id,
        social_account_id=page.id,
        artifact_version_id=v.id,
        media_type="video" if obj.mime_type.startswith("video/") else "photo",
        caption=body.caption,
        scheduled_at=when,
        timezone=ctx.workspace.timezone,
        idempotency_key=uuid.uuid4().hex,
        approved_by=ctx.user.id,
    )
    ctx.db.add(job)
    ctx.db.flush()
    ctx.audit(
        "publishing.scheduled", "publishing_job", job.id, page=page.external_id, at=when.isoformat()
    )
    ctx.db.commit()
    return _out(ctx.db, job)


def _editable(ctx, job_id: uuid.UUID) -> PublishingJob:
    job = ctx.get(PublishingJob, job_id)
    if job.status not in ("scheduled", "failed"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Bài đã/đang đăng, không sửa được")
    return job


@router.patch("/{job_id}", response_model=PublishOut)
def patch_job(job_id: uuid.UUID, body: PublishPatch, ctx: Marketing):
    job = _editable(ctx, job_id)
    if body.caption is not None:
        job.caption = body.caption
    if body.scheduled_at is not None:
        job.scheduled_at, job.status, job.last_error = body.scheduled_at, "scheduled", None
    ctx.audit("publishing.updated", "publishing_job", job.id)
    ctx.db.commit()
    return _out(ctx.db, job)


@router.post("/{job_id}/publish-now", response_model=PublishOut)
def publish_now(job_id: uuid.UUID, ctx: Marketing):
    job = _editable(ctx, job_id)
    job.scheduled_at, job.status, job.last_error = utcnow(), "scheduled", None
    ctx.db.commit()
    return _out(ctx.db, job)


@router.post("/{job_id}/cancel", response_model=PublishOut)
def cancel_job(job_id: uuid.UUID, ctx: Marketing):
    job = _editable(ctx, job_id)
    job.status = "cancelled"
    ctx.audit("publishing.cancelled", "publishing_job", job.id)
    ctx.db.commit()
    return _out(ctx.db, job)
