import io
from urllib.parse import parse_qs, urlparse

import httpx
from PIL import Image

from app.core import storage
from app.core.config import get_settings
from app.creative import publishing
from app.social import meta
from tests.conftest import signup


def test_oauth_connects_linked_instagram_with_page_token(client, monkeypatch):
    h = signup(client)
    monkeypatch.setattr(get_settings(), "meta_app_id", "123")
    url = client.post("/api/v1/integrations/meta/connect", headers=h).json()["url"]
    state = parse_qs(urlparse(url).query)["state"][0]
    pages = [
        {
            "id": "111",
            "name": "Lotus Page",
            "access_token": "page-token",
            "instagram_business_account": {"id": "178", "username": "lotus.spa"},
        },
        {"id": "222", "name": "No IG", "access_token": "t2"},
    ]
    monkeypatch.setattr(meta, "exchange_code_for_pages", lambda code: pages)
    monkeypatch.setattr(meta, "subscribe_page", lambda *a: None)

    r = client.get(
        "/api/v1/integrations/meta/callback",
        params={"state": state, "code": "c"},
        follow_redirects=False,
    )
    assert r.headers["location"].endswith("connected=3")
    accounts = client.get("/api/v1/integrations/social-accounts", headers=h).json()
    assert sorted((a["provider"], a["external_id"], a["name"]) for a in accounts) == [
        ("facebook", "111", "Lotus Page"),
        ("facebook", "222", "No IG"),
        ("instagram", "178", "@lotus.spa"),
    ]


def test_instagram_photo_is_converted_to_jpeg(client):
    png = io.BytesIO()
    Image.new("RGBA", (8, 8), (200, 100, 50, 255)).save(png, "PNG")
    storage.put_bytes("ws/p/thumbnail.png", png.getvalue(), "image/png")
    key = publishing._jpeg_copy("ws/p/thumbnail.png")
    assert key == "ws/p/thumbnail.ig.jpg"
    assert Image.open(io.BytesIO(storage.read_bytes(key, 10**6))).format == "JPEG"


def test_reel_waits_for_container_then_publishes(monkeypatch):
    monkeypatch.setattr(get_settings(), "meta_dry_run", False)
    monkeypatch.setattr(meta.time, "sleep", lambda s: None)
    calls, states = [], iter(["IN_PROGRESS", "FINISHED"])

    def fake(method, url, params, timeout):
        calls.append((method, url.rsplit("/", 1)[-1], params))
        path = url.rsplit("/", 1)[-1]
        body = (
            {"id": "c1"}
            if path == "media"
            else {"id": "reel9"}
            if path == "media_publish"
            else {"status_code": next(states)}
        )
        return httpx.Response(200, json=body)

    monkeypatch.setattr(meta.httpx, "request", fake)
    res = meta.publish_instagram("178", "tok", "video", "https://r2/v.mp4", "Đá nóng")
    assert (res.ok, res.message_id) == (True, "reel9")
    create = calls[0][2]
    assert (create["media_type"], create["video_url"]) == ("REELS", "https://r2/v.mp4")
    assert [c[1] for c in calls] == ["media", "c1", "c1", "media_publish"]
    assert calls[-1][2]["creation_id"] == "c1"


def test_failed_container_is_not_published(monkeypatch):
    monkeypatch.setattr(get_settings(), "meta_dry_run", False)
    paths = []

    def fake(method, url, params, timeout):
        paths.append(url.rsplit("/", 1)[-1])
        if paths[-1] == "media":
            return httpx.Response(200, json={"id": "c1"})
        return httpx.Response(200, json={"status_code": "ERROR", "status": "bad aspect ratio"})

    monkeypatch.setattr(meta.httpx, "request", fake)
    res = meta.publish_instagram("178", "tok", "video", "https://r2/v.mp4", "")
    assert (res.ok, res.error) == (False, "bad aspect ratio")
    assert "media_publish" not in paths


def test_facebook_error_page_returns_to_settings_with_its_message(client):
    r = client.get(
        "/api/v1/integrations/meta/callback",
        params={"error_code": "1349048", "error_message": "Không thể tải URL"},
        follow_redirects=False,
    )
    assert r.status_code == 307
    assert (
        "tab=integrations&meta_error=Kh%C3%B4ng+th%E1%BB%83+t%E1%BA%A3i+URL"
        in r.headers["location"]
    )
