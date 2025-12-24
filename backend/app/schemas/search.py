from pydantic import BaseModel


class SearchResultItem(BaseModel):
    document_id: str
    title: str
    score: float
    rerank_score: float | None = None
    excerpt: str
    page_number: int | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
