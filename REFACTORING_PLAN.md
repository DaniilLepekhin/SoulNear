# 🔧 План рефакторинга структуры проекта

## Текущая проблема

```
❌ SoulNear/
   ├── soul_bot/      # Продакшн
   ├── soul_test_bot/ # Тест (99% дубликат)
   
Проблемы:
- Дублирование кода
- Рассинхронизация
- Токен захардкожен в soul_test_bot
- Сложно поддерживать
```

## Целевая архитектура

```
✅ SoulNear/
   ├── soul_bot/           # ЕДИНСТВЕННАЯ кодовая база
   │   ├── .env.prod       # Продакшн конфиг (в .gitignore)
   │   ├── .env.test       # Тест конфиг (в .gitignore)
   │   ├── .env.example    # Шаблон
   │   ├── bot/
   │   ├── database/
   │   ├── tests/
   │   └── bot.py
   ├── scripts/
   │   ├── run_prod.sh
   │   ├── run_test.sh
   │   └── migrate.sh
   └── README.md
```

---

## Этапы миграции

### Этап 1: Бэкап
```bash
# Сделай бэкап на всякий случай
cp -r soul_bot soul_bot_backup
cp -r soul_test_bot soul_test_bot_backup
```

### Этап 2: Создаём .env файлы

**soul_bot/.env.prod:**
```env
ENV=prod
BOT_TOKEN=<твой продакшн токен>
TEST=false
POSTGRES_DB=soul_bot
OPENAI_API_KEY=<твой ключ>
# ... остальное
```

**soul_bot/.env.test:**
```env
ENV=test
BOT_TOKEN=7838929567:AAELlItbyGN8KvzeYdY-28id6Fhtf6Zn0PY
TEST=true
POSTGRES_DB=soul_test_bot
OPENAI_API_KEY=<твой ключ>
ELEVEN_LABS_KEY=<твой ключ>
# ... остальное
```

**soul_bot/.env.example:**
```env
ENV=prod
BOT_TOKEN=your_bot_token_here
TEST=false
POSTGRES_DB=soul_bot
OPENAI_API_KEY=your_openai_api_key_here
# ... шаблон для разработчиков
```

### Этап 3: Обновляем config.py

```python
import os
from dotenv import load_dotenv

# Определяем окружение
ENV = os.getenv('ENV', 'prod')

# Загружаем соответствующий .env файл
env_file = f'.env.{ENV}'
load_dotenv(env_file)

print(f"🚀 Загружен конфиг: {env_file}")

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

TEST = os.getenv('TEST', 'false').lower() == 'true'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ELEVEN_LABS_KEY = os.getenv('ELEVEN_LABS_KEY')

# Ассистенты
HELPER_ID = os.getenv('HELPER_ID')
SOULSLEEP_ID = os.getenv('SOULSLEEP_ID')
RELATIONSHIPS_ID = os.getenv('RELATIONSHIPS_ID')
MONEY_ID = os.getenv('MONEY_ID')
CONFIDENCE_ID = os.getenv('CONFIDENCE_ID')
FEARS_ID = os.getenv('FEARS_ID')

# Юкасса
SHOP_ID = int(os.getenv('SHOP_ID', '476767'))
SECRET_KEY = os.getenv('SECRET_KEY')

# PostgreSQL
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')

ADMINS = [580613548, 946195257, 73744901, 389209990]
```

### Этап 4: Создаём скрипты запуска

**scripts/run_prod.sh:**
```bash
#!/bin/bash
cd soul_bot
export ENV=prod
python bot.py
```

**scripts/run_test.sh:**
```bash
#!/bin/bash
cd soul_bot
export ENV=test
python bot.py
```

### Этап 5: Мерджим уникальные фичи

```bash
# Проверяем, есть ли что-то уникальное в soul_test_bot
diff -r soul_bot soul_test_bot | grep "Only in soul_test_bot"

# Если есть (например, webapp.py) — копируем
cp soul_test_bot/bot/handlers/user/webapp.py soul_bot/bot/handlers/user/
```

### Этап 6: Обновляем .gitignore

```gitignore
# Environment files
.env.prod
.env.test
.env

# Old backups
soul_bot_backup/
soul_test_bot_backup/

# Test data
soul_bot/bot/media/voices/
soul_bot/ready/
```

### Этап 7: Удаляем дубликат

```bash
# Когда убедился, что всё работает
rm -rf soul_test_bot
rm -rf repair_bot  # тоже дубликат?
```

### Этап 8: Обновляем README

```markdown
## Запуск

### Продакшн:
```bash
ENV=prod python bot.py
# или
./scripts/run_prod.sh
```

### Тестирование:
```bash
ENV=test python bot.py
# или
./scripts/run_test.sh
```

### Разработка:
1. Скопируй `.env.example` → `.env.test`
2. Заполни токены
3. `ENV=test python bot.py`
```

---

## Преимущества после рефакторинга

✅ **Единая кодовая база** — изменения в одном месте  
✅ **Безопасность** — токены в .env, не в коде  
✅ **Гибкость** — можно создавать любые окружения (.env.dev, .env.staging)  
✅ **Git friendly** — одна история, легко мерджить  
✅ **Масштабируемость** — легко добавить новые окружения  

---

## Чек-лист миграции

- [ ] Бэкап soul_bot и soul_test_bot
- [ ] Создать .env.prod, .env.test, .env.example
- [ ] Обновить config.py (load_dotenv с ENV)
- [ ] Создать скрипты запуска
- [ ] Протестировать запуск с ENV=test
- [ ] Протестировать запуск с ENV=prod (на копии!)
- [ ] Скопировать уникальные файлы из soul_test_bot
- [ ] Обновить .gitignore
- [ ] Обновить документацию
- [ ] Коммит изменений
- [ ] Удалить soul_test_bot (после подтверждения)
- [ ] Profit! 🎉

---

## Откат (если что-то пошло не так)

```bash
# Восстановить из бэкапа
rm -rf soul_bot
cp -r soul_bot_backup soul_bot

# Или через git
git checkout HEAD -- soul_bot/
```

---

## Время выполнения

- Этапы 1-4: 15 минут (подготовка)
- Этап 5-7: 10 минут (мердж и удаление)
- Этап 8: 5 минут (документация)

**Итого: 30 минут** → чистый, поддерживаемый проект


