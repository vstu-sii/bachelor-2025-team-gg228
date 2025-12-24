from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import importlib
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = (REPO_ROOT / "backend").resolve()
# Ensure our backend package is first on sys.path (CI sometimes pre-populates paths).
sys.path = [p for p in sys.path if Path(p or ".").resolve() != BACKEND_DIR]
sys.path.insert(0, str(BACKEND_DIR))

# If some dependency imported a different top-level `app` package before we adjust sys.path,
# force reload from our backend/app package.
importlib.invalidate_caches()
for name in list(sys.modules.keys()):
    if name == "app" or name.startswith("app."):
        sys.modules.pop(name, None)


@pytest.fixture
def app_and_db(monkeypatch) -> tuple[FastAPI, sessionmaker]:
    from app.api.router import api_router
    from app.db.session import get_db
    from app.models.base import Base

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(api_router)
    app.dependency_overrides[get_db] = override_get_db
    return app, TestingSessionLocal


@pytest.fixture
def client(app_and_db) -> Generator[TestClient, None, None]:
    app, _ = app_and_db
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db(app_and_db) -> Generator[Session, None, None]:
    _, SessionLocal = app_and_db
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def admin_token(client: TestClient, db: Session) -> str:
    from app.auth.security import get_password_hash
    from app.core.config import settings
    from app.models.user import User

    admin = User(
        email=settings.panel_email,
        hashed_password=get_password_hash(settings.panel_password),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()

    res = client.post("/api/auth/login", json={"email": settings.panel_email, "password": settings.panel_password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def user_token(client: TestClient) -> str:
    res = client.post("/api/auth/register", json={"email": "user@example.com", "password": "password123"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]
