"""Style Library (BRD MOD-04 Style Packs): workspace defaults, project override, prompt preview."""

import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_, select

from app.ai.composer import (
    MODALITIES,
    ResolvedStyle,
    compose,
    ensure_presets,
    latest_version,
    normalize_blocks,
    resolve_style,
)
from app.deps import Admin, AnyMember, Marketing
from app.models import Project, StyleAssignment, StylePack, StylePackVersion

router = APIRouter(tags=["styles"])
Modality = Literal["image", "video", "audio"]


class BlockIn(BaseModel):
    id: str | None = None
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(default="other", max_length=40)
    content: str = Field(min_length=1, max_length=1200)
    priority: int = Field(default=50, ge=0, le=100)
    applies_to: list[Modality] = Field(default_factory=lambda: ["image", "video"], min_length=1)
    enabled: bool = True


class PackIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    blocks: list[BlockIn] = Field(min_length=1, max_length=30)
    change_summary: str = Field(default="", max_length=500)


class PackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str
    status: str
    is_preset: bool = False
    version_id: uuid.UUID | None = None
    version_number: int | None = None
    blocks: list[dict] = []
    created_at: datetime


class AssignmentsIn(BaseModel):
    image: uuid.UUID | None = None
    video: uuid.UUID | None = None
    audio: uuid.UUID | None = None


class ProjectStyleIn(BaseModel):
    modality: Modality
    mode: Literal["inherit", "pack", "off"]
    style_pack_id: uuid.UUID | None = None


class PreviewIn(BaseModel):
    modality: Modality = "image"
    brief: str = Field(default="Close-up of a hot stone massage on a guest's back", max_length=1000)
    extra_instruction: str = Field(default="", max_length=500)
    project_id: uuid.UUID | None = None


def _pack_out(db, pack: StylePack) -> PackOut:
    v = latest_version(db, pack.id)
    out = PackOut.model_validate(pack)
    out.is_preset = pack.workspace_id is None
    if v:
        out.version_id, out.version_number, out.blocks = v.id, v.version_number, v.blocks
    return out


def _visible_pack(ctx, pack_id: uuid.UUID) -> StylePack:
    pack = ctx.db.get(StylePack, pack_id)
    if pack is None or pack.workspace_id not in (None, ctx.ws_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Style pack not found")
    return pack


@router.get("/style-packs", response_model=list[PackOut])
def list_packs(ctx: AnyMember):
    ensure_presets(ctx.db)
    ctx.db.commit()
    packs = ctx.db.scalars(
        select(StylePack)
        .where(or_(StylePack.workspace_id == ctx.ws_id, StylePack.workspace_id.is_(None)))
        .where(StylePack.status == "active")
        .order_by(StylePack.workspace_id.is_(None), StylePack.created_at)
    ).all()
    return [_pack_out(ctx.db, p) for p in packs]


@router.post("/style-packs", response_model=PackOut, status_code=201)
def create_pack(body: PackIn, ctx: Admin):
    pack = StylePack(
        workspace_id=ctx.ws_id, name=body.name, description=body.description, created_by=ctx.user.id
    )
    ctx.db.add(pack)
    ctx.db.flush()
    ctx.db.add(
        StylePackVersion(
            style_pack_id=pack.id,
            version_number=1,
            created_by=ctx.user.id,
            change_summary=body.change_summary or "Tạo mới",
            blocks=normalize_blocks([b.model_dump() for b in body.blocks]),
        )
    )
    ctx.audit("style.created", "style_pack", pack.id)
    ctx.db.commit()
    return _pack_out(ctx.db, pack)


@router.post("/style-packs/{pack_id}/duplicate", response_model=PackOut, status_code=201)
def duplicate_pack(pack_id: uuid.UUID, ctx: Admin):
    src = _visible_pack(ctx, pack_id)
    v = latest_version(ctx.db, src.id)
    pack = StylePack(
        workspace_id=ctx.ws_id,
        name=f"{src.name} (bản sao)",
        description=src.description,
        created_by=ctx.user.id,
    )
    ctx.db.add(pack)
    ctx.db.flush()
    ctx.db.add(
        StylePackVersion(
            style_pack_id=pack.id,
            version_number=1,
            created_by=ctx.user.id,
            change_summary=f"Nhân bản từ {src.name}",
            blocks=v.blocks if v else [],
        )
    )
    ctx.audit("style.duplicated", "style_pack", pack.id, source=str(src.id))
    ctx.db.commit()
    return _pack_out(ctx.db, pack)


@router.put("/style-packs/{pack_id}", response_model=PackOut)
def update_pack(pack_id: uuid.UUID, body: PackIn, ctx: Admin):
    """Always a new version: earlier versions stay exactly as used by past generations."""
    pack = _visible_pack(ctx, pack_id)
    if pack.workspace_id is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Preset hệ thống không sửa được; hãy nhân bản"
        )
    last = latest_version(ctx.db, pack.id)
    pack.name, pack.description = body.name, body.description
    ctx.db.add(
        StylePackVersion(
            style_pack_id=pack.id,
            version_number=(last.version_number + 1) if last else 1,
            created_by=ctx.user.id,
            change_summary=body.change_summary,
            blocks=normalize_blocks([b.model_dump() for b in body.blocks]),
        )
    )
    ctx.audit("style.versioned", "style_pack", pack.id, summary=body.change_summary)
    ctx.db.commit()
    return _pack_out(ctx.db, pack)


@router.delete("/style-packs/{pack_id}", status_code=204)
def archive_pack(pack_id: uuid.UUID, ctx: Admin):
    pack = _visible_pack(ctx, pack_id)
    if pack.workspace_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Không lưu trữ được preset hệ thống")
    pack.status = "archived"
    for a in ctx.db.scalars(
        select(StyleAssignment).where(StyleAssignment.style_pack_id == pack.id)
    ):
        ctx.db.delete(a)
    ctx.audit("style.archived", "style_pack", pack.id)
    ctx.db.commit()


def _assignment(db, ws_id, project_key: str, modality: str) -> StyleAssignment | None:
    return db.scalar(
        select(StyleAssignment).where(
            StyleAssignment.workspace_id == ws_id,
            StyleAssignment.project_key == project_key,
            StyleAssignment.modality == modality,
        )
    )


def _effective(db, ws_id, project_id=None) -> dict:
    return {
        m: {k: v for k, v in vars(resolve_style(db, ws_id, project_id, m)).items() if k != "blocks"}
        for m in MODALITIES
    }


@router.get("/style-assignments")
def get_assignments(ctx: AnyMember, project_id: uuid.UUID | None = None):
    if project_id:
        ctx.get(Project, project_id)
    out = _effective(ctx.db, ctx.ws_id, project_id)
    ctx.db.commit()
    return out


@router.put("/style-assignments")
def put_assignments(body: AssignmentsIn, ctx: Admin):
    for m in MODALITIES:
        pack_id = getattr(body, m)
        a = _assignment(ctx.db, ctx.ws_id, "", m)
        if pack_id is None:
            if a:
                ctx.db.delete(a)
            continue
        _visible_pack(ctx, pack_id)
        if a is None:
            ctx.db.add(
                StyleAssignment(
                    workspace_id=ctx.ws_id, project_key="", modality=m, style_pack_id=pack_id
                )
            )
        else:
            a.style_pack_id = pack_id
    ctx.audit(
        "style.defaults_updated",
        "workspace",
        ctx.ws_id,
        **{m: str(getattr(body, m)) for m in MODALITIES},
    )
    ctx.db.commit()
    return _effective(ctx.db, ctx.ws_id)


@router.put("/projects/{project_id}/style")
def put_project_style(project_id: uuid.UUID, body: ProjectStyleIn, ctx: Marketing):
    """Project override; never touches the workspace default."""
    p = ctx.get(Project, project_id)
    a = _assignment(ctx.db, ctx.ws_id, str(p.id), body.modality)
    if body.mode == "inherit":
        if a:
            ctx.db.delete(a)
    else:
        pack_id = body.style_pack_id if body.mode == "pack" else None
        if body.mode == "pack":
            if pack_id is None:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Chọn style pack")
            _visible_pack(ctx, pack_id)
        if a is None:
            ctx.db.add(
                StyleAssignment(
                    workspace_id=ctx.ws_id,
                    project_id=p.id,
                    project_key=str(p.id),
                    modality=body.modality,
                    style_pack_id=pack_id,
                )
            )
        else:
            a.style_pack_id = pack_id
    ctx.audit("style.project_override", "project", p.id, modality=body.modality, mode=body.mode)
    ctx.db.commit()
    return _effective(ctx.db, ctx.ws_id, p.id)


@router.post("/style-packs/{pack_id}/preview")
def preview_pack(pack_id: uuid.UUID, body: PreviewIn, ctx: AnyMember):
    pack = _visible_pack(ctx, pack_id)
    v = latest_version(ctx.db, pack.id)
    style = ResolvedStyle(
        source="preview",
        pack_id=str(pack.id),
        pack_name=pack.name,
        version_id=str(v.id),
        version_number=v.version_number,
        blocks=v.blocks,
    )
    return compose(
        modality=body.modality,
        task="Preview",
        subject=body.brief,
        style=style,
        extra_instruction=body.extra_instruction,
    ).to_dict()


@router.post("/style-preview")
def preview_effective(body: PreviewIn, ctx: AnyMember):
    """'Xem prompt đã ghép' with the style the project/workspace actually resolves to."""
    if body.project_id:
        ctx.get(Project, body.project_id)
    style = resolve_style(ctx.db, ctx.ws_id, body.project_id, body.modality)
    ctx.db.commit()
    return compose(
        modality=body.modality,
        task="Preview",
        subject=body.brief,
        style=style,
        extra_instruction=body.extra_instruction,
    ).to_dict()
