from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"ok": True}


def test_register_and_me(client: TestClient):
    res = client.post("/api/auth/register", json={"email": "a@example.com", "password": "password123"})
    assert res.status_code == 200
    token = res.json()["access_token"]

    me = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    data = me.json()
    assert data["email"] == "a@example.com"
    assert data["role"] == "user"
    assert data["is_active"] is True


def test_login_wrong_password_returns_400(client: TestClient):
    client.post("/api/auth/register", json={"email": "b@example.com", "password": "password123"})
    res = client.post("/api/auth/login", json={"email": "b@example.com", "password": "wrong"})
    assert res.status_code == 400
    assert res.json()["detail"] == "Incorrect email or password"


def test_admin_routes_require_auth(client: TestClient):
    res = client.get("/api/admin/users")
    assert res.status_code == 401


def test_admin_routes_forbidden_for_regular_user(client: TestClient, user_token: str):
    res = client.get("/api/admin/users", headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 403
    assert res.json()["detail"] == "Admin only"
