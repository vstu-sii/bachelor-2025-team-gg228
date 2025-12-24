from __future__ import annotations

import uuid
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chunk import Chunk
from app.models.document import Document


def ingest_document(db: Session, title: str, file: UploadFile, uploaded_by: str | None = None) -> Document:
    from app.services.embeddings import embed_texts
    from app.services.file_parser import chunk_text, extract_text
    from app.services.milvus_client import insert_embeddings

    data = file.file.read()
    text, num_pages = extract_text(file.filename, data)

    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix.lower()
    if ext not in {".pdf", ".docx"}:
        # extract_text уже валидирует тип, но пусть имя файла тоже будет корректным
        ext = ".bin"
    doc_id = str(uuid.uuid4())
    stored_filename = f"{doc_id}{ext}"
    path = settings.storage_dir / stored_filename
    with open(path, "wb") as f:
        f.write(data)

    doc = Document(
        id=doc_id,
        title=title,
        filename=stored_filename,
        content_type=file.content_type or "application/octet-stream",
        uploaded_by=uploaded_by,
        num_pages=num_pages,
        status="processed",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    chunks = list(chunk_text(text))
    vectors = embed_texts(chunks) if chunks else []

    chunk_rows: list[Chunk] = []
    milvus_rows: list[dict] = []
    for idx, (chunk_text_value, vec) in enumerate(zip(chunks, vectors)):
        chunk = Chunk(
            document_id=doc.id,
            chunk_index=idx,
            page_number=None,
            text=chunk_text_value,
        )
        db.add(chunk)
        db.flush()
        chunk_rows.append(chunk)
        milvus_rows.append(
            {
                "chunk_id": chunk.id,
                "document_id": doc.id,
                "page_number": 0,
                "chunk_index": idx,
                "embedding": vec,
            }
        )

    db.commit()
    if milvus_rows:
        insert_embeddings(milvus_rows)

    return doc
