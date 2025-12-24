from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path


def binom_two_sided_pvalue(n: int, k: int) -> float:
    """
    Two-sided binomial test p-value for sign test with p=0.5.
    Here k = number of successes out of n.
    """
    if n <= 0:
        return 1.0
    p = 0.5
    pmf = [math.comb(n, i) * (p**i) * ((1 - p) ** (n - i)) for i in range(n + 1)]
    obs = pmf[k]
    return float(sum(x for x in pmf if x <= obs + 1e-15))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="ml/experiments/ab_tests/results.jsonl")
    ap.add_argument("--summary", default="ml/experiments/ab_tests/results.summary.json")
    ap.add_argument("--out-md", default="reports/quality-metrics.md")
    args = ap.parse_args()

    summary = json.loads(Path(args.summary).read_text(encoding="utf-8"))
    total_rows = int(summary["total_rows"])
    variants = summary["summary"]

    # row_id -> variant -> win
    by_row: dict[int, dict[str, int]] = defaultdict(dict)
    with open(args.results, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            by_row[int(obj["row_id"])][str(obj["variant"])] = int(obj["win"])

    variant_ids = [v["variant"] for v in variants]
    pairwise = []
    for i in range(len(variant_ids)):
        for j in range(i + 1, len(variant_ids)):
            a = variant_ids[i]
            b = variant_ids[j]
            wins_a = 0
            wins_b = 0
            ties = 0
            for rid in range(1, total_rows + 1):
                wa = by_row.get(rid, {}).get(a)
                wb = by_row.get(rid, {}).get(b)
                if wa is None or wb is None:
                    continue
                if wa == wb:
                    ties += 1
                elif wa > wb:
                    wins_a += 1
                else:
                    wins_b += 1
            n = wins_a + wins_b
            pval = binom_two_sided_pvalue(n, wins_a) if n else 1.0
            pairwise.append({"a": a, "b": b, "wins_a": wins_a, "wins_b": wins_b, "ties": ties, "p_value": pval})

    out_path = Path(args.out_md)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# Quality metrics (A/B reranker strategies)")
    lines.append("")
    lines.append(f"Дата: 2025-12-24")
    lines.append("")
    lines.append("## Датасет")
    lines.append("")
    lines.append(f"- Формат: jsonl `{Path(args.results).as_posix()}` (pairwise: query/positive/negative)")
    lines.append(f"- Размер выборки: {total_rows} (>=50)")
    lines.append("")
    lines.append("## Метрики")
    lines.append("")
    lines.append("- `pairwise_accuracy`: доля примеров, где positive ранжируется выше negative.")
    lines.append("- `latency_ms`: время скоринга пары кандидатов (mean/p95/p99).")
    lines.append("- `error_rate`: доля ошибок при скоринге (exceptions/invalid outputs).")
    lines.append("")
    lines.append("## Результаты по вариантам")
    lines.append("")
    lines.append("| Variant | Type | Pairwise acc | Wins | Errors | Mean ms | p95 ms | p99 ms |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for v in variants:
        lines.append(
            f"| {v['variant']} | {v['type']} | {v['accuracy']:.4f} | {v['wins']}/{v['total']} | {v['errors']} | {v['mean_ms']:.2f} | {v['p95_ms']:.2f} | {v['p99_ms']:.2f} |"
        )
    lines.append("")
    lines.append("## Pairwise сравнение (sign test, приближённо)")
    lines.append("")
    lines.append("| A | B | A better | B better | Ties | p-value |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for p in pairwise:
        lines.append(f"| {p['a']} | {p['b']} | {p['wins_a']} | {p['wins_b']} | {p['ties']} | {p['p_value']:.4f} |")
    lines.append("")
    lines.append("## Интерпретация")
    lines.append("")
    lines.append("- Для принятия решения по «победителю» учитывайте одновременно `pairwise_accuracy` и `p95 latency`.")
    lines.append("- Если `p-value` > 0.05, различия могут быть статистически неубедительными на текущем объёме.")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()

