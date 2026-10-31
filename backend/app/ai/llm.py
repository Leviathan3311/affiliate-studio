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

from app.core.config import get_settings
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


# --- Stream 2: Gemini only (research, scripts, project context, orchestrator) ---


@dataclass
class GeminiResult:
    data: dict
    model: str
    sources: list[dict]  # [{index, url, title}] from Google Search grounding, never model-invented


def _parse_json_text(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)


RETRYABLE = {429, 500, 502, 503, 504}


def gemini_json(
    db: Session,
    *,
    system: str,
    parts: list[dict],
    purpose: str,
    workspace_id: uuid.UUID | None,
    deep: bool = False,
    search: bool = False,
    timeout: float | None = None,
) -> GeminiResult:
    """One Gemini call returning JSON. `parts` are Gemini content parts (text / inline_data).
    Falls back through gemini_fallback_models on overload (503), quota (429) or timeouts."""
    s = get_settings()
    if not s.gemini_api_key:
        raise LLMUnavailable("gemini: no api key")
    chain = ([s.gemini_deep_model] if deep else []) + [s.gemini_model, *s.gemini_fallback_models]
    models = list(dict.fromkeys(chain))
    parts = [{"text": mask_pii(p["text"])} if "text" in p else p for p in parts]
    errors = []
    for model in models:
        body: dict = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"},
        }
        if search:
            body["tools"] = [{"google_search": {}}]
        rec = AIUsageRecord(
            workspace_id=workspace_id, purpose=purpose, provider="gemini", model=model
        )
        started = time.monotonic()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {"x-goog-api-key": s.gemini_api_key}
        wait = timeout or s.research_timeout_seconds
        try:
            r = httpx.post(url, headers=headers, json=body, timeout=wait)
            if r.status_code == 400 and search:
                # Some models refuse JSON mode together with tools: ask for JSON in text instead.
                body["generationConfig"].pop("responseMimeType")
                r = httpx.post(url, headers=headers, json=body, timeout=wait)
            if r.status_code in RETRYABLE:
                raise httpx.HTTPStatusError(f"HTTP {r.status_code}", request=r.request, response=r)
            r.raise_for_status()
            out = r.json()
            cand = out["candidates"][0]
            text = "".join(p.get("text", "") for p in cand["content"]["parts"])
            usage = out.get("usageMetadata", {})
            rec.input_tokens = usage.get("promptTokenCount", 0)
            rec.output_tokens = usage.get("candidatesTokenCount", 0)
            chunks = cand.get("groundingMetadata", {}).get("groundingChunks", [])
            sources = [
                {"index": i, "url": c["web"].get("uri", ""), "title": c["web"].get("title", "")}
                for i, c in enumerate(chunks)
                if "web" in c
            ]
            return GeminiResult(_parse_json_text(text), model, sources)
        except httpx.HTTPStatusError as e:
            rec.success, rec.error = False, f"HTTP {e.response.status_code}"
            errors.append(f"{model}: {rec.error}")
            if e.response.status_code not in RETRYABLE:
                break  # bad request/auth: another model will not help
        except (httpx.TransportError, json.JSONDecodeError, KeyError, IndexError) as e:
            rec.success, rec.error = False, f"{type(e).__name__}: {e}"[:500]
            errors.append(f"{model}: {rec.error}")
        finally:
            rec.latency_ms = int((time.monotonic() - started) * 1000)
            db.add(rec)
    raise LLMUnavailable("gemini: " + "; ".join(errors))
