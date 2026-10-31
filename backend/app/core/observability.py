"""Langfuse Cloud tracing + prompt management (system design v2.3 §3.3).

Every customer reply becomes one trace (session_id = conversation_id, user_id = customer_id) with
three spans: LightRAG retrieval, prompt assembly, LLM generation. System prompts live in Langfuse
Prompt Management (label "production") so they can be fixed in the Playground without a deploy;
the prompt in code is the fallback. Without LANGFUSE_* keys everything here is a no-op.
"""

import logging
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

from app.core.config import get_settings

log = logging.getLogger("growthpilot.observability")


class _NoOp:
    def update(self, **_: Any) -> "_NoOp":
        return self


@lru_cache
def client():
    s = get_settings()
    if not (s.langfuse_public_key and s.langfuse_secret_key):
        return None
    from langfuse import Langfuse

    from app.ai.llm import mask_pii

    def mask(data: Any, **_: Any) -> Any:  # PII never leaves the server, in traces either
        if isinstance(data, str):
            return mask_pii(data)
        if isinstance(data, dict):
            return {k: mask(v) for k, v in data.items()}
        if isinstance(data, list):
            return [mask(v) for v in data]
        return data

    return Langfuse(
        public_key=s.langfuse_public_key,
        secret_key=s.langfuse_secret_key,
        base_url=s.langfuse_base_url,
        environment=s.env,
        mask=mask,
    )


@contextmanager
def trace(name: str, *, session_id: str | None = None, user_id: str | None = None, **metadata: Any):
    """Root of one unit of work; nested span()/generation() calls attach to it."""
    lf = client()
    if lf is None:
        yield _NoOp()
        return
    from langfuse import propagate_attributes

    with (
        lf.start_as_current_observation(name=name, as_type="span", metadata=metadata) as obs,
        propagate_attributes(session_id=session_id, user_id=user_id, trace_name=name),
    ):
        yield obs


@contextmanager
def span(name: str, *, as_type: str = "span", **kwargs: Any):
    lf = client()
    if lf is None:
        yield _NoOp()
        return
    with lf.start_as_current_observation(name=name, as_type=as_type, **kwargs) as obs:
        yield obs


def prompt(name: str, fallback: str) -> tuple[str, Any]:
    """(template, langfuse prompt object or None). Cached 60s by the SDK; fallback on any error."""
    lf = client()
    if lf is None:
        return fallback, None
    try:
        p = lf.get_prompt(name, label="production", fallback=fallback, cache_ttl_seconds=60)
        return p.prompt, p
    except Exception as e:  # noqa: BLE001 — Langfuse down must never stop replies
        log.warning("langfuse prompt %s unavailable: %s", name, e)
        return fallback, None


def flush() -> None:
    lf = client()
    if lf is not None:
        lf.flush()
