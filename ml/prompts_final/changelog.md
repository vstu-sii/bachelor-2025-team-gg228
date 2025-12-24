# Prompts / strategy changelog

## 2025-12-24

- Добавлена A/B инфраструктура для ранжирования (`ml/experiments/ab_tests/`).
- Прогон на `backend/data/training/rerank.jsonl` (N=120) показал:
  - `A_overlap_v1` (token overlap) — `pairwise_accuracy=1.0000`, очень низкая latency.
  - `B_rubert_tiny2_zero_shot` (base cross-encoder без обучения) — низкое качество.
  - `C_hybrid_v1` — близко к `A`, но значительно медленнее.
- Зафиксирован текущий победитель как `A_overlap_v1` в `ml/prompts_final/strategy.json`.

Ограничение: результаты на текущем датасете могут быть переоценены из-за “утечки” (positive тексты могут содержать много слов из query). Следующий шаг — собрать более жёсткий eval set.

