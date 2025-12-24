# Отчёт: API тестирование

Дата: 2025-12-24

## Цель

Проверить ключевые FastAPI endpoints на:

- базовую корректность ответов,
- валидацию/ошибки авторизации,
- RBAC (admin vs user),
- отсутствие жёсткой зависимости тестов от Milvus/эмбеддингов/парсинга PDF.

## Что сделано

- Добавлен health endpoint: `GET /api/health`.
- Добавлен набор автотестов `pytest` в `tests/api/` (используется SQLite in-memory и моки тяжёлых функций).

## Покрытие (по группам)

- Health: `GET /api/health`
- Auth:
  - `POST /api/auth/register`
  - `POST /api/auth/login` (в т.ч. неверный пароль)
- Users:
  - `GET /api/users/me` (JWT)
- Admin (RBAC):
  - `GET/POST/PATCH /api/admin/users` (401/403/успешные сценарии)
  - `GET /api/admin/metrics` (пустые данные)
  - `GET/POST/DELETE /api/admin/documents` (через mock ingest)
- Search:
  - `POST /api/search`
  - `POST /api/baseline/search`

## Результат прогона

Локальный прогон в контейнере backend:

- `10 passed`

## Известные ограничения

- Не выполняются интеграционные тесты с реальными Milvus/Postgres и реальным парсингом PDF/DOCX (это отдельный слой e2e/smoke).
- Performance-тесты не автоматизированы (есть только рекомендации в требованиях).
