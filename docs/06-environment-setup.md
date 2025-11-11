# Настройка окружений и унифицированной кодовой базы

## 1. Подготовь .env файлы

```bash
cd soul_bot
cp .env.prod.TEMPLATE .env.prod
cp .env.test.TEMPLATE .env.test
```

### .env.prod (production)
- `BOT_TOKEN` — основной бот от @BotFather
- `OPENAI_API_KEY` — ключ OpenAI
- `POSTGRES_PASSWORD` — пароль к production БД
- ID ассистентов (`HELPER_ID`, `SOULSLEEP_ID`, и т.д.) — из OpenAI Assistants

### .env.test (test)
- Уже содержит тестовый `BOT_TOKEN`
- Заполни `OPENAI_API_KEY`, `POSTGRES_PASSWORD`, ассистентов

> Файлы `.env.prod` и `.env.test` находятся в `.gitignore` — **не коммитим** их.

## 2. Проверь конфигурацию

```bash
python test_refactoring.py
```

Ожидаемый вывод:
```
✅ Production окружение: PASSED
✅ Test окружение: PASSED
🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!
```

Если проверка падает:
- Убедись, что токены заполнены без лишних пробелов или кавычек.
- Проверь, что PostgreSQL запущен и базы созданы:
  ```bash
  psql -U postgres -c "CREATE DATABASE soul_bot;"
  psql -U postgres -c "CREATE DATABASE soul_test_bot;"
  ```

## 3. Запусти ботов

```bash
# Production
ENV=prod python bot.py
# или
../scripts/run_prod.sh

# Test
ENV=test python bot.py
# или
../scripts/run_test.sh
```

Можно держать оба процесса в разных терминалах — они используют разные базы данных.

## 4. Что сделать после успешной проверки

1. Удалить дубликаты, если старые папки ещё лежат в корне:
   ```bash
   cd /Users/nikitagorokhov/dev/SoulNear
   rm -rf soul_test_bot
   rm -rf soul_bot_backup soul_test_bot_backup   # опционально, спустя несколько дней
   ```
2. Зафиксировать изменения:
   ```bash
   cd soul_bot
   git status
   git add .
   git commit -m "refactor: unify prod/test bots with env configs"
   git push
   ```

## 5. Быстрый справочник

- Production бот: `ENV=prod python bot.py`
- Test бот: `ENV=test python bot.py`
- Проверка настроек: `python test_refactoring.py`
- Скрипты: `../scripts/run_prod.sh`, `../scripts/run_test.sh`

## 6. FAQ

**Где взять токены?**  
- BOT_TOKEN: @BotFather  
- OPENAI_API_KEY: https://platform.openai.com/api-keys  
- Assistant IDs: https://platform.openai.com/assistants

**Можно ли запускать два бота одновременно?**  
Да. Они работают с разными базами (`soul_bot` и `soul_test_bot`).

**Что делать, если всё сломалось?**  
- Вернись к бэкапу: `cp -r soul_bot_backup soul_bot`  
- Проверь логи: `tail -f log.txt`  
- Убедись, что `.env.prod` и `.env.test` заполнены корректно

**Как ускорить запуск?**  
Добавь алиасы в `~/.zshrc` или `~/.bashrc`:
```bash
alias soul-prod='cd ~/dev/SoulNear/soul_bot && ENV=prod python bot.py'
alias soul-test='cd ~/dev/SoulNear/soul_bot && ENV=test python bot.py'
```

## 7. Мини-чеклист перед коммитом

- [ ] `.env.prod` и `.env.test` заполнены и не попали в git
- [ ] `python test_refactoring.py` прошёл
- [ ] `ENV=test python bot.py` отвечает в Telegram
- [ ] `ENV=prod python bot.py` отвечает (после смены токена)
- [ ] `log.txt` не содержит `ERROR`/`CRITICAL`

Следуя этой инструкции, production и test окружения работают из одной кодовой базы без копирования проектов.

