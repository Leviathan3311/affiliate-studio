import uuid

from sqlalchemy import func, select

from app.core import storage
from app.models import Brand, Service, WorkspaceMember
from tests.conftest import signup


def _delete(client, headers, name):
    return client.request("DELETE", "/api/v1/workspace", json={"name": name}, headers=headers)


def test_owner_deletes_workspace_with_its_data_and_media(client, db):
    keep = signup(client, workspace="Lotus Spa")
    gone = {**keep}
    r = client.post("/api/v1/workspaces", json={"name": "Menard"}, headers=keep)
    gone["X-Workspace-Id"] = ws_id = r.json()["id"]
    assert (
        client.post("/api/v1/services", json={"name": "Gội đầu"}, headers=gone).status_code == 201
    )
    storage.put_bytes(f"ws/{ws_id}/projects/p/a.png", b"x", "image/png")

    assert _delete(client, gone, "Lotus Spa").status_code == 422
    assert _delete(client, gone, " Menard ").status_code == 204

    names = [w["name"] for w in client.get("/api/v1/auth/me", headers=keep).json()["workspaces"]]
    assert names == ["Lotus Spa"]
    assert client.get("/api/v1/workspace", headers=gone).status_code == 404
    for model in (WorkspaceMember, Brand, Service):
        assert (
            db.scalar(
                select(func.count())
                .select_from(model)
                .where(model.workspace_id == uuid.UUID(ws_id))
            )
            == 0
        )
    assert not storage.local_path(f"ws/{ws_id}/projects/p/a.png").exists()
    assert client.get("/api/v1/workspace", headers=keep).status_code == 200


def test_only_owner_can_delete(client):
    owner = signup(client)
    r = client.post(
        "/api/v1/auth/register", json={"email": "admin@spa.vn", "password": "secret123"}
    )
    admin = {
        "Authorization": f"Bearer {r.json()['access_token']}",
        "X-Workspace-Id": owner["X-Workspace-Id"],
    }
    client.post(
        "/api/v1/workspace/members", json={"email": "admin@spa.vn", "role": "admin"}, headers=owner
    )
    assert _delete(client, admin, "Lotus Spa").status_code == 403
    assert client.get("/api/v1/workspace", headers=owner).status_code == 200


def test_delete_works_with_bookings_and_their_restrict_keys(client):
    from tests.test_bookings_and_rbac import START, book, setup_spa

    h, branch, service, customer = setup_spa(client)
    assert book(client, h, branch, service, customer, START).status_code == 201
    assert _delete(client, h, "Lotus Spa").status_code == 204
    assert client.get("/api/v1/workspace", headers=h).status_code == 404
