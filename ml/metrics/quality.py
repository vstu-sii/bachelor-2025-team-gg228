from __future__ import annotations

from dataclasses import dataclass
import statistics
from typing import Iterable


@dataclass(frozen=True)
class VariantSummary:
    variant: str
    wins: int
    total: int
    errors: int
    accuracy: float
    mean_ms: float
    p95_ms: float
    p99_ms: float


def _quantile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    idx = int(round((len(sorted_vals) - 1) * p))
    idx = max(0, min(len(sorted_vals) - 1, idx))
    return float(sorted_vals[idx])


def summarize_variant(
    variant: str,
    wins: int,
    total: int,
    errors: int,
    latencies_ms: Iterable[float],
) -> VariantSummary:
    lat = sorted(float(x) for x in latencies_ms)
    mean_ms = float(statistics.mean(lat)) if lat else 0.0
    p95_ms = _quantile(lat, 0.95)
    p99_ms = _quantile(lat, 0.99)
    acc = (wins / total) if total else 0.0
    return VariantSummary(
        variant=variant,
        wins=wins,
        total=total,
        errors=errors,
        accuracy=float(acc),
        mean_ms=mean_ms,
        p95_ms=p95_ms,
        p99_ms=p99_ms,
    )

