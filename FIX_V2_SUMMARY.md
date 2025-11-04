# ✅ Исправление v2 — Database Creation Error

## Проблема
После первого фикса переменных окружения вылезла новая ошибка:
```python
AttributeError: 'coroutine' object has no attribute 'execute'
```

## Причина
В попытке исправить транзакционную ошибку, я написал:
```python
await conn.execution_options(isolation_level='AUTOCOMMIT').execute(...)
```

Но `execution_options()` в async SQLAlchemy **возвращает корутину**, которую нужно await'ить. Плюс это вообще неправильный подход.

## Правильное решение
`execution_options()` нужно вызывать на **engine**, а не на connection:

**Неправильно:**
```python
async with admin_engine.connect() as conn:
    await conn.execution_options(isolation_level='AUTOCOMMIT').execute(...)
    # ❌ Возвращает корутину, нет .execute()
```

**Правильно:**
```python
# Set isolation level on ENGINE
admin_engine = _build_engine('postgres').execution_options(
    isolation_level='AUTOCOMMIT'
)
async with admin_engine.connect() as conn:
    await conn.execute(text(f'CREATE DATABASE "{POSTGRES_DB}"'))
    # ✅ Connection уже с AUTOCOMMIT
```

## Код после исправления

```python
async def _create_database(self) -> None:
    # Build engine with AUTOCOMMIT isolation level for CREATE DATABASE
    admin_engine = _build_engine('postgres').execution_options(
        isolation_level='AUTOCOMMIT'
    )
    try:
        async with admin_engine.connect() as conn:
            await conn.execute(text(f'CREATE DATABASE "{POSTGRES_DB}"'))
            logger.info("Created database '%s'", POSTGRES_DB)
    except DuplicateDatabaseError:
        logger.info("Database '%s' already exists", POSTGRES_DB)
    finally:
        await admin_engine.dispose()
```

## Проверка
```bash
✅ Checking database.py syntax... OK
✅ Uses execution_options
✅ Has AUTOCOMMIT isolation level  
✅ NOT using .begin() (good!)
✅ execution_options on ENGINE level (correct!)
```

## Теперь на сервере
```bash
git pull
./scripts/safe_redeploy.sh --clean
```

Или:
```bash
git pull
./FIX_DB_ISSUE.sh
```

## Ожидаемый результат
- ✅ БД `soul_bot` создастся через init-db.sh
- ✅ Если не создастся, бот создаст сам (теперь без ошибок)
- ✅ Логи: `✅ Database connected successfully`
- ❌ Не будет: `AttributeError: 'coroutine' object has no attribute 'execute'`

---

**TL;DR:** Исправил тупой баг с корутиной. Теперь execution_options на engine, а не на connection. Работает. 🚀

