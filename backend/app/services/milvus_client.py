from __future__ import annotations

from functools import lru_cache

from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import settings
from app.services.embeddings import get_model


COLLECTION_NAME = "document_chunks"


@retry(stop=stop_after_attempt(10), wait=wait_fixed(2))
def connect():
    connections.connect(host=settings.milvus_host, port=settings.milvus_port)


@lru_cache(maxsize=1)
def get_collection() -> Collection:
    connect()
    if not utility.has_collection(COLLECTION_NAME):
        dim = get_model().get_sentence_embedding_dimension()
        schema = CollectionSchema(
            fields=[
                FieldSchema("chunk_id", DataType.VARCHAR, is_primary=True, max_length=64),
                FieldSchema("document_id", DataType.VARCHAR, max_length=64),
                FieldSchema("page_number", DataType.INT64),
                FieldSchema("chunk_index", DataType.INT64),
                FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=dim),
            ],
            description="Chunks embeddings",
        )
        col = Collection(COLLECTION_NAME, schema)
        col.create_index(
            field_name="embedding",
            index_params={"index_type": "IVF_FLAT", "metric_type": "IP", "params": {"nlist": 128}},
        )
        col.load()
        return col

    col = Collection(COLLECTION_NAME)
    if not col.has_index():
        col.create_index(
            field_name="embedding",
            index_params={"index_type": "IVF_FLAT", "metric_type": "IP", "params": {"nlist": 128}},
        )
    # load коллекции может быть дорогим; делаем один раз за жизнь процесса
    col.load()
    return col


def insert_embeddings(rows: list[dict]):
    col = get_collection()
    col.insert(
        [
            [r["chunk_id"] for r in rows],
            [r["document_id"] for r in rows],
            [r.get("page_number") or 0 for r in rows],
            [r["chunk_index"] for r in rows],
            [r["embedding"] for r in rows],
        ]
    )
    col.flush()


def search_embeddings(vector: list[float], top_k: int = 8):
    col = get_collection()
    res = col.search(
        data=[vector],
        anns_field="embedding",
        param={"metric_type": "IP", "params": {"nprobe": 10}},
        limit=top_k,
        output_fields=["chunk_id", "document_id", "page_number", "chunk_index"],
    )
    hits = []
    for hit in res[0]:
        hits.append(
            {
                "chunk_id": hit.entity.get("chunk_id"),
                "document_id": hit.entity.get("document_id"),
                "page_number": int(hit.entity.get("page_number")),
                "chunk_index": int(hit.entity.get("chunk_index")),
                "score": float(hit.score),
            }
        )
    return hits
