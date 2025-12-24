import argparse
import json
import random

from sqlalchemy import create_engine
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--postgres", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    engine = create_engine(args.postgres, pool_pre_ping=True)

    with Session(engine) as db:
        rows = db.execute(
            sa_text(
                """
            SELECT c.document_id, c.chunk_index, c.text, d.title
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            ORDER BY random()
            LIMIT :limit
            """
            ),
            {"limit": args.limit},
        ).fetchall()

        if not rows:
            raise SystemExit("No chunks found in DB. Upload documents first.")

        by_doc = {}
        for r in rows:
            by_doc.setdefault(r[0], []).append(r)

        all_rows = rows[:]
        with open(args.out, "w", encoding="utf-8") as f:
            for doc_id, items in by_doc.items():
                for r in items:
                    chunk_text = (r[2] or "").strip()
                    if len(chunk_text) < 200:
                        continue
                    # "query" как короткое резюме: первые 200 символов
                    query = chunk_text[:200]
                    positive = chunk_text
                    # negative: чанк из другого документа
                    neg = random.choice([x for x in all_rows if x[0] != doc_id])[2]
                    neg = (neg or "").strip()
                    if len(neg) < 50:
                        continue
                    f.write(json.dumps({"query": query, "positive": positive, "negative": neg}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
