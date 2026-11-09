"""Meta connection + webhook gateway (MOD-06, system design §4.2 / §5.2)."""

import json
import logging
import uuid
from datetime import datetime
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.deps import DB, Admin, AnyMember
from app.core.security import create_token, decode_token, encrypt_secret, verify_meta_signature
from app.models import AuditLog, SocialAccount, WebhookEvent
from app.social import meta

log = logging.getLogger("growthpilot.meta")
router = APIRouter(tags=["integrations"])


class SocialAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    provider: str
    external_id: str
    name: str
    status: str
    created_at: datetime


class ManualConnect(BaseModel):
    page_id: str = Field(pattern=r"^\d{5,30}$")
    name: str = Field(default="", max_length=300)
    page_access_token: str = Field(min_length=20, max_length=1000)


def _upsert_page(
    db,
    workspace_id: uuid.UUID,
    page_id: str,
    name: str,
    token: str,
    provider: str = "facebook",
) -> SocialAccount:
    """An Instagram account is stored with the token of the Page it is linked to."""
    acc = db.scalar(
        select(SocialAccount).where(
            SocialAccount.provider == provider, SocialAccount.external_id == page_id
        )
    )
    if acc and acc.workspace_id != workspace_id:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Tài khoản này đã được kết nối với một cửa hàng khác"
        )
    if acc is None:
        acc = SocialAccount(
            workspace_id=workspace_id, provider=provider, external_id=page_id, token_encrypted=""
        )
        db.add(acc)
    acc.name, acc.token_encrypted, acc.status = name, encrypt_secret(token), "connected"
    db.flush()
    return acc


@router.post("/integrations/meta/connect")
def meta_connect(ctx: Admin):
    if not get_settings().meta_app_id:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Chưa bật kết nối Facebook, vui lòng liên hệ hỗ trợ",
        )
    state = create_token(str(ctx.user.id), minutes=10, ws=str(ctx.ws_id), purpose="meta_oauth")
    return {"url": meta.oauth_url(state)}


@router.get("/integrations/meta/callback")
def meta_callback(
    db: DB,
    state: str = "",
    code: str | None = None,
    error: str | None = None,
    error_message: str | None = None,
):
    target = f"{get_settings().frontend_url}/app/settings?tab=integrations"
    if error_message and not code:
        # Facebook's own error page (e.g. the app's domains are not set) comes back without state.
        return RedirectResponse(f"{target}&{urlencode({'meta_error': error_message[:300]})}")
    try:
        claims = decode_token(state)
        assert claims.get("purpose") == "meta_oauth"
        ws_id, user_id = uuid.UUID(claims["ws"]), uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, AssertionError, KeyError, ValueError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid state") from None
    if error or not code:
        return RedirectResponse(f"{target}&meta_error={error or 'cancelled'}")
    try:
        pages = meta.exchange_code_for_pages(code)
    except httpx.HTTPError as e:
        log.warning("meta oauth exchange failed: %s", e)
        return RedirectResponse(f"{target}&meta_error=exchange_failed")

    connected = 0
    for p in pages:
        try:
            with db.begin_nested():
                acc = _upsert_page(db, ws_id, p["id"], p.get("name", ""), p["access_token"])
            meta.subscribe_page(acc.external_id, p["access_token"])
            connected += 1
        except (HTTPException, httpx.HTTPError) as e:
            log.warning("page %s not connected: %s", p.get("id"), e)
        if ig := p.get("instagram_business_account"):
            try:
                with db.begin_nested():
                    _upsert_page(
                        db,
                        ws_id,
                        ig["id"],
                        "@" + ig.get("username", ""),
                        p["access_token"],
                        provider="instagram",
                    )
                connected += 1
            except HTTPException as e:
                log.warning("instagram %s not connected: %s", ig.get("id"), e.detail)
    db.add(
        AuditLog(
            workspace_id=ws_id,
            actor_user_id=user_id,
            action="meta.connected",
            target_type="workspace",
            target_id=str(ws_id),
            meta={"accounts": connected},
        )
    )
    db.commit()
    return RedirectResponse(f"{target}&connected={connected}")


@router.post(
    "/integrations/social-accounts/manual", response_model=SocialAccountOut, status_code=201
)
def manual_connect(body: ManualConnect, ctx: Admin):
    """Pilot path: paste a Page access token (e.g. from Graph API Explorer) before App Review."""
    acc = _upsert_page(ctx.db, ctx.ws_id, body.page_id, body.name, body.page_access_token)
    if not get_settings().meta_dry_run:
        try:
            meta.subscribe_page(body.page_id, body.page_access_token)
        except httpx.HTTPError as e:
            ctx.db.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Meta từ chối token: {e}") from None
    ctx.audit("meta.page_connected", "social_account", acc.id, page_id=body.page_id)
    ctx.db.commit()
    return acc


@router.get("/integrations/social-accounts", response_model=list[SocialAccountOut])
def list_accounts(ctx: AnyMember):
    return ctx.db.scalars(
        select(SocialAccount).where(SocialAccount.workspace_id == ctx.ws_id)
    ).all()


@router.delete("/integrations/social-accounts/{account_id}", status_code=204)
def disconnect(account_id: uuid.UUID, ctx: Admin):
    acc = ctx.get(SocialAccount, account_id)
    acc.status, acc.token_encrypted = "disconnected", ""
    ctx.audit("meta.page_disconnected", "social_account", acc.id)
    ctx.db.commit()


def accept_webhook(db, body: bytes, signature: str | None) -> bool:
    """Verify + enqueue one Meta delivery. Shared by the HTTP route and the edge-queue drain."""
    s = get_settings()
    if (s.meta_app_secret or s.env != "dev") and not verify_meta_signature(body, signature):
        return False
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return False
    for key, event in meta.parse_messaging_events(payload):
        try:
            with db.begin_nested():
                db.add(WebhookEvent(dedupe_key=key, page_id=event["page_id"], payload=event))
        except IntegrityError:
            pass  # duplicate delivery; already queued
    return True


# --- Webhook gateway: verify, enqueue, ACK. Never call the LLM here (NFR webhook ACK). ---


@router.get("/webhooks/meta", response_class=PlainTextResponse)
def webhook_verify(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
):
    if mode == "subscribe" and token == get_settings().meta_verify_token:
        return challenge
    raise HTTPException(status.HTTP_403_FORBIDDEN, "verification failed")


@router.post("/webhooks/meta", response_class=PlainTextResponse)
async def webhook_receive(request: Request, db: DB):
    body = await request.body()
    if not accept_webhook(db, body, request.headers.get("x-hub-signature-256")):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "bad signature or payload")
    db.commit()
    return "EVENT_RECEIVED"
