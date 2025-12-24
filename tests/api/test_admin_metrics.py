from __future__ import annotations

from fastapi.testclient import TestClient


def test_metrics_empty(client: TestClient, admin_token: str):
    res = client.get("/api/admin/metrics", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total_users"] >= 1
    assert data["total_documents"] == 0
    assert data["total_searches"] == 0
    assert isinstance(data["last_events"], list)
