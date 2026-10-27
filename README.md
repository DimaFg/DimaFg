# Сайт-портфолио фотографа

Монорепозиторий по ТЗ: публичный сайт на Next.js, API на FastAPI, PostgreSQL, фоновый worker
уведомлений, Caddy как reverse proxy с TLS. Визуальная основа — `prototype/index_2.html`.

```
api/        FastAPI (модульный монолит): заявки, портфолио, услуги, уведомления, auth-модели
  app/core/       конфигурация, БД, единый формат ошибок, request_id, JSON-логи
  app/modules/    leads · portfolio · services · notifications (outbox + worker) · auth · audit
  alembic/        миграции
  tests/          pytest на реальном PostgreSQL
web/        Next.js 16 + TypeScript, статическая генерация публичных страниц
  src/components/ Header, Hero, About, ArtistStatement, Portfolio, PortfolioFilters, PhotoCard,
                  PhotoLightbox, Services, ServiceCard, LeadForm, ContactInformation, Footer …
  src/content/    тестовый контент (услуги, категории, кадры, тексты)
  src/config/     открытые бизнес-решения через NEXT_PUBLIC_* переменные
  src/styles/     CSS прототипа, разделённый по смысловым модулям
deploy/     Caddyfile (TLS, защитные заголовки, CSP, лимит тела запроса)
prototype/  исходный index_2.html
docs/       статус работ и принятые решения
```

## Локальный запуск без Docker

Нужны Python 3.12+, [uv](https://docs.astral.sh/uv/), Node 22 и PostgreSQL 16.

```bash
# API
cd api
uv sync
export DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:5432/photo
uv run alembic upgrade head
uv run python -m app.cli seed           # категории и услуги из прототипа
uv run uvicorn app.main:app --reload    # http://127.0.0.1:8000/api/docs
uv run python -m app.cli worker         # в отдельном терминале: уведомления о заявках

# Фронтенд (проксирует /api на 127.0.0.1:8000, см. API_INTERNAL_URL)
cd web
npm install
npm run dev                             # http://localhost:3000
```

Тесты и проверки:

```bash
cd api && TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:5432/photo_test uv run pytest
cd api && uv run ruff check . && uv run ruff format --check .
cd web && npm run typecheck && npm run lint && npm run build
```

Типы клиента генерируются из OpenAPI-схемы FastAPI, вручную их не пишем:

```bash
cd api && uv run python -m app.cli openapi > ../web/openapi.json
cd web && npm run gen:api
```

## Запуск через Docker Compose (local / одиночный VPS)

```bash
cp .env.example .env    # заполнить POSTGRES_PASSWORD, APP_SECRET, SITE_ADDRESS, контакты
docker compose up -d --build
```

Порядок старта: `db` → `migrate` (Alembic + seed, один раз) → `api` и `worker` → `web` → `caddy`.
Наружу открыты только 80/443 Caddy. При `SITE_ADDRESS=example.ru` Caddy сам выпускает
и продлевает TLS-сертификат.

Первый администратор (публичной регистрации нет):

```bash
docker compose exec api python -m app.cli create-admin --email owner@example.ru
docker compose exec api python -m app.cli set-password --email owner@example.ru  # смена пароля
```

## Уведомления о заявках

Заявка сохраняется в PostgreSQL вместе с outbox-заданием в одной транзакции. Отправкой занимается
worker, а не HTTP-запрос: при сбое Telegram или почты задание повторяется с экспоненциальной
паузой (до `OUTBOX_MAX_ATTEMPTS`), а успешно отработавшие каналы повторно не дёргаются.
Каналы включаются переменными `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` и `SMTP_*`; если не
настроен ни один, worker пишет в лог обезличенную запись с номером заявки.

## Антиспам формы

Honeypot-поле, минимальное время заполнения, лимиты на IP (HMAC-отпечаток, обнуляется через
30 дней) и на контакт, лимиты длины, `Idempotency-Key` и серверная дедупликация повторной
отправки. Заявки от ботов сохраняются со статусом `spam` без уведомления, а бот получает обычный
ответ.

Правила работы с секретами и персональными данными — в [SECURITY.md](./SECURITY.md),
статус работ и принятые решения — в [docs/status.md](./docs/status.md).
