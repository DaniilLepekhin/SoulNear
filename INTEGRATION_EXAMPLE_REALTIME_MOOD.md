# 🚨 Интеграция Realtime Mood Detector

**Файл:** `soul_bot/bot/services/realtime_mood_detector.py` ✅ СОЗДАН  
**Интеграция в:** `soul_bot/bot/services/openai_service.py`

---

## 📋 Пошаговая интеграция

### Шаг 1: Импорт модуля

```python
# soul_bot/bot/services/openai_service.py
# В начале файла добавить:

from bot.services.realtime_mood_detector import (
    detect_urgent_emotional_signals,
    should_override_system_prompt,
    build_emergency_prompt
)
```

### Шаг 2: Модификация get_chat_completion()

**Найти функцию:**
```python
async def get_chat_completion(
    user_id: int,
    message: str,
    assistant_type: str,
    model: str = "gpt-4-turbo-preview",
    max_history_messages: int = 10,
    temperature: float = 0.7
) -> Optional[str]:
```

**БЫЛО (lines 366-368):**
```python
try:
    # 1. Строим system prompt
    system_prompt = await build_system_prompt(user_id, assistant_type)
```

**СТАЛО:**
```python
try:
    # 🚨 STEP 0: Проверяем экстренные эмоциональные сигналы (< 1ms)
    urgent_signal = detect_urgent_emotional_signals(message)
    
    # 1. Строим system prompt
    if should_override_system_prompt(urgent_signal):
        # EMERGENCY MODE: используем экстренный prompt
        base_instructions = _get_base_instructions(assistant_type)
        system_prompt = build_emergency_prompt(
            emotion=urgent_signal.emotion,
            base_instructions=base_instructions
        )
        
        logger.warning(
            f"🚨 EMERGENCY MODE activated for user {user_id}: "
            f"{urgent_signal.emotion} (urgency: {urgent_signal.urgency})"
        )
    else:
        # NORMAL MODE: стандартный персонализированный prompt
        system_prompt = await build_system_prompt(user_id, assistant_type)
```

### Шаг 3: Логирование (опционально)

После успешного ответа добавить:

```python
# После line 415 (return assistant_message):

# Логируем emergency events
if urgent_signal and urgent_signal.urgency == 'high':
    logger.info(
        f"Emergency response sent to user {user_id}: "
        f"emotion={urgent_signal.emotion}, "
        f"confidence={urgent_signal.confidence:.2f}, "
        f"keywords={urgent_signal.trigger_keywords}"
    )
```

---

## 🧪 Тестирование

### Test Case 1: Паническая атака

**Input:**
```python
user_message = "помогите у меня паническая атака прямо сейчас"
```

**Ожидаемый результат:**
- `detect_urgent_emotional_signals()` → `EmotionalSignal(urgency='high', emotion='panic')`
- `should_override_system_prompt()` → `True`
- `system_prompt` = emergency prompt для panic
- Ответ бота: короткий, конкретный, техники дыхания

**Проверка в логах:**
```
WARNING: 🚨 EMERGENCY MODE activated for user 123456: panic (urgency: high)
```

---

### Test Case 2: Обычное сообщение

**Input:**
```python
user_message = "какая погода сегодня"
```

**Ожидаемый результат:**
- `detect_urgent_emotional_signals()` → `None`
- `should_override_system_prompt()` → `False`
- `system_prompt` = стандартный персонализированный prompt
- Ответ бота: обычный

---

### Test Case 3: Суицидальные мысли

**Input:**
```python
user_message = "не хочу больше жить всё бессмысленно"
```

**Ожидаемый результат:**
- `detect_urgent_emotional_signals()` → `EmotionalSignal(urgency='high', emotion='despair')`
- `should_override_system_prompt()` → `True`
- `system_prompt` = emergency prompt для despair
- Ответ бота: эмпатия, безопасность, конкретная помощь

**Проверка в логах:**
```
WARNING: 🚨 EMERGENCY MODE activated for user 123456: despair (urgency: high)
```

---

## 📊 Метрики (опционально)

Можно добавить отслеживание emergency events:

```python
# soul_bot/bot/services/openai_service.py

# После отправки ответа (line ~428):

if urgent_signal:
    # Инкрементим статистику emergency events
    await db_statistic_day.increment(f'emergency_{urgent_signal.emotion}')
    
    # Если urgency=high → уведомляем админов (опционально)
    if urgent_signal.urgency == 'high':
        await _send_admin_notification(
            f"🚨 Emergency: {urgent_signal.emotion} detected for user {user_id}"
        )
```

---

## 🔧 Конфигурация (опционально)

Можно добавить feature flag для включения/выключения:

```python
# soul_bot/config.py

FEATURE_FLAGS = {
    ...
    'ENABLE_REALTIME_MOOD_DETECTION': os.getenv('ENABLE_REALTIME_MOOD_DETECTION', 'true').lower() == 'true',
}
```

**В openai_service.py:**
```python
from config import is_feature_enabled

# В get_chat_completion():
if is_feature_enabled('ENABLE_REALTIME_MOOD_DETECTION'):
    urgent_signal = detect_urgent_emotional_signals(message)
else:
    urgent_signal = None
```

---

## ✅ Checklist

- [ ] Импортировать модуль в `openai_service.py`
- [ ] Добавить проверку `detect_urgent_emotional_signals()` перед `build_system_prompt()`
- [ ] Добавить логирование emergency events
- [ ] Протестировать на panic case
- [ ] Протестировать на despair case
- [ ] Протестировать на обычном сообщении
- [ ] (Опционально) Добавить метрики
- [ ] (Опционально) Добавить feature flag

---

## 🎯 Итого

**Изменения в коде:** ~15 строк  
**Новый файл:** `realtime_mood_detector.py` (уже создан ✅)  
**Время интеграции:** 15-20 минут  
**Impact:** 🔥 CRITICAL (9/10)

**Результат:** Бот будет немедленно реагировать на экстренные эмоциональные сигналы, не дожидаясь pattern analysis.

---

**P.S.** После интеграции запустить:
```bash
python soul_bot/bot/services/realtime_mood_detector.py
# Должны пройти все 5 тестов ✅
```

