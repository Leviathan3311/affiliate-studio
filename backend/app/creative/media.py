"""Media job lifecycle between the Control Plane and the Kaggle GPU notebooks (system design §2).

Notebook 1 (kind=studio): FLUX.2 studio image + thumbnail -> MiniMax H3 video+SFX -> ACE-Step BGM
-> FFmpeg mix at 25%. Notebook 2 (kind=shorts): WhisperX -> Gemini viral cut -> YOLOv8-face 9:16
crop + karaoke subtitles. Notebooks poll /worker/jobs/claim and upload straight to R2 with the
presigned PUT URLs handed out here, so they never hold storage credentials.
"""

import logging
import re
import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import speech
from app.ai.agents import FRAMINGS, VIDEO_SHOTS, brand_facts
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
# H3 wrote a garbled end card ("wi chrến hện") over a final "reveal" shot with a "brand jingle"
NO_TEXT_VIDEO = NO_TEXT + " No captions, subtitles, title cards or end card ever appear."
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


ORIGIN = re.compile(
    r"vietnam|việt|asian|chinese|korean|japanese|thai|western|european|caucasian|african|indian|latin",
    re.IGNORECASE,
)


def _continuity(script: dict, with_product: bool = True) -> str:
    """The script's fixed product, person and room, appended to every shot so each separately
    generated frame shows the same ones (scripts written before this have none)."""
    c = script.get("continuity") or {}
    # "when shown": forcing the product into every frame put the mask on a woman who was only
    # looking in a mirror, and turned the mirror into a second mask.
    labels = (
        ("product", "Product (only where this shot shows it)"),
        ("talent", "Person"),
        ("setting", "Setting"),
    )
    c = dict(c)
    talent = c.get("talent", "").strip()
    # Viewers are Vietnamese: a person described without one came out Western ("a shop owner").
    if talent and not ORIGIN.search(talent):
        c["talent"] = f"Vietnamese {talent[:1].lower()}{talent[1:]}"
    parts = [
        f"{label}: {c[k].strip()}"
        for k, label in labels
        if c.get(k, "").strip() and (with_product or k != "product")
    ]
    if not parts:
        return ""
    # A keyframe edited from a master where the product is in hand showed it worn and held at once.
    one = (
        " Never more than one of this product in the frame." if c.get("product", "").strip() else ""
    )
    if not with_product:
        one = " The product is not in this shot; hands hold only what the shot describes."
    # The motif usually is the product's own light ("the mask's teal glow"): in a shot without the
    # product it painted the mask onto the face of a woman who was only looking in a mirror.
    motif = (
        f" Recurring motif: {c['motif'].strip()}."
        if with_product and c.get("motif", "").strip()
        else ""
    )
    return " Same in every shot. " + "; ".join(parts) + "." + one + motif


def _camera(shot: dict) -> str:
    return f"Camera: {FRAMINGS.get(shot.get('framing', ''), 'Medium shot')}. "


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
    # No brand facts in any picture prompt: the models painted the brand name onto the set and
    # misspelled it. The thumbnail headline is drawn by the notebook in a real Vietnamese font.
    common = {"extra_instruction": extra_instruction, "disable_style": disable_style}
    shots = script["shots"][:MAX_SHOTS]
    first = shots[0]
    same = _continuity(script)
    # The key visual is a product hero of its own, not shot 1: an opening shot about the problem
    # (no product yet) was drawn with the product forced in. Every shot gets its own first frame.
    c = script.get("continuity") or {}
    hero = (
        f"Camera: Medium shot. {c['talent']} holds {c['product']} at chest height and looks at it "
        f"with a soft smile, in {c.get('setting') or 'a bright, tidy shop interior'}."
        if c.get("product") and c.get("talent")
        else _camera(first) + first["visual_prompt"]
    )

    master = compose(
        modality="image",
        task="Photoreal studio advertising key visual, vertical 9:16, product kept identical to the "
        f"reference photo with the background re-staged.{NO_TEXT}",
        subject=hero + same,
        references=[{k: r[k] for k in ("role", "title", "preserve")} for r in refs],
        style=styles["image"],
        **common,
    )
    thumbnail = compose(
        modality="image",
        task="Vertical 9:16 Facebook thumbnail/banner. Keep the upper third a calm, plain background "
        f"for a headline that is added afterwards.{NO_TEXT}",
        subject=hero + same,
        references=[{k: r[k] for k in ("role", "title", "preserve")} for r in refs],
        style=styles["image"],
        **common,
    )
    # Shots without the product start from a plate: the master with the product edited out, so
    # the same woman and room carry without FLUX keeping the mask from the reference (a hand
    # mirror came out as a second mask).
    plate = None
    if any(not s.get("shows_product", True) for s in shots):
        plate = compose(
            modality="image",
            task="Edit the reference image: remove the product completely, her hands rest empty in "
            "her lap; keep the same person, pose, clothes, light and room unchanged." + NO_TEXT,
            subject=_continuity(script, with_product=False).strip(),
            style=styles["image"],
            **common,
        )
    # Each shot starts from its own FLUX frame: animating the key visual into a different scene
    # made H3 morph it (a face mask landed on a skin close-up of shot 1). The notebook passes the
    # studio master as the reference image, so person, product and room carry.
    keyframes = [
        compose(
            modality="image",
            task="Photoreal first frame of one shot of the same vertical 9:16 video ad. "
            "Same person, room and product design as the reference image, but the product is only "
            f"where this shot puts it; new camera framing and action.{NO_TEXT}",
            subject=_camera(s)
            + s["visual_prompt"]
            + _continuity(script, s.get("shows_product", True)),
            references=[{k: r[k] for k in ("role", "title", "preserve")} for r in refs],
            style=styles["image"],
            **common,
        )
        for s in shots
    ]
    clips = [
        compose(
            modality="video",
            task=f"Image-to-video with synchronized audio (SFX, ambience, voice if any), 9:16.{NO_TEXT_VIDEO}",
            # English only: the Vietnamese description adds nothing the video model can read.
            subject=f"{_camera(s)}{s['visual_prompt']}. Motion: {s['motion'] or 'slow push-in'}. "
            f"Sound: {s['sfx'] or 'soft room ambience'}."
            f"{_continuity(script, s.get('shows_product', True))}",
            style=styles["video"],
            **common,
        )
        for s in shots
    ]
    duration = int(min(60, max(10, sum(s["duration_seconds"] for s in shots) + 2)))
    bgm = compose(
        modality="audio",
        task=f"{duration}s background music bed for an advertisement, loopable ending.",
        subject=script.get("music_mood") or "warm, light ambient",
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
    # A Short per benefit, cut from the same finished shots: opening + that shot + call to action
    shorts = [[0, m, len(shots) - 1] for m in range(1, len(shots) - 1)] if len(shots) >= 4 else []
    for k, plan in enumerate(shorts, 1):
        label = shots[plan[1]].get("on_screen_text") or f"cảnh {plan[1] + 1}"
        arts[f"short_{k}"] = _new_artifact(db, project, "short", f"Short {k} — {label}")
    job.output_keys = {
        "studio_master": _key(job, "studio_master.png"),
        "thumbnail": _key(job, "thumbnail.png"),
        "bgm": _key(job, "bgm_track.wav"),
        "final_video": _key(job, "final_commercial.mp4"),
        **{f"short_{k}": _key(job, f"short_{k}.mp4") for k in range(1, len(shorts) + 1)},
    }
    job.artifact_ids = {name: str(a.id) for name, a in arts.items()}  # type: ignore[assignment]
    job.payload = {
        "script_version_id": str(script_version.id),
        "aspect_ratio": "9:16",
        "references": refs,
        "studio_master": {"prompt": master.prompt, "model": master.model},
        "plate": {"prompt": plate.prompt, "model": plate.model} if plate else None,
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
                "on_screen_text": s.get("on_screen_text", ""),
                "highlight": s.get("highlight", ""),
                "stat": s.get("stat", ""),
                "transition": s.get("transition", "cut"),
                "voiceover": s.get("voiceover", ""),
                "model": c.model,
                "keyframe": {
                    "prompt": k.prompt,
                    "model": k.model,
                    "base": "master" if s.get("shows_product", True) else "plate",
                },
            }
            for c, s, k in zip(clips, shots, keyframes, strict=True)
        ],
        "bgm": {"prompt": bgm.prompt, "duration_seconds": duration, "model": bgm.model},
        # accent: the highlighted word and the stat cards (champagne gold of the default style)
        "mix": {"bgm_volume": 0.25, "accent": "#E9C77B"},
        "shorts": [{"shots": plan} for plan in shorts],
    }
    if any(s["voiceover"] for s in job.payload["shots"]):
        job.status = "preparing"  # prepare_voiceover() queues it once every line is spoken
        job.payload["mix"]["bgm_volume"] = 0.15  # music sits under the voice
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


def prepare_voiceover(db: Session, job: MediaJob) -> None:
    """Speak each shot's line, store it next to the job's outputs and lengthen a shot whose line
    runs longer than planned, then hand the job to the GPU queue."""
    shots = []
    for i, shot in enumerate(job.payload["shots"]):
        shot = dict(shot)
        if shot.get("voiceover"):
            wav = speech.speak(shot["voiceover"])
            shot["voice_key"] = _key(job, f"voice_{i}.wav")
            storage.put_bytes(shot["voice_key"], wav, "audio/wav")
            spoken = speech.seconds(wav) + 0.8  # starts 0.3 s in, a breath at the end
            shot["duration_seconds"] = min(10, max(shot["duration_seconds"], round(spoken, 1)))
        shots.append(shot)
    total = int(min(60, max(10, sum(s["duration_seconds"] for s in shots) + 2)))
    job.payload = {
        **job.payload,
        "shots": shots,
        "bgm": {**job.payload["bgm"], "duration_seconds": total},
    }
    job.status, job.stage = "queued", ""


def presigned_payload(job: MediaJob) -> dict:
    """What the notebook receives on claim: fresh GET/PUT URLs, never storage credentials."""
    payload = dict(job.payload)
    if job.kind == "studio":
        payload["references"] = [
            {**r, "url": storage.presign_get(r["key"])} for r in payload.get("references", [])
        ]
        payload["shots"] = [
            {**s, "voice_url": storage.presign_get(s["voice_key"])} if s.get("voice_key") else s
            for s in payload["shots"]
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
