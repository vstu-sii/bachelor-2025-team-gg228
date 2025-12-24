from __future__ import annotations

from fastapi.testclient import TestClient


def test_admin_documents_crud(client: TestClient, admin_token: str, monkeypatch):
    import app.services.ingest as ingest_service

    from app.models.document import Document

    def fake_ingest_document(db, title, file, uploaded_by):
        doc = Document(
            title=title,
            filename=(file.filename or "file.pdf"),
            content_type=(file.content_type or "application/octet-stream"),
            uploaded_by=uploaded_by,
            status="processed",
            num_pages=0,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    monkeypatch.setattr(ingest_service, "ingest_document", fake_ingest_document)

    headers = {"Authorization": f"Bearer {admin_token}"}

    empty = client.get("/api/admin/documents", headers=headers)
    assert empty.status_code == 200
    assert empty.json() == []

    upload = client.post(
        "/api/admin/documents",
        headers=headers,
        data={"title": "Док 1"},
        files={"file": ("doc.pdf", b"fake", "application/pdf")},
    )
    assert upload.status_code == 200, upload.text
    doc = upload.json()
    assert doc["title"] == "Док 1"

    listed = client.get("/api/admin/documents", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    delete = client.delete(f"/api/admin/documents/{doc['id']}", headers=headers)
    assert delete.status_code == 200
    assert delete.json() == {"ok": True}

    listed2 = client.get("/api/admin/documents", headers=headers)
    assert listed2.status_code == 200
    assert listed2.json() == []
