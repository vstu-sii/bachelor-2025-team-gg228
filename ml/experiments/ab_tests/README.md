# A/B experiments (reranking)

Здесь лежит минимальная инфраструктура для A/B сравнения вариантов ранжирования на pairwise датасете формата:

```json
{"query":"...","positive":"...","negative":"..."}
```

## Варианты

См. `ml/experiments/ab_tests/variants.json`.

## Запуск (локально через контейнер reranker)

```bash
docker build -t poisk-reranker ./reranker
docker run --rm -v "$PWD":/w -w /w \
  -e HF_HOME=/w/models/hf -e HF_HUB_DISABLE_TELEMETRY=1 \
  poisk-reranker python ml/experiments/ab_tests/run_ab.py \
  --data backend/data/training/rerank.jsonl --limit 120 --shuffle-candidates

python ml/experiments/ab_tests/analyze_ab.py \
  --results ml/experiments/ab_tests/results.jsonl \
  --summary ml/experiments/ab_tests/results.summary.json \
  --out-md reports/quality-metrics.md
```

## Langfuse (опционально)

Если выставить:

- `LANGFUSE_TRACING_ENABLED=true`
- `LANGFUSE_PUBLIC_KEY=...`
- `LANGFUSE_SECRET_KEY=...`
- (при необходимости) `LANGFUSE_HOST=...`

то можно добавить флаг `--langfuse` к `run_ab.py`, и каждый пример будет отправляться как span `ab_rerank_eval`.

