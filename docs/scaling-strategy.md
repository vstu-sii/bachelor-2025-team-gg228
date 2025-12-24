# Scaling strategy

Дата: 2025-12-24

## 1) Цели

- Масштабирование чтения (поиск) без деградации p95/p99.
- Устойчивость к сбоям (auto-restart, healthchecks, алерты).
- Разделение “быстрого пути” поиска и фоновых задач (ингест/индексация).

## 2) Текущая архитектура (compose)

- `nginx` — единая точка входа.
- `backend` (FastAPI) — API, парсинг, чанкинг, эмбеддинги, поиск, auth.
- `postgredb` — метаданные/пользователи/события.
- `standalone` (Milvus) — векторный индекс.
- `reranker` — переранжирование (опционально).
- Observability: `prometheus`, `grafana`, `alertmanager`, `cadvisor`, `postgres-exporter`.

## 3) Стратегия масштабирования по компонентам

### Backend (FastAPI)

**Горизонтально**:

- Вынести state из приложения (уже сделано: Postgres/Milvus).
- Добавить реплики `backend` и балансировку через `nginx`.
- Разделить эндпоинты “search” и “ingest”, если ingest начинает мешать поиску (в отдельный воркер/очередь).

**Производительность**:

- Греть модели при старте (уже есть warmup для эмбеддингов).
- Кешировать эмбеддинги частых запросов (опционально через Redis).
- Включить лимиты на размер файла и таймауты на обработку.

### Reranker

- Масштабировать отдельным deployment/replicas.
- Для стабильности: фиксировать `RERANKER_MODEL_PATH` и прогревать модель при старте.
- При росте нагрузки — рассмотреть batching на уровне сервиса (пакетирование кандидатов) и/или GPU.

### Postgres

- На MVP: вертикальное масштабирование + регулярные бэкапы.
- Дальше: read replicas для чтения метрик/аналитики, pgbouncer для соединений.

### Milvus

- На MVP: standalone.
- Дальше: переход на Milvus cluster (etcd/minio уже выделены) и настройка ресурсов/индексов под workload.

## 4) Autoscaling (план)

### Docker Swarm (минимально)

- `backend`/`reranker` — scale replicas (`--replicas N`) + healthchecks.
- `nginx` — load-balancer на входе, sticky sessions не нужны (JWT).

### Kubernetes (рекомендовано для production)

- `backend`/`reranker`:
  - `Deployment` + `HPA` по CPU/RPS/latency,
  - `readinessProbe` на `/api/health` и `/health`,
  - `livenessProbe` для auto-restart.
- `Postgres`:
  - managed service (желательно) или `StatefulSet` + PVC.
- `Milvus`:
  - официальный Helm chart (cluster) + отдельные PVC.

## 5) Healthchecks и алерты (что уже сделано)

- Healthchecks:
  - `backend`: `/api/health`
  - `reranker`: `/health`
- Prometheus rules:
  - `BackendDown`, `HighSearchLatencyP95`, `RerankerSlowP95`, `PostgresExporterDown`

## 6) Что измеряем (SLO/SLI)

См. `docs/requirements-v3.md`:

- p95 latency `/search` baseline / rerank
- error rate (4xx/5xx)
- RPS и “пустые выдачи”
- offline качество reranker (pairwise accuracy)

