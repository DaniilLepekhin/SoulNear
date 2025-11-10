# WebApp API Deployment Guide

## Проблема: 502 Bad Gateway

Ошибка 502 возникает когда:
- API сервис (webapp_api) не может подключиться к базе данных
- Отсутствует `.env` файл с настройками

## Решение

### 1. Создать .env файл на сервере

SSH в сервер и создайте файл `/home/SoulNear/webapp_api/.env`:

```bash
ssh root@37.221.127.100 -p 61943
cd /home/SoulNear/webapp_api
nano .env
```

### 2. Содержимое .env файла

```.env
# OpenAI Configuration (скопируйте из /home/SoulNear/soul_bot/.env)
OPENAI_API_KEY=sk-...
HELPER_ID=asst_...
SOULSLEEP_ID=asst_...
RELATIONSHIPS_ID=asst_...
MONEY_ID=asst_...
CONFIDENCE_ID=asst_...
FEARS_ID=asst_...

# Database Configuration (ДОЛЖНЫ СОВПАДАТЬ с soul_bot)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<пароль_из_soul_bot_env>
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=soul_bot

# Telegram Bot Token (для /api/audio endpoint)
BOT_TOKEN=<token_из_soul_bot_env>
```

**ВАЖНО:** Значения `POSTGRES_*` и `BOT_TOKEN` нужно скопировать из `/home/SoulNear/soul_bot/.env`

### 3. Проверить права доступа

```bash
chmod 600 /home/SoulNear/webapp_api/.env
```

### 4. Перезапустить сервис

```bash
systemctl restart soul-webapp.service
```

### 5. Проверить логи

```bash
journalctl -u soul-webapp.service -f
```

### 6. Проверить API

```bash
curl http://localhost:5000/api/practices
```

Должен вернуть JSON с practices, videos и music.

## Структура nginx

Убедитесь что nginx проксирует `/api/*` на порт 5000:

```nginx
location /api/ {
    proxy_pass http://localhost:5000/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}
```

## Проверка работоспособности

После настройки проверьте:

1. **Локально на сервере:**
   ```bash
   curl http://localhost:5000/api/practices
   ```

2. **Через nginx:**
   ```bash
   curl http://localhost/api/practices
   ```

3. **Извне:**
   ```bash
   curl http://37.221.127.100/api/practices
   ```

Все три запроса должны возвращать одинаковый JSON ответ со статусом 200.

## Troubleshooting

### Ошибка: "Empty reply from server"
- Проверьте что сервис запущен: `systemctl status soul-webapp.service`
- Проверьте логи: `journalctl -u soul-webapp.service -n 50`
- Возможно приложение падает при запуске из-за отсутствия .env

### Ошибка: "Connection refused"
- Сервис не запущен
- Запустите: `systemctl start soul-webapp.service`

### Ошибка 502 от nginx
- Бэкенд недоступен на порту 5000
- Проверьте что приложение слушает на правильном порту:
  ```bash
  netstat -tlnp | grep 5000
  ```

### База данных не найдена
- Убедитесь что `POSTGRES_DB` в webapp_api/.env совпадает с soul_bot/.env
- По умолчанию используется имя `soul_bot`
