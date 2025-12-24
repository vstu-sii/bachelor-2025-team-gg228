# Отчёт: performance тестирование

Дата: 2025-12-24

## Цель

- Проверить, что система выдерживает базовую нагрузку без деградации UX и ошибок.
- Зафиксировать p95 latency и error rate на ключевых endpoint’ах.

## Инструмент

- k6 (`grafana/k6`)

## Сценарии

1) Smoke: `tests/performance/k6/smoke.js`
- `/api/health`
- `/api/auth/register`
- `/api/users/me`
- (опционально) `/api/admin/metrics`

2) Load: `tests/performance/k6/load.js`
- `/api/health` (как минимальный “пульс”)

## Результаты (заполнить после прогона)

- Конфигурация: `VUS=__`, `DURATION=__`, `BASE_URL=__`
- Ошибки: `http_req_failed=__`
- Latency p95: `http_req_duration p95=__ ms`

## Bottlenecks / выводы

- TBD

## Рекомендации

- Добавить отдельный сценарий нагрузки для `/api/search` (требует поднятого Milvus и прогретых моделей).
- Снять p95 отдельно для baseline vs rerank и сравнить с SLO из `docs/requirements-v3.md`.

