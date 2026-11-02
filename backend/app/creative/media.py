"""Media job lifecycle between the Control Plane and the Kaggle GPU notebooks (system design §2).

Notebook 1 (kind=studio): FLUX.2 studio image + thumbnail -> MiniMax H3 video+SFX -> ACE-Step BGM
-> FFmpeg mix at 25%. Notebook 2 (kind=shorts): WhisperX -> Gemini viral cut -> YOLOv8-face 9:16
crop + karaoke subtitles. Notebooks poll /worker/jobs/claim and upload straight to R2 with the
presigned PUT URLs handed out here, so they never hold storage credentials.
"""

import logging
import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.agents import VIDEO_SHOTS, brand_facts
from app.core import storage
from app.core.config import get_settings
from app.core.db import utcnow
from app.creative.composer import compose, resolve_style
from app.models import (
    Artifact,
    ArtifactVersion,
    MediaJob,
    Project,
    ProjectInput,
    Service,
    StorageObject,
)

MAX_SHOTS = VIDEO_SHOTS
NO_TEXT = " No text, letters, logos or watermarks anywhere in the frame."
MAX_SHORTS = 5
MIME = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "mp4": "video/mp4",
    "wav": "audio/wav",
    "ass": "text/plain",
}
CATEGORY = {
    "image/png": "image",
    "image/jpeg": "image",
    "video/mp4": "video",
    "audio/wav": "audio",
    "text/plain": "subtitle",
}

log = logging.getLogger("growthpilot.media")


def _key(job: MediaJob, name: str) -> str:
    return f"ws/{job.workspace_id}/projects/{job.project_id}/jobs/{job.id}/{name}"


def _new_artifact(db: Session, project: Project, kind: str, name: str) -> Artifact:
    a = Artifact(
        workspace_id=project.workspace_id,
        project_id=project.id,
        kind=kind,
        display_name=name[:200],
        status="generating",
        updated_at=utcnow(),
    )
    db.add(a)
    db.flush()
    return a


def _references(db: Session, project: Project, roles: tuple[str, ...]) -> list[dict]:
    rows = db.execute(
        select(ProjectInput, StorageObject)
        .join(StorageObject, StorageObject.id == ProjectInput.storage_object_id)
        .where(
            ProjectInput.project_id == project.id,
            ProjectInput.role.in_(roles),
            StorageObject.status == "ready",
            StorageObject.mime_type.like("image/%"),
        )
        .order_by(ProjectInput.created_at)
    ).all()
    return [
        {"role": i.role, "title": i.title or o.filename, "preserve": i.preserve, "key": o.key}
        for i, o in rows
    ]


def _continuity(script: dict) -> str:
    """The script's fixed product, person and room, appended to every shot so each separately
    generated frame shows the same ones (scripts written before this have none)."""
    c = script.get("continuity") or {}
    parts = [
        f"{label}: {c[k].strip()}"
        for k, label in (("product", "Product"), ("talent", "Person"), ("setting", "Setting"))
        if c.get(k, "").strip()
    ]
    if not parts:
        return ""
    # A keyframe edited from a master where the product is in hand showed it worn and held at once.
    one = " Exactly one of this product in the frame." if c.get("product", "").strip() else ""
    return " Same in every shot. " + "; ".join(parts) + "." + one


def create_studio_job(
    db: Session,
    project: Project,
    script_version: ArtifactVersion,
    user_id: uuid.UUID | None,
    extra_instruction: str = "",
    disable_style: bool = False,
) -> MediaJob:
    script = script_version.content
    refs = _references(db, project, ("product", "facility", "logo", "staff"))
    styles = {
        m: resolve_style(db, project.workspace_id, project.id, m)
        for m in ("image", "video", "audio")
    }
    # No brand facts in any picture prompt: the models painted the spa name onto the set and
    # misspelled it. The thumbnail headline is drawn by the notebook in a real Vietnamese font.
    common = {"extra_instruction": extra_instruction, "disable_style": disable_style}
    shots = script["shots"][:MAX_SHOTS]
    first = shots[0]
    same = _continuity(script)

    master = compose(
        modality="image",
        task="Photoreal studio advertising key visual, vertical 9:16, product kept identical to the "
        f"reference photo with the background re-staged.{NO_TEXT}",
        subject=first["visual_prompt"] + same,
        references=[{k: r[k] for k in ("role", "title", "preserve")} for r in refs],
        style=styles["image"],
        **common,
    )
    thumbnail = compose(
        modality="image",
        task="Vertical 9:16 Facebook thumbnail/banner. Keep the upper third a calm, plain background "
        f"for a headline that is added afterwards.{NO_TEXT}",
        subject=first["visual_prompt"] + same,
        references=[{k: r[k] for k in ("role", "title", "preserve")} for r in refs],
        style=styles["image"],
        **common,
    )
    # Each shot after the first starts from its own FLUX frame: animating the key visual into a
    # different scene made H3 morph it (a face mask landed on a skin close-up of shot 1). The
    # notebook passes the studio master as the reference image, so person, product and room carry.
    keyframes = [
        compose(
            modality="image",
            task="Photoreal first frame of the next shot of the same vertical 9:16 spa video ad. "
            "Same person, room and product design as the reference image, but the product is only "
            f"where this shot puts it; new camera framing and action.{NO_TEXT}",
            subject=s["visual_prompt"] + same,
            references=[{k: r[k] for k in ("role", "title", "preserve")} for r in refs],
            style=styles["image"],
            **common,
        )
        for s in shots[1:]
    ]
    clips = [
        compose(
            modality="video",
            task=f"Image-to-video with synchronized audio (SFX, ambience, voice if any), 9:16.{NO_TEXT}",
            # English only: the Vietnamese description adds nothing the video model can read.
            subject=f"{s['visual_prompt']}. Motion: {s['motion'] or 'slow push-in'}. "
            f"Sound: {s['sfx'] or 'soft spa ambience'}.{same}",
            style=styles["video"],
            **common,
        )
        for s in shots
    ]
    duration = int(min(60, max(10, sum(s["duration_seconds"] for s in shots) + 2)))
    bgm = compose(
        modality="audio",
        task=f"{duration}s background music bed for a spa advertisement, loopable ending.",
        subject=script.get("music_mood") or "calm spa ambient",
        style=styles["audio"],
        **common,
    )

    job = MediaJob(
        workspace_id=project.workspace_id, project_id=project.id, kind="studio", created_by=user_id
    )
    db.add(job)
    db.flush()
    title = script["title"]
    arts = {
        "studio_master": _new_artifact(db, project, "image", f"Ảnh studio — {title}"),
        "thumbnail": _new_artifact(db, project, "image", f"Thumbnail — {title}"),
        "final_video": _new_artifact(db, project, "video", f"Video quảng cáo — {title}"),
    }
    job.output_keys = {
        "studio_master": _key(job, "studio_master.png"),
        "thumbnail": _key(job, "thumbnail.png"),
        "bgm": _key(job, "bgm_track.wav"),
        "final_video": _key(job, "final_commercial.mp4"),
    }
    job.artifact_ids = {name: str(a.id) for name, a in arts.items()}  # type: ignore[assignment]
    job.payload = {
        "script_version_id": str(script_version.id),
        "aspect_ratio": "9:16",
        "references": refs,
        "studio_master": {"prompt": master.prompt, "model": master.model},
        "thumbnail": {
            "prompt": thumbnail.prompt,
            "model": thumbnail.model,
            "headline": script["hook"],
        },
        "shots": [
            {
                "prompt": c.prompt,
                "negative_prompt": c.negative_prompt,
                "duration_seconds": s["duration_seconds"],
                "model": c.model,
                # None for the first shot: it starts from the studio master
                "keyframe": {"prompt": k.prompt, "model": k.model} if k else None,
            }
            for c, s, k in zip(clips, shots, [None, *keyframes], strict=True)
        ],
        "bgm": {"prompt": bgm.prompt, "duration_seconds": duration, "model": bgm.model},
        "mix": {"bgm_volume": 0.25},
    }
    job.prompt_snapshot = {
        "styles": {m: {k: v for k, v in vars(st).items()} for m, st in styles.items()},
        "studio_master": master.to_dict(),
        "thumbnail": thumbnail.to_dict(),
        "shots": [c.to_dict() for c in clips],
        "keyframes": [k.to_dict() for k in keyframes],
        "bgm": bgm.to_dict(),
        "user_instruction": extra_instruction,
        "created_at": utcnow().isoformat(),
    }
    return job


def create_shorts_job(
    db: Session,
    project: Project,
    source: StorageObject,
    user_id: uuid.UUID | None,
    target_count: int = 3,
    min_seconds: int = 15,
    max_seconds: int = 30,
    cta: str = "",
) -> MediaJob:
    service = db.get(Service, project.service_id) if project.service_id else None
    job = MediaJob(
        workspace_id=project.workspace_id, project_id=project.id, kind="shorts", created_by=user_id
    )
    db.add(job)
    db.flush()
    job.output_keys = {
        **{f"short_{i}": _key(job, f"short_{i}.mp4") for i in range(1, MAX_SHORTS + 1)},
        **{f"cover_{i}": _key(job, f"cover_{i}.jpg") for i in range(1, MAX_SHORTS + 1)},
        **{f"subtitle_{i}": _key(job, f"short_{i}.ass") for i in range(1, MAX_SHORTS + 1)},
    }
    job.payload = {
        "source_key": source.key,
        "language": "vi",
        "target_count": min(target_count, MAX_SHORTS),
        "min_seconds": min_seconds,
        "max_seconds": max_seconds,
        "output_size": [1080, 1920],
        "brand_context": {
            "project": project.name,
            "service": service.name if service else "",
            "audience": project.audience,
            "cta": cta,
            "facts": brand_facts(db, project),
        },
    }
    job.prompt_snapshot = {
        "selector_model": get_settings().gemini_model,
        "created_at": utcnow().isoformat(),
    }
    return job


def presigned_payload(job: MediaJob) -> dict:
    """What the notebook receives on claim: fresh GET/PUT URLs, never storage credentials."""
    payload = dict(job.payload)
    if job.kind == "studio":
        payload["references"] = [
            {**r, "url": storage.presign_get(r["key"])} for r in payload.get("references", [])
        ]
    else:
        payload["source_url"] = storage.presign_get(payload["source_key"])
    uploads = {}
    for name, key in job.output_keys.items():
        mime = MIME[key.rsplit(".", 1)[1]]
        uploads[name] = {"key": key, "content_type": mime, "url": storage.presign_put(key, mime)}
    return {
        "id": str(job.id),
        "kind": job.kind,
        "attempt": job.attempts,
        "payload": payload,
        "uploads": uploads,
    }


def claim(db: Session, worker_id: str, kinds: list[str]) -> MediaJob | None:
    stmt = (
        select(MediaJob)
        .where(MediaJob.status == "queued", MediaJob.kind.in_(kinds))
        .order_by(MediaJob.created_at)
        .limit(1)
    )
    if db.get_bind().dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)
    job = db.scalar(stmt)
    if job is None:
        return None
    job.status, job.worker_id, job.stage, job.progress = "running", worker_id, "claimed", 0.0
    job.attempts += 1
    job.heartbeat_at = utcnow()
    return job


def _store(db: Session, job: MediaJob, name: str) -> StorageObject | None:
    key = job.output_keys[name]
    size = storage.size_of(key)
    if size is None:
        return None
    mime = MIME[key.rsplit(".", 1)[1]]
    obj = StorageObject(
        workspace_id=job.workspace_id,
        project_id=job.project_id,
        key=key,
        filename=key.rsplit("/", 1)[1],
        mime_type=mime,
        byte_size=size,
        category=CATEGORY[mime],
        status="ready",
    )
    db.add(obj)
    db.flush()
    return obj


def _add_version(
    db: Session, art: Artifact, obj: StorageObject, job: MediaJob, content: dict
) -> None:
    last = db.scalar(
        select(ArtifactVersion.version_number)
        .where(ArtifactVersion.artifact_id == art.id)
        .order_by(ArtifactVersion.version_number.desc())
        .limit(1)
    )
    v = ArtifactVersion(
        workspace_id=art.workspace_id,
        artifact_id=art.id,
        version_number=(last or 0) + 1,
        content=content,
        storage_object_id=obj.id,
        actor="worker",
        provider="kaggle",
        model=content.get("model"),
        media_job_id=job.id,
    )
    db.add(v)
    db.flush()
    art.current_version_id, art.status, art.updated_at = v.id, "ready", utcnow()


def complete(db: Session, job: MediaJob, outputs: dict) -> list[str]:
    """outputs: name -> metadata dict reported by the notebook. Returns names missing in storage."""
    missing = []
    project = db.get(Project, job.project_id)
    if job.kind == "studio":
        for name, art_id in job.artifact_ids.items():  # type: ignore[union-attr]
            art = db.get(Artifact, uuid.UUID(art_id))
            obj = _store(db, job, name) if name in outputs else None
            if obj is None:
                missing.append(name)
                art.status, art.error = "failed", "Notebook không trả về tệp này"
                continue
            snap = job.prompt_snapshot.get(name) or {}
            model = snap.get("model") or "minimax-h3+ace-step-1.5+ffmpeg"
            _add_version(
                db,
                art,
                obj,
                job,
                {
                    **outputs[name],
                    "model": model,
                    "script_version_id": job.payload["script_version_id"],
                },
            )
        if "bgm" in outputs:
            _store(db, job, "bgm")
    else:
        for i in range(1, MAX_SHORTS + 1):
            name = f"short_{i}"
            if name not in outputs:
                continue
            obj = _store(db, job, name)
            if obj is None:
                missing.append(name)
                continue
            meta = outputs[name]
            art = _new_artifact(
                db, project, "short", f"Short {i} — {meta.get('title') or project.name}"
            )
            cover = _store(db, job, f"cover_{i}") if f"cover_{i}" in outputs else None
            sub = _store(db, job, f"subtitle_{i}") if f"subtitle_{i}" in outputs else None
            _add_version(
                db,
                art,
                obj,
                job,
                {
                    **meta,
                    "cover_object_id": str(cover.id) if cover else None,
                    "subtitle_object_id": str(sub.id) if sub else None,
                    "model": "whisperx+gemini+yolov8-face",
                },
            )
            job.artifact_ids = [*(job.artifact_ids or []), str(art.id)]  # type: ignore[list-item]
    job.status = "succeeded" if not missing else "failed"
    job.error = f"Thiếu tệp đầu ra: {', '.join(missing)}" if missing else None
    job.progress, job.stage, job.finished_at = 1.0, "done", utcnow()
    job.result = outputs
    return missing


def fail(db: Session, job: MediaJob, error: str, retryable: bool) -> None:
    if retryable and job.attempts < 3:
        job.status, job.stage, job.error = "queued", "retry", error[:2000]
        return
    job.status, job.error, job.finished_at = "failed", error[:2000], utcnow()
    ids = job.artifact_ids.values() if isinstance(job.artifact_ids, dict) else []
    for art_id in ids:
        art = db.get(Artifact, uuid.UUID(art_id))
        if art and art.status == "generating":
            art.status, art.error = "failed", error[:500]


def wake_worker(kind: str) -> None:
    """Start the Modal worker for this job kind unless one is already running or starting."""
    app = get_settings().modal_app
    if not app:
        return
    try:
        import modal

        fn = modal.Function.from_name(app, kind)
        stats = fn.get_current_stats()
        if stats.num_total_runners == 0 and stats.backlog == 0:
            fn.spawn()
    except Exception as e:  # noqa: BLE001 — Kaggle stays a manual fallback; never fail the request
        log.warning("could not start the %s worker on Modal: %s", kind, type(e).__name__)


def requeue_stale(db: Session) -> int:
    """Kaggle sessions die (12h limit, quota) and Modal containers time out: give abandoned jobs back."""
    cutoff = utcnow() - timedelta(minutes=get_settings().media_job_stale_minutes)
    stale = db.scalars(
        select(MediaJob).where(MediaJob.status == "running", MediaJob.heartbeat_at < cutoff)
    ).all()
    for job in stale:
        fail(db, job, "Worker mất kết nối (hết phiên Kaggle?)", retryable=True)
    return len(stale)
