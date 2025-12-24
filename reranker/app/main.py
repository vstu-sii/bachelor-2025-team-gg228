import time
from fastapi import FastAPI

from app.model import score_pairs
from app.model import get_model as _get_model
from app.model import get_tokenizer as _get_tokenizer
from app.observability import get_langfuse
from app.schemas import RerankRequest, RerankResponseItem

app = FastAPI(title="Reranker")

@app.on_event("startup")
def warmup():
    # preload model/tokenizer to avoid first-request stall
    _get_tokenizer()
    _get_model()


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/rerank", response_model=list[RerankResponseItem])
def rerank(req: RerankRequest):
    query = (req.query or "").strip()
    if not query or not req.candidates:
        return []

    lf = get_langfuse()
    started = time.perf_counter()
    pairs = [(query, c.excerpt or "") for c in req.candidates]
    if lf:
        with lf.start_as_current_span(
            name="reranker_infer",
            input={"candidates": len(pairs), "query_len": len(query)},
        ) as span:
            scores = score_pairs(pairs)
            span.update(output={"duration_ms": int((time.perf_counter() - started) * 1000)})
    else:
        scores = score_pairs(pairs)
    items = []
    for c, s in zip(req.candidates, scores):
        items.append(RerankResponseItem(**c.model_dump(), rerank_score=float(s)))

    items.sort(key=lambda x: (x.rerank_score, x.score), reverse=True)
    return items
