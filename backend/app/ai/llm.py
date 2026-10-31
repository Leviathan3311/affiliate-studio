"""LLM Router (system design §3.1).

Stream 1 (customer engagement): Groq `qwen/qwen3.8-27b` primary -> Gemini 3.8 Flash fallback.
Stream 2 (research/scripts) will call Gemini directly via `route=("gemini",)`.
"""

import json
import re
import time
import uuid
from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AIUsageRecord

_PHONE = re.compile(r"(?<!\d)(?:\+?84|0)(?:[\s.\-]?\d){8,10}(?!\d)")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def mask_pii(text: str) -> str:
    """Free-tier providers may train on prompts (system design §3.2): strip phone/email first."""
    return _EMAIL.sub("[EMAIL]", _PHONE.sub("[SĐT]", text))


class LLMUnavailable(Exception):
    pass


@dataclass
class LLMResult:
    data: dict
    provider: str
    model: str


def _groq(system: str, user: str) -> tuple[dict, int, int]:
    s = get_settings()
    r = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {s.groq_api_key}"},
        json={
            "model": s.groq_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
        },
        timeout=s.llm_timeout_seconds,
    )
    r.raise_for_status()
    body = r.json()
    usage = body.get("usage", {})
    content = body["choices"][0]["message"]["content"]
    return json.loads(content), usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def _gemini(system: str, user: str) -> tuple[dict, int, int]:
    s = get_settings()
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{s.gemini_model}:generateContent",
        headers={"x-goog-api-key": s.gemini_api_key},
        json={
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3},
        },
        timeout=s.llm_timeout_seconds,
    )
    r.raise_for_status()
    body = r.json()
    usage = body.get("usageMetadata", {})
    text = body["candidates"][0]["content"]["parts"][0]["text"]
    return (
        json.loads(text),
        usage.get("promptTokenCount", 0),
        usage.get("candidatesTokenCount", 0),
    )


_PROVIDERS = {
    "groq": (_groq, lambda s: s.groq_api_key, lambda s: s.groq_model),
    "gemini": (_gemini, lambda s: s.gemini_api_key, lambda s: s.gemini_model),
}


def complete_json(
    db: Session,
    *,
    system: str,
    user: str,
    purpose: str,
    workspace_id: uuid.UUID | None,
    route: tuple[str, ...] = ("groq", "gemini"),
) -> LLMResult:
    """Try providers in order; fall back on 429/5xx/timeout/bad JSON. Logs every attempt."""
    s = get_settings()
    user = mask_pii(user)
    errors = []
    for name in route:
        call, key, model = _PROVIDERS[name]
        if not key(s):
            errors.append(f"{name}: no api key")
            continue
        started = time.monotonic()
        rec = AIUsageRecord(
            workspace_id=workspace_id, purpose=purpose, provider=name, model=model(s)
        )
        try:
            data, tin, tout = call(system, user)
            rec.input_tokens, rec.output_tokens = tin, tout
            return LLMResult(data, name, model(s))
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError) as e:
            rec.success, rec.error = False, f"{type(e).__name__}: {e}"[:500]
            errors.append(f"{name}: {rec.error}")
        finally:
            rec.latency_ms = int((time.monotonic() - started) * 1000)
            db.add(rec)
    raise LLMUnavailable("; ".join(errors) or "no providers")
