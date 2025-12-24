# Поиск источников (MVP)

Проект: сайт для поиска источников по тексту/документу (PDF/DOCX) на базе вашей LLM‑модели и векторного поиска.

## Архитектура

- **Backend**: FastAPI + Postgres (метаданные/чанки) + Milvus (векторные эмбеддинги).
- **Frontend**: React (Vite) + Tailwind CSS.
- **Панель управления** (скрытая): раздел сайта с доступом по ролям:
  - загрузка источников (PDF/DOCX),
  - просмотр/удаление загруженных документов,
  - управление пользователями,
  - метрики запросов,
  - дальнейшее расширение.

### Как работает поиск

1. Оператор загружает документы‑источники.
2. Backend:
   - сохраняет файл,
   - извлекает текст,
   - режет на чанки,
   - считает эмбеддинги,
   - кладёт эмбеддинги в Milvus, текст/метаданные — в Postgres.
3. Пользователь загружает свой PDF/DOCX или вставляет текст.
4. Backend извлекает текст (если файл), строит эмбеддинг запроса и ищет похожие чанки в Milvus, возвращая список источников.

### Ваша LLM

В `backend/app/services/llm.py` есть интерфейс для подключения вашей модели.  
По умолчанию включён только векторный поиск; можно включить LLM‑переранжирование через env:

```
USE_CUSTOM_LLM=true
CUSTOM_LLM_ENDPOINT=http://your-llm:port/infer
```

## Запуск

1. Скопируйте `.env.example` → `.env` и при необходимости поменяйте параметры.
2. Запустите:

```
docker compose up --build
```

Сайт будет на `http://localhost/`, API на `http://localhost/api/`.

## Observability (MLOps)

- **Prometheus**: `http://localhost:9090` (скрейпит `backend:8000/metrics`)
- **Grafana**: `http://localhost:3002` (логин/пароль по умолчанию: `admin`/`admin`)
- **Langfuse**: `http://localhost:3001`

Чтобы включить трейсинг в backend/reranker:

- в Langfuse создайте Project и возьмите **Public/Secret key**
- положите их в `.env` как `LANGFUSE_PUBLIC_KEY` и `LANGFUSE_SECRET_KEY`
- поставьте `LANGFUSE_TRACING_ENABLED=true`

## Реранкер (своя модель)

- Сервис `reranker` живёт в `reranker/` и предоставляет `POST /rerank`.
- Backend включает переранжирование, если `USE_CUSTOM_LLM=true` и `CUSTOM_LLM_ENDPOINT` указывает на реранкер.
- Обучение/эксперименты: `training/README.md`.

## Локальная разработка

- Backend: `uvicorn app.main:app --reload`
- Frontend: `npm install && npm run dev`
