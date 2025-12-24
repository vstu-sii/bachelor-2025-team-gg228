from __future__ import annotations

import re
import time
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.search_event import SearchEvent
from app.schemas.search import SearchResultItem


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _make_excerpt(source_text: str, query: str, max_len: int = 420) -> str:
    text = _normalize_ws(source_text)
    if not text:
        return ""

    q = _normalize_ws(query).lower()
    tokens = [t for t in re.findall(r"\w+", q) if len(t) >= 4]
    seen: set[str] = set()
    uniq_tokens: list[str] = []
    for t in tokens:
        if t in seen:
            continue
        seen.add(t)
        uniq_tokens.append(t)
        if len(uniq_tokens) >= 8:
            break

    lower = text.lower()
    pos = -1
    for t in uniq_tokens:
        p = lower.find(t)
        if p != -1 and (pos == -1 or p < pos):
            pos = p

    if pos == -1:
        snippet = text[:max_len]
        if len(text) > max_len:
            snippet = snippet.rsplit(" ", 1)[0] + "…"
        return snippet

    window_before = 180
    window_after = 220
    start = max(0, pos - window_before)
    end = min(len(text), pos + window_after)

    # try align to sentence boundaries near start/end
    left_zone = text[max(0, start - 120) : start + 1]
    left_cut = max(left_zone.rfind(". "), left_zone.rfind("! "), left_zone.rfind("? "))
    if left_cut != -1:
        start = max(0, start - 120) + left_cut + 2

    right_zone = text[end : min(len(text), end + 120)]
    right_cut_candidates = [right_zone.find(". "), right_zone.find("! "), right_zone.find("? ")]
    right_cut = min([c for c in right_cut_candidates if c != -1], default=-1)
    if right_cut != -1:
        end = end + right_cut + 1

    snippet = text[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet


def search_sources(
    db: Session,
    text: str | None,
    file: UploadFile | None,
    user_id: str | None = None,
    min_similarity_percent: float | None = None,
    rerank: bool = True,
):
    from app.services.embeddings import embed_query
    from app.services.file_parser import extract_text
    from app.services.llm import rerank_sources
    from app.services.milvus_client import search_embeddings

    if not text and not file:
        return "", []

    started = time.perf_counter()
    has_file = bool(file)
    if file:
        data = file.file.read()
        text, _ = extract_text(file.filename, data)

    query_text = (text or "").strip()
    if not query_text:
        return "", []

    min_score: float | None = None
    if min_similarity_percent is not None:
        try:
            p = float(min_similarity_percent)
            p = 0.0 if p < 0 else 100.0 if p > 100 else p
            min_score = p / 100.0
        except Exception:
            min_score = None

    t0 = time.perf_counter()
    vector = embed_query(query_text)
    t_embed = time.perf_counter() - t0

    t1 = time.perf_counter()
    hits = search_embeddings(vector)
    t_milvus = time.perf_counter() - t1

    if min_score is not None:
        hits = [h for h in hits if h["score"] >= min_score]

    try:
        chunk_ids = [h["chunk_id"] for h in hits]
        doc_ids = list({h["document_id"] for h in hits})
        idxs = set()
        for h in hits:
            idxs.add(h["chunk_index"])
            idxs.add(h["chunk_index"] - 1)
            idxs.add(h["chunk_index"] + 1)
        idxs = {i for i in idxs if i >= 0}

        chunks = (
            db.query(Chunk)
            .filter(Chunk.id.in_(chunk_ids))
            .all()
        )
        chunks_by_id = {c.id: c for c in chunks}

        neighbor_chunks_by_key: dict[tuple[str, int], Chunk] = {}
        if doc_ids and idxs:
            neighbor_chunks = (
                db.query(Chunk)
                .filter(Chunk.document_id.in_(doc_ids))
                .filter(Chunk.chunk_index.in_(list(idxs)))
                .all()
            )
            neighbor_chunks_by_key = {(c.document_id, c.chunk_index): c for c in neighbor_chunks}

        docs = (
            db.query(Document)
            .filter(Document.id.in_([h["document_id"] for h in hits]))
            .all()
        )
        docs_by_id = {d.id: d for d in docs}

        results: list[dict] = []
        for h in hits:
            chunk = chunks_by_id.get(h["chunk_id"])
            doc = docs_by_id.get(h["document_id"])
            if not chunk or not doc:
                continue
            context_parts: list[str] = []
            prev = neighbor_chunks_by_key.get((chunk.document_id, chunk.chunk_index - 1))
            nxt = neighbor_chunks_by_key.get((chunk.document_id, chunk.chunk_index + 1))
            if prev:
                context_parts.append(prev.text)
            context_parts.append(chunk.text)
            if nxt:
                context_parts.append(nxt.text)
            excerpt = _make_excerpt("\n".join(context_parts), query_text)
            results.append(
                {
                    "document_id": doc.id,
                    "title": doc.title,
                    "score": h["score"],
                    "excerpt": excerpt,
                    "page_number": h.get("page_number") or None,
                }
            )

        if rerank:
            results = rerank_sources(query_text, results)
        duration_ms = int((time.perf_counter() - started) * 1000)

        # лёгкая диагностика производительности (видно в docker logs backend)
        try:
            import logging

            logging.getLogger("uvicorn.error").info(
                "search timing: embed=%.3fs milvus=%.3fs hits=%d rerank=%s",
                t_embed,
                t_milvus,
                len(hits),
                rerank and settings.use_custom_llm,
            )
        except Exception:
            pass

        event = SearchEvent(
            user_id=user_id,
            query_len=len(query_text),
            query_preview=query_text[:200],
            has_file=has_file,
            duration_ms=duration_ms,
            results_count=len(results),
        )
        db.add(event)
        db.commit()

        return query_text, [SearchResultItem(**r) for r in results]
    finally:
        pass
