"""Publishing calendar (MOD-05): approved creative -> Facebook Page or Instagram, now or later."""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.core import storage
from app.core.db import utcnow
from app.core.deps import Marketing
from app.models import (
    Artifact,
    ArtifactVersion,
    Project,
    PublishingJob,
    SocialAccount,
    StorageObject,
)

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
            "page_name": (page.name + (" · Instagram" if page.provider == "instagram" else ""))
            if page
            else "",
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
        raise HTTPException(status.HTTP_409_CONFLICT, "Chỉ đăng được ảnh hoặc video đã duyệt")
    page = ctx.get(SocialAccount, body.social_account_id)
    if page.status != "connected":
        raise HTTPException(status.HTTP_409_CONFLICT, "Tài khoản chưa kết nối")
    if page.provider == "instagram" and len(body.caption) > 2200:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Instagram chỉ nhận nội dung tối đa 2.200 ký tự"
        )
    v = ctx.db.get(ArtifactVersion, art.current_version_id)
    obj = ctx.db.get(StorageObject, v.storage_object_id) if v.storage_object_id else None
    if obj is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ảnh hoặc video này chưa có tệp để đăng")
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


# --- photo posts: the shop's own picture, no project or AI generation needed ---

PHOTO_MIME = {"image/jpeg", "image/png", "image/webp"}
PHOTO_PROJECT = "Ảnh đăng bài"


class PhotoPresignIn(BaseModel):
    filename: str = Field(min_length=1, max_length=200)
    content_type: str
    byte_size: int = Field(gt=0)


class PhotoPostIn(BaseModel):
    object_id: uuid.UUID
    caption: str = Field(default="", max_length=5000)
    social_account_ids: list[uuid.UUID] = Field(min_length=1, max_length=10)
    scheduled_at: AwareDatetime | None = None  # None = publish now


def _photo_project(ctx) -> Project:
    """One project per workspace holds the photos posted from Lịch đăng (history and storage)."""
    p = ctx.db.scalar(
        select(Project).where(Project.workspace_id == ctx.ws_id, Project.name == PHOTO_PROJECT)
    )
    if p is None:
        p = Project(workspace_id=ctx.ws_id, name=PHOTO_PROJECT, created_by=ctx.user.id)
        ctx.db.add(p)
        ctx.db.flush()
    return p


@router.post("/photos/presign")
def presign_photo(body: PhotoPresignIn, ctx: Marketing):
    if body.content_type not in PHOTO_MIME:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Chỉ nhận ảnh JPG, PNG, WEBP")
    if body.byte_size > 8 * 1024 * 1024:  # Facebook and Instagram both cap photos at 8 MB
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Ảnh tối đa 8 MB")
    p = _photo_project(ctx)
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in body.filename)[-120:]
    obj = StorageObject(
        workspace_id=ctx.ws_id,
        project_id=p.id,
        key=f"ws/{ctx.ws_id}/projects/{p.id}/posts/{uuid.uuid4().hex}-{safe}",
        filename=body.filename,
        mime_type=body.content_type,
        byte_size=body.byte_size,
        category="upload",
    )
    ctx.db.add(obj)
    ctx.db.commit()
    return {
        "object_id": obj.id,
        "upload_url": storage.presign_put(obj.key, obj.mime_type, 3600),
        "headers": {"Content-Type": obj.mime_type},
    }


@router.post("/photos", response_model=list[PublishOut], status_code=201)
def post_photo(body: PhotoPostIn, ctx: Marketing):
    obj = ctx.get(StorageObject, body.object_id)
    size = storage.size_of(obj.key)
    if size is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ảnh chưa tải lên xong")
    obj.byte_size, obj.status = size, "ready"
    art = Artifact(
        workspace_id=ctx.ws_id,
        project_id=obj.project_id,
        kind="image",
        display_name=f"Ảnh · {obj.filename}"[:200],
        status="approved",
        updated_at=utcnow(),
    )
    ctx.db.add(art)
    ctx.db.flush()
    v = ArtifactVersion(
        workspace_id=ctx.ws_id,
        artifact_id=art.id,
        version_number=1,
        content={"source": "upload", "filename": obj.filename},
        actor="user",
        created_by=ctx.user.id,
        storage_object_id=obj.id,
    )
    ctx.db.add(v)
    ctx.db.flush()
    art.current_version_id = v.id
    ctx.db.commit()
    return [
        create_job(
            PublishIn(
                artifact_id=art.id,
                social_account_id=acc,
                caption=body.caption,
                scheduled_at=body.scheduled_at,
            ),
            ctx,
        )
        for acc in body.social_account_ids
    ]
