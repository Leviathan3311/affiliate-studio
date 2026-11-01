"""Spa knowledge for the LLMs (system design v2.3 §3.2): two layers on the same PostgreSQL.

1. SQL facts — services, prices, offers, hours read straight from the tables. Prices quoted to a
   customer only ever come from here, never from retrieved text.
2. LightRAG — brand profile, service descriptions, FAQ/policies/contraindications and confirmed
   campaign contexts, indexed into Postgres (PGKV / PGVector / PGTableGraph / PGDocStatus) with
   one LightRAG workspace per spa. Queried in `hybrid` mode for context only; Qwen/Gemini answer.

LightRAG is optional at runtime: without Postgres or a Gemini key (tests, local SQLite) and on any
retrieval error, callers fall back to keyword matching so replying to customers never blocks.
"""

import asyncio
import hashlib
import logging
import os
import re
import threading
import uuid
from concurrent.futures import TimeoutError as FutureTimeout
from functools import lru_cache
from urllib.parse import unquote

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import utcnow
from app.core.observability import span
from app.models import Brand, KnowledgeDocument, KnowledgeSyncState, Project, Service

log = logging.getLogger("growthpilot.knowledge")
SERVICE_LIMIT = 30
FAQ_LIMIT = 5
CONTEXT_CHARS = 2400  # ~600-800 tokens: Groq free tier is 8k TPM (system design §3.4)
EMBED_DIM = 1536  # gemini-embedding-2 is 3072; 1536 fits pgvector HNSW (max 2000 dims)
RETRIEVE_TIMEOUT = 12.0  # warm instance: embed + keyword call + PG queries
_PRICE = re.compile(
    r"(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s*(k|nghìn|ngàn|tr|triệu|đ|vnđ|vnd)?(?!\w)",
    re.IGNORECASE,
)


# ---------- layer 1: SQL facts ----------


def extract_prices(text: str) -> set[int]:
    """VND amounts mentioned in text. Bare numbers < 1000 are ignored (durations, counts)."""
    out = set()
    for num, unit in _PRICE.findall(text):
        unit = (unit or "").lower()
        if unit in ("k", "nghìn", "ngàn"):
            value = float(num.replace(",", ".")) * 1_000
        elif unit in ("tr", "triệu"):
            value = float(num.replace(",", ".")) * 1_000_000
        else:
            value = float(re.sub(r"[.,]", "", num))
        if value >= 1000:
            out.add(int(value))
    return out


def vnd(n: int) -> str:
    return f"{n:,}đ".replace(",", ".")


def _price_text(s: Service) -> str:
    if s.price_min and s.price_max and s.price_max != s.price_min:
        return f"{vnd(s.price_min)} - {vnd(s.price_max)}"
    return vnd(s.price_min) if s.price_min else "chưa công bố giá (không được báo giá)"


def sql_facts(db: Session, workspace_id: uuid.UUID) -> tuple[list[str], set[int]]:
    """Verified facts + every price the AI may quote (from services, offers and FAQ text)."""
    brand = db.scalar(select(Brand).where(Brand.workspace_id == workspace_id))
    services = db.scalars(
        select(Service)
        .where(Service.workspace_id == workspace_id, Service.active)
        .limit(SERVICE_LIMIT)
    ).all()
    lines, prices = [], set()
    if brand:
        lines.append(
            f"Spa: {brand.name}. Địa chỉ: {brand.address}. Hotline: {brand.hotline}. "
            f"Giờ mở cửa: {brand.opening_hours}."
        )
    for s in services:
        promo = f" Ưu đãi: {s.promotion}" if s.promotion else ""
        lines.append(f"- {s.name} ({s.duration_minutes} phút): {_price_text(s)}.{promo}")
        prices |= {p for p in (s.price_min, s.price_max) if p} | extract_prices(s.promotion)
    for d in db.scalars(
        select(KnowledgeDocument.content).where(KnowledgeDocument.workspace_id == workspace_id)
    ):
        prices |= extract_prices(d)
    return lines, prices


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"\w+", text.lower()) if len(t) > 1}


def _keyword_context(db: Session, workspace_id: uuid.UUID, query: str) -> str:
    # Fallback when LightRAG is unavailable: plain keyword overlap over FAQ/policy docs.
    docs = db.scalars(
        select(KnowledgeDocument).where(KnowledgeDocument.workspace_id == workspace_id)
    ).all()
    q = _tokens(query)
    docs = sorted(docs, key=lambda d: -len(q & _tokens(d.title + " " + d.content)))[:FAQ_LIMIT]
    return "\n".join(f"- {d.title}: {d.content}" for d in docs)


def build_context(db: Session, workspace_id: uuid.UUID, query: str) -> tuple[str, set[int]]:
    """Prompt-ready knowledge for one question: SQL facts first, then retrieved context."""
    lines, prices = sql_facts(db, workspace_id)
    retrieved = retrieve(workspace_id, query) if query.strip() else None
    source = "lightrag" if retrieved else "keyword"
    if retrieved is None:
        retrieved = _keyword_context(db, workspace_id, query)
    text = "BẢNG GIÁ & THÔNG TIN CHÍNH XÁC (SQL):\n" + "\n".join(lines)
    if retrieved:
        text += f"\n\nTRI THỨC LIÊN QUAN ({source}; giá trong phần này không được dùng để báo giá):\n{retrieved}"
    return text, prices


# ---------- documents to index ----------


def documents(db: Session, workspace_id: uuid.UUID) -> dict[str, str]:
    """doc_id -> text. Stable ids so edits replace the old version in the graph."""
    docs: dict[str, str] = {}
    brand = db.scalar(select(Brand).where(Brand.workspace_id == workspace_id))
    if brand:
        docs["brand"] = (
            f"Thương hiệu {brand.name}. {brand.description}\nĐịa chỉ: {brand.address}. "
            f"Giờ mở cửa: {brand.opening_hours}.\nKhông được nói/cam kết: {brand.forbidden_claims}"
        )
    for s in db.scalars(select(Service).where(Service.workspace_id == workspace_id)):
        state = "đang cung cấp" if s.active else "đã ngừng cung cấp"
        docs[f"service:{s.id}"] = (
            f"Dịch vụ {s.name} ({state}), thời lượng {s.duration_minutes} phút.\n{s.description}\n"
            + (f"Ưu đãi áp dụng: {s.promotion}" if s.promotion else "")
        )
    for d in db.scalars(
        select(KnowledgeDocument).where(KnowledgeDocument.workspace_id == workspace_id)
    ):
        kind = "Chính sách" if d.kind == "policy" else "Câu hỏi thường gặp"
        docs[f"knowledge:{d.id}"] = f"{kind}: {d.title}\n{d.content}"
    for p in db.scalars(
        select(Project).where(
            Project.workspace_id == workspace_id,
            Project.status == "active",
            Project.context_confirmed_at.is_not(None),
        )
    ):
        ctx = p.context or {}
        facts = "; ".join(
            f["fact"] for f in ctx.get("key_facts", []) if f.get("source") != "unverified"
        )
        docs[f"project:{p.id}"] = (
            f"Chiến dịch {p.name}: {ctx.get('summary', '')}\nThông điệp: {'; '.join(ctx.get('key_messages', []))}\n"
            f"Dữ kiện đã xác minh: {facts}"
        )
    return {k: v.strip() for k, v in docs.items() if v.strip()}


def sync(db: Session, workspace_id: uuid.UUID) -> dict[str, int]:
    """Re-index only what changed since the last run (hash per document)."""
    if not enabled():
        return {}
    current = documents(db, workspace_id)
    hashes = {k: hashlib.sha256(v.encode()).hexdigest() for k, v in current.items()}
    state = {
        r.doc_id: r
        for r in db.scalars(
            select(KnowledgeSyncState).where(KnowledgeSyncState.workspace_id == workspace_id)
        )
    }
    changed = [k for k, h in hashes.items() if state.get(k) is None or state[k].content_hash != h]
    removed = [k for k in state if k not in hashes]
    if not changed and not removed:
        return {"changed": 0, "removed": 0}
    rt = _runtime()
    for doc_id in removed + [k for k in changed if k in state]:
        rt.run(_delete(workspace_id, doc_id), timeout=300)
    failed = 0
    for doc_id in changed:
        if not rt.run(_insert(workspace_id, doc_id, current[doc_id]), timeout=900):
            failed += 1  # no state row: the next sync retries it (Gemini overloads are transient)
            continue
        row = state.get(doc_id) or KnowledgeSyncState(workspace_id=workspace_id, doc_id=doc_id)
        row.content_hash, row.synced_at = hashes[doc_id], utcnow()
        db.add(row)
    for doc_id in removed:
        db.delete(state[doc_id])
    db.flush()
    return {"changed": len(changed) - failed, "removed": len(removed), "failed": failed}


# ---------- layer 2: LightRAG runtime ----------


def enabled() -> bool:
    s = get_settings()
    if not (s.lightrag_enabled and s.database_url.startswith("postgresql") and s.gemini_api_key):
        return False
    if _is_supabase() and not os.path.exists(s.postgres_ssl_root_cert):
        _warn_missing_ca()
        return False
    return True


def _is_supabase() -> bool:
    return "supabase.co" in get_settings().database_url


@lru_cache
def _warn_missing_ca() -> None:
    log.warning(
        "LightRAG off: Supabase needs its CA for verified TLS. Download it from Project Settings -> "
        "Database -> SSL Configuration and set POSTGRES_SSL_ROOT_CERT; using keyword retrieval meanwhile."
    )


def retrieve(workspace_id: uuid.UUID, query: str) -> str | None:
    if not enabled():
        return None
    with span("lightrag.retrieve", as_type="retriever", input={"query": query}) as obs:
        try:
            ctx = _runtime().run(_query(workspace_id, query), timeout=RETRIEVE_TIMEOUT)
        except (FutureTimeout, Exception) as e:  # noqa: BLE001 — retrieval must never block a reply
            log.warning("lightrag retrieve failed: %s", e)
            obs.update(level="WARNING", status_message=str(e)[:200])
            return None
        ctx = (ctx or "").strip()[:CONTEXT_CHARS] or None
        obs.update(output=ctx)
        return ctx


class _Runtime:
    """One asyncio loop thread owning every LightRAG instance (asyncpg pools are loop-bound)."""

    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        self.rags: dict[str, object] = {}
        threading.Thread(target=self.loop.run_forever, name="lightrag", daemon=True).start()

    def run(self, coro, timeout: float):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)


_RT: _Runtime | None = None
_RT_LOCK = threading.Lock()


def _runtime() -> _Runtime:
    global _RT
    with _RT_LOCK:
        if _RT is None:
            _configure_postgres_env()
            _RT = _Runtime()
        return _RT


def _configure_postgres_env() -> None:
    """LightRAG's PG storages read POSTGRES_* env vars; derive them from DATABASE_URL."""
    from sqlalchemy.engine import make_url

    u = make_url(get_settings().database_url)
    os.environ.update(
        POSTGRES_HOST=u.host or "",
        POSTGRES_PORT=str(u.port or 5432),
        POSTGRES_USER=u.username or "",
        POSTGRES_PASSWORD=unquote(u.password or ""),
        POSTGRES_DATABASE=u.database or "postgres",
        POSTGRES_MAX_CONNECTIONS=os.environ.get("POSTGRES_MAX_CONNECTIONS", "4"),
    )
    root_cert = get_settings().postgres_ssl_root_cert
    if root_cert:  # verified TLS against the provider's CA (Supabase ships its own)
        os.environ.update(POSTGRES_SSL_MODE="verify-full", POSTGRES_SSL_ROOT_CERT=root_cert)
    else:
        os.environ.setdefault("POSTGRES_SSL_MODE", "require")


async def _rag(workspace_id: uuid.UUID):
    from lightrag import LightRAG
    from lightrag.utils import EmbeddingFunc

    key = f"ws_{workspace_id.hex}"
    rt = _runtime()
    if key not in rt.rags:
        s = get_settings()
        rag = LightRAG(
            working_dir=os.path.join(s.local_media_dir, "lightrag"),
            workspace=key,
            kv_storage="PGKVStorage",
            vector_storage="PGVectorStorage",
            graph_storage="PGTableGraphStorage",
            doc_status_storage="PGDocStatusStorage",
            llm_model_func=_llm,
            llm_model_name=s.lightrag_llm_model,
            embedding_func=EmbeddingFunc(
                embedding_dim=EMBED_DIM,
                max_token_size=2048,
                func=_embed,
                model_name=s.gemini_embedding_model,
            ),
            addon_params={"language": "Vietnamese"},
        )
        await rag.initialize_storages()
        rt.rags[key] = rag
    return rt.rags[key]


async def _query(workspace_id: uuid.UUID, query: str) -> str:
    from lightrag import QueryParam

    rag = await _rag(workspace_id)
    # Keywords supplied up front skip LightRAG's LLM keyword-extraction call: a customer reply then
    # costs one embedding + Postgres queries, not an extra (rate-limited) Gemini request.
    param = QueryParam(
        mode="hybrid", only_need_context=True, hl_keywords=[query], ll_keywords=[query]
    )
    return await rag.aquery(query, param=param)


async def _insert(workspace_id: uuid.UUID, doc_id: str, text: str) -> bool:
    """True when LightRAG finished extraction (it records failures instead of raising)."""
    rag = await _rag(workspace_id)
    await rag.ainsert(text, ids=[doc_id], file_paths=[doc_id])
    status = (await rag.doc_status.get_by_id(doc_id) or {}).get("status")
    return str(getattr(status, "value", status)).lower() == "processed"


async def _delete(workspace_id: uuid.UUID, doc_id: str) -> None:
    rag = await _rag(workspace_id)
    await rag.adelete_by_doc_id(doc_id)


# ---------- Gemini bindings for LightRAG (same fallback chain as the rest of stream 2) ----------

_GEMINI = "https://generativelanguage.googleapis.com/v1beta/models"


async def _llm(prompt, system_prompt=None, history_messages=None, **kwargs) -> str:
    s = get_settings()
    json_mode = bool(kwargs.get("keyword_extraction") or kwargs.get("response_format"))
    history = "\n".join(f"{m['role']}: {m['content']}" for m in history_messages or [])
    body = {
        "contents": [{"role": "user", "parts": [{"text": f"{history}\n{prompt}".strip()}]}],
        "generationConfig": {
            "temperature": 0.1,
            **({"responseMimeType": "application/json"} if json_mode else {}),
        },
    }
    if system_prompt:
        body["systemInstruction"] = {"parts": [{"text": system_prompt}]}
    errors = []
    # Entity extraction and query keywords don't need the strongest model: lite first, short timeout
    # so an overloaded model falls through to the next one instead of hanging the whole index run.
    chain = [s.lightrag_llm_model, s.gemini_model, *s.gemini_fallback_models]
    async with httpx.AsyncClient(timeout=60) as client:
        for model in dict.fromkeys(chain):
            try:
                r = await client.post(
                    f"{_GEMINI}/{model}:generateContent",
                    headers={"x-goog-api-key": s.gemini_api_key},
                    json=body,
                )
            except httpx.TransportError as e:  # timeouts included
                errors.append(f"{model}: {type(e).__name__}")
                continue
            if r.status_code == 200:
                parts = r.json()["candidates"][0]["content"]["parts"]
                return "".join(p.get("text", "") for p in parts)
            errors.append(f"{model}: HTTP {r.status_code}")
            if r.status_code not in (429, 500, 502, 503, 504):
                break
    raise RuntimeError("gemini (lightrag): " + "; ".join(errors))


async def _embed(texts: list[str], **_) -> "np.ndarray":  # noqa: F821
    import numpy as np

    s = get_settings()
    model = s.gemini_embedding_model
    out = []
    async with httpx.AsyncClient(timeout=120) as client:
        for i in range(0, len(texts), 100):  # batchEmbedContents caps at 100 per call
            reqs = [
                {
                    "model": f"models/{model}",
                    "content": {"parts": [{"text": t}]},
                    "outputDimensionality": EMBED_DIM,
                }
                for t in texts[i : i + 100]
            ]
            r = await client.post(
                f"{_GEMINI}/{model}:batchEmbedContents",
                headers={"x-goog-api-key": s.gemini_api_key},
                json={"requests": reqs},
            )
            r.raise_for_status()
            out.extend(e["values"] for e in r.json()["embeddings"])
    return np.array(out, dtype=np.float32)
