# Quality metrics (A/B reranker strategies)

Дата: 2025-12-24

## Датасет

- Формат: jsonl `ml/experiments/ab_tests/results.jsonl` (pairwise: query/positive/negative)
- Размер выборки: 120 (>=50)

## Метрики

- `pairwise_accuracy`: доля примеров, где positive ранжируется выше negative.
- `latency_ms`: время скоринга пары кандидатов (mean/p95/p99).
- `error_rate`: доля ошибок при скоринге (exceptions/invalid outputs).

## Результаты по вариантам

| Variant | Type | Pairwise acc | Wins | Errors | Mean ms | p95 ms | p99 ms |
|---|---|---:|---:|---:|---:|---:|---:|
| A_overlap_v1 | heuristic_overlap | 1.0000 | 120/120 | 0 | 0.17 | 0.23 | 0.28 |
| B_rubert_tiny2_zero_shot | crossencoder | 0.1917 | 23/120 | 0 | 38.71 | 15.56 | 23.99 |
| C_hybrid_v1 | hybrid | 0.9917 | 119/120 | 0 | 14.55 | 15.40 | 15.79 |

## Pairwise сравнение (sign test, приближённо)

| A | B | A better | B better | Ties | p-value |
|---|---|---:|---:|---:|---:|
| A_overlap_v1 | B_rubert_tiny2_zero_shot | 97 | 0 | 23 | 0.0000 |
| A_overlap_v1 | C_hybrid_v1 | 1 | 0 | 119 | 1.0000 |
| B_rubert_tiny2_zero_shot | C_hybrid_v1 | 0 | 96 | 24 | 0.0000 |

## Интерпретация

- Для принятия решения по «победителю» учитывайте одновременно `pairwise_accuracy` и `p95 latency`.
- Если `p-value` > 0.05, различия могут быть статистически неубедительными на текущем объёме.
