# Reranker (обучение/эксперименты baseline)

Цель: дообучить небольшую русскоязычную модель на задачу **переранжирования источников**.

## Что нужно

- Python 3.11+
- (желательно) GPU, но можно и CPU для small‑моделей

## Базовый пайплайн

1) Сгенерировать датасет из вашей базы документов:

```
python training/generate_dataset.py --postgres "$POSTGRES_DSN" --out training/data/rerank.jsonl
```

2) Обучить модель:

```
python training/train_reranker.py --data training/data/rerank.jsonl --out models/reranker
```

Проверить baseline-метрику (pairwise accuracy):

```
python training/evaluate_reranker.py --data training/data/rerank.jsonl --model models/reranker
```

3) Подключить в docker:

- примонтировать `./models/reranker` в `reranker` сервис
- указать `RERANKER_MODEL_PATH=/models/reranker`

## Формат датасета (jsonl)

Каждая строка:

```json
{"query":"...","positive":"...","negative":"..."}
```
