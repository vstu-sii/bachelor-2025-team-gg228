from __future__ import annotations

import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, Text

from app.models.base import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    text = Column(Text, nullable=False)

