# Performance / Load testing

## Предпосылки

- Поднятый стек (минимум `nginx`, `backend`, `postgredb`; для реального теста поиска — ещё `standalone`/Milvus).
- Рекомендуется запускать k6 в Docker.

## Smoke test (быстрый прогон)

Через опубликованные порты:

```bash
docker run --rm -v "$PWD":/w -w /w -e BASE_URL=http://localhost grafana/k6:0.54.0 run /w/tests/performance/k6/smoke.js
```

Или внутри compose сети (в `docker-compose.yml` сеть называется `milvus`):

```bash
docker run --rm --network milvus -v "$PWD":/w -w /w -e BASE_URL=http://nginx grafana/k6:0.54.0 run /w/tests/performance/k6/smoke.js
```

## Load test (нагрузка)

Пример (через localhost):

```bash
docker run --rm -v "$PWD":/w -w /w -e BASE_URL=http://localhost -e VUS=20 -e DURATION=60s grafana/k6:0.54.0 run /w/tests/performance/k6/load.js
```

Параметры:

- `BASE_URL` — базовый URL (например `http://localhost` или `http://nginx`).
- `VUS` — количество виртуальных пользователей (по умолчанию 10).
- `DURATION` — длительность (например `60s`, по умолчанию `30s`).
- `ADMIN_EMAIL`/`ADMIN_PASSWORD` — если заданы, включается проверка admin endpoints.
