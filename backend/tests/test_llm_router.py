import httpx
import pytest

from app.ai import llm
from app.ai.engagement import extract_prices
from app.config import get_settings


@pytest.fixture
def keys(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "groq_api_key", "g")
    monkeypatch.setattr(s, "gemini_api_key", "m")


def _rate_limited(*a):
    req = httpx.Request("POST", "https://api.groq.com")
    raise httpx.HTTPStatusError("429", request=req, response=httpx.Response(429, request=req))


def test_falls_back_to_gemini_on_groq_429(db, keys, monkeypatch):
    seen = []
    monkeypatch.setitem(llm._PROVIDERS, "groq", (_rate_limited, *llm._PROVIDERS["groq"][1:]))
    monkeypatch.setitem(
        llm._PROVIDERS,
        "gemini",
        (lambda s, u: (seen.append(u) or {"ok": 1}, 10, 5), *llm._PROVIDERS["gemini"][1:]),
    )
    out = llm.complete_json(db, system="s", user="gọi 0987654321", purpose="t", workspace_id=None)
    assert out.provider == "gemini" and out.data == {"ok": 1}
    assert seen == ["gọi [SĐT]"]  # PII masked before leaving the server
    db.flush()
    from app.models import AIUsageRecord

    recs = db.query(AIUsageRecord).order_by(AIUsageRecord.provider.desc()).all()
    assert [(r.provider, r.success) for r in recs] == [("groq", False), ("gemini", True)]


def test_no_keys_raises(db):
    with pytest.raises(llm.LLMUnavailable):
        llm.complete_json(db, system="s", user="u", purpose="t", workspace_id=None)


def test_extract_prices():
    assert extract_prices("giá 450.000đ, combo 1,2 triệu, còn 199k, 90 phút") == {
        450000,
        1200000,
        199000,
    }
    # units must be whole words: "12 Trần Quốc Thảo" is an address, not 12 triệu
    assert extract_prices("Spa ở 12 Trần Quốc Thảo, 3 tầng") == set()
