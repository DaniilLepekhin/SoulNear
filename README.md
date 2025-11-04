# SoulNear - Telegram Bot Projects


Этот репозиторий содержит полную копию всех проектов Telegram ботов SoulNear, скачанных с продакшн сервера.

## 🎯 Quick Start

### 🐳 Вариант 1: Docker (рекомендуется)

```bash
# 1. Setup конфигурации
make setup

# 2. Заполните .env.prod
nano .env.prod

# 3. Запустите все сервисы (бот + API + PostgreSQL)
make up

# 4. Проверьте логи
make logs
```

**📖 Подробнее:** см. [Документация по деплою](./docs/04-testing-deployment.md)

### 🚀 Деплой на сервере
```bash
./scripts/safe_redeploy.sh
```
**📖 Инструкции:** см. [Документация по деплою](./docs/04-testing-deployment.md)

### 🐍 Вариант 2: Локальный запуск

1. **Setup:**
   ```bash
   cd soul_bot
   pip install -r requirements.txt
   # .env файлы уже настроены
   ```

2. **Запуск:**
   ```bash
   ENV=test python bot.py   # Тестовый бот
   ENV=prod python bot.py   # Production бот
   ```
---

## 📁 Структура проектов

### 🧠 soul_bot ⭐ MAIN PROJECT
**Основной бот с AI-ассистентом (production + test)**

**Новая архитектура (после рефакторинга):**
- Unified codebase для prod + test
- Environment-based конфигурация (.env.prod / .env.test)
- Feature flags для безопасного деплоя
- Dual API support (Assistant + ChatCompletion)

**Возможности:**
- 7 типов AI-ассистентов (helper, sleeper, relationships, money, confidence, fears, quiz)
- Динамические промпты на основе профиля пользователя
- История диалогов (context awareness)
- Голосовые сообщения (STT/TTS)
- Premium функции и медиа контент
- Платежи через YooKassa

**Tech stack:**
- OpenAI ChatCompletion API (+ fallback на Assistant API)
- PostgreSQL (soul_bot + soul_test_bot БД)
- Aiogram 3.x
- SQLAlchemy + asyncpg

### 🤖 repair_bot
**Административный бот** (не трогать)
- Резервное копирование БД
- Мониторинг ботов

### 🆘 support_bot
**Бот поддержки** (не трогать)
- Обработка обращений пользователей

### 🌐 webapp_v2
**React веб-приложение** (не трогать)

## 🛠 Технологии

- **Python 3.12+**
- **aiogram 3.19+** - Telegram Bot API
- **PostgreSQL** - База данных
- **OpenAI API** - ИИ ассистент
- **YooKassa** - Платежная система
- **APScheduler** - Планировщик задач
- **SQLAlchemy** - ORM
- **asyncpg** - Асинхронный PostgreSQL драйвер

## 📋 Установка

### Quick Setup

```bash
# 1. Clone (если еще не сделано)
cd /Users/nikitagorokhov/dev/SoulNear

# 2. Install dependencies
cd soul_bot
pip install -r requirements.txt

# 3. Setup databases
createdb soul_bot        # Production DB
createdb soul_test_bot   # Test DB

# 4. Check .env files (уже настроены)
ls -la soul_bot/.env.*
```

### Запуск бота

```bash
cd soul_bot

# Test mode (безопасно для экспериментов)
ENV=test python bot.py

# Production mode
ENV=prod python bot.py
```

### Тестирование

```bash
# Smoke tests (быстрая проверка)
cd soul_bot
pytest tests/smoke_tests.py -v

# Или через скрипт
./scripts/test_stage.sh
```

**Подробнее:** [SETUP_ENV.md](./soul_bot/SETUP_ENV.md)

## ⚙️ Конфигурация

### Environment-based config
```python
# soul_bot/config.py динамически загружает:
ENV = os.getenv('ENV', 'prod')
# .env.prod или .env.test
```

### Feature Flags
```bash
# .env.test / .env.prod
USE_CHAT_COMPLETION=true         # ✅ Stage 1 (работает!)
ENABLE_STYLE_SETTINGS=false      # ⏳ Stage 2
ENABLE_USER_PROFILES=false       # ⏳ Stage 3
ENABLE_PATTERN_ANALYSIS=false    # ⏳ Stage 3
ENABLE_DYNAMIC_QUIZ=false        # ⏳ Stage 4
ENABLE_TUNE_STYLE=false          # ⏳ Stage 6
```

**Преимущества:**
- ✅ Мгновенный откат (set flag = false)
- ✅ Плавная миграция
- ✅ A/B тестирование

## 📊 База данных

### Существующие таблицы
- `users` - Пользователи
- `statistic_day` - Дневная статистика
- `ads` - Реклама
- `media` / `media_category` - Медиа контент
- `aiogram_state` - FSM состояния

### ✨ Новые таблицы (Stage 1)
- `user_profiles` - Настройки стиля + паттерны + инсайты
- `conversation_history` - Полная история диалогов
- `quiz_sessions` - Сессии квизов

**Схема:** см. [Архитектура проекта](./docs/01-project-overview.md#база-данных)

## 📚 Документация

Полная документация проекта находится в директории [`docs/`](./docs/):

### 📖 Основные документы:
- **[01-project-overview.md](./docs/01-project-overview.md)** - обзор проекта, архитектура, tech stack
- **[02-implementation-roadmap.md](./docs/02-implementation-roadmap.md)** - этапы реализации и выполнение
- **[03-key-features.md](./docs/03-key-features.md)** - ключевые функции и их реализация
- **[04-testing-deployment.md](./docs/04-testing-deployment.md)** - тестирование и деплой
- **[05-technical-decisions.md](./docs/05-technical-decisions.md)** - технические решения и нюансы

### 🚀 Быстрый старт:
1. Начни с [Обзора проекта](./docs/01-project-overview.md)
2. Изучи [План реализации](./docs/02-implementation-roadmap.md)
3. Для деплоя см. [Тестирование и деплой](./docs/04-testing-deployment.md)

## 🛠️ Development Workflow

```bash
# 1. Включить feature flag для новой фичи
echo "ENABLE_YOUR_FEATURE=true" >> soul_bot/.env.test

# 2. Разработка (пиши код)
# 3. Тестирование
cd soul_bot && ENV=test python bot.py

# 4. Smoke tests
pytest tests/smoke_tests.py -v

# 5. Если OK - включи на PROD
echo "ENABLE_YOUR_FEATURE=true" >> soul_bot/.env.prod

# 6. Коммит
git add . && git commit -m "feat: описание" && git push origin dev
```

**Подробнее:** см. [Документация по разработке](./docs/04-testing-deployment.md#rollout-process)

## 🔒 Безопасность

⚠️ **ВНИМАНИЕ**: Этот репозиторий содержит реальные токены и ключи API. 
При использовании в продакшне обязательно:
- Смените все токены и ключи
- Используйте переменные окружения
- Настройте правильные права доступа

## 📝 Лицензия

Проект предназначен для внутреннего использования SoulNear.

---

**Последнее обновление:** Ноябрь 2025

**Документация:** Все документы консолидированы в [`docs/`](./docs/)  
