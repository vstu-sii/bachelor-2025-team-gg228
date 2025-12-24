from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import get_optional_user
from app.db.session import get_db
from app.models.user import User
from app.observability.langfuse_client import get_langfuse
from app.observability.metrics import SEARCH_DURATION_SECONDS, SEARCH_REQUESTS_TOTAL
from app.schemas.search import SearchResponse
from sqlalchemy.orm import Session
import time

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    min_similarity_percent: float | None = Form(default=None),
    rerank: bool = Form(default=True),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    mode = "rerank" if rerank else "baseline"
    started = time.perf_counter()
    SEARCH_REQUESTS_TOTAL.labels(mode=mode).inc()

    lf = get_langfuse()
    from app.services.search import search_sources
    if lf:
        with lf.start_as_current_span(
            name="search",
            input={"has_file": bool(file), "text_len": len(text or ""), "min_similarity_percent": min_similarity_percent, "rerank": rerank},
            metadata={"user_id": (user.id if user else None)},
        ) as span:
            query_text, results = search_sources(
                db=db,
                text=text,
                file=file,
                user_id=(user.id if user else None),
                min_similarity_percent=min_similarity_percent,
                rerank=rerank,
            )
            span.update(output={"results": len(results)})
    else:
        query_text, results = search_sources(
            db=db,
            text=text,
            file=file,
            user_id=(user.id if user else None),
            min_similarity_percent=min_similarity_percent,
            rerank=rerank,
        )

    SEARCH_DURATION_SECONDS.labels(mode=mode).observe(time.perf_counter() - started)
    return SearchResponse(query=query_text, results=results)
