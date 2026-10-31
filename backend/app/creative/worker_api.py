"""API the Kaggle notebooks call (over Cloudflare Tunnel). Auth: Bearer MEDIA_WORKER_TOKEN."""

import hmac
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.db import utcnow
from app.core.deps import DB
from app.creative import media
from app.models import MediaJob

router = APIRouter(prefix="/worker", tags=["media-worker"])


def worker_auth(authorization: Annotated[str | None, Header()] = None) -> None:
    token = get_settings().media_worker_token
    given = (authorization or "").removeprefix("Bearer ")
    if not token or not hmac.compare_digest(token, given):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid worker token")


Worker = Annotated[None, Depends(worker_auth)]


class ClaimIn(BaseModel):
    worker_id: str = Field(min_length=1, max_length=100)
    kinds: list[str] = Field(min_length=1)


class ProgressIn(BaseModel):
    stage: str = Field(max_length=48)
    progress: float = Field(ge=0, le=1)


class CompleteIn(BaseModel):
    outputs: dict[str, dict]  # output name (from uploads) -> metadata (duration, timecodes, title…)


class FailIn(BaseModel):
    error: str = Field(max_length=4000)
    retryable: bool = False


def _running(db, job_id: uuid.UUID) -> MediaJob:
    job = db.get(MediaJob, job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "job not found")
    return job


@router.post("/jobs/claim")
def claim(body: ClaimIn, db: DB, _: Worker):
    job = media.claim(db, body.worker_id, body.kinds)
    if job is None:
        db.commit()
        return {"job": None}
    out = media.presigned_payload(job)
    db.commit()
    return {"job": out}


@router.post("/jobs/{job_id}/progress")
def progress(job_id: uuid.UUID, body: ProgressIn, db: DB, _: Worker):
    """Heartbeat. Returns cancel=true when the user cancelled so the notebook can stop early."""
    job = _running(db, job_id)
    if job.status != "running":
        return {"cancel": True}
    job.stage, job.progress, job.heartbeat_at = body.stage, body.progress, utcnow()
    db.commit()
    return {"cancel": False}


@router.post("/jobs/{job_id}/complete")
def complete(job_id: uuid.UUID, body: CompleteIn, db: DB, _: Worker):
    job = _running(db, job_id)
    if job.status != "running":
        raise HTTPException(status.HTTP_409_CONFLICT, f"job is {job.status}")
    unknown = set(body.outputs) - set(job.output_keys)
    if unknown:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"unknown outputs: {sorted(unknown)}"
        )
    missing = media.complete(db, job, body.outputs)
    db.commit()
    return {"status": job.status, "missing": missing}


@router.post("/jobs/{job_id}/fail")
def fail(job_id: uuid.UUID, body: FailIn, db: DB, _: Worker):
    job = _running(db, job_id)
    if job.status == "running":
        media.fail(db, job, body.error, body.retryable)
        db.commit()
    return {"status": job.status}
