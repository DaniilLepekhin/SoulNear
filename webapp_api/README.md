# SoulNear WebApp API

Backend API для SoulNear WebApp. Использует ту же базу данных и OpenAI ассистентов что и основной бот.

## Установка

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Конфигурация

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
nano .env
```

## Запуск

```bash
python app.py
```

API будет доступен на порту 8888.

## Endpoints

### GET /
Отдает index.html webapp

### POST /api/chat
Отправить сообщение ассистенту

Request:
```json
{
  "user_id": 123456,
  "message": "Привет!",
  "assistant_type": "helper"  // helper, sleeper, relationships, money, confidence, fears
}
```

Response:
```json
{
  "status": "success",
  "response": "Ответ от ассистента"
}
```

### POST /api/reset
Сбросить контекст разговора (создать новый thread)

Request:
```json
{
  "user_id": 123456,
  "assistant_type": "helper"
}
```

### GET /health
Проверка здоровья API

## Архитектура

```
WebApp (JS) → API (Quart) → OpenAI Assistants
                ↓
           PostgreSQL (shared with bot)
```

API **НЕ ВЛИЯЕТ** на работу бота, только читает/обновляет thread_id в общей БД.
