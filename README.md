# AI Lead Qualification Agent for Telegram (DOE)

Универсальный Telegram AI-агент для квалификации входящих лидов, ответов на вопросы по базе знаний (RAG) и передачи диалога живому менеджеру.

Проект построен по DOE-подходу:
- `directives/` — регламенты и SOP
- `orchestration/` — промпты и логика оркестрации
- `execution/` — рабочий код, интеграции, БД, тесты

## Универсальный продукт
Это универсальный AI-агент для продаж и первичной квалификации, который подходит под любой бизнес:
- услуги,
- e-commerce,
- образовательные проекты,
- B2B и локальные сервисы.

Перед запуском агент тонко настраивается под конкретную нишу и компанию:
- правила квалификации и веса скоринга,
- risk-триггеры эскалации,
- база знаний клиента,
- язык и стиль коммуникации.

После настройки продукт готов к запуску в кратчайшие сроки. Базовая платформа уже реализована, для старта нужны только данные клиента для тонкой конфигурации.

## Что умеет
- Свободный диалог в Telegram (не только кнопки).
- Сбор полей лида: запрос, срок, бюджет, контакт.
- Скоринг 0-100, статус `qualified / not_qualified`, теплота `cold/warm/hot`.
- Ответы на вопросы клиента по базе знаний (RAG).
- Эскалация менеджеру по risk-триггерам.
- Карточка лида в чат менеджеров + кнопка `Взять лид`.
- Фиксация в БД, кто забрал лид.
- SLA-алерт при `pending_human` старше 1 часа.

## Стек
- Python 3.13
- aiogram 3
- PostgreSQL 16
- Docker / Docker Compose
- OpenAI SDK (`OPENAI_BASE_URL=https://polza.ai/api/v1`)

## Быстрый старт

### 1) Установить зависимости
```powershell
python -m venv execution\.venv
.\execution\.venv\Scripts\python.exe -m pip install -r execution\requirements.txt
```

### 2) Поднять PostgreSQL
```powershell
docker compose -f execution\docker-compose.yml up -d db
Get-Content execution\sql\schema.sql -Raw | docker exec -i execution-db-1 psql -U leadbot -d leadbot
```

### 3) Настроить `.env`
Создайте `execution/.env`:
```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WORK_CHAT_ID=-100...
TELEGRAM_WORK_TOPIC_ID=0
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://polza.ai/api/v1
OPENAI_MODEL=openai/gpt-4.1-mini
DATABASE_URL=postgresql://leadbot:leadbot@localhost:5432/leadbot
AMO_BASE_URL=
AMO_ACCESS_TOKEN=
DEFAULT_CLIENT_ID=default
```

### 4) Заполнить базу знаний клиента
- `execution/clients/<client_id>.json`
- `execution/clients/<client_id>/kb/*.md`

### 5) Запустить бота
```powershell
cd execution
.\.venv\Scripts\python.exe main.py
```

### 6) Тесты
```powershell
$env:PYTHONPATH='execution'
.\execution\.venv\Scripts\python.exe -m pytest execution\tests -q
```

## E2E-тест
1. Напишите `/start` в личку боту.
2. Отправьте лид-сообщение:
   - `Нужна точная цена и договор сегодня, бюджет 200к, срок 2 недели, мой контакт @username`
3. Проверьте:
- бот отправил лид в менеджерский чат;
- есть карточка и кнопка `Взять лид`;
- после клика приходит сообщение, кто назначен на лид.

## amoCRM (подробно)

### Что уже реализовано
- Есть клиент amoCRM: `execution/app/crm.py`
- Есть retry на отправку (3 попытки, backoff).
- Есть контракт payload: `execution/contracts/amocrm_payload.schema.json`

### Что нужно от клиента для включения
1. `AMO_BASE_URL` (пример: `https://yourdomain.amocrm.ru`)
2. `AMO_ACCESS_TOKEN`
3. Коды custom fields в amoCRM для:
- intent
- timeline
- budget
- contact
- score

### Как включить
1. Заполнить `.env`:
```env
AMO_BASE_URL=https://yourdomain.amocrm.ru
AMO_ACCESS_TOKEN=...
```
2. Обновить маппинг полей в `execution/app/crm.py` (блок `custom_fields_values`).
3. Перезапустить бота.

### Проверка интеграции
1. Отправить тестовый лид боту.
2. Убедиться, что в amoCRM появилась сделка.
3. Проверить, что поля `intent/timeline/budget/contact/score` заполнены корректно.

## Документы для внедрения и продаж
- Шаблон онбординга клиента: `directives/client-onboarding-template.md`
- Карточка продукта: `directives/product-card.md`

## Roadmap
- Полное включение amoCRM на реальных field code.
- Персистентная память диалога между перезапусками из БД.
- Админка управления `client_config` и KB.