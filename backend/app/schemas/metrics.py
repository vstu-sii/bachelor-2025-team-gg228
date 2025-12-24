from datetime import datetime

from pydantic import BaseModel


class SearchEventOut(BaseModel):
    id: str
    created_at: datetime
    user_id: str | None = None
    query_len: int
    query_preview: str | None = None
    has_file: bool
    duration_ms: int
    results_count: int

    class Config:
        from_attributes = True


class MetricsOut(BaseModel):
    total_users: int
    active_users: int
    total_documents: int
    total_searches: int
    searches_24h: int
    last_events: list[SearchEventOut]

