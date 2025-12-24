from pydantic import BaseModel


class Candidate(BaseModel):
    document_id: str
    title: str
    score: float
    excerpt: str
    page_number: int | None = None


class RerankRequest(BaseModel):
    query: str
    candidates: list[Candidate]


class RerankResponseItem(Candidate):
    rerank_score: float

