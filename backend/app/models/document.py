from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.models.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="processed", nullable=False)
    num_pages = Column(Integer, default=0, nullable=False)

