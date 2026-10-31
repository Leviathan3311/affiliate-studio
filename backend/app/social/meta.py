"""Meta Graph API client (BRD §7, MOD-06). Thin wrappers; no SDK."""

from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings
from app.core.db import utcnow

SCOPES = (
    "pages_show_list,pages_messaging,pages_manage_metadata,pages_read_engagement,pages_manage_posts"
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
    """code -> user token -> pages the user manages (each with its own page access token)."""
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
        params={"access_token": user_token, "fields": "id,name,access_token"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("data", [])


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
