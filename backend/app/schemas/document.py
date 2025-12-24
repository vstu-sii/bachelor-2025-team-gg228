from datetime import datetime
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    title: str
    filename: str
    content_type: str
    uploaded_at: datetime
    status: str
    num_pages: int

    class Config:
        from_attributes = True

