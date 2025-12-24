from __future__ import annotations

from fastapi.testclient import TestClient


def test_admin_can_create_and_update_user(client: TestClient, admin_token: str):
    create = client.post(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": "new@example.com", "password": "password123", "role": "user", "is_active": True},
    )
    assert create.status_code == 200, create.text
    user = create.json()
    assert user["email"] == "new@example.com"
    assert user["role"] == "user"
    assert user["is_active"] is True

    user_id = user["id"]
    patch = client.patch(
        f"/api/admin/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "admin", "is_active": False},
    )
    assert patch.status_code == 200, patch.text
    updated = patch.json()
    assert updated["role"] == "admin"
    assert updated["is_active"] is False

    login = client.post("/api/auth/login", json={"email": "new@example.com", "password": "password123"})
    assert login.status_code == 400
