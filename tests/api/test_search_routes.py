from __future__ import annotations

from fastapi.testclient import TestClient


def test_search_empty_request_returns_empty_payload(client: TestClient, monkeypatch):
    import app.services.search as search_service

    def fake_search_sources(*args, **kwargs):
        return "", []

    monkeypatch.setattr(search_service, "search_sources", fake_search_sources)

    res = client.post("/api/search", files={})
    assert res.status_code == 200
    assert res.json() == {"query": "", "results": []}

    res2 = client.post("/api/baseline/search", files={})
    assert res2.status_code == 200
    assert res2.json() == {"query": "", "results": []}


def test_search_with_text_returns_results(client: TestClient, monkeypatch):
    import app.services.search as search_service

    from app.schemas.search import SearchResultItem

    def fake_search_sources(db, text, file, user_id=None, min_similarity_percent=None, rerank=True):
        return (text or "").strip(), [
            SearchResultItem(
                document_id="doc-1",
                title="Документ 1",
                score=0.9,
                excerpt="Фрагмент текста",
                page_number=1,
            )
        ]

    monkeypatch.setattr(search_service, "search_sources", fake_search_sources)

    res = client.post("/api/search", data={"text": "запрос", "min_similarity_percent": "30", "rerank": "true"})
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["query"] == "запрос"
    assert len(payload["results"]) == 1
    assert payload["results"][0]["document_id"] == "doc-1"
