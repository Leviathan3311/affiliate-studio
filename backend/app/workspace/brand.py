"""Brand & Service Profile (MOD-02): the only source of truth the AI may quote."""

import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.deps import AnyMember, Marketing
from app.models import Branch, Brand, KnowledgeDocument, Service

router = APIRouter(tags=["brand"])


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BrandIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    industry: str = Field(default="", max_length=100)
    tone_of_voice: str = Field(default="", max_length=2000)
    hotline: str = Field(default="", max_length=32)
    address: str = Field(default="", max_length=1000)
    opening_hours: str = Field(default="", max_length=200)
    description: str = Field(default="", max_length=4000)
    forbidden_claims: str = Field(default="", max_length=2000)


class BrandOut(BrandIn, ORM):
    pass


class BranchIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str = Field(default="", max_length=1000)
    capacity: int | None = Field(default=None, ge=1, le=500)


class ServiceIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    duration_minutes: int = Field(default=60, ge=5, le=600)
    price_min: int | None = Field(default=None, ge=0)
    price_max: int | None = Field(default=None, ge=0)
    promotion: str = Field(default="", max_length=1000)
    active: bool = True

    @model_validator(mode="after")
    def price_range(self):
        if self.price_min and self.price_max and self.price_max < self.price_min:
            raise ValueError("price_max phải ≥ price_min")
        return self


class KnowledgeIn(BaseModel):
    kind: Literal["faq", "policy"] = "faq"
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1, max_length=8000)


@router.get("/brand", response_model=BrandOut)
def get_brand(ctx: AnyMember):
    return ctx.db.scalar(select(Brand).where(Brand.workspace_id == ctx.ws_id))


@router.put("/brand", response_model=BrandOut)
def put_brand(body: BrandIn, ctx: Marketing):
    brand = ctx.db.scalar(select(Brand).where(Brand.workspace_id == ctx.ws_id))
    for k, v in body.model_dump().items():
        setattr(brand, k, v)
    ctx.audit("brand.updated", "brand", brand.id)
    ctx.db.commit()
    return brand


def _crud(path: str, model, schema: type[BaseModel], order_by) -> None:
    """List/create/replace/delete for a simple workspace-scoped table."""
    out = create_model(f"{model.__name__}Out", __base__=(schema, ORM), id=(uuid.UUID, ...))
    name = model.__tablename__

    @router.get(f"/{path}", response_model=list[out], name=f"list_{name}")
    def list_(ctx: AnyMember):
        return ctx.db.scalars(
            select(model).where(model.workspace_id == ctx.ws_id).order_by(order_by)
        ).all()

    @router.post(f"/{path}", response_model=out, status_code=201, name=f"create_{name}")
    def create(body: schema, ctx: Marketing):  # type: ignore[valid-type]
        obj = model(workspace_id=ctx.ws_id, **body.model_dump())
        ctx.db.add(obj)
        ctx.db.flush()
        ctx.audit(f"{name}.created", name, obj.id)
        ctx.db.commit()
        return obj

    @router.put(f"/{path}/{{obj_id}}", response_model=out, name=f"update_{name}")
    def update(obj_id: uuid.UUID, body: schema, ctx: Marketing):  # type: ignore[valid-type]
        obj = ctx.get(model, obj_id)
        for k, v in body.model_dump().items():
            setattr(obj, k, v)
        ctx.audit(f"{name}.updated", name, obj.id)
        ctx.db.commit()
        return obj

    @router.delete(f"/{path}/{{obj_id}}", status_code=204, name=f"delete_{name}")
    def delete(obj_id: uuid.UUID, ctx: Marketing):
        ctx.db.delete(ctx.get(model, obj_id))
        ctx.audit(f"{name}.deleted", name, obj_id)
        try:
            ctx.db.commit()
        except IntegrityError:
            raise HTTPException(409, "Đang có lịch hẹn dùng mục này; hãy tắt thay vì xoá") from None


_crud("branches", Branch, BranchIn, Branch.created_at)
_crud("services", Service, ServiceIn, Service.name)
_crud("knowledge", KnowledgeDocument, KnowledgeIn, KnowledgeDocument.created_at)
