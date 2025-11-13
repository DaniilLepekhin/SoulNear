# WebApp API v2

Новая версия API для webapp_v2, использующая тот же подход что и soul_bot (ChatCompletion API).

## 🚀 Основные изменения

### Было (v1):
- ❌ Использовал Assistants API (устаревший подход)
- ❌ Хранил thread_id в таблице users
- ❌ Не было персонализации
- ❌ Не использовал новые таблицы

### Стало (v2):
- ✅ Использует ChatCompletion API (как soul_bot)
- ✅ Работает с таблицами: `conversation_history`, `chat_messages`, `user_profiles`
- ✅ Полная персонализация через user_profiles
- ✅ Поддержка всех assistant_type из бота
- ✅ Единая кодовая база с soul_bot

## 📊 Архитектура

```
webapp_api/
├── app_v2.py           # Новый API на базе ChatCompletion
├── app.py              # Старый API (для совместимости)
├── requirements.txt    # Обновленные зависимости
├── Dockerfile          # Dockerfile с поддержкой soul_bot
└── README_V2.md       # Документация

soul_bot/               # Общий код
├── database/
│   ├── models/        # Модели БД
│   └── repository/    # Репозитории
└── bot/services/
    └── openai_service.py  # ChatCompletion логика
```

## 🔌 API Endpoints

### Chat
- `POST /api/chat` - Отправить сообщение и получить ответ
- `GET /api/chat/history/<user_id>` - Получить историю чата
- `POST /api/chat/save` - Сохранить сообщение
- `POST /api/chat/clear` - Очистить историю

### User & Profile
- `GET /api/user/<user_id>` - Информация о пользователе
- `GET /api/profile/<user_id>` - Полный профиль
- `GET /api/profile/<user_id>/patterns` - Паттерны пользователя
- `GET /api/profile/<user_id>/insights` - Инсайты
- `GET /api/profile/<user_id>/emotional-state` - Эмоциональное состояние

### Practices
- `GET /api/practices` - Все практики по категориям

### Mood Tracking
- `POST /api/mood/save` - Сохранить настроение
- `GET /api/mood/history/<user_id>` - История настроения

## 🚀 Запуск

### Локально

```bash
# Установить зависимости
cd webapp_api
pip install -r requirements.txt

# Запустить
python app_v2.py
```

### Docker

```bash
# Билд и запуск через docker-compose
docker-compose up -d api

# Логи
docker logs -f soulnear_api

# Рестарт после изменений
docker-compose restart api
```

## 🔧 Конфигурация

В `.env.prod`:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost  # для локального запуска
POSTGRES_PORT=5432
POSTGRES_DB=soul_bot

# OpenAI
OPENAI_API_KEY=sk-...

# Assistant IDs (не нужны для ChatCompletion, но оставлены для совместимости)
HELPER_ID=asst_...
```

## 📝 Примеры использования

### Отправить сообщение

```javascript
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    user_id: 123456789,
    message: "Привет!",
    assistant_type: "helper"
  })
});

const data = await response.json();
console.log(data.response);
```

### Получить профиль

```javascript
const response = await fetch('/api/profile/123456789');
const data = await response.json();

console.log(data.data.patterns);      // Паттерны пользователя
console.log(data.data.insights);      // Инсайты
console.log(data.data.emotional_state); // Эмоциональное состояние
```

## 🔀 Миграция с v1

1. **База данных** - новые таблицы создаются автоматически soul_bot
2. **Эндпоинты** - совместимы с webapp_v2, только URL может измениться
3. **Формат ответов** - идентичный, изменения минимальные

## 🐛 Отладка

```bash
# Проверить health check
curl http://localhost:8001/health

# Проверить подключение к БД
docker logs soulnear_api | grep "Database connection"

# Проверить ошибки
docker logs soulnear_api | grep ERROR
```

## 📚 Связанные файлы

- `soul_bot/bot/services/openai_service.py` - Основная логика ChatCompletion
- `soul_bot/database/repository/conversation_history.py` - Работа с историей
- `soul_bot/database/repository/user_profile.py` - Работа с профилями
- `webapp_v2/src/services/api.ts` - Frontend клиент

## ✨ Преимущества v2

1. **Единая кодовая база** - один источник правды для bot и api
2. **Персонализация** - каждый ответ учитывает профиль пользователя
3. **Гибкость** - полный контроль над промптами и контекстом
4. **Современность** - ChatCompletion API вместо deprecated Assistants
5. **Производительность** - быстрее, меньше запросов к OpenAI

## 🔜 Roadmap

- [ ] WebSocket поддержка для real-time чатов
- [ ] Стриминг ответов
- [ ] Кеширование промптов
- [ ] Метрики и мониторинг
- [ ] Rate limiting per user
