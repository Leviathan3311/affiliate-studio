"""Meta Graph API client (BRD §7, MOD-06). Thin wrappers; no SDK."""

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings
from app.core.db import utcnow

log = logging.getLogger(__name__)

SCOPES = (
    "pages_show_list,pages_messaging,pages_manage_metadata,pages_read_engagement,pages_manage_posts,"
    "instagram_basic,instagram_content_publish"
)


def _graph(path: str) -> str:
    return f"https://graph.facebook.com/{get_settings().meta_graph_version}/{path}"


def redirect_uri() -> str:
    return f"{get_settings().api_public_url}/api/v1/integrations/meta/callback"


def oauth_url(state: str) -> str:
    s = get_settings()
    q = urlencode(
        {
            "client_id": s.meta_app_id,
            "redirect_uri": redirect_uri(),
            "state": state,
            "scope": SCOPES,
        }
    )
    return f"https://www.facebook.com/{s.meta_graph_version}/dialog/oauth?{q}"


def exchange_code_for_pages(code: str) -> list[dict]:
    """code -> user token -> pages the user manages (each with its own page access token).

    A Page with a linked Instagram professional account also carries `instagram_business_account`;
    that account is published to with the same Page token.
    """
    s = get_settings()
    r = httpx.get(
        _graph("oauth/access_token"),
        params={
            "client_id": s.meta_app_id,
            "client_secret": s.meta_app_secret,
            "redirect_uri": redirect_uri(),
            "code": code,
        },
        timeout=15,
    )
    r.raise_for_status()
    short_token = r.json()["access_token"]
    # Page tokens inherit the user token's lifetime: from a long-lived user token they never expire.
    r = httpx.get(
        _graph("oauth/access_token"),
        params={
            "grant_type": "fb_exchange_token",
            "client_id": s.meta_app_id,
            "client_secret": s.meta_app_secret,
            "fb_exchange_token": short_token,
        },
        timeout=15,
    )
    r.raise_for_status()
    user_token = r.json()["access_token"]
    r = httpx.get(
        _graph("me/accounts"),
        params={
            "access_token": user_token,
            "fields": "id,name,access_token,instagram_business_account{id,username}",
        },
        timeout=15,
    )
    r.raise_for_status()
    pages = r.json().get("data", [])
    if not pages:  # say why in the log: a Page not ticked in the dialog, or a declined permission
        perms = httpx.get(_graph("me/permissions"), params={"access_token": user_token}, timeout=15)
        if perms.is_success:
            log.warning(
                "meta oauth: no pages returned; permissions %s",
                {p["permission"]: p["status"] for p in perms.json().get("data", [])},
            )
    return pages


def subscribe_page(page_id: str, page_token: str) -> None:
    r = httpx.post(
        _graph(f"{page_id}/subscribed_apps"),
        params={"access_token": page_token, "subscribed_fields": "messages,messaging_postbacks"},
        timeout=15,
    )
    r.raise_for_status()


@dataclass
class SendResult:
    ok: bool
    status: str  # sent | dry_run | failed
    message_id: str | None = None
    error: str | None = None


def send_text(page_token: str, psid: str, text: str) -> SendResult:
    """Send API, messaging_type RESPONSE (standard 24h window only)."""
    if get_settings().meta_dry_run:
        return SendResult(True, "dry_run")
    try:
        r = httpx.post(
            _graph("me/messages"),
            params={"access_token": page_token},
            json={
                "recipient": {"id": psid},
                "messaging_type": "RESPONSE",
                "message": {"text": text},
            },
            timeout=15,
        )
    except httpx.HTTPError as e:
        return SendResult(False, "failed", error=f"{type(e).__name__}: {e}")
    if r.status_code >= 400:
        err = (
            r.json().get("error", {})
            if r.headers.get("content-type", "").startswith("application/json")
            else {}
        )
        return SendResult(False, "failed", error=err.get("message") or r.text[:300])
    return SendResult(True, "sent", message_id=r.json().get("message_id"))


@dataclass
class InboundMessage:
    page_id: str
    psid: str
    mid: str
    text: str
    sent_at: datetime


def parse_messaging_events(payload: dict) -> list[tuple[str, dict]]:
    """Split a webhook POST into (dedupe_key, single-event payload) pairs."""
    out = []
    if payload.get("object") != "page":
        return out
    for entry in payload.get("entry", []):
        page_id = str(entry.get("id"))
        for ev in entry.get("messaging", []):
            msg = ev.get("message") or {}
            if msg.get("is_echo"):
                continue  # our own outbound, already stored
            if mid := msg.get("mid"):
                out.append((f"msg:{mid}", {"page_id": page_id, **ev}))
    return out


def to_inbound(event: dict) -> InboundMessage:
    msg = event["message"]
    text = msg.get("text") or ("[tệp đính kèm]" if msg.get("attachments") else "")
    return InboundMessage(
        page_id=event["page_id"],
        psid=str(event["sender"]["id"]),
        mid=msg["mid"],
        text=text,
        sent_at=datetime.fromtimestamp(ts / 1000, UTC)
        if (ts := event.get("timestamp"))
        else utcnow(),
    )


def fetch_profile_name(page_token: str, psid: str) -> str:
    if get_settings().meta_dry_run:
        return ""
    try:
        r = httpx.get(
            _graph(psid), params={"access_token": page_token, "fields": "name"}, timeout=10
        )
        return r.json().get("name", "") if r.status_code == 200 else ""
    except httpx.HTTPError:
        return ""


def publish(
    page_id: str, page_token: str, media_type: str, media_url: str, caption: str
) -> SendResult:
    """Organic Page post (MOD-05). Photo via /photos, video via graph-video /videos with file_url."""
    if get_settings().meta_dry_run:
        return SendResult(True, "dry_run", message_id=None)
    if media_type == "photo":
        url, data = _graph(f"{page_id}/photos"), {"url": media_url, "message": caption}
    else:
        v = get_settings().meta_graph_version
        url = f"https://graph-video.facebook.com/{v}/{page_id}/videos"
        data = {"file_url": media_url, "description": caption}
    try:
        r = httpx.post(url, params={"access_token": page_token}, data=data, timeout=120)
    except httpx.HTTPError as e:
        # Unknown outcome: the post may exist. Caller must not blindly retry (no duplicate posts).
        return SendResult(False, "unknown", error=f"{type(e).__name__}: {e}")
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if r.status_code >= 400:
        return SendResult(
            False, "failed", error=body.get("error", {}).get("message") or r.text[:300]
        )
    return SendResult(True, "sent", message_id=body.get("post_id") or body.get("id"))


def _ig_call(method: str, path: str, token: str, **data) -> tuple[dict, str | None]:
    """One Instagram Graph call: (body, error message or None)."""
    r = httpx.request(method, _graph(path), params={"access_token": token, **data}, timeout=60)
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if r.status_code >= 400:
        return body, body.get("error", {}).get("message") or r.text[:300]
    return body, None


def publish_instagram(
    ig_id: str, page_token: str, media_type: str, media_url: str, caption: str
) -> SendResult:
    """Instagram feed photo or Reel (MOD-05): create a media container, wait for it, publish it.

    Instagram fetches the file itself, so media_url must be public (a presigned R2 link works).
    Photos must be JPEG.
    """
    if get_settings().meta_dry_run:
        return SendResult(True, "dry_run", message_id=None)
    if media_type == "photo":
        media = {"image_url": media_url}
    else:
        media = {"media_type": "REELS", "video_url": media_url, "share_to_feed": "true"}
    try:
        body, err = _ig_call("POST", f"{ig_id}/media", page_token, caption=caption, **media)
        if err:
            return SendResult(False, "failed", error=err)
        container = body["id"]
        # Videos are transcoded first; publishing before FINISHED fails.
        for _ in range(60):
            body, err = _ig_call("GET", container, page_token, fields="status_code,status")
            state = body.get("status_code")
            if err or state in ("ERROR", "EXPIRED"):
                return SendResult(False, "failed", error=err or body.get("status") or state)
            if state in ("FINISHED", None):
                break
            time.sleep(5)
        else:
            return SendResult(False, "failed", error="Instagram xử lý video quá lâu, thử lại sau")
    except httpx.HTTPError as e:
        return SendResult(False, "failed", error=f"{type(e).__name__}: {e}")
    try:
        body, err = _ig_call("POST", f"{ig_id}/media_publish", page_token, creation_id=container)
    except httpx.HTTPError as e:
        # Same as Page posts: the Reel may be live, so never retry blindly.
        return SendResult(False, "unknown", error=f"{type(e).__name__}: {e}")
    if err:
        return SendResult(False, "failed", error=err)
    return SendResult(True, "sent", message_id=body.get("id"))
