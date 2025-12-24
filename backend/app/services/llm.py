from __future__ import annotations

import time
import requests

from app.core.config import settings
from app.observability.langfuse_client import get_langfuse
from app.observability.metrics import RERANK_CALLS_TOTAL, RERANK_DURATION_SECONDS


def rerank_sources(query: str, candidates: list[dict]) -> list[dict]:
    """
    Точка интеграции вашей LLM‑модели.
    candidates: [{"document_id":..., "title":..., "score":..., "excerpt":...}, ...]
    Возвращает те же элементы в нужном порядке/с доп. полями.
    """
    if not settings.use_custom_llm or not settings.custom_llm_endpoint:
        return candidates

    lf = get_langfuse()
    started = time.perf_counter()
    try:
        if lf:
            with lf.start_as_current_span(
                name="rerank",
                input={"query": query[:500], "candidates": len(candidates)},
            ) as span:
                resp = requests.post(
                    settings.custom_llm_endpoint,
                    json={"query": query, "candidates": candidates},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                span.update(output={"returned": len(data) if isinstance(data, list) else None})
        else:
            resp = requests.post(
                settings.custom_llm_endpoint,
                json={"query": query, "candidates": candidates},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        if isinstance(data, list):
            return data
    except Exception:
        return candidates
    finally:
        dur = time.perf_counter() - started
        RERANK_CALLS_TOTAL.inc()
        RERANK_DURATION_SECONDS.observe(dur)

    return candidates
