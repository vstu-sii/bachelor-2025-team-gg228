from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.document import Document
from app.models.search_event import SearchEvent
from app.models.user import User
from app.schemas.metrics import MetricsOut, SearchEventOut

router = APIRouter(prefix="/admin/metrics", tags=["admin"])


@router.get("", response_model=MetricsOut)
def metrics(db: Session = Depends(get_db), _: object = Depends(require_admin)):
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    total_documents = db.query(func.count(Document.id)).scalar() or 0
    total_searches = db.query(func.count(SearchEvent.id)).scalar() or 0

    since = datetime.utcnow() - timedelta(hours=24)
    searches_24h = db.query(func.count(SearchEvent.id)).filter(SearchEvent.created_at >= since).scalar() or 0

    last = db.query(SearchEvent).order_by(SearchEvent.created_at.desc()).limit(50).all()
    return MetricsOut(
        total_users=total_users,
        active_users=active_users,
        total_documents=total_documents,
        total_searches=total_searches,
        searches_24h=searches_24h,
        last_events=[SearchEventOut.model_validate(x) for x in last],
    )

