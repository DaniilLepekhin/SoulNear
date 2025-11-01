# 🐳 SoulNear Docker Setup

Простой и быстрый запуск всего проекта в Docker контейнерах.

## 📦 Что включено

- **PostgreSQL 15** - база данных
- **Telegram Bot** - основной бот на aiogram
- **WebApp API** - Quart API для веб-приложения

## 🚀 Быстрый старт

### 1. Подготовка

Скопируйте файл конфигурации:

```bash
cp .env.example .env.prod
```

Отредактируйте `.env.prod` и заполните все необходимые значения:
- `BOT_TOKEN` - токен Telegram бота
- `OPENAI_API_KEY` - ключ OpenAI API
- `POSTGRES_PASSWORD` - пароль для PostgreSQL
- Остальные ключи по необходимости

### 2. Запуск

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f bot
docker-compose logs -f api
docker-compose logs -f postgres
```

### 3. Остановка

```bash
# Остановить все сервисы
docker-compose down

# Остановить и удалить volumes (включая БД!)
docker-compose down -v
```

## 🔧 Разные окружения

Проект поддерживает несколько окружений (prod/test/dev):

```bash
# Production
ENV=prod docker-compose up -d

# Test
ENV=test docker-compose up -d

# Dev
ENV=dev docker-compose up -d
```

Создайте соответствующие `.env.prod`, `.env.test`, `.env.dev` файлы.

## 📊 Управление

### Проверка статуса

```bash
docker-compose ps
```

### Перезапуск сервиса

```bash
docker-compose restart bot
docker-compose restart api
```

### Пересборка после изменения кода

```bash
# Пересобрать все
docker-compose build

# Пересобрать конкретный сервис
docker-compose build bot

# Пересобрать и запустить
docker-compose up -d --build
```

### Подключение к PostgreSQL

```bash
# Через docker exec
docker exec -it soulnear_postgres psql -U postgres -d soul_bot

# Или через хост (порт 5432)
psql -h localhost -U postgres -d soul_bot
```

### Бэкап базы данных

```bash
# Создать бэкап
docker exec soulnear_postgres pg_dump -U postgres soul_bot > backup.sql

# Восстановить бэкап
docker exec -i soulnear_postgres psql -U postgres soul_bot < backup.sql
```

## 🐛 Отладка

### Просмотр логов в реальном времени

```bash
docker-compose logs -f --tail=100
```

### Выполнение команд внутри контейнера

```bash
# Зайти в контейнер бота
docker exec -it soulnear_bot bash

# Зайти в контейнер API
docker exec -it soulnear_api bash

# Выполнить Python скрипт
docker exec soulnear_bot python -c "from config import *; print(POSTGRES_DB)"
```

### Проверка здоровья сервисов

```bash
# Проверка API
curl http://localhost:8888/health

# Проверка PostgreSQL
docker exec soulnear_postgres pg_isready -U postgres
```

## 📝 Структура файлов

```
.
├── docker-compose.yml          # Основной файл композиции
├── .env.example                # Пример конфигурации
├── .env.prod                   # Production конфигурация (создать)
├── .dockerignore               # Игнорируемые файлы
├── soul_bot/
│   ├── Dockerfile              # Dockerfile для бота
│   └── ...
└── webapp_api/
    ├── Dockerfile              # Dockerfile для API
    └── ...
```

## ⚠️ Важно

1. **Никогда не коммитьте .env файлы с реальными ключами!**
2. Используйте сильные пароли для `POSTGRES_PASSWORD`
3. В production окружении рекомендуется использовать Docker secrets
4. Volume `postgres_data` сохраняет данные БД между перезапусками

## 🔥 Production Tips

1. **Мониторинг:**
   ```bash
   docker stats
   ```

2. **Автоматический рестарт:** Все сервисы настроены с `restart: unless-stopped`

3. **Ограничение ресурсов:** Добавьте в `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1'
         memory: 1G
   ```

4. **Логирование:** Настройте rotation логов в docker daemon

## 🆘 Проблемы и решения

### Бот не может подключиться к БД

Проверьте:
- PostgreSQL запущен: `docker-compose ps postgres`
- Правильность credentials в `.env.prod`
- Healthcheck проходит: `docker inspect soulnear_postgres`

### API не отвечает

```bash
# Проверьте логи
docker-compose logs api

# Проверьте, что порт не занят
lsof -i :8888

# Попробуйте рестарт
docker-compose restart api
```

### База данных не инициализируется

```bash
# Удалите volume и пересоздайте
docker-compose down -v
docker-compose up -d
```

---

**Сделано с ❤️ и капелькой Docker магии**

