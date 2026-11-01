"""Style resolution + Prompt Composer (BRD MOD-04 Style Packs, §9.3.1).

Deterministic: same inputs + adapter version -> same prompt. Style blocks are declarative text only;
they can never override safety, verified facts or asset-preservation rules (those come first).
"""

import re
import uuid
from dataclasses import asdict, dataclass, field

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import StyleAssignment, StylePack, StylePackVersion

MODALITIES = ("image", "video", "audio")
COMPOSER_VERSION = "1"

# What each Kaggle-hosted model actually accepts (system design §2).
ADAPTERS: dict[str, dict] = {
    "flux2-klein": {
        "modality": "image",
        "version": "1",
        "negative_prompt": False,  # FLUX has no negative prompt input: folded into text
        "reference_image": True,
        "max_chars": 2400,
    },
    "minimax-h3": {
        "modality": "video",
        "version": "1",
        "negative_prompt": True,
        "reference_image": True,
        "max_chars": 1800,
    },
    "ace-step-1.5": {
        "modality": "audio",
        "version": "1",
        "negative_prompt": False,
        "reference_image": False,
        "max_chars": 600,
    },
}
DEFAULT_MODEL = {"image": "flux2-klein", "video": "minimax-h3", "audio": "ace-step-1.5"}

SAFETY = {
    "image": "Commercial spa advertising image. No fake before/after comparison, no medical or "
    "treatment-result claims, no nudity, no fake logos or watermarks, legible text only if requested.",
    "video": "Commercial spa advertising video. No fake before/after, no medical or result claims, "
    "no nudity; natural motion, no morphing faces or hands.",
    "audio": "Instrumental commercial background music, no vocals, no copyrighted melodies.",
}

# Platform presets (workspace_id = NULL). Examples, not a mandated look.
PRESETS = [
    {
        "name": "Luxury Beige Spa",
        "description": "Sang trọng, tĩnh, tông be/ngà/vàng champagne",
        "blocks": [
            {
                "name": "Art direction",
                "category": "art_direction",
                "priority": 100,
                "applies_to": ["image", "video"],
                "content": "Premium, calm, refined luxury spa visual direction, editorial quality.",
            },
            {
                "name": "Palette",
                "category": "color_palette",
                "priority": 90,
                "applies_to": ["image", "video"],
                "content": "Warm beige, ivory and muted champagne gold; avoid oversaturated colors.",
            },
            {
                "name": "Lighting",
                "category": "lighting",
                "priority": 80,
                "applies_to": ["image", "video"],
                "content": "Soft diffused natural light, natural skin tones, controlled highlights.",
            },
            {
                "name": "Composition",
                "category": "composition",
                "priority": 70,
                "applies_to": ["image"],
                "content": "Clean editorial composition with generous negative space for headline text.",
            },
            {
                "name": "Camera",
                "category": "camera_motion",
                "priority": 70,
                "applies_to": ["video"],
                "content": "Slow dolly-in and gentle handheld drift, 24fps cinematic, shallow depth of field.",
            },
            {
                "name": "Materials",
                "category": "materials",
                "priority": 60,
                "applies_to": ["image", "video"],
                "content": "Natural stone, linen towels, light oak wood, fresh orchids, warm water.",
            },
            {
                "name": "Music mood",
                "category": "music",
                "priority": 60,
                "applies_to": ["audio"],
                "content": "ambient, soft piano, warm pads, 70 bpm, relaxing, spa, gentle",
            },
            {
                "name": "Avoid",
                "category": "negative_constraints",
                "priority": 10,
                "applies_to": ["image", "video"],
                "content": "clutter, neon colors, plastic-looking skin, distorted hands, extra fingers, "
                "fake logos, watermarks, text artifacts",
            },
        ],
    },
    {
        "name": "Clinical Clean",
        "description": "Sạch, sáng, chuyên nghiệp kiểu phòng khám da",
        "blocks": [
            {
                "name": "Art direction",
                "category": "art_direction",
                "priority": 100,
                "applies_to": ["image", "video"],
                "content": "Clean, bright, professional skincare clinic aesthetic, trustworthy.",
            },
            {
                "name": "Palette",
                "category": "color_palette",
                "priority": 90,
                "applies_to": ["image", "video"],
                "content": "White, soft mint and pale grey with one accent of the brand color.",
            },
            {
                "name": "Lighting",
                "category": "lighting",
                "priority": 80,
                "applies_to": ["image", "video"],
                "content": "Even high-key softbox lighting.",
            },
            {
                "name": "Music mood",
                "category": "music",
                "priority": 60,
                "applies_to": ["audio"],
                "content": "minimal electronic, light percussion, 95 bpm, modern, clean, optimistic",
            },
            {
                "name": "Avoid",
                "category": "negative_constraints",
                "priority": 10,
                "applies_to": ["image", "video"],
                "content": "medical equipment close-ups, needles, blood, harsh shadows, watermarks",
            },
        ],
    },
]


def ensure_presets(db: Session) -> None:
    def seeded() -> bool:
        return bool(
            db.scalar(select(StylePack.id).where(StylePack.workspace_id.is_(None)).limit(1))
        )

    if seeded():
        return
    if db.get_bind().dialect.name == "postgresql":
        # The settings page asks for packs and assignments at once: without the lock both
        # requests saw no presets and each seeded a copy.
        db.execute(text("SELECT pg_advisory_xact_lock(hashtext('style_presets'))"))
        if seeded():
            return
    for p in PRESETS:
        pack = StylePack(workspace_id=None, name=p["name"], description=p["description"])
        db.add(pack)
        db.flush()
        db.add(
            StylePackVersion(
                style_pack_id=pack.id, version_number=1, blocks=normalize_blocks(p["blocks"])
            )
        )
    db.flush()


def normalize_blocks(blocks: list[dict]) -> list[dict]:
    out = []
    for i, b in enumerate(blocks):
        out.append(
            {
                "id": b.get("id") or uuid.uuid4().hex[:12],
                "name": b["name"].strip(),
                "category": b.get("category", "other"),
                "content": b["content"].strip(),
                "priority": int(b.get("priority", 50)),
                "applies_to": sorted(
                    set(b.get("applies_to") or ["image", "video"]) & set(MODALITIES)
                ),
                "enabled": bool(b.get("enabled", True)),
                "sort_order": i,
            }
        )
    return out


def latest_version(db: Session, pack_id: uuid.UUID) -> StylePackVersion | None:
    return db.scalar(
        select(StylePackVersion)
        .where(StylePackVersion.style_pack_id == pack_id)
        .order_by(StylePackVersion.version_number.desc())
        .limit(1)
    )


@dataclass
class ResolvedStyle:
    source: str  # project | workspace | platform | none
    pack_id: str | None = None
    pack_name: str | None = None
    version_id: str | None = None
    version_number: int | None = None
    blocks: list[dict] = field(default_factory=list)


def resolve_style(
    db: Session, workspace_id: uuid.UUID, project_id: uuid.UUID | None, modality: str
) -> ResolvedStyle:
    """project override -> workspace default -> first platform preset."""
    ensure_presets(db)
    for key, source in ((str(project_id) if project_id else None, "project"), ("", "workspace")):
        if key is None:
            continue
        a = db.scalar(
            select(StyleAssignment).where(
                StyleAssignment.workspace_id == workspace_id,
                StyleAssignment.project_key == key,
                StyleAssignment.modality == modality,
            )
        )
        if a is not None:
            if a.style_pack_id is None:
                return ResolvedStyle(source=source)
            return _resolved(db, db.get(StylePack, a.style_pack_id), source)
    preset = db.scalar(
        select(StylePack)
        .where(StylePack.workspace_id.is_(None))
        .order_by(StylePack.created_at)
        .limit(1)
    )
    return _resolved(db, preset, "platform") if preset else ResolvedStyle(source="none")


def _resolved(db: Session, pack: StylePack, source: str) -> ResolvedStyle:
    v = latest_version(db, pack.id)
    return ResolvedStyle(
        source=source,
        pack_id=str(pack.id),
        pack_name=pack.name,
        version_id=str(v.id) if v else None,
        version_number=v.version_number if v else None,
        blocks=v.blocks if v else [],
    )


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


@dataclass
class Composed:
    model: str
    adapter_version: str
    modality: str
    prompt: str
    negative_prompt: str | None
    applied_blocks: list[dict]
    unsupported: list[str]
    style: dict

    def to_dict(self) -> dict:
        return asdict(self)


def compose(
    *,
    modality: str,
    task: str,
    subject: str,
    brand_facts: list[str] | None = None,
    references: list[dict] | None = None,
    style: ResolvedStyle | None = None,
    extra_instruction: str = "",
    disable_style: bool = False,
    model: str | None = None,
) -> Composed:
    model = model or DEFAULT_MODEL[modality]
    adapter = ADAPTERS[model]
    style = style or ResolvedStyle(source="none")
    blocks = [] if disable_style else style.blocks
    usable = sorted(
        (b for b in blocks if b.get("enabled", True) and modality in b.get("applies_to", [])),
        key=lambda b: (-b["priority"], b.get("sort_order", 0), b["id"]),
    )
    seen, applied = set(), []
    for b in usable:
        if _norm(b["content"]) not in seen:
            seen.add(_norm(b["content"]))
            applied.append(b)
    negatives = [b for b in applied if b["category"] == "negative_constraints"]
    positives = [b for b in applied if b["category"] != "negative_constraints"]

    sections = [SAFETY[modality], f"Task: {task.strip()}", f"Subject: {subject.strip()}"]
    if extra_instruction.strip():
        # A one-off instruction for this run wins over default style (BRD precedence).
        sections.append(f"For this generation specifically: {extra_instruction.strip()}")
    if brand_facts:
        sections.append("Facts to keep exactly as written: " + "; ".join(brand_facts))
    for r in references or []:
        rule = " Keep it unchanged (shape, label, colors)." if r.get("preserve") else ""
        sections.append(f"Reference image ({r['role']}): {r.get('title') or r['role']}.{rule}")
    if positives:
        sections.append("Visual style: " + " ".join(b["content"] for b in positives))

    unsupported = []
    negative_text = ", ".join(b["content"] for b in negatives) or None
    negative_prompt = negative_text
    if negative_text and not adapter["negative_prompt"]:
        sections.append(f"Avoid: {negative_text}")
        negative_prompt = None
        unsupported.append("negative_prompt:approximate")
    if references and not adapter["reference_image"]:
        unsupported.append("reference_image:unsupported")

    prompt = "\n".join(sections)
    if len(prompt) > adapter["max_chars"]:
        prompt = prompt[: adapter["max_chars"]]
        unsupported.append("prompt:truncated")
    return Composed(
        model=model,
        adapter_version=f"{COMPOSER_VERSION}.{adapter['version']}",
        modality=modality,
        prompt=prompt,
        negative_prompt=negative_prompt,
        applied_blocks=[
            {"id": b["id"], "name": b["name"], "category": b["category"]} for b in applied
        ],
        unsupported=unsupported,
        style={k: v for k, v in asdict(style).items() if k != "blocks"},
    )
