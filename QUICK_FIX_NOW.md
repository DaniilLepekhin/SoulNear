# 🚨 БЫСТРОЕ РЕШЕНИЕ ОШИБКИ БД

## Проблема
```
ERROR › CREATE DATABASE cannot run inside a transaction block
```

## Причина
1. `init-db.sh` не запустился (старый volume уже существует)
2. Бот пытается создать БД сам, но делает это внутри транзакции (asyncpg так не умеет)

## ✅ Решение (выбери один вариант)

### Вариант 1: Автоматический скрипт (рекомендуется)
```bash
./FIX_DB_ISSUE.sh
```

Этот скрипт:
- Остановит контейнеры
- Удалит старый postgres volume
- Запустит всё заново (init-db.sh создаст БД)

### Вариант 2: Вручную
```bash
# 1. Остановить
docker-compose down

# 2. Удалить контейнеры
docker rm -f soulnear_postgres soulnear_bot soulnear_api

# 3. Удалить volume (БД будет пересоздана)
docker volume rm soulnear_postgres_data

# 4. Запустить заново
docker-compose up -d --build

# 5. Подождать 10 сек
sleep 10

# 6. Проверить логи
docker-compose logs --tail=50 bot
```

### Вариант 3: Создать БД вручную (если хочешь сохранить данные)
```bash
# Подключиться к postgres контейнеру
docker exec -it soulnear_postgres psql -U nikitagorokhov -d postgres

# Создать БД
CREATE DATABASE soul_bot;

# Выйти
\q

# Перезапустить бота
docker-compose restart bot

# Проверить
docker-compose logs --tail=50 bot
```

---

## ⚠️ Важно про WARNING

```
WARNING: The POSTGRES_PASSWORD variable is not set
```

Это **НЕ проблема**! Это появляется при `docker-compose down` со **старым** docker-compose.yml (до git pull).

После `git pull` используется новый конфиг, где переменные загружаются правильно.

---

## 🔧 Что исправлено в коде

В `soul_bot/database/database.py` исправлен баг:

**Было:**
```python
async with admin_engine.begin() as conn:  # ← транзакция!
    await conn.execute(text(f'CREATE DATABASE "{POSTGRES_DB}"'))
```

**Стало:**
```python
async with admin_engine.connect() as conn:
    await conn.execution_options(isolation_level='AUTOCOMMIT').execute(
        text(f'CREATE DATABASE "{POSTGRES_DB}"')
    )
```

Теперь если БД не создастся через init-db.sh, бот сможет создать её сам.

---

## ✅ После исправления

Проверь что всё работает:
```bash
# Статус
docker-compose ps

# Логи без ошибок
docker-compose logs --tail=100 bot

# Бот должен запуститься
# Вместо ошибки увидишь:
# "✅ Database connected successfully"
```

---

**TL;DR:** Запусти `./FIX_DB_ISSUE.sh` и всё заработает! 🚀

