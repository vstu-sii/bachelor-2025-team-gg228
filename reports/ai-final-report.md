# Итоговый AI отчёт (A/B + метрики качества)

Дата: 2025-12-24

## 1) Что сравнивали

В продукте “улучшенный поиск” реализован как опциональное переранжирование результатов. Для текущей версии проекта “промпты” как генеративный слой не являются обязательным компонентом, поэтому в качестве A/B вариантов сравнивались **стратегии ранжирования** (proxy для “prompt/model variants”):

- `A_overlap_v1`: эвристика по пересечению токенов (Jaccard overlap).
- `B_rubert_tiny2_zero_shot`: cross-encoder `cointegrated/rubert-tiny2` без дообучения.
- `C_hybrid_v1`: смешивание model score + overlap.

Конфиг вариантов: `ml/experiments/ab_tests/variants.json`.

## 2) Датасет и протокол

- Датасет: `backend/data/training/rerank.jsonl`
- Протокол: pairwise сравнение (`query`, `positive`, `negative`), кандидаты перемешиваются (`--shuffle-candidates`) для исключения bias по позиции.
- Объём: N=120 примеров (требование 50+ выполнено).
- Инструменты:
  - прогон: `ml/experiments/ab_tests/run_ab.py`
  - анализ: `ml/experiments/ab_tests/analyze_ab.py`
  - опциональная трассировка/логирование в Langfuse: `--langfuse`

## 3) Метрики качества

Зафиксированы и посчитаны:

- `pairwise_accuracy` — насколько часто positive ранжируется выше negative.
- `latency_ms` — mean/p95/p99 на скоринг пары кандидатов.
- `error_rate` — доля ошибок скоринга.

Сводка: `reports/quality-metrics.md`.

## 4) Итоги A/B

- На текущем датасете победил `A_overlap_v1` (максимальная `pairwise_accuracy` при минимальной latency).
- `B_rubert_tiny2_zero_shot` показал низкое качество, что ожидаемо (у base модели classifier head не обучен под задачу).
- `C_hybrid_v1` почти повторяет качество `A`, но медленнее.

Текущий выбор зафиксирован в `ml/prompts_final/strategy.json`.

## 5) Важное ограничение (качество оценки)

Текущая выборка выглядит **слишком простой**: высокая лексическая близость positive к query может приводить к завышению метрик у overlap-эвристики. Это означает:

- `pairwise_accuracy` на этом датасете **не гарантирует** улучшение качества в реальном поиске по базе документов.

## 6) Рекомендации по улучшению экспериментов

1) Собрать более репрезентативный eval set:
   - более “жёсткие” negative (лексически похожие, но нерелевантные),
   - 20–50 ручных кейсов из домена,
   - кандидаты >2 (top‑K из retrieval), чтобы считать nDCG/MRR.
2) Для model-based rerank:
   - дообучить cross-encoder на доменном датасете,
   - сравнивать baseline vs rerank на одинаковом наборе запросов.
3) Если подключается LLM-реранкер:
   - фиксировать schema-output, считать `invalid_output_rate` (proxy hallucination rate),
   - логировать в Langfuse версии “prompt/model” и latency.

