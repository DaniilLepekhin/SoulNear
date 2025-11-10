# 🔧 Исправление ошибки 502 Bad Gateway

## Симптомы
```
[Error] Failed to load resource: the server responded with a status of 502 (Bad Gateway) (practices, line 0)
[Error] ❌ getPractices error: – Error: HTTP error! status: 502
```

## Причина
WebApp API не может подключиться к базе данных PostgreSQL потому что:
- Отсутствует файл `.env` с настройками подключения
- Без `.env` приложение использует дефолтные значения и не может найти БД

## Быстрое решение (на сервере)

### 1. Скопировать настройки из soul_bot

```bash
cd /home/SoulNear/webapp_api
cat ../soul_bot/.env | grep -E "POSTGRES_|BOT_TOKEN|OPENAI" > .env
```

### 2. Перезапустить сервис

```bash
systemctl restart soul-webapp.service
```

### 3. Проверить

```bash
curl http://localhost:5000/api/practices
```

Должен вернуть JSON со статусом 200.

## Подробная документация

См. [DEPLOYMENT.md](./DEPLOYMENT.md) для полной инструкции по развертыванию.

## Проверка статуса

```bash
# Проверка сервиса
systemctl status soul-webapp.service

# Логи
journalctl -u soul-webapp.service -f

# Проверка порта
netstat -tlnp | grep 5000
```

## Что делать если не помогло

1. **Проверьте логи сервиса:**
   ```bash
   journalctl -u soul-webapp.service -n 100
   ```

2. **Проверьте подключение к БД:**
   ```bash
   psql -U postgres -d soul_bot -c "SELECT COUNT(*) FROM users;"
   ```

3. **Проверьте права доступа:**
   ```bash
   ls -la /home/SoulNear/webapp_api/.env
   chmod 600 /home/SoulNear/webapp_api/.env
   ```

4. **Проверьте установлены ли зависимости:**
   ```bash
   cd /home/SoulNear/webapp_api
   pip3 install -r requirements.txt
   ```

## Архитектура

```
Frontend (WebApp)
    ↓ HTTP Request to /api/practices
NGINX (:80)
    ↓ proxy_pass to localhost:5000
WebApp API (Quart app on :5000)
    ↓ Reads .env for DB credentials
PostgreSQL (:5432)
    ↓ Returns practices data
```

Ошибка 502 = разрыв между NGINX и WebApp API.
Чаще всего из-за того что WebApp API не может стартовать из-за отсутствия .env файла.
