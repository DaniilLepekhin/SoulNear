# 🚀 Шпаргалка по деплою

## TL;DR — Деплой на сервере

```bash
# Быстрый способ (БЕЗ потери БД):
./scripts/safe_redeploy.sh

# С очисткой БД (fresh start):
./scripts/safe_redeploy.sh --clean

# Или одной строкой:
docker-compose down && git pull && docker rm -f soulnear_postgres soulnear_bot soulnear_api 2>/dev/null || true && make rebuild && make logs-bot
```

## Первый запуск

```bash
# 1. Проверь .env.prod
ls -la .env.prod

# 2. Заполни placeholder'ы (HELPER_ID, RELATIONSHIPS_ID, SECRET_KEY)
nano .env.prod

# 3. Проверь конфиг
./validate-env.sh

# 4. Запусти
make rebuild

# 5. Логи
make logs-bot
```

## Быстрые команды

```bash
make rebuild      # Пересобрать и запустить
make restart-bot  # Перезапустить только бота
make logs-bot     # Логи бота (live)
make ps           # Статус сервисов
make backup       # Бэкап БД
docker-compose ps # Детальный статус
```

## Проверка здоровья

```bash
# Статус
docker-compose ps

# Переменные загрузились?
docker exec soulnear_bot env | grep BOT_TOKEN

# Логи без ошибок?
make logs-bot
```

## ❌ Не делай

```bash
make redeploy               # Удалит БД!
export OPENAI_API_KEY=...   # Не нужно экспортировать
```

## ✅ Файлы на месте

- `/проект/.env.prod` — все переменные (НЕ в soul_bot/!)
- `/проект/docker-compose.yml` — ссылается на .env.prod
- `/проект/scripts/safe_redeploy.sh` — безопасный деплой

## Если проблемы

```bash
# WARNING about missing variables?
git pull  # Обнови docker-compose.yml

# ContainerConfig error?
docker rm -f soulnear_postgres soulnear_bot soulnear_api

# CREATE DATABASE transaction error?
./FIX_DB_ISSUE.sh  # Или: ./scripts/safe_redeploy.sh --clean

# Бот не видит переменные?
ls -la .env.prod && grep env_file docker-compose.yml
```

---

**Всё. Работает. Деплой за 5 секунд.** 🎉

