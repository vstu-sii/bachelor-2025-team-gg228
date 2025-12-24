import time
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user
from app.db.session import get_db
from app.models.user import User
from app.observability.langfuse_client import get_langfuse
from app.observability.metrics import SEARCH_DURATION_SECONDS, SEARCH_REQUESTS_TOTAL
from app.schemas.search import SearchResponse

router = APIRouter(prefix="/baseline", tags=["baseline"])


@router.post("/search", response_model=SearchResponse)
def baseline_search(
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    min_similarity_percent: float | None = Form(default=None),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    started = time.perf_counter()
    SEARCH_REQUESTS_TOTAL.labels(mode="baseline").inc()
    lf = get_langfuse()
    from app.services.search import search_sources
    if lf:
        with lf.start_as_current_span(
            name="baseline_search",
            input={"has_file": bool(file), "text_len": len(text or ""), "min_similarity_percent": min_similarity_percent},
            metadata={"user_id": (user.id if user else None)},
        ) as span:
            query_text, results = search_sources(
                db=db,
                text=text,
                file=file,
                user_id=(user.id if user else None),
                min_similarity_percent=min_similarity_percent,
                rerank=False,
            )
            span.update(output={"results": len(results)})
    else:
        query_text, results = search_sources(
            db=db,
            text=text,
            file=file,
            user_id=(user.id if user else None),
            min_similarity_percent=min_similarity_percent,
            rerank=False,
        )

    SEARCH_DURATION_SECONDS.labels(mode="baseline").observe(time.perf_counter() - started)
    # baseline = без reranker
    return SearchResponse(query=query_text, results=results)
