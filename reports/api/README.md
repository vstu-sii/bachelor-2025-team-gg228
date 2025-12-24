# API тестирование

Дата: 2025-12-24

## Как запускать

Из корня репозитория:

1) Установить зависимости тестов:

```bash
python -m pip install -r backend/requirements.txt -r backend/requirements-test.txt
```

2) Запустить тесты:

```bash
pytest -q tests/api
```

## Что покрыто

- `/api/health`
- `/api/auth/register`, `/api/auth/login`
- `/api/users/me` (JWT)
- `/api/admin/users` (RBAC: 401/403/успешные сценарии)
- `/api/admin/metrics` (пустой набор)
- `/api/search`, `/api/baseline/search` (через стаб/mock, без Milvus/эмбеддингов)
- `/api/admin/documents` (через стаб/mock, без парсинга PDF/DOCX)
