"""Project Creative Workspace (BRD MOD-02A, journey §6.2). The project is the single source of
truth for a campaign; chat drives it, the Project Library stores its deliverables."""

import logging
import string
import uuid
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy import func, select

from app.ai import agents
from app.ai.llm import LLMUnavailable
from app.core import db as dbmod
from app.core import storage
from app.core.config import get_settings
from app.core.db import utcnow
from app.core.deps import AnyMember, Marketing
from app.creative import media
from app.models import (
    INPUT_ROLES,
    Artifact,
    ArtifactVersion,
    ChatMessage,
    MediaJob,
    Project,
    ProjectInput,
    Service,
    StorageObject,
)

log = logging.getLogger("growthpilot.projects")
router = APIRouter(tags=["projects"])
TRASH_DAYS = 30
UPLOAD_MIME = {
    "application/pdf": "document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
    "text/plain": "document",
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
    "video/mp4": "video",
    "video/quicktime": "video",
}


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- schemas ----------


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    objective: str = Field(default="promote_service", max_length=48)
    service_id: uuid.UUID | None = None
    audience: str = Field(default="", max_length=2000)
    location: str = Field(default="", max_length=200)
    start_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    brief: str = Field(default="", max_length=20000)
    research_urls: list[HttpUrl] = Field(default_factory=list, max_length=8)


class ProjectPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    objective: str | None = Field(default=None, max_length=48)
    service_id: uuid.UUID | None = None
    audience: str | None = Field(default=None, max_length=2000)
    location: str | None = Field(default=None, max_length=200)
    start_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    brief: str | None = Field(default=None, max_length=20000)
    research_urls: list[HttpUrl] | None = Field(default=None, max_length=8)


class ProjectOut(ORM):
    id: uuid.UUID
    name: str
    objective: str
    service_id: uuid.UUID | None
    audience: str
    location: str
    start_date: str | None
    end_date: str | None
    brief: str
    research_urls: list[str]
    status: str
    context: dict | None
    context_confirmed_at: datetime | None
    deleted_at: datetime | None
    created_at: datetime
    counts: dict[str, int] = {}
    storage_bytes: int = 0
    cover_url: str | None = None


class PresignIn(BaseModel):
    filename: str = Field(min_length=1, max_length=300)
    content_type: str
    byte_size: int = Field(gt=0)


class InputIn(BaseModel):
    object_id: uuid.UUID
    role: Literal[INPUT_ROLES] = "reference"  # type: ignore[valid-type]
    title: str = Field(default="", max_length=300)
    description: str = Field(default="", max_length=2000)
    usage_confirmed: bool = False
    preserve: bool = False


class InputPatch(BaseModel):
    role: Literal[INPUT_ROLES] | None = None  # type: ignore[valid-type]
    title: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    usage_confirmed: bool | None = None
    preserve: bool | None = None


class InputOut(ORM):
    id: uuid.UUID
    role: str
    title: str
    description: str
    usage_confirmed: bool
    preserve: bool
    filename: str = ""
    mime_type: str = ""
    byte_size: int = 0
    url: str = ""
    created_at: datetime


class ContextPatch(BaseModel):
    context: dict
    confirm: bool = True


class VersionOut(ORM):
    id: uuid.UUID
    version_number: int
    parent_version_id: uuid.UUID | None
    content: dict
    actor: str
    provider: str | None
    model: str | None
    media_job_id: uuid.UUID | None
    created_at: datetime
    url: str | None = None
    mime_type: str | None = None
    byte_size: int | None = None


class ArtifactOut(ORM):
    id: uuid.UUID
    kind: str
    display_name: str
    variant_key: str | None
    status: str
    pinned: bool
    error: str | None
    created_at: datetime
    updated_at: datetime | None
    current: VersionOut | None = None
    version_count: int = 0


class ArtifactDetail(ArtifactOut):
    versions: list[VersionOut] = []


class ArtifactPatch(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    pinned: bool | None = None
    archived: bool | None = None


class ScriptEdit(BaseModel):
    content: dict


class ResearchIn(BaseModel):
    mode: Literal["quick", "standard", "deep"] = "standard"


class ScriptsIn(BaseModel):
    count: int = Field(default=3, ge=1, le=5)
    instruction: str = Field(default="", max_length=2000)


class ReviseIn(BaseModel):
    instruction: str = Field(min_length=1, max_length=2000)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    artifact_id: uuid.UUID | None = None


class ChatOut(ORM):
    id: uuid.UUID
    role: str
    content: str
    artifact_id: uuid.UUID | None
    action: dict | None
    created_at: datetime


class GenerateIn(BaseModel):
    script_artifact_id: uuid.UUID
    extra_instruction: str = Field(default="", max_length=1000)
    disable_style: bool = False


class ShortsIn(BaseModel):
    source_artifact_id: uuid.UUID | None = None
    source_input_id: uuid.UUID | None = None
    target_count: int = Field(default=3, ge=1, le=5)
    cta: str = Field(default="", max_length=200)


class JobOut(ORM):
    id: uuid.UUID
    kind: str
    status: str
    stage: str
    progress: float
    attempts: int
    error: str | None
    created_at: datetime
    finished_at: datetime | None
    prompt_snapshot: dict


# ---------- helpers ----------


def _project(ctx, project_id: uuid.UUID, allow_deleted: bool = False) -> Project:
    p = ctx.get(Project, project_id)
    if p.status == "deleted" and not allow_deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return p


def _artifact(ctx, artifact_id: uuid.UUID) -> Artifact:
    a = ctx.get(Artifact, artifact_id)
    _project(ctx, a.project_id)
    return a


def _version_out(db, v: ArtifactVersion | None) -> VersionOut | None:
    if v is None:
        return None
    out = VersionOut.model_validate(v)
    if v.storage_object_id:
        obj = db.get(StorageObject, v.storage_object_id)
        if obj and obj.status == "ready":
            out.url, out.mime_type, out.byte_size = (
                storage.presign_get(obj.key),
                obj.mime_type,
                obj.byte_size,
            )
    return out


def _artifact_out(db, a: Artifact, cls=ArtifactOut, **extra):
    current = db.get(ArtifactVersion, a.current_version_id) if a.current_version_id else None
    count = db.scalar(select(func.count()).where(ArtifactVersion.artifact_id == a.id))
    return cls.model_validate(
        {
            **ArtifactOut.model_validate(a).model_dump(exclude={"current", "version_count"}),
            "current": _version_out(db, current),
            "version_count": count,
            **extra,
        }
    )


def _project_out(db, p: Project) -> ProjectOut:
    counts = dict(
        db.execute(
            select(Artifact.kind, func.count())
            .where(Artifact.project_id == p.id, Artifact.status != "archived")
            .group_by(Artifact.kind)
        ).all()
    )
    used = db.scalar(
        select(func.coalesce(func.sum(StorageObject.byte_size), 0)).where(
            StorageObject.project_id == p.id, StorageObject.status == "ready"
        )
    )
    cover = db.scalar(
        select(StorageObject)
        .join(ArtifactVersion, ArtifactVersion.storage_object_id == StorageObject.id)
        .join(Artifact, Artifact.current_version_id == ArtifactVersion.id)
        .where(
            Artifact.project_id == p.id, Artifact.kind == "image", StorageObject.status == "ready"
        )
        .order_by(Artifact.created_at)
        .limit(1)
    )
    out = ProjectOut.model_validate(p)
    out.counts, out.storage_bytes = counts, int(used)
    out.cover_url = storage.presign_get(cover.key) if cover else None
    return out


def _add_version(
    db, art: Artifact, content: dict, actor: str, *, model=None, user_id=None
) -> ArtifactVersion:
    last = db.get(ArtifactVersion, art.current_version_id) if art.current_version_id else None
    v = ArtifactVersion(
        workspace_id=art.workspace_id,
        artifact_id=art.id,
        version_number=(last.version_number + 1) if last else 1,
        parent_version_id=last.id if last else None,
        content=content,
        actor=actor,
        provider="gemini" if model else None,
        model=model,
        created_by=user_id,
    )
    db.add(v)
    db.flush()
    art.current_version_id, art.updated_at = v.id, utcnow()
    return v


def _next_variant_keys(db, project_id: uuid.UUID, n: int) -> list[str]:
    used = set(
        db.scalars(
            select(Artifact.variant_key).where(
                Artifact.project_id == project_id, Artifact.kind == "script"
            )
        )
    )
    return [k for k in string.ascii_uppercase if k not in used][:n]


def _latest_research(db, project_id: uuid.UUID) -> dict | None:
    art = db.scalar(
        select(Artifact)
        .where(
            Artifact.project_id == project_id,
            Artifact.kind == "research",
            Artifact.status.in_(("ready", "selected")),
        )
        .order_by(Artifact.created_at.desc())
        .limit(1)
    )
    v = db.get(ArtifactVersion, art.current_version_id) if art and art.current_version_id else None
    return v.content if v else None


def _in_background(fn, *args) -> None:
    """Runs a stream-2 task with its own session; failures land on the artifact, not lost."""
    with dbmod.SessionLocal() as db:
        try:
            fn(db, *args)
            db.commit()
        except Exception as e:
            db.rollback()
            log.exception("background task %s failed", fn.__name__)
            msg = (
                "Chưa cấu hình GEMINI_API_KEY"
                if "no api key" in str(e)
                else f"{type(e).__name__}: {e}"
            )
            flat = [x for a in args for x in (a if isinstance(a, list) else [a])]
            for art_id in [a for a in flat if isinstance(a, uuid.UUID)]:
                art = db.get(Artifact, art_id)
                if art and art.status == "generating":
                    art.status, art.error = "failed", msg[:500]
            db.commit()


# ---------- background jobs (stream 2) ----------


def task_context(db, project_id: uuid.UUID) -> None:
    p = db.get(Project, project_id)
    p.context = agents.build_project_context(db, p).model_dump()
    p.context_confirmed_at = None


def task_research(db, project_id: uuid.UUID, art_id: uuid.UUID, mode: str) -> None:
    p, art = db.get(Project, project_id), db.get(Artifact, art_id)
    report, model = agents.run_research(db, p, mode)
    _add_version(db, art, report, "ai", model=model)
    art.status = "ready"


def task_scripts(db, project_id: uuid.UUID, art_ids: list[uuid.UUID], instruction: str) -> None:
    p = db.get(Project, project_id)
    variants, model = agents.generate_scripts(
        db, p, _latest_research(db, project_id), len(art_ids), instruction
    )
    arts = [db.get(Artifact, i) for i in art_ids]
    for art, v in zip(arts, variants, strict=False):
        art.display_name = f"Kịch bản {art.variant_key} — {v['title']}"[:200]
        _add_version(db, art, v, "ai", model=model)
        art.status = "ready"
    for art in arts[len(variants) :]:
        art.status, art.error = "failed", "AI trả về ít phương án hơn yêu cầu"


def task_revise(db, art_id: uuid.UUID, instruction: str, user_id: uuid.UUID | None) -> None:
    art = db.get(Artifact, art_id)
    current = db.get(ArtifactVersion, art.current_version_id)
    revised, model = agents.revise_script(
        db, db.get(Project, art.project_id), current.content, instruction
    )
    revised["instruction"] = instruction
    _add_version(db, art, revised, "ai", model=model, user_id=user_id)
    art.status = "selected" if art.error == "selected" else "ready"
    art.error = None


def _start_research(ctx, p: Project, mode: str, bg: BackgroundTasks) -> Artifact:
    label = {
        "quick": "Quick Insight",
        "standard": "Nghiên cứu thị trường",
        "deep": "Deep Research",
    }[mode]
    art = Artifact(
        workspace_id=ctx.ws_id,
        project_id=p.id,
        kind="research",
        display_name=f"{label} — {utcnow():%d/%m}",
        status="generating",
        updated_at=utcnow(),
    )
    ctx.db.add(art)
    ctx.db.flush()
    bg.add_task(_in_background, task_research, p.id, art.id, mode)
    return art


def _start_scripts(
    ctx, p: Project, count: int, instruction: str, bg: BackgroundTasks
) -> list[Artifact]:
    arts = []
    for key in _next_variant_keys(ctx.db, p.id, count):
        a = Artifact(
            workspace_id=ctx.ws_id,
            project_id=p.id,
            kind="script",
            variant_key=key,
            display_name=f"Kịch bản {key}",
            status="generating",
            updated_at=utcnow(),
        )
        ctx.db.add(a)
        arts.append(a)
    if not arts:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Dự án đã có đủ 26 kịch bản; lưu trữ bớt rồi viết thêm"
        )
    ctx.db.flush()
    bg.add_task(_in_background, task_scripts, p.id, [a.id for a in arts], instruction)
    return arts


def _start_revise(ctx, art: Artifact, instruction: str, bg: BackgroundTasks) -> None:
    if art.kind != "script" or not art.current_version_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Chỉ sửa được kịch bản đã có nội dung")
    # remember the selected state across the generating phase
    art.error = "selected" if art.status == "selected" else None
    art.status = "generating"
    bg.add_task(_in_background, task_revise, art.id, instruction, ctx.user.id)


# ---------- projects ----------


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(ctx: AnyMember, include_deleted: bool = False):
    stmt = select(Project).where(Project.workspace_id == ctx.ws_id)
    if not include_deleted:
        stmt = stmt.where(Project.status != "deleted")
    return [
        _project_out(ctx.db, p) for p in ctx.db.scalars(stmt.order_by(Project.created_at.desc()))
    ]


@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectIn, ctx: Marketing):
    if body.service_id:
        ctx.get(Service, body.service_id)
    data = body.model_dump()
    data["research_urls"] = [str(u) for u in body.research_urls]
    p = Project(workspace_id=ctx.ws_id, created_by=ctx.user.id, **data)
    ctx.db.add(p)
    ctx.db.flush()
    ctx.audit("project.created", "project", p.id)
    ctx.db.commit()
    return _project_out(ctx.db, p)


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: uuid.UUID, ctx: AnyMember):
    return _project_out(ctx.db, _project(ctx, project_id, allow_deleted=True))


@router.patch("/projects/{project_id}", response_model=ProjectOut)
def patch_project(project_id: uuid.UUID, body: ProjectPatch, ctx: Marketing):
    """Wizard autosave: only the fields sent are written."""
    p = _project(ctx, project_id)
    changes = body.model_dump(exclude_unset=True)
    if changes.get("service_id"):
        ctx.get(Service, changes["service_id"])
    if changes.get("research_urls") is not None:
        changes["research_urls"] = [str(u) for u in changes["research_urls"]]
    for k, v in changes.items():
        setattr(p, k, v)
    if p.status == "draft" and p.brief and p.service_id:
        p.status = "active"
    ctx.db.commit()
    return _project_out(ctx.db, p)


@router.post("/projects/{project_id}/archive", response_model=ProjectOut)
def archive_project(project_id: uuid.UUID, ctx: Marketing):
    p = _project(ctx, project_id)
    p.status = "archived"
    ctx.audit("project.archived", "project", p.id)
    ctx.db.commit()
    return _project_out(ctx.db, p)


@router.delete("/projects/{project_id}", response_model=ProjectOut)
def delete_project(project_id: uuid.UUID, ctx: Marketing):
    """Soft delete into Trash; the worker purges storage after TRASH_DAYS."""
    p = _project(ctx, project_id)
    p.status, p.deleted_at = "deleted", utcnow()
    for job in ctx.db.scalars(
        select(MediaJob).where(MediaJob.project_id == p.id, MediaJob.status == "queued")
    ):
        job.status = "cancelled"
    ctx.audit("project.deleted", "project", p.id)
    ctx.db.commit()
    return _project_out(ctx.db, p)


@router.post("/projects/{project_id}/restore", response_model=ProjectOut)
def restore_project(project_id: uuid.UUID, ctx: Marketing):
    p = _project(ctx, project_id, allow_deleted=True)
    if p.status != "deleted" or p.deleted_at < utcnow() - timedelta(days=TRASH_DAYS):
        raise HTTPException(status.HTTP_409_CONFLICT, "Dự án không còn trong thùng rác")
    p.status, p.deleted_at = "active", None
    ctx.audit("project.restored", "project", p.id)
    ctx.db.commit()
    return _project_out(ctx.db, p)


# ---------- inputs & assets ----------


@router.post("/projects/{project_id}/inputs/presign")
def presign_input(project_id: uuid.UUID, body: PresignIn, ctx: Marketing):
    p = _project(ctx, project_id)
    category = UPLOAD_MIME.get(body.content_type)
    if category is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Chỉ nhận PDF, DOCX, TXT, JPG, PNG, WEBP, MP4, MOV",
        )
    s = get_settings()
    if body.byte_size > s.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Tối đa {s.max_upload_mb} MB mỗi tệp"
        )
    used = ctx.db.scalar(
        select(func.coalesce(func.sum(StorageObject.byte_size), 0)).where(
            StorageObject.workspace_id == ctx.ws_id, StorageObject.status == "ready"
        )
    )
    if used + body.byte_size > s.storage_quota_mb * 1024 * 1024:
        raise HTTPException(
            status.HTTP_507_INSUFFICIENT_STORAGE,
            "Hết dung lượng lưu trữ; xoá bớt tệp cũ hoặc nâng gói",
        )
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in body.filename)[-120:]
    obj = StorageObject(
        workspace_id=ctx.ws_id,
        project_id=p.id,
        key=f"ws/{ctx.ws_id}/projects/{p.id}/uploads/{uuid.uuid4().hex}-{safe}",
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


def _input_out(inp: ProjectInput, obj: StorageObject) -> InputOut:
    out = InputOut.model_validate(inp)
    out.filename, out.mime_type, out.byte_size = obj.filename, obj.mime_type, obj.byte_size
    out.url = storage.presign_get(obj.key)
    return out


@router.post("/projects/{project_id}/inputs", response_model=InputOut, status_code=201)
def confirm_input(project_id: uuid.UUID, body: InputIn, ctx: Marketing):
    p = _project(ctx, project_id)
    obj = ctx.get(StorageObject, body.object_id)
    if obj.project_id != p.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Upload not found")
    size = storage.size_of(obj.key)
    if size is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Tệp chưa tải lên xong")
    obj.byte_size, obj.status = size, "ready"
    inp = ProjectInput(
        workspace_id=ctx.ws_id,
        project_id=p.id,
        storage_object_id=obj.id,
        **body.model_dump(exclude={"object_id"}),
    )
    ctx.db.add(inp)
    ctx.audit(
        "project.input_added", "project", p.id, role=body.role, usage_confirmed=body.usage_confirmed
    )
    ctx.db.commit()
    return _input_out(inp, obj)


@router.get("/projects/{project_id}/inputs", response_model=list[InputOut])
def list_inputs(project_id: uuid.UUID, ctx: AnyMember):
    p = _project(ctx, project_id)
    rows = ctx.db.execute(
        select(ProjectInput, StorageObject)
        .join(StorageObject, StorageObject.id == ProjectInput.storage_object_id)
        .where(ProjectInput.project_id == p.id, StorageObject.status == "ready")
        .order_by(ProjectInput.created_at)
    ).all()
    return [_input_out(i, o) for i, o in rows]


@router.patch("/project-inputs/{input_id}", response_model=InputOut)
def patch_input(input_id: uuid.UUID, body: InputPatch, ctx: Marketing):
    inp = ctx.get(ProjectInput, input_id)
    _project(ctx, inp.project_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(inp, k, v)
    ctx.db.commit()
    return _input_out(inp, ctx.db.get(StorageObject, inp.storage_object_id))


@router.delete("/project-inputs/{input_id}", status_code=204)
def delete_input(input_id: uuid.UUID, ctx: Marketing):
    inp = ctx.get(ProjectInput, input_id)
    _project(ctx, inp.project_id)
    obj = ctx.db.get(StorageObject, inp.storage_object_id)
    storage.delete(obj.key)
    obj.status = "deleted"
    ctx.db.delete(inp)
    ctx.audit("project.input_deleted", "storage_object", obj.id, bytes=obj.byte_size)
    ctx.db.commit()


# ---------- context ----------


@router.post("/projects/{project_id}/context/build", status_code=202)
def build_context(project_id: uuid.UUID, ctx: Marketing, bg: BackgroundTasks):
    p = _project(ctx, project_id)
    bg.add_task(_in_background, task_context, p.id)
    return {"status": "building"}


@router.patch("/projects/{project_id}/context", response_model=ProjectOut)
def patch_context(project_id: uuid.UUID, body: ContextPatch, ctx: Marketing):
    p = _project(ctx, project_id)
    p.context = agents.ProjectContext.model_validate(body.context).model_dump()
    p.context_confirmed_at = utcnow() if body.confirm else None
    ctx.audit("project.context_updated", "project", p.id, confirmed=body.confirm)
    ctx.db.commit()
    return _project_out(ctx.db, p)


# ---------- artifacts (Project Library) ----------


@router.get("/projects/{project_id}/artifacts", response_model=list[ArtifactOut])
def list_artifacts(
    project_id: uuid.UUID, ctx: AnyMember, kind: str | None = None, include_archived: bool = False
):
    p = _project(ctx, project_id)
    stmt = select(Artifact).where(Artifact.project_id == p.id)
    if kind:
        stmt = stmt.where(Artifact.kind == kind)
    if not include_archived:
        stmt = stmt.where(Artifact.status != "archived")
    stmt = stmt.order_by(
        Artifact.pinned.desc(), Artifact.kind, Artifact.variant_key, Artifact.created_at
    )
    return [_artifact_out(ctx.db, a) for a in ctx.db.scalars(stmt)]


@router.get("/artifacts/{artifact_id}", response_model=ArtifactDetail)
def get_artifact(artifact_id: uuid.UUID, ctx: AnyMember):
    a = _artifact(ctx, artifact_id)
    versions = ctx.db.scalars(
        select(ArtifactVersion)
        .where(ArtifactVersion.artifact_id == a.id)
        .order_by(ArtifactVersion.version_number.desc())
    ).all()
    return _artifact_out(
        ctx.db, a, ArtifactDetail, versions=[_version_out(ctx.db, v) for v in versions]
    )


@router.patch("/artifacts/{artifact_id}", response_model=ArtifactOut)
def patch_artifact(artifact_id: uuid.UUID, body: ArtifactPatch, ctx: Marketing):
    a = _artifact(ctx, artifact_id)
    if body.display_name is not None:
        a.display_name = body.display_name
    if body.pinned is not None:
        a.pinned = body.pinned
    if body.archived is not None and a.status != "generating":
        a.status = "archived" if body.archived else "ready"
    a.updated_at = utcnow()
    ctx.db.commit()
    return _artifact_out(ctx.db, a)


@router.post("/artifacts/{artifact_id}/versions", response_model=ArtifactOut)
def save_version(artifact_id: uuid.UUID, body: ScriptEdit, ctx: Marketing):
    """Manual edit of a script: new version, original kept."""
    a = _artifact(ctx, artifact_id)
    if a.kind != "script":
        raise HTTPException(status.HTTP_409_CONFLICT, "Chỉ sửa tay được kịch bản")
    content = agents.ScriptVariant.model_validate(body.content).model_dump()
    content["flags"] = agents._script_flags(ctx.db, ctx.db.get(Project, a.project_id), content)
    _add_version(ctx.db, a, content, "user", user_id=ctx.user.id)
    ctx.db.commit()
    return _artifact_out(ctx.db, a)


@router.post("/artifacts/{artifact_id}/duplicate", response_model=ArtifactOut, status_code=201)
def duplicate_artifact(artifact_id: uuid.UUID, ctx: Marketing):
    a = _artifact(ctx, artifact_id)
    if a.kind != "script" or not a.current_version_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Chỉ nhân bản được kịch bản")
    key = _next_variant_keys(ctx.db, a.project_id, 1)
    copy = Artifact(
        workspace_id=a.workspace_id,
        project_id=a.project_id,
        kind="script",
        variant_key=key[0] if key else None,
        display_name=f"{a.display_name} (bản sao)"[:200],
        status="ready",
        updated_at=utcnow(),
    )
    ctx.db.add(copy)
    ctx.db.flush()
    _add_version(
        ctx.db,
        copy,
        ctx.db.get(ArtifactVersion, a.current_version_id).content,
        "user",
        user_id=ctx.user.id,
    )
    ctx.db.commit()
    return _artifact_out(ctx.db, copy)


@router.post("/artifacts/{artifact_id}/select", response_model=ArtifactOut)
def select_artifact(artifact_id: uuid.UUID, ctx: Marketing):
    """One selected script per project; selection never auto-generates anything."""
    a = _artifact(ctx, artifact_id)
    if a.status not in ("ready", "selected"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Phương án chưa sẵn sàng")
    for other in ctx.db.scalars(
        select(Artifact).where(
            Artifact.project_id == a.project_id,
            Artifact.kind == a.kind,
            Artifact.status == "selected",
        )
    ):
        other.status = "ready"
    a.status, a.updated_at = "selected", utcnow()
    ctx.audit("artifact.selected", "artifact", a.id, version=str(a.current_version_id))
    ctx.db.commit()
    return _artifact_out(ctx.db, a)


@router.post("/artifacts/{artifact_id}/approve", response_model=ArtifactOut)
def approve_artifact(artifact_id: uuid.UUID, ctx: Marketing):
    a = _artifact(ctx, artifact_id)
    if a.kind not in ("image", "video", "short") or a.status not in ("ready", "selected"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Chỉ duyệt được ảnh/video đã tạo xong")
    a.status, a.updated_at = "approved", utcnow()
    ctx.audit("artifact.approved", "artifact", a.id, version=str(a.current_version_id))
    ctx.db.commit()
    return _artifact_out(ctx.db, a)


@router.delete("/artifacts/{artifact_id}", status_code=204)
def delete_artifact(artifact_id: uuid.UUID, ctx: Marketing):
    a = _artifact(ctx, artifact_id)
    for v in ctx.db.scalars(select(ArtifactVersion).where(ArtifactVersion.artifact_id == a.id)):
        if v.storage_object_id:
            obj = ctx.db.get(StorageObject, v.storage_object_id)
            if obj and obj.status == "ready":
                storage.delete(obj.key)
                obj.status = "deleted"
    a.current_version_id = None
    ctx.db.flush()
    ctx.db.delete(a)
    ctx.audit("artifact.deleted", "artifact", artifact_id)
    ctx.db.commit()


# ---------- AI actions ----------


def _gemini_ready() -> None:
    if not get_settings().gemini_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI nghiên cứu và viết kịch bản chưa được bật, vui lòng liên hệ hỗ trợ",
        )


@router.post("/projects/{project_id}/research", response_model=ArtifactOut, status_code=202)
def start_research(project_id: uuid.UUID, body: ResearchIn, ctx: Marketing, bg: BackgroundTasks):
    _gemini_ready()
    p = _project(ctx, project_id)
    if body.mode == "quick":
        # Cache freshness (MOD-03A): reuse a report from the last 7 days instead of re-searching.
        fresh = ctx.db.scalar(
            select(Artifact)
            .where(
                Artifact.project_id == p.id,
                Artifact.kind == "research",
                Artifact.status == "ready",
                Artifact.created_at > utcnow() - timedelta(days=7),
            )
            .order_by(Artifact.created_at.desc())
            .limit(1)
        )
        if fresh:
            return _artifact_out(ctx.db, fresh)
    art = _start_research(ctx, p, body.mode, bg)
    ctx.db.commit()
    return _artifact_out(ctx.db, art)


@router.post("/projects/{project_id}/scripts", response_model=list[ArtifactOut], status_code=202)
def start_scripts(project_id: uuid.UUID, body: ScriptsIn, ctx: Marketing, bg: BackgroundTasks):
    _gemini_ready()
    p = _project(ctx, project_id)
    arts = _start_scripts(ctx, p, body.count, body.instruction, bg)
    ctx.db.commit()
    return [_artifact_out(ctx.db, a) for a in arts]


@router.post("/artifacts/{artifact_id}/revise", response_model=ArtifactOut, status_code=202)
def revise(artifact_id: uuid.UUID, body: ReviseIn, ctx: Marketing, bg: BackgroundTasks):
    _gemini_ready()
    a = _artifact(ctx, artifact_id)
    _start_revise(ctx, a, body.instruction, bg)
    ctx.db.commit()
    return _artifact_out(ctx.db, a)


@router.get("/projects/{project_id}/chat", response_model=list[ChatOut])
def chat_history(project_id: uuid.UUID, ctx: AnyMember):
    p = _project(ctx, project_id)
    return ctx.db.scalars(
        select(ChatMessage)
        .where(ChatMessage.project_id == p.id)
        .order_by(ChatMessage.created_at)
        .limit(200)
    ).all()


@router.post("/projects/{project_id}/chat", response_model=list[ChatOut])
def chat(project_id: uuid.UUID, body: ChatIn, ctx: Marketing, bg: BackgroundTasks):
    _gemini_ready()
    p = _project(ctx, project_id)
    db = ctx.db
    selected = None
    art = _artifact(ctx, body.artifact_id) if body.artifact_id else None
    if art and art.kind == "script" and art.current_version_id:
        selected = db.get(ArtifactVersion, art.current_version_id).content
    history = [
        {"role": m.role, "content": m.content}
        for m in db.scalars(
            select(ChatMessage)
            .where(ChatMessage.project_id == p.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(10)
        )
    ][::-1]
    user_msg = ChatMessage(
        workspace_id=ctx.ws_id,
        project_id=p.id,
        artifact_id=art.id if art else None,
        role="user",
        content=body.message,
        user_id=ctx.user.id,
    )
    db.add(user_msg)
    try:
        out = agents.orchestrate(db, p, history, body.message, selected)
    except LLMUnavailable:
        db.commit()
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "AI đang bận, thử lại sau ít phút"
        ) from None

    action: dict = {"type": out.action}
    if out.action == "research":
        action["artifact_ids"] = [str(_start_research(ctx, p, out.research_mode, bg).id)]
    elif out.action == "generate_scripts":
        action["artifact_ids"] = [
            str(a.id) for a in _start_scripts(ctx, p, out.count, out.instruction, bg)
        ]
    elif out.action == "revise_script" and art:
        _start_revise(ctx, art, out.instruction or body.message, bg)
        action["artifact_ids"] = [str(art.id)]
    elif out.action == "build_context":
        bg.add_task(_in_background, task_context, p.id)
    elif out.action == "propose_generation" and art:
        action["script_artifact_id"] = str(art.id)  # UI shows a confirm button; nothing runs yet
    reply = ChatMessage(
        workspace_id=ctx.ws_id,
        project_id=p.id,
        artifact_id=art.id if art else None,
        role="assistant",
        content=out.reply,
        action=action,
    )
    db.add(reply)
    db.commit()
    return [user_msg, reply]


# ---------- media generation (Kaggle) ----------


@router.post("/projects/{project_id}/generate", response_model=JobOut, status_code=202)
def generate(project_id: uuid.UUID, body: GenerateIn, ctx: Marketing):
    """Explicit 'Generate ảnh & video' on the selected script only (BRD: never auto-generate)."""
    p = _project(ctx, project_id)
    art = _artifact(ctx, body.script_artifact_id)
    if art.project_id != p.id or art.kind != "script" or art.status != "selected":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Hãy chọn một kịch bản (Dùng kịch bản này) trước khi tạo ảnh/video",
        )
    version = ctx.db.get(ArtifactVersion, art.current_version_id)
    job = media.create_studio_job(
        ctx.db, p, version, ctx.user.id, body.extra_instruction, body.disable_style
    )
    ctx.audit("media.generate", "media_job", job.id, script_version=str(version.id))
    ctx.db.commit()
    return job


@router.post("/projects/{project_id}/shorts", response_model=JobOut, status_code=202)
def make_shorts(project_id: uuid.UUID, body: ShortsIn, ctx: Marketing):
    p = _project(ctx, project_id)
    if body.source_artifact_id:
        art = _artifact(ctx, body.source_artifact_id)
        v = ctx.db.get(ArtifactVersion, art.current_version_id) if art.current_version_id else None
        obj = ctx.db.get(StorageObject, v.storage_object_id) if v and v.storage_object_id else None
    elif body.source_input_id:
        inp = ctx.get(ProjectInput, body.source_input_id)
        if not inp.usage_confirmed:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Cần xác nhận quyền sử dụng video trước khi cắt Shorts"
            )
        obj = ctx.db.get(StorageObject, inp.storage_object_id)
    else:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Chọn video nguồn")
    if (
        obj is None
        or obj.project_id != p.id
        or not obj.mime_type.startswith("video/")
        or obj.status != "ready"
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "Hãy chọn một video đã tạo xong trong dự án")
    job = media.create_shorts_job(ctx.db, p, obj, ctx.user.id, body.target_count, cta=body.cta)
    ctx.audit("media.shorts", "media_job", job.id, source=str(obj.id))
    ctx.db.commit()
    return job


@router.get("/projects/{project_id}/jobs", response_model=list[JobOut])
def list_jobs(project_id: uuid.UUID, ctx: AnyMember):
    p = _project(ctx, project_id)
    return ctx.db.scalars(
        select(MediaJob).where(MediaJob.project_id == p.id).order_by(MediaJob.created_at.desc())
    ).all()


@router.post("/media-jobs/{job_id}/cancel", response_model=JobOut)
def cancel_job(job_id: uuid.UUID, ctx: Marketing):
    job = ctx.get(MediaJob, job_id)
    if job.status not in ("queued", "running"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Việc này đã xong hoặc đã dừng")
    media.fail(ctx.db, job, "Người dùng đã huỷ", retryable=False)
    job.status = "cancelled"
    ctx.db.commit()
    return job


@router.get("/storage/usage")
def storage_usage(ctx: AnyMember):
    rows = ctx.db.execute(
        select(StorageObject.project_id, StorageObject.category, func.sum(StorageObject.byte_size))
        .where(StorageObject.workspace_id == ctx.ws_id, StorageObject.status == "ready")
        .group_by(StorageObject.project_id, StorageObject.category)
    ).all()
    total = sum(r[2] for r in rows)
    quota = get_settings().storage_quota_mb * 1024 * 1024
    by_category: dict[str, int] = {}
    by_project: dict[str, int] = {}
    for pid, cat, n in rows:
        by_category[cat] = by_category.get(cat, 0) + n
        by_project[str(pid)] = by_project.get(str(pid), 0) + n
    return {
        "used_bytes": total,
        "quota_bytes": quota,
        "by_category": by_category,
        "by_project": by_project,
    }
