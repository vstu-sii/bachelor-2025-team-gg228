from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
from typing import Any


TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> set[str]:
    toks = [t.lower() for t in TOKEN_RE.findall(text or "")]
    return {t for t in toks if len(t) >= 3}


def score_overlap(query: str, doc: str) -> float:
    a = _tokens(query)
    b = _tokens(doc)
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


@lru_cache(maxsize=8)
def _get_tokenizer(model_id: str):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(model_id)


@lru_cache(maxsize=8)
def _get_model(model_id: str):
    from transformers import AutoModelForSequenceClassification

    model = AutoModelForSequenceClassification.from_pretrained(model_id)
    model.eval()
    return model


def score_crossencoder(model_id: str, pairs: list[tuple[str, str]], max_length: int) -> list[float]:
    import torch

    tok = _get_tokenizer(model_id)
    model = _get_model(model_id)

    with torch.no_grad():
        batch = tok(
            [p[0] for p in pairs],
            [p[1] for p in pairs],
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        out = model(**batch).logits
        if out.shape[-1] == 1:
            probs = torch.sigmoid(out).squeeze(-1)
            return probs.cpu().tolist()
        probs = torch.softmax(out, dim=-1)
        return probs[:, -1].cpu().tolist()


@dataclass(frozen=True)
class Variant:
    id: str
    type: str
    model: str | None = None
    max_length: int = 256
    alpha: float = 0.8
    notes: str | None = None


def load_variants(path: Path) -> list[Variant]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    out: list[Variant] = []
    for v in obj.get("variants", []):
        out.append(
            Variant(
                id=str(v["id"]),
                type=str(v["type"]),
                model=(str(v["model"]) if v.get("model") else None),
                max_length=int(v.get("max_length", 256)),
                alpha=float(v.get("alpha", 0.8)),
                notes=(str(v.get("notes")) if v.get("notes") else None),
            )
        )
    if not out:
        raise SystemExit(f"No variants found in {path}")
    return out


def maybe_langfuse():
    enabled = os.getenv("LANGFUSE_TRACING_ENABLED", "").lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return None
    if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY"):
        return None
    try:
        from langfuse import Langfuse
    except Exception:
        return None
    return Langfuse()


def pick_winner(scores: list[float]) -> int:
    # index of max score; stable for ties (first max)
    best = 0
    best_s = scores[0] if scores else float("-inf")
    for i, s in enumerate(scores):
        if s > best_s:
            best_s = s
            best = i
    return best


def run_one_variant(v: Variant, query: str, candidates: list[str]) -> tuple[list[float], float, str | None]:
    started = time.perf_counter()
    err: str | None = None
    try:
        if v.type == "heuristic_overlap":
            scores = [score_overlap(query, c) for c in candidates]
        elif v.type == "crossencoder":
            if not v.model:
                raise ValueError("model is required for crossencoder")
            pairs = [(query, c) for c in candidates]
            scores = score_crossencoder(v.model, pairs, max_length=v.max_length)
        elif v.type == "hybrid":
            if not v.model:
                raise ValueError("model is required for hybrid")
            pairs = [(query, c) for c in candidates]
            model_scores = score_crossencoder(v.model, pairs, max_length=v.max_length)
            overlap_scores = [score_overlap(query, c) for c in candidates]
            a = float(v.alpha)
            scores = [a * ms + (1.0 - a) * os_ for ms, os_ in zip(model_scores, overlap_scores)]
        else:
            raise ValueError(f"Unknown variant type: {v.type}")
        return scores, (time.perf_counter() - started) * 1000, err
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        return [0.0 for _ in candidates], (time.perf_counter() - started) * 1000, err


def summarize_latencies(lat_ms: list[float]) -> dict[str, float]:
    if not lat_ms:
        return {"mean_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}
    lat_sorted = sorted(lat_ms)

    def q(p: float) -> float:
        if len(lat_sorted) == 1:
            return lat_sorted[0]
        idx = int(round((len(lat_sorted) - 1) * p))
        return lat_sorted[max(0, min(len(lat_sorted) - 1, idx))]

    return {
        "mean_ms": float(statistics.mean(lat_sorted)),
        "p95_ms": float(q(0.95)),
        "p99_ms": float(q(0.99)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="jsonl with {query,positive,negative}")
    ap.add_argument("--variants", default=str(Path(__file__).with_name("variants.json")))
    ap.add_argument("--out", default="ml/experiments/ab_tests/results.jsonl")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--shuffle-candidates", action="store_true", help="shuffle pos/neg order per row")
    ap.add_argument("--langfuse", action="store_true", help="emit spans if LANGFUSE_* env set")
    args = ap.parse_args()

    random.seed(args.seed)
    variants = load_variants(Path(args.variants))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lf = maybe_langfuse() if args.langfuse else None

    rows: list[dict[str, Any]] = []
    with open(args.data, "r", encoding="utf-8") as f:
        for line in f:
            if len(rows) >= args.limit:
                break
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            q = str(obj.get("query", "")).strip()
            pos = str(obj.get("positive", "")).strip()
            neg = str(obj.get("negative", "")).strip()
            if not q or not pos or not neg:
                continue
            rows.append({"query": q, "positive": pos, "negative": neg})

    if len(rows) < 50:
        raise SystemExit(f"Need >= 50 rows, got {len(rows)} (use --limit or another dataset)")

    per_variant_lat: dict[str, list[float]] = {v.id: [] for v in variants}
    per_variant_wins: dict[str, int] = {v.id: 0 for v in variants}
    per_variant_errors: dict[str, int] = {v.id: 0 for v in variants}

    with open(out_path, "w", encoding="utf-8") as out_f:
        for idx, r in enumerate(rows, start=1):
            query = r["query"]
            pos = r["positive"]
            neg = r["negative"]
            candidates = [pos, neg]
            truth_winner = 0  # pos should win

            order = [0, 1]
            if args.shuffle_candidates:
                random.shuffle(order)
                candidates = [candidates[i] for i in order]
                truth_winner = order.index(0)

            for v in variants:
                scores, lat_ms, err = run_one_variant(v, query, candidates)
                chosen = pick_winner(scores)
                win = 1 if chosen == truth_winner else 0

                per_variant_lat[v.id].append(lat_ms)
                per_variant_wins[v.id] += win
                if err:
                    per_variant_errors[v.id] += 1

                record = {
                    "row_id": idx,
                    "variant": v.id,
                    "variant_type": v.type,
                    "query_len": len(query),
                    "candidates_order": order,
                    "scores": scores,
                    "chosen_index": chosen,
                    "truth_index": truth_winner,
                    "win": win,
                    "latency_ms": lat_ms,
                    "error": err,
                }
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

                if lf:
                    with lf.start_as_current_span(
                        name="ab_rerank_eval",
                        input={"variant": v.id, "row_id": idx, "query_len": len(query), "candidates": len(candidates)},
                        metadata={"variant_type": v.type},
                    ) as span:
                        span.update(
                            output={
                                "scores": scores,
                                "chosen_index": chosen,
                                "truth_index": truth_winner,
                                "win": win,
                                "latency_ms": lat_ms,
                                "error": err,
                            }
                        )

    summary = []
    total = len(rows)
    for v in variants:
        wins = per_variant_wins[v.id]
        acc = wins / total if total else 0.0
        lats = summarize_latencies(per_variant_lat[v.id])
        summary.append(
            {
                "variant": v.id,
                "type": v.type,
                "accuracy": round(acc, 4),
                "wins": wins,
                "total": total,
                "errors": per_variant_errors[v.id],
                **{k: round(float(val), 2) for k, val in lats.items()},
            }
        )

    summary_path = out_path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps({"total_rows": total, "summary": summary}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote: {out_path}")
    print(f"Wrote: {summary_path}")


if __name__ == "__main__":
    main()

