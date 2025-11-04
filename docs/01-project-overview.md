# SoulNear Bot - Обзор проекта

## Архитектура

SoulNear Bot — Telegram-бот с AI-ассистентом для психологической поддержки и самоанализа.

### Основные компоненты

- **soul_bot** — основной бот (production + test в единой кодовой базе)
- **webapp_api** — REST API для веб-приложения
- **webapp_v2** — React веб-приложение
- **repair_bot** — административный бот (резервное копирование, мониторинг)
- **support_bot** — бот поддержки

### Tech Stack

- **Python 3.12+** с aiogram 3.19+
- **PostgreSQL** — основная БД
- **OpenAI API** — GPT-4o для чата, GPT-4o-mini для анализа
- **Docker Compose** — оркестрация сервисов
- **YooKassa** — платежная система

### Конфигурация

Унифицированная кодовая база с environment-based конфигурацией:

- `.env.prod` — production настройки
- `.env.test` — тестовые настройки
- Feature flags для безопасного деплоя

```bash
ENV=prod python bot.py  # Production
ENV=test python bot.py  # Test
```

---

## Основные возможности

### 1. AI-ассистенты (7 типов)

- **helper** — общая поддержка
- **sleeper** — работа со снами
- **relationships** — отношения
- **money** — финансы
- **confidence** — уверенность
- **fears** — страхи
- **quiz** — квизы

### 2. Персонализация

- Настройки стиля (тон, личность, длина ответов)
- Автоматический анализ паттернов пользователя
- Адаптация ответов на основе истории диалогов
- Эмоциональное состояние и инсайты

### 3. Адаптивные квизы

- Динамическая генерация вопросов
- Анализ паттернов mid-quiz
- Адаптивное ветвление (follow-up вопросы)
- Глубокий финальный анализ

### 4. Голосовые сообщения

- STT (Speech-to-Text) для входящих
- TTS (Text-to-Speech) для ответов

---

## База данных

### Основные таблицы

- `users` — пользователи
- `user_profiles` — профили с паттернами, инсайтами, настройками
- `conversation_history` — полная история диалогов
- `quiz_sessions` — сессии квизов
- `statistic_day` — дневная статистика
- `media` / `media_category` — медиа контент

### Особенности

- JSONB для гибкого хранения (паттерны, инсайты, эмоциональное состояние)
- Embeddings для дедупликации паттернов (1536 dimensions)
- История диалогов для контекстного общения

---

## Feature Flags

Безопасная миграция через feature flags:

```bash
USE_CHAT_COMPLETION=true          # ChatCompletion API (Stage 1)
ENABLE_STYLE_SETTINGS=true        # Настройки стиля (Stage 2)
ENABLE_USER_PROFILES=true         # Профили пользователей (Stage 3)
ENABLE_PATTERN_ANALYSIS=true      # Анализ паттернов (Stage 3)
ENABLE_DYNAMIC_QUIZ=true          # Адаптивные квизы (Stage 4)
ENABLE_ADAPTIVE_QUIZ=true         # Адаптивное ветвление в квизах
```

---

## Структура проекта

```
SoulNear/
├── soul_bot/              # Основной бот
│   ├── bot/
│   │   ├── handlers/     # Обработчики команд
│   │   ├── keyboards/     # Inline клавиатуры
│   │   ├── services/     # Бизнес-логика
│   │   └── functions/    # Утилиты
│   ├── database/
│   │   ├── models/        # SQLAlchemy модели
│   │   └── repository/   # Репозитории
│   └── tests/            # Тесты
├── webapp_api/           # REST API
├── webapp_v2/            # React приложение
├── docker/               # Docker конфигурация
├── scripts/              # Утилиты и скрипты
└── docs/                 # Документация
```

---

## Быстрый старт

### Docker (рекомендуется)

```bash
make setup    # Создать .env.prod
make up       # Запустить все сервисы
make logs     # Логи
```

### Локальный запуск

```bash
cd soul_bot
pip install -r requirements.txt
ENV=test python bot.py
```

---

**Подробнее:** см. `02-implementation-roadmap.md` и `04-testing-deployment.md`

