from __future__ import annotations

import argparse

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.chunk import Chunk
from app.services.embeddings import embed_texts
from app.services.milvus_client import COLLECTION_NAME, connect, insert_embeddings


def batched(items: list, batch_size: int):
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=64)
    args = ap.parse_args()

    db: Session = SessionLocal()
    try:
        chunks = db.query(Chunk).order_by(Chunk.document_id.asc(), Chunk.chunk_index.asc()).all()
        if not chunks:
            print("No chunks found. Upload documents first.")
            return

        connect()
        # NB: мы не делаем drop коллекции автоматически, чтобы не сносить данные случайно.
        # Если Milvus пустой (после очистки volumes) — вставка просто создаст коллекцию.
        print(f"Reindexing {len(chunks)} chunks into Milvus collection '{COLLECTION_NAME}' ...")

        total = 0
        for batch in batched(chunks, args.batch_size):
            texts = [c.text for c in batch]
            vectors = embed_texts(texts)
            rows = []
            for c, v in zip(batch, vectors):
                rows.append(
                    {
                        "chunk_id": c.id,
                        "document_id": c.document_id,
                        "page_number": c.page_number or 0,
                        "chunk_index": c.chunk_index,
                        "embedding": v,
                    }
                )
            insert_embeddings(rows)
            total += len(rows)
            print(f"  inserted: {total}/{len(chunks)}")

        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

