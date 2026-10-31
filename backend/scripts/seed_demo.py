"""Demo data for local development: `uv run python -m scripts.seed_demo`.

Runs the real pipeline (signed webhook -> worker ingest -> engagement agent). Without LLM keys
the agent output is canned and marked as demo; with GROQ/GEMINI keys set it calls them for real.
Login: demo@growthpilot.vn / demo12345
"""

import hashlib
import hmac
import json
import time
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app import worker
from app.ai import engagement_agent
from app.ai.llm import LLMResult
from app.core.config import get_settings
from app.main import app
from app.social import meta

EMAIL, PASSWORD = "demo@growthpilot.vn", "demo12345"
PAGE_ID = "100200300400"

CANNED = {
    "psid-lan": {
        "intent": "booking_request",
        "confidence": 0.92,
        "lead_score": 82,
        "summary": "Chị Lan muốn đặt chăm sóc da cơ bản chiều thứ Bảy, hỏi giá.",
        "reply": "Dạ chăm sóc da cơ bản bên em giá 450.000đ cho 60 phút ạ. Chiều thứ Bảy chị muốn "
        "đến khung giờ nào để em giữ chỗ cho chị nha?",
        "needs_human": False,
        "reason": "Hỏi giá và muốn đặt lịch cụ thể",
    },
    "psid-minh": {
        "intent": "promotion_inquiry",
        "confidence": 0.81,
        "lead_score": 55,
        "summary": "Anh Minh hỏi ưu đãi gội đầu dưỡng sinh cho khách mới.",
        "reply": "Dạ hiện bên em đang giảm còn 199k cho khách mới ạ.",
        "needs_human": False,
        "reason": "Hỏi ưu đãi",
    },
    "psid-thu": {
        "intent": "complaint",
        "confidence": 0.88,
        "lead_score": 20,
        "summary": "Chị Thu phàn nàn phải chờ 30 phút dù đã đặt lịch.",
        "reply": "Dạ em rất xin lỗi chị về việc phải chờ lâu. Em xin phép chuyển quản lý liên hệ "
        "chị ngay ạ.",
        "needs_human": True,
        "reason": "Khiếu nại, cần nhân viên",
    },
}

MESSAGES = [
    ("psid-lan", "Chào spa, cho em hỏi giá chăm sóc da cơ bản ạ", 95),
    ("psid-lan", "Chiều thứ 7 này còn chỗ không spa?", 92),
    ("psid-minh", "Gội đầu dưỡng sinh có ưu đãi cho khách mới không?", 50),
    ("psid-thu", "Hôm qua mình đặt 3h mà phải chờ gần 30 phút mới được làm", 20),
    ("psid-hoa", "Spa ở đường nào vậy ạ", 8),
]


def fake_llm(db, *, system, user, purpose, workspace_id, **_):
    for psid, data in CANNED.items():
        if any(text in user for p, text, _ in MESSAGES if p == psid):
            return LLMResult(dict(data), "demo", "canned")
    return LLMResult(
        {
            "intent": "location_inquiry",
            "confidence": 0.9,
            "lead_score": 30,
            "summary": "Khách hỏi địa chỉ spa.",
            "reply": "Dạ spa bên em ở 12 Trần Quốc Thảo, Phường Võ Thị Sáu, Quận 3 ạ.",
            "needs_human": False,
            "reason": "Hỏi địa chỉ",
        },
        "demo",
        "canned",
    )


def main() -> None:
    s = get_settings()
    if not (s.groq_api_key or s.gemini_api_key):
        engagement_agent.complete_json = fake_llm  # demo only
    # Meta profile lookup is off in dry-run mode; give the demo customers names.
    names = {
        "psid-lan": "Nguyễn Thị Lan",
        "psid-minh": "Trần Minh",
        "psid-thu": "Lê Thu",
        "psid-hoa": "Phạm Hoa",
    }
    meta.fetch_profile_name = lambda token, psid: names.get(psid, "")
    c = TestClient(app)
    r = c.post(
        "/api/v1/auth/register",
        json={"email": EMAIL, "password": PASSWORD, "full_name": "Ngọc Anh"},
    )
    if r.status_code == 409:
        print("demo user exists; nothing to do")
        return
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    ws = c.post("/api/v1/workspaces", json={"name": "Lotus Spa Quận 3"}, headers=h).json()
    h["X-Workspace-Id"] = ws["id"]
    c.put(
        "/api/v1/brand",
        headers=h,
        json={
            "name": "Lotus Spa Quận 3",
            "tone_of_voice": "Xưng em, gọi khách là chị/anh, nhẹ nhàng, ngắn gọn.",
            "hotline": "0903 123 456",
            "address": "12 Trần Quốc Thảo, Phường Võ Thị Sáu, Quận 3, TP.HCM",
            "opening_hours": "9:00 – 20:30, cả tuần",
            "description": "Spa chăm sóc da và thư giãn, 6 giường, có chỗ đỗ xe máy.",
            "forbidden_claims": "Không hứa trị dứt điểm mụn hay nám; không so sánh với spa khác.",
        },
    )
    branch = c.post("/api/v1/branches", headers=h, json={"name": "Quận 3", "capacity": 6}).json()
    services = [
        {"name": "Chăm sóc da cơ bản", "duration_minutes": 60, "price_min": 450000},
        {"name": "Massage body đá nóng", "duration_minutes": 90, "price_min": 650000},
        {
            "name": "Gội đầu dưỡng sinh",
            "duration_minutes": 45,
            "price_min": 180000,
            "promotion": "Giảm 20% cho khách lần đầu, áp dụng đến 30/11/2026",
        },
        {
            "name": "Triệt lông vùng nách",
            "duration_minutes": 30,
            "price_min": 300000,
            "price_max": 450000,
        },
    ]
    svc = [c.post("/api/v1/services", headers=h, json=x).json() for x in services]
    for title, content in [
        (
            "Có chỗ đỗ ô tô không?",
            "Spa có chỗ đỗ xe máy miễn phí; ô tô đỗ tại bãi Trần Quốc Thảo cách 50m.",
        ),
        ("Huỷ lịch thế nào?", "Báo trước 3 giờ để được đổi lịch miễn phí."),
        ("Thanh toán", "Nhận tiền mặt, chuyển khoản và thẻ."),
    ]:
        c.post("/api/v1/knowledge", headers=h, json={"title": title, "content": content})
    c.post(
        "/api/v1/integrations/social-accounts/manual",
        headers=h,
        json={
            "page_id": PAGE_ID,
            "name": "Lotus Spa Quận 3",
            "page_access_token": "EAAD" + "0" * 40,
        },
    )

    now = datetime.now(UTC)
    for i, (psid, text, minutes_ago) in enumerate(MESSAGES):
        ts = int((now - timedelta(minutes=minutes_ago)).timestamp() * 1000)
        payload = {
            "object": "page",
            "entry": [
                {
                    "id": PAGE_ID,
                    "time": ts,
                    "messaging": [
                        {
                            "sender": {"id": psid},
                            "recipient": {"id": PAGE_ID},
                            "timestamp": ts,
                            "message": {"mid": f"m_demo_{i}_{int(time.time())}", "text": text},
                        }
                    ],
                }
            ],
        }
        body = json.dumps(payload).encode()
        sig = "sha256=" + hmac.new(s.meta_app_secret.encode(), body, hashlib.sha256).hexdigest()
        c.post("/api/v1/webhooks/meta", content=body, headers={"X-Hub-Signature-256": sig})
    while worker.run_once():
        pass

    lan = next(
        x
        for x in c.get("/api/v1/conversations", headers=h).json()
        if x["customer_name"] == "Nguyễn Thị Lan"
    )
    start = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)
    c.post(
        "/api/v1/bookings",
        headers=h,
        json={
            "customer_id": lan["customer_id"],
            "branch_id": branch["id"],
            "service_id": svc[0]["id"],
            "start_at": start.isoformat(),
            "status": "confirmed",
            "conversation_id": lan["id"],
        },
    )
    print(f"seeded workspace {ws['id']} — login {EMAIL} / {PASSWORD}")


if __name__ == "__main__":
    main()
