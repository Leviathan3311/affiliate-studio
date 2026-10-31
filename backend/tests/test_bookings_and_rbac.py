from datetime import UTC, datetime, timedelta

from tests.conftest import signup

START = datetime(2026, 11, 2, 3, 0, tzinfo=UTC)


def setup_spa(client, capacity=1):
    h = signup(client)
    branch = client.post(
        "/api/v1/branches", json={"name": "Q1", "capacity": capacity}, headers=h
    ).json()
    service = client.post(
        "/api/v1/services",
        json={"name": "Massage", "duration_minutes": 90, "price_min": 500000},
        headers=h,
    ).json()
    customer = client.post("/api/v1/customers", json={"display_name": "Chị Lan"}, headers=h).json()
    return h, branch, service, customer


def book(client, h, branch, service, customer, start, **kw):
    return client.post(
        "/api/v1/bookings",
        json={
            "customer_id": customer["id"],
            "branch_id": branch["id"],
            "service_id": service["id"],
            "start_at": start.isoformat(),
            **kw,
        },
        headers=h,
    )


def test_capacity_prevents_double_booking(client):
    h, branch, service, customer = setup_spa(client, capacity=1)
    first = book(client, h, branch, service, customer, START)
    assert first.status_code == 201
    assert first.json()["end_at"].startswith("2026-11-02T04:30")
    assert first.json()["expected_value"] == 500000
    # overlaps 03:00-04:30
    assert book(client, h, branch, service, customer, START + timedelta(hours=1)).status_code == 409
    # back-to-back is fine
    assert (
        book(client, h, branch, service, customer, START + timedelta(minutes=90)).status_code == 201
    )
    # cancelled bookings free the slot
    client.patch(f"/api/v1/bookings/{first.json()['id']}", json={"status": "cancelled"}, headers=h)
    assert book(client, h, branch, service, customer, START).status_code == 201


def test_status_transitions_and_revenue(client):
    h, branch, service, customer = setup_spa(client)
    b = book(client, h, branch, service, customer, START).json()
    url = f"/api/v1/bookings/{b['id']}"
    assert client.patch(url, json={"status": "completed"}, headers=h).status_code == 409
    assert client.patch(url, json={"actual_revenue": 1}, headers=h).status_code == 409
    for s in ("confirmed", "arrived"):
        assert client.patch(url, json={"status": s}, headers=h).status_code == 200
    r = client.patch(url, json={"status": "completed", "actual_revenue": 650000}, headers=h)
    assert r.status_code == 200 and r.json()["actual_revenue"] == 650000

    lead = client.get("/api/v1/leads", headers=h).json()[0]
    assert lead["status"] == "booked"
    ov = client.get("/api/v1/analytics/overview", headers=h).json()
    assert ov["bookings_total"] == 1 and ov["actual_revenue"] == 650000
    assert ov["lead_to_booking_rate"] == 1.0


def test_rbac_marketing_cannot_touch_inbox_or_settings(client):
    owner = signup(client)
    r = client.post("/api/v1/auth/register", json={"email": "mkt@spa.vn", "password": "secret123"})
    mkt = {
        "Authorization": f"Bearer {r.json()['access_token']}",
        "X-Workspace-Id": owner["X-Workspace-Id"],
    }
    assert (
        client.post(
            "/api/v1/workspace/members",
            json={"email": "mkt@spa.vn", "role": "marketing"},
            headers=owner,
        ).status_code
        == 201
    )
    assert client.get("/api/v1/conversations", headers=mkt).status_code == 403
    assert (
        client.patch("/api/v1/workspace", json={"reply_mode": "auto"}, headers=mkt).status_code
        == 403
    )
    assert client.post("/api/v1/services", json={"name": "Gội đầu"}, headers=mkt).status_code == 201


def test_last_owner_cannot_be_demoted(client):
    owner = signup(client)
    me = client.get("/api/v1/auth/me", headers=owner).json()
    r = client.patch(f"/api/v1/workspace/members/{me['id']}", json={"role": "admin"}, headers=owner)
    assert r.status_code == 409


def test_settings_validation(client):
    h = signup(client)
    assert (
        client.patch("/api/v1/workspace", json={"active_start": "25:00"}, headers=h).status_code
        == 422
    )
    assert (
        client.patch("/api/v1/workspace", json={"timezone": "Mars/Base"}, headers=h).status_code
        == 422
    )
    r = client.patch("/api/v1/workspace", json={"active_start": "07:30"}, headers=h)
    assert r.status_code == 200 and r.json()["active_start"] == "07:30"
