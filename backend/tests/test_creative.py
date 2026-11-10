from urllib.parse import urlsplit

import pytest
from sqlalchemy import select

from app.ai import agents
from app.ai.llm import GeminiResult
from app.core.config import get_settings
from app.creative import publishing
from app.creative.composer import ResolvedStyle, compose, normalize_blocks
from app.models import MediaJob, PublishingJob
from tests.conftest import connect_page, signup

SCRIPT = {
    "title": "Thư giãn sau giờ làm",
    "angle": "Giải toả căng thẳng",
    "insight": "Dân văn phòng mỏi vai gáy",
    "hook": "Vai gáy mỏi nhừ sau 8 tiếng?",
    "key_message": "60 phút đá nóng cho cơ thể nhẹ tênh",
    "cta": "Nhắn Page để giữ chỗ",
    "duration_seconds": 18,
    "voiceover": "",
    "music_mood": "soft piano ambient",
    "caption": "Massage đá nóng 650.000đ",
    "hashtags": ["#spa"],
    "continuity": {
        "product": "smooth black basalt stones",
        "talent": "a Vietnamese woman in her thirties, hair in a bun",
        "setting": "",
    },
    "shots": [
        {
            "description": "Đá nóng trên lưng",
            "visual_prompt": "hot basalt stones on a woman's back",
            "motion": "slow push-in",
            "on_screen_text": "Vai gáy mỏi?",
            "sfx": "water",
            "duration_seconds": 5,
        },
        {
            "description": "Phòng spa",
            "visual_prompt": "candle-lit treatment room",
            "motion": "pan right",
            "on_screen_text": "",
            "sfx": "",
            "duration_seconds": 5,
        },
    ],
}


@pytest.fixture
def gemini(monkeypatch):
    """Fake stream-2 model: returns per-purpose canned JSON, records calls."""
    calls = []

    def fake(db, *, system, parts, purpose, workspace_id, deep=False, search=False, timeout=None):
        calls.append(purpose)
        if purpose.startswith("scripts.generate"):
            v2 = {**SCRIPT, "title": "Ưu đãi lần đầu", "caption": "Giảm còn 199k"}
            return GeminiResult(
                {"variants": [SCRIPT, v2, {**SCRIPT, "title": "Cặp đôi"}]}, "gemini-test", []
            )
        if purpose.startswith("research"):
            return GeminiResult(
                {
                    "research_summary": "Khách văn phòng Q3 quan tâm thư giãn cuối tuần",
                    "evidence": [
                        {"claim": "Nhiều spa Q3 quảng cáo đá nóng", "source_index": 0},
                        {"claim": "60% khách thích cuối tuần", "source_index": 7},
                    ],
                    "confidence": "medium",
                },
                "gemini-test",
                [{"index": 0, "url": "https://example.vn/spa-q3", "title": "Spa Q3"}],
            )
        raise AssertionError(purpose)

    monkeypatch.setattr(agents, "gemini_json", fake)
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test")
    monkeypatch.setattr(get_settings(), "media_worker_token", "worker-secret")
    return calls


def put_presigned(client, url: str, data: bytes, mime: str):
    parts = urlsplit(url)
    r = client.put(f"{parts.path}?{parts.query}", content=data, headers={"Content-Type": mime})
    assert r.status_code == 200, r.text


@pytest.fixture
def spa(client):
    h = signup(client)
    svc = client.post(
        "/api/v1/services",
        headers=h,
        json={"name": "Massage đá nóng", "duration_minutes": 90, "price_min": 650000},
    ).json()
    p = client.post(
        "/api/v1/projects",
        headers=h,
        json={"name": "Đá nóng tháng 11", "service_id": svc["id"], "brief": "Đẩy massage đá nóng"},
    ).json()
    return h, p


def test_composer_is_deterministic_and_filters_by_modality():
    blocks = normalize_blocks(
        [
            {
                "name": "Palette",
                "category": "color_palette",
                "content": "Warm beige",
                "priority": 90,
                "applies_to": ["image", "video"],
            },
            {
                "name": "Poster",
                "category": "composition",
                "content": "Negative space for headline",
                "priority": 70,
                "applies_to": ["image"],
            },
            {
                "name": "Dup",
                "category": "lighting",
                "content": "warm   BEIGE",
                "priority": 10,
                "applies_to": ["image"],
            },
            {
                "name": "Avoid",
                "category": "negative_constraints",
                "content": "neon, watermark",
                "priority": 5,
                "applies_to": ["image", "video"],
            },
        ]
    )
    style = ResolvedStyle(
        source="workspace",
        pack_id="p",
        pack_name="Beige",
        version_id="v",
        version_number=2,
        blocks=blocks,
    )
    a = compose(modality="image", task="t", subject="s", style=style)
    assert a == compose(modality="image", task="t", subject="s", style=style)
    assert "Negative space" in a.prompt and a.prompt.lower().count("warm beige") == 1
    assert "Avoid: neon, watermark" in a.prompt and a.negative_prompt is None  # FLUX: folded in
    assert a.unsupported == ["negative_prompt:approximate"]
    v = compose(modality="video", task="t", subject="s", style=style)
    assert "Negative space" not in v.prompt and v.negative_prompt == "neon, watermark"
    off = compose(modality="image", task="t", subject="s", style=style, disable_style=True)
    assert "Warm beige" not in off.prompt and off.applied_blocks == []
    # safety comes first and a style block can never remove it
    assert a.prompt.startswith("Commercial advertising image")


def test_project_to_kaggle_to_published_post(client, db, spa, gemini):
    h, p = spa
    base = f"/api/v1/projects/{p['id']}"

    # upload a product photo through the presigned flow
    pre = client.post(
        f"{base}/inputs/presign",
        headers=h,
        json={"filename": "serum.png", "content_type": "image/png", "byte_size": 4},
    ).json()
    put_presigned(client, pre["upload_url"], b"\x89PNG", "image/png")
    inp = client.post(
        f"{base}/inputs",
        headers=h,
        json={
            "object_id": pre["object_id"],
            "role": "product",
            "preserve": True,
            "usage_confirmed": True,
        },
    ).json()
    assert inp["byte_size"] == 4

    # Kịch bản A/B/C; the one quoting an unknown price is flagged
    arts = client.post(f"{base}/scripts", headers=h, json={"count": 3}).json()
    assert [a["display_name"] for a in arts] == ["Kịch bản A", "Kịch bản B", "Kịch bản C"]
    scripts = client.get(f"{base}/artifacts?kind=script", headers=h).json()
    assert scripts[0]["display_name"] == "Kịch bản A — Thư giãn sau giờ làm"
    assert scripts[1]["current"]["content"]["flags"] == ["unverified_price"]
    assert scripts[0]["current"]["content"]["flags"] == []

    a = scripts[0]
    assert (
        client.post(f"{base}/generate", headers=h, json={"script_artifact_id": a["id"]}).status_code
        == 409
    )
    client.post(f"/api/v1/artifacts/{a['id']}/select", headers=h)
    job = client.post(f"{base}/generate", headers=h, json={"script_artifact_id": a["id"]}).json()
    assert job["status"] == "queued"
    snap = job["prompt_snapshot"]
    assert snap["styles"]["image"]["pack_name"] == "Luxury Beige Spa"  # platform preset default
    assert "Keep it unchanged" in snap["studio_master"]["prompt"]  # preserved product reference
    # the key visual is a product hero, not shot 1 (which may be about the problem, without it)
    assert "holds smooth black basalt stones" in snap["studio_master"]["prompt"]
    assert SCRIPT["shots"][0]["visual_prompt"] not in snap["studio_master"]["prompt"]
    assert len(snap["shots"]) == 2
    # one product, person and room in every separately generated frame and clip
    for c in [snap["studio_master"], *snap["keyframes"], *snap["shots"]]:
        assert (
            "Product (only where this shot shows it): smooth black basalt stones; "
            "Person: a Vietnamese woman" in c["prompt"]
        )
    assert "Setting:" not in snap["shots"][0]["prompt"]  # empty parts are left out
    # models misspell painted text: no brand facts in any picture, the headline is drawn later
    for c in [snap["studio_master"], snap["thumbnail"], *snap["keyframes"], *snap["shots"]]:
        assert "Facts to keep" not in c["prompt"] and "No text, letters, logos" in c["prompt"]

    # Kaggle notebook 1
    w = {"Authorization": "Bearer worker-secret"}
    assert (
        client.post(
            "/api/v1/worker/jobs/claim", json={"worker_id": "nb1", "kinds": ["studio"]}
        ).status_code
        == 401
    )
    claimed = client.post(
        "/api/v1/worker/jobs/claim", headers=w, json={"worker_id": "nb1", "kinds": ["studio"]}
    ).json()["job"]
    assert claimed["payload"]["references"][0]["url"]
    assert claimed["payload"]["thumbnail"]["headline"] == SCRIPT["hook"]  # drawn by the notebook
    # every shot gets its own first frame, edited from the product hero (the studio master)
    first, second = claimed["payload"]["shots"]
    assert "Same person, room and product design" in first["keyframe"]["prompt"]
    assert "Keep it unchanged" in second["keyframe"]["prompt"]
    for up in claimed["uploads"].values():
        put_presigned(client, up["url"], b"x" * 10, up["content_type"])
    assert client.post(
        f"/api/v1/worker/jobs/{claimed['id']}/progress",
        headers=w,
        json={"stage": "flux", "progress": 0.3},
    ).json() == {"cancel": False}
    done = client.post(
        f"/api/v1/worker/jobs/{claimed['id']}/complete",
        headers=w,
        json={
            "outputs": {
                "studio_master": {"width": 1080},
                "thumbnail": {},
                "final_video": {"duration": 12.0},
                "bgm": {},
            }
        },
    ).json()
    assert done == {"status": "succeeded", "missing": []}

    videos = client.get(f"{base}/artifacts?kind=video", headers=h).json()
    assert videos[0]["status"] == "ready" and videos[0]["current"]["mime_type"] == "video/mp4"

    # publishing requires approval, then runs (dry-run) via the worker
    page = connect_page(client, h)
    body = {"artifact_id": videos[0]["id"], "social_account_id": page["id"], "caption": "Đá nóng"}
    assert client.post("/api/v1/publishing-jobs", headers=h, json=body).status_code == 409
    client.post(f"/api/v1/artifacts/{videos[0]['id']}/approve", headers=h)
    pj = client.post("/api/v1/publishing-jobs", headers=h, json=body).json()
    assert pj["media_type"] == "video"
    db.expire_all()
    for j in publishing.due_jobs(db):
        publishing.run_job(db, j)
    db.commit()
    assert db.get(PublishingJob, __import__("uuid").UUID(pj["id"])).status == "published"

    # the same video to the Instagram account linked to that Page
    from app.models import SocialAccount

    fb = db.get(SocialAccount, __import__("uuid").UUID(page["id"]))
    ig = SocialAccount(
        workspace_id=fb.workspace_id,
        provider="instagram",
        external_id="178",
        name="@lotus",
        token_encrypted=fb.token_encrypted,
    )
    db.add(ig)
    db.commit()
    body["social_account_id"] = str(ig.id)
    long = {**body, "caption": "x" * 2201}
    assert client.post("/api/v1/publishing-jobs", headers=h, json=long).status_code == 422
    pj = client.post("/api/v1/publishing-jobs", headers=h, json=body).json()
    assert pj["page_name"] == "@lotus · Instagram"
    db.expire_all()
    for j in publishing.due_jobs(db):
        publishing.run_job(db, j)
    db.commit()
    assert db.get(PublishingJob, __import__("uuid").UUID(pj["id"])).status == "published"


def test_research_demotes_claims_without_real_source(client, spa, gemini, monkeypatch):
    from app.ai import sources

    page = {
        "index": 0,
        "url": "https://example.vn/spa-q3",
        "title": "Spa Q3",
        "text": "Đá nóng 590k",
    }
    monkeypatch.setattr(sources, "fetch_all", lambda urls: ([page], ["https://down.vn: 503"]))
    h, p = spa
    client.patch(
        f"/api/v1/projects/{p['id']}",
        headers=h,
        json={"research_urls": ["https://example.vn/spa-q3"]},
    )
    art = client.post(
        f"/api/v1/projects/{p['id']}/research", headers=h, json={"mode": "standard"}
    ).json()
    report = client.get(f"/api/v1/artifacts/{art['id']}", headers=h).json()["current"]["content"]
    assert report["evidence"] == [
        {
            "claim": "Nhiều spa Q3 quảng cáo đá nóng",
            "source_url": "https://example.vn/spa-q3",
            "source_title": "Spa Q3",
        }
    ]
    assert "(chưa có nguồn) 60% khách thích cuối tuần" in report["assumptions"]
    assert report["source_mode"] == "provided_urls" and report["unreachable_sources"] == [
        "https://down.vn: 503"
    ]


def test_research_url_fetch_blocks_private_addresses():
    from app.ai.sources import BlockedURL, _check_public

    for url in (
        "http://127.0.0.1:8000/admin",
        "http://169.254.169.254/latest/meta-data",
        "file:///etc/passwd",
        "http://localhost/",
    ):
        with pytest.raises(BlockedURL):
            _check_public(url)


def test_shorts_job_creates_one_artifact_per_clip(client, db, spa, gemini):
    h, p = spa
    base = f"/api/v1/projects/{p['id']}"
    pre = client.post(
        f"{base}/inputs/presign",
        headers=h,
        json={"filename": "spa.mp4", "content_type": "video/mp4", "byte_size": 3},
    ).json()
    put_presigned(client, pre["upload_url"], b"abc", "video/mp4")
    inp = client.post(
        f"{base}/inputs", headers=h, json={"object_id": pre["object_id"], "role": "source_video"}
    ).json()
    assert (
        client.post(f"{base}/shorts", headers=h, json={"source_input_id": inp["id"]}).status_code
        == 409
    )
    client.patch(f"/api/v1/project-inputs/{inp['id']}", headers=h, json={"usage_confirmed": True})
    client.post(f"{base}/shorts", headers=h, json={"source_input_id": inp["id"], "target_count": 2})
    w = {"Authorization": "Bearer worker-secret"}
    job = client.post(
        "/api/v1/worker/jobs/claim", headers=w, json={"worker_id": "nb2", "kinds": ["shorts"]}
    ).json()["job"]
    assert job["payload"]["source_url"] and job["payload"]["target_count"] == 2
    for name in ("short_1", "short_2", "cover_1"):
        up = job["uploads"][name]
        put_presigned(client, up["url"], b"v", up["content_type"])
    client.post(
        f"/api/v1/worker/jobs/{job['id']}/complete",
        headers=w,
        json={
            "outputs": {
                "short_1": {"title": "Hook đá nóng", "start": 3.2, "end": 21.0},
                "short_2": {"title": "CTA", "start": 40.0, "end": 58.5},
                "cover_1": {},
            }
        },
    )
    shorts = client.get(f"{base}/artifacts?kind=short", headers=h).json()
    assert [s["display_name"] for s in shorts] == ["Short 1 — Hook đá nóng", "Short 2 — CTA"]
    assert shorts[0]["current"]["content"]["start"] == 3.2


def test_stale_kaggle_job_is_requeued(client, db, spa, gemini):
    from datetime import timedelta

    from app.core.db import utcnow
    from app.creative.media import requeue_stale

    h, p = spa
    client.post(f"/api/v1/projects/{p['id']}/scripts", headers=h, json={"count": 1})
    a = client.get(f"/api/v1/projects/{p['id']}/artifacts?kind=script", headers=h).json()[0]
    client.post(f"/api/v1/artifacts/{a['id']}/select", headers=h)
    client.post(
        f"/api/v1/projects/{p['id']}/generate", headers=h, json={"script_artifact_id": a["id"]}
    )
    w = {"Authorization": "Bearer worker-secret"}
    client.post(
        "/api/v1/worker/jobs/claim", headers=w, json={"worker_id": "nb1", "kinds": ["studio"]}
    )
    db.expire_all()
    job = db.scalar(select(MediaJob))
    job.heartbeat_at = utcnow() - timedelta(hours=1)
    assert requeue_stale(db) == 1 and job.status == "queued"


def test_projects_are_tenant_isolated(client, spa, gemini):
    _h, p = spa
    other = signup(client, email="b@spa.vn", workspace="Other")
    assert client.get(f"/api/v1/projects/{p['id']}", headers=other).status_code == 404
    assert client.get("/api/v1/projects", headers=other).json() == []


def test_project_style_override_and_new_versions(client, spa, gemini):
    h, p = spa
    packs = client.get("/api/v1/style-packs", headers=h).json()
    preset = next(x for x in packs if x["name"] == "Clinical Clean")
    mine = client.post(f"/api/v1/style-packs/{preset['id']}/duplicate", headers=h).json()
    upd = client.put(
        f"/api/v1/style-packs/{mine['id']}",
        headers=h,
        json={
            "name": mine["name"],
            "change_summary": "giảm tone ấm",
            "blocks": [{"name": "Palette", "content": "Cool white", "applies_to": ["image"]}],
        },
    ).json()
    assert upd["version_number"] == 2
    client.put(
        f"/api/v1/projects/{p['id']}/style",
        headers=h,
        json={"modality": "image", "mode": "pack", "style_pack_id": mine["id"]},
    )
    eff = client.get(f"/api/v1/style-assignments?project_id={p['id']}", headers=h).json()
    assert eff["image"]["source"] == "project" and eff["image"]["version_number"] == 2
    assert (
        client.get("/api/v1/style-assignments", headers=h).json()["image"]["source"] == "platform"
    )
    client.put(
        f"/api/v1/projects/{p['id']}/style", headers=h, json={"modality": "video", "mode": "off"}
    )
    prev = client.post(
        "/api/v1/style-preview", headers=h, json={"modality": "video", "project_id": p["id"]}
    ).json()
    assert prev["applied_blocks"] == []
    assert (
        client.put(
            f"/api/v1/style-packs/{preset['id']}",
            headers=h,
            json={"name": "x", "blocks": [{"name": "a", "content": "b"}]},
        ).status_code
        == 403
    )


def test_script_and_media_assistants_keep_separate_conversations(client, spa, gemini, monkeypatch):
    h, p = spa
    base = f"/api/v1/projects/{p['id']}"
    _, b, _ = client.post(f"{base}/scripts", headers=h, json={"count": 3}).json()
    seen = {}
    fake_scripts = agents.gemini_json

    def fake(db, *, system, parts, purpose, workspace_id, **kw):
        if not purpose.startswith("project.chat"):
            return fake_scripts(
                db, system=system, parts=parts, purpose=purpose, workspace_id=workspace_id, **kw
            )
        seen[purpose] = "\n".join(x["text"] for x in parts)
        if purpose == "project.chat.script":
            return GeminiResult(
                {
                    "reply": "Đang viết",
                    "action": "generate_scripts",
                    "count": 1,
                    "instruction": "gộp",
                },
                "gemini-test",
                [],
            )
        # the media assistant may not write scripts; only propose a confirmed re-generation
        return GeminiResult(
            {"reply": "Làm lại nhé", "action": "propose_generation", "instruction": "tông ấm"},
            "gemini-test",
            [],
        )

    monkeypatch.setattr(agents, "gemini_json", fake)
    out = client.post(f"{base}/chat", headers=h, json={"message": "gộp A với B"}).json()
    assert out[1]["action"]["type"] == "generate_scripts"
    assert "Kịch bản A — Thư giãn sau giờ làm" in seen["project.chat.script"]  # sees the list

    client.post(f"/api/v1/artifacts/{b['id']}/select", headers=h)
    out = client.post(
        f"{base}/chat", headers=h, json={"message": "ảnh ấm hơn", "scope": "media"}
    ).json()
    assert out[1]["action"] == {
        "type": "propose_generation",
        "script_artifact_id": b["id"],
        "note": "tông ấm",
    }

    script_chat = client.get(f"{base}/chat", headers=h).json()
    media_chat = client.get(f"{base}/chat?scope=media", headers=h).json()
    assert [m["content"] for m in script_chat] == ["gộp A với B", "Đang viết"]
    assert [m["content"] for m in media_chat] == ["ảnh ấm hơn", "Làm lại nhé"]


def test_script_without_continuity_is_upgraded_before_generating(
    client, db, spa, gemini, monkeypatch
):
    h, p = spa
    old = {k: v for k, v in SCRIPT.items() if k != "continuity"}
    seen = []

    def fake(db, *, system, parts, purpose, workspace_id, deep=False, search=False, timeout=None):
        seen.append(purpose)
        if purpose == "scripts.generate":
            return GeminiResult({"variants": [old]}, "gemini-test", [])
        assert purpose == "scripts.revise"
        return GeminiResult([SCRIPT], "gemini-test", [])  # Gemini sometimes wraps it in a list

    monkeypatch.setattr(agents, "gemini_json", fake)
    base = f"/api/v1/projects/{p['id']}"
    client.post(f"{base}/scripts", headers=h, json={"count": 1})
    a = client.get(f"{base}/artifacts?kind=script", headers=h).json()[0]
    assert (
        "continuity" not in a["current"]["content"]
        or not a["current"]["content"]["continuity"]["product"]
    )
    client.post(f"/api/v1/artifacts/{a['id']}/select", headers=h)
    job = client.post(f"{base}/generate", headers=h, json={"script_artifact_id": a["id"]}).json()

    assert seen == ["scripts.generate", "scripts.revise"]
    assert "smooth black basalt stones" in job["prompt_snapshot"]["shots"][0]["prompt"]
    a = client.get(f"/api/v1/artifacts/{a['id']}", headers=h).json()
    assert a["current"]["version_number"] == 2 and a["status"] == "selected"


def test_voiceover_is_spoken_before_the_job_is_queued(client, db, spa, gemini, monkeypatch):
    import io
    import wave

    from app.ai import speech

    def fake_wav(seconds: float) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1), w.setsampwidth(2), w.setframerate(8000)
            w.writeframes(b"\0\0" * int(8000 * seconds))
        return buf.getvalue()

    spoken = []
    monkeypatch.setattr(speech, "speak", lambda text: spoken.append(text) or fake_wav(6.0))
    voiced = {
        **SCRIPT,
        "shots": [{**SCRIPT["shots"][0], "voiceover": "Vai gáy mỏi nhừ?"}, SCRIPT["shots"][1]],
    }
    gemini_fake = agents.gemini_json

    def fake(db, **kw):
        if kw["purpose"] == "scripts.generate":
            return GeminiResult({"variants": [voiced]}, "gemini-test", [])
        return gemini_fake(db, **kw)

    monkeypatch.setattr(agents, "gemini_json", fake)
    h, p = spa
    base = f"/api/v1/projects/{p['id']}"
    client.post(f"{base}/scripts", headers=h, json={"count": 1})
    a = client.get(f"{base}/artifacts?kind=script", headers=h).json()[0]
    client.post(f"/api/v1/artifacts/{a['id']}/select", headers=h)
    job = client.post(f"{base}/generate", headers=h, json={"script_artifact_id": a["id"]}).json()
    assert job["status"] == "preparing"  # nothing for the GPU until the voice exists

    claimed = client.post(
        "/api/v1/worker/jobs/claim",
        headers={"Authorization": "Bearer worker-secret"},
        json={"worker_id": "nb1", "kinds": ["studio"]},
    ).json()["job"]
    assert spoken == ["Vai gáy mỏi nhừ?"]
    first, second = claimed["payload"]["shots"]
    assert first["voice_url"] and first["duration_seconds"] == 6.8  # 5 s planned, 6 s spoken
    assert "voice_url" not in second and second["duration_seconds"] == 5


def test_five_shot_ad_gets_one_short_per_benefit(client, db, spa, gemini, monkeypatch):
    shot = SCRIPT["shots"][0]
    five = {**SCRIPT, "shots": [{**shot, "on_screen_text": f"Ý {i}"} for i in range(1, 6)]}
    real = agents.gemini_json

    def fake(db, **kw):
        if kw["purpose"] == "scripts.generate":
            return GeminiResult({"variants": [five]}, "gemini-test", [])
        return real(db, **kw)

    monkeypatch.setattr(agents, "gemini_json", fake)
    h, p = spa
    base = f"/api/v1/projects/{p['id']}"
    client.post(f"{base}/scripts", headers=h, json={"count": 1})
    a = client.get(f"{base}/artifacts?kind=script", headers=h).json()[0]
    client.post(f"/api/v1/artifacts/{a['id']}/select", headers=h)
    client.post(f"{base}/generate", headers=h, json={"script_artifact_id": a["id"]})
    shorts = client.get(f"{base}/artifacts?kind=short", headers=h).json()
    assert sorted(s["display_name"] for s in shorts) == [
        "Short 1 — Ý 2",
        "Short 2 — Ý 3",
        "Short 3 — Ý 4",
    ]

    w = {"Authorization": "Bearer worker-secret"}
    job = client.post(
        "/api/v1/worker/jobs/claim", headers=w, json={"worker_id": "nb1", "kinds": ["studio"]}
    ).json()["job"]
    assert [s["shots"] for s in job["payload"]["shorts"]] == [[0, 1, 4], [0, 2, 4], [0, 3, 4]]
    for up in job["uploads"].values():
        put_presigned(client, up["url"], b"x" * 10, up["content_type"])
    names = ("studio_master", "thumbnail", "final_video", "bgm", "short_1", "short_2", "short_3")
    done = client.post(
        f"/api/v1/worker/jobs/{job['id']}/complete",
        headers=w,
        json={"outputs": {n: {} for n in names}},
    ).json()
    assert done == {"status": "succeeded", "missing": []}
    shorts = client.get(f"{base}/artifacts?kind=short", headers=h).json()
    assert {s["status"] for s in shorts} == {"ready"}


def test_shot_camera_grammar_is_normalised_and_reaches_the_prompts():
    from app.ai.agents import Shot
    from app.creative.media import _camera, _continuity

    s = Shot.model_validate(
        {"description": "", "visual_prompt": "x", "framing": "Close-Up", "transition": "whip"}
    )
    assert (s.framing, s.transition) == ("close_up", "cut")  # unknown values fall back, never fail
    assert _camera(s.model_dump()) == "Camera: Close-up. "
    script = {"continuity": {"product": "a white LED mask", "motif": "the teal-green glow"}}
    assert "Recurring motif: the teal-green glow." in _continuity(script)
    assert "motif" not in _continuity(script, with_product=False)


def test_shot_without_the_product_starts_from_a_plate(client, db, spa, gemini, monkeypatch):
    first = {**SCRIPT["shots"][0], "shows_product": False, "visual_prompt": "she looks in a mirror"}
    script = {**SCRIPT, "shots": [first, SCRIPT["shots"][1]]}
    real = agents.gemini_json

    def fake(db, **kw):
        if kw["purpose"] == "scripts.generate":
            return GeminiResult({"variants": [script]}, "gemini-test", [])
        return real(db, **kw)

    monkeypatch.setattr(agents, "gemini_json", fake)
    h, p = spa
    base = f"/api/v1/projects/{p['id']}"
    client.post(f"{base}/scripts", headers=h, json={"count": 1})
    a = client.get(f"{base}/artifacts?kind=script", headers=h).json()[0]
    client.post(f"/api/v1/artifacts/{a['id']}/select", headers=h)
    client.post(f"{base}/generate", headers=h, json={"script_artifact_id": a["id"]})
    job = client.post(
        "/api/v1/worker/jobs/claim",
        headers={"Authorization": "Bearer worker-secret"},
        json={"worker_id": "nb1", "kinds": ["studio"]},
    ).json()["job"]
    plate, (no, yes) = job["payload"]["plate"], job["payload"]["shots"]
    assert "remove the product" in plate["prompt"] and "basalt" not in plate["prompt"]
    assert no["keyframe"]["base"] == "plate" and yes["keyframe"]["base"] == "master"
    for prompt in (no["keyframe"]["prompt"], no["prompt"]):  # neither the frame nor the clip
        assert "basalt" not in prompt and "The product is not in this shot" in prompt
    assert "basalt" in yes["prompt"]


def test_project_context_accepts_objects_where_strings_were_asked():
    from app.ai.agents import ProjectContext

    ctx = ProjectContext.model_validate(
        {"summary": "s", "services": [{"name": "Gói Tự làm", "price": "499.000đ"}, "Phí cài đặt"]}
    )
    assert ctx.services == ["Gói Tự làm · 499.000đ", "Phí cài đặt"]


def test_research_accepts_objects_where_strings_were_asked():
    from app.ai.agents import ResearchOut

    out = ResearchOut.model_validate(
        {
            "research_summary": "s",
            "target_audience": [{"segment": "Chủ quán cafe", "where": "TP.HCM"}],
        }
    )
    assert out.target_audience == ["Chủ quán cafe · TP.HCM"]


def test_voiceover_uses_vieneu_and_falls_back_to_gemini(monkeypatch):
    from app.ai import speech
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "modal_app", "growthpilot")
    monkeypatch.setattr(speech, "_gemini", lambda text: b"gemini")
    monkeypatch.setattr(speech, "_vieneu", lambda text: b"vieneu")
    assert speech.speak("Xin chào") == b"vieneu"

    def down(text):
        raise RuntimeError("modal down")

    monkeypatch.setattr(speech, "_vieneu", down)
    assert speech.speak("Xin chào") == b"gemini"


def test_invented_stat_cards_are_dropped_and_absolute_claims_flagged(client, db):
    import uuid

    from app.ai.agents import _script_flags
    from app.models import Project

    h = signup(client)
    client.post(
        "/api/v1/services",
        json={"name": "Gội đầu", "price_min": 150000, "promotion": "Giảm 20 phút"},
        headers=h,
    )
    p = Project(workspace_id=uuid.UUID(h["X-Workspace-Id"]), name="P", brief="Dùng thử 14 ngày")
    db.add(p)
    db.commit()
    shot = {"on_screen_text": "x", "voiceover": "", "stat": ""}
    variant = {
        "hook": "AI trả lời 24/7",
        "key_message": "",
        "cta": "",
        "caption": "",
        "voiceover": "",
        "shots": [{**shot, "stat": "100%"}, {**shot, "stat": "14 ngày"}, {**shot, "stat": "98%"}],
    }
    flags = _script_flags(db, p, variant)
    assert [s["stat"] for s in variant["shots"]] == ["", "14 ngày", ""]
    assert "absolute_claim" in flags
