from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.models.base import Base


class SearchEvent(Base):
    __tablename__ = "search_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(String, nullable=True, index=True)
    query_len = Column(Integer, default=0, nullable=False)
    query_preview = Column(Text, nullable=True)
    has_file = Column(Boolean, default=False, nullable=False)
    duration_ms = Column(Integer, default=0, nullable=False)
    results_count = Column(Integer, default=0, nullable=False)

