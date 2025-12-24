import logging
import threading
import time
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from prometheus_fastapi_instrumentator import Instrumentator

from app.api.router import api_router
from app.auth.security import get_password_hash
from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.models.base import Base
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.search_event import SearchEvent
from app.models.user import User
from sqlalchemy import text
from sqlalchemy import inspect
from app.services.embeddings import get_model
from app.services.milvus_client import get_collection
from app.observability.metrics import (
    ACTIVE_USERS,
    SEARCHES_24H,
    TOTAL_DOCUMENTS,
    TOTAL_SEARCHES,
    TOTAL_USERS,
)
from sqlalchemy import func


app = FastAPI(title=settings.app_name)
logger = logging.getLogger("uvicorn.error")

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    insp = inspect(engine)
    if "users" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("users")}
        with engine.begin() as conn:
            if "is_active" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"))
            if "created_at" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT NOW()"))

    # Warm up heavy deps so first request doesn't hang behind proxy timeouts.
    try:
        get_model()
        logger.info("Embedding model warmed up")
    except Exception as e:
        logger.warning("Embedding model warmup failed: %s", e)

    def _milvus_warmup():
        try:
            get_collection()
            logger.info("Milvus collection ready")
        except Exception as e:
            logger.warning("Milvus warmup failed: %s", e)

    # Не блокируем startup: Milvus/gRPC иногда стартует медленно.
    threading.Thread(target=_milvus_warmup, daemon=True).start()

    def _update_business_metrics():
        while True:
            db = SessionLocal()
            try:
                total_users = db.query(func.count(User.id)).scalar() or 0
                active_users = db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
                total_documents = db.query(func.count(Document.id)).scalar() or 0
                total_searches = db.query(func.count(SearchEvent.id)).scalar() or 0
                since = datetime.utcnow() - timedelta(hours=24)
                searches_24h = db.query(func.count(SearchEvent.id)).filter(SearchEvent.created_at >= since).scalar() or 0

                TOTAL_USERS.set(total_users)
                ACTIVE_USERS.set(active_users)
                TOTAL_DOCUMENTS.set(total_documents)
                TOTAL_SEARCHES.set(total_searches)
                SEARCHES_24H.set(searches_24h)
            except Exception as e:
                logger.warning("Business metrics update failed: %s", e)
            finally:
                db.close()
            time.sleep(30)

    threading.Thread(target=_update_business_metrics, daemon=True).start()

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == settings.panel_email).first()
        if not admin:
            admin = User(
                email=settings.panel_email,
                hashed_password=get_password_hash(settings.panel_password),
                role="admin",
            )
            db.add(admin)
            db.commit()
        else:
            admin.role = "admin"
            if not (admin.hashed_password or "").startswith("$pbkdf2-sha256$"):
                admin.hashed_password = get_password_hash(settings.panel_password)
                db.commit()
    finally:
        db.close()
