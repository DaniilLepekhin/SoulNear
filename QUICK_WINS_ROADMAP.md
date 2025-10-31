# 🚀 Quick Wins Roadmap - Приоритетные улучшения

**Дата:** 31 октября 2025  
**Цель:** Поднять рейтинг системы с 7.5/10 до 9.0/10

---

## 📊 Статус

| Задача | Статус | Время | Impact |
|--------|--------|-------|--------|
| 1. Realtime mood detector | ✅ ГОТОВ | - | 🔥 9/10 |
| 2. Context relevance check | 📋 TODO | 1-2ч | 🔥 8/10 |
| 3. Unified style settings | 📋 TODO | 1ч | 🔥 8/10 |
| 4. Adaptive formatting | 📋 TODO | 3-4ч | 7/10 |
| 5. Legacy cleanup | 📋 TODO | 30м | 6/10 |

---

## ✅ #1: Realtime Mood Detector (DONE)

**Создано:**
- ✅ `soul_bot/bot/services/realtime_mood_detector.py` - модуль детекции
- ✅ `INTEGRATION_EXAMPLE_REALTIME_MOOD.md` - гайд по интеграции
- ✅ Тесты пройдены (5/5)

**Что делает:**
```
User: "у меня паническая атака"
Bot: [EMERGENCY MODE] "Сейчас тебе страшно, но ты в безопасности. 
     Давай дышать вместе: вдох на 4 счёта, выдох на 6..."
```

**Интеграция:** 15-20 минут (см. `INTEGRATION_EXAMPLE_REALTIME_MOOD.md`)

---

## 📋 #2: Context Relevance Check

**Проблема:**
```
User: "Какая погода сегодня?"
Bot: "Ты писал: 'опять прокрастинирую' — ты повторял это 5 раз..."
User: "???"
```

**Решение:**

### Файл: `soul_bot/bot/services/personalization/engine.py`

**Добавить ПЕРЕД line 131:**

```python
async def _is_personalization_relevant(user_message: str, primary_pattern: dict) -> bool:
    """
    Проверяет релевантность паттерна к текущему сообщению
    
    Fast heuristic (< 5ms):
    - Factual questions → False ("какая погода", "сколько стоит")
    - Emotional content → True ("грустно", "не могу")
    - Pattern keywords in message → True
    """
    # 1. Factual question indicators
    factual_indicators = ['какая', 'какой', 'сколько', 'когда', 'где', 'кто', 'что такое']
    if any(indicator in user_message.lower() for indicator in factual_indicators):
        return False
    
    # 2. Pattern keywords present?
    pattern_tags = primary_pattern.get('tags', [])
    if any(tag.lower() in user_message.lower() for tag in pattern_tags):
        return True
    
    # 3. Emotional content?
    emotional_keywords = ['чувствую', 'грустно', 'тревожно', 'боюсь', 'злюсь', 'не могу', 'страшно']
    if any(kw in user_message.lower() for kw in emotional_keywords):
        return True
    
    # 4. Short message (< 10 words) → probably not emotional
    if len(user_message.split()) < 10:
        return False
    
    return True  # Default: apply personalization
```

**Модифицировать функцию `build_personalized_response()` (line 131):**

```python
async def build_personalized_response(...) -> str:
    """Construct short personalized answer using detected patterns."""

    try:
        patterns_data = getattr(profile, 'patterns', {}) or {}
        patterns: List[dict] = patterns_data.get('patterns', []) if isinstance(patterns_data, dict) else []
    except Exception:
        logger.debug("[%s] personalization skipped: invalid profile", user_id)
        return base_response

    primary_pattern = _select_primary_pattern(patterns)

    if not primary_pattern:
        logger.debug("[%s] personalization skipped: no pattern with evidence", user_id)
        return base_response
    
    # 🔥 НОВОЕ: Проверяем релевантность
    is_relevant = await _is_personalization_relevant(user_message, primary_pattern)
    
    if not is_relevant:
        logger.debug("[%s] personalization skipped: not relevant to current message", user_id)
        return base_response
    
    # Остальная логика без изменений...
    evidence_list = primary_pattern['evidence']
    # ...
```

**Время:** 1-2 часа  
**Тестирование:** Попробовать factual questions после интеграции

---

## 📋 #3: Unified Style Settings

**Проблема:** 5 тапов для изменения одной настройки

### Файл: `soul_bot/bot/keyboards/profile.py`

**Заменить (lines 21-52):**

```python
# УДАЛИТЬ старые меню:
# - style_settings_menu
# - tone_menu
# - personality_menu
# - length_menu

# ДОБАВИТЬ новое unified меню:

style_settings_unified = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='━━━ ТОН ━━━', callback_data='noop')],  # Header
    [
        InlineKeyboardButton(text='🎩', callback_data='tone_formal'),
        InlineKeyboardButton(text='😊', callback_data='tone_friendly'),
        InlineKeyboardButton(text='😏', callback_data='tone_sarcastic'),
        InlineKeyboardButton(text='🔥', callback_data='tone_motivating'),
    ],
    [InlineKeyboardButton(text='━━ ЛИЧНОСТЬ ━━', callback_data='noop')],  # Header
    [
        InlineKeyboardButton(text='🧙 Наставник', callback_data='personality_mentor'),
        InlineKeyboardButton(text='👥 Друг', callback_data='personality_friend'),
        InlineKeyboardButton(text='💪 Коуч', callback_data='personality_coach'),
    ],
    [InlineKeyboardButton(text='━━━ ДЛИНА ━━━', callback_data='noop')],  # Header
    [
        InlineKeyboardButton(text='⚡⚡', callback_data='length_ultra_brief'),
        InlineKeyboardButton(text='⚡', callback_data='length_brief'),
    ],
    [
        InlineKeyboardButton(text='📝', callback_data='length_medium'),
        InlineKeyboardButton(text='📚', callback_data='length_detailed'),
    ],
    [InlineKeyboardButton(text='↩️ Назад к профилю', callback_data='profile')]
])
```

### Файл: `soul_bot/bot/handlers/user/profile.py`

**Модифицировать все handlers (tone/personality/length):**

```python
@dp.callback_query(F.data.startswith('tone_'))
async def update_tone_inline(call: CallbackQuery):
    """Изменить тон БЕЗ перехода на другой экран"""
    tone = call.data.replace('tone_', '')
    user_id = call.from_user.id
    
    # Обновляем БД
    await db_user_profile.update_style(user_id, tone_style=tone)
    
    # Получаем обновлённый профиль
    profile = await db_user_profile.get_or_create(user_id)
    
    # ОБНОВЛЯЕМ текст (показываем текущие настройки)
    await call.message.edit_text(
        text=_render_style_settings_text(profile),
        reply_markup=style_settings_unified,
        parse_mode='HTML'
    )
    
    # Quick feedback
    await call.answer("✅ Тон обновлён", show_alert=False)


# Аналогично для personality_ и length_ handlers
```

**Добавить helper функцию:**

```python
def _render_style_settings_text(profile) -> str:
    """Форматирует текст настроек стиля с текущими значениями"""
    tone_map = {
        'formal': '🎩 Формальный',
        'friendly': '😊 Дружелюбный',
        'sarcastic': '😏 Ироничный',
        'motivating': '🔥 Мотивирующий'
    }
    
    personality_map = {
        'mentor': '🧙 Наставник',
        'friend': '👥 Друг',
        'coach': '💪 Коуч'
    }
    
    length_map = {
        'ultra_brief': '⚡⚡ Очень коротко',
        'brief': '⚡ Кратко',
        'medium': '📝 Средне',
        'detailed': '📚 Подробно'
    }
    
    return f"""🎨 <b>Настройки стиля общения</b>

<b>Текущие настройки:</b>
├ Тон: {tone_map.get(profile.tone_style, 'не установлен')}
├ Личность: {personality_map.get(profile.personality, 'не установлена')}
└ Длина: {length_map.get(profile.message_length, 'не установлена')}

💡 Нажми на кнопку ниже, чтобы изменить настройку.
Изменения применяются моментально!"""
```

**Время:** 1 час  
**Результат:** 1 тап вместо 5 🎉

---

## 📋 #4: Adaptive Formatting

**Проблема:** Одинаковое форматирование для коротких (20 слов) и длинных (300+ слов) сообщений

### Файл (новый): `soul_bot/bot/services/formatting_service.py`

```python
"""
Адаптивное форматирование ответов бота
"""
import re


def format_bot_message(text: str, message_length_preference: str) -> str:
    """
    Адаптивное форматирование в зависимости от длины
    
    Rules:
    - Ultra brief (< 50 words): NO formatting (чтобы не перегружать)
    - Brief (50-100 words): Minimal bold для ключевых слов
    - Medium (100-300 words): Bold + lists
    - Detailed (300+ words): Full formatting + sections + emojis
    """
    word_count = len(text.split())
    
    if word_count < 50:
        return text  # Ultra brief: оставить как есть
    
    elif word_count < 100:
        return _apply_minimal_formatting(text)
    
    elif word_count < 300:
        return _apply_medium_formatting(text)
    
    else:
        return _apply_detailed_formatting(text)


def _apply_minimal_formatting(text: str) -> str:
    """Brief: выделяем только action verbs"""
    action_verbs = ['начни', 'сделай', 'попробуй', 'выдели', 'запиши', 'подумай']
    
    for verb in action_verbs:
        # Выделяем глаголы в начале предложения
        text = re.sub(rf'\b({verb})\b', r'<b>\1</b>', text, flags=re.IGNORECASE)
    
    return text


def _apply_medium_formatting(text: str) -> str:
    """Medium: bold + списки"""
    lines = text.split('\n')
    result = []
    
    # 1. Выделяем имя (если есть в начале)
    if lines and lines[0].strip().endswith(','):
        name = lines[0].strip()[:-1]
        lines[0] = f"<b>{name}</b>,"
    
    # 2. Конвертируем numbered lists в bullet points
    for line in lines:
        if re.match(r'^\d+\.\s', line):
            line = '• ' + re.sub(r'^\d+\.\s', '', line)
        result.append(line)
    
    return '\n'.join(result)


def _apply_detailed_formatting(text: str) -> str:
    """Detailed: секции + структура"""
    # Определяем секции по ключевым словам
    sections = {
        'паттерн': '🧠',
        'инсайт': '💡',
        'рекомендац': '📌',
        'примеры': '📝',
        'шаги': '🔢',
        'итого': '✅'
    }
    
    formatted = text
    for keyword, emoji in sections.items():
        formatted = re.sub(
            rf'^({keyword}.*?):\s*',
            rf'<b>{emoji} \1:</b>\n',
            formatted,
            flags=re.IGNORECASE | re.MULTILINE
        )
    
    # Конвертируем lists
    formatted = re.sub(r'^\d+\.\s', '• ', formatted, flags=re.MULTILINE)
    
    return formatted
```

### Интеграция в `soul_bot/bot/services/openai_service.py`

**После line 405:**

```python
if profile and profile.message_length:
    assistant_message = _enforce_message_length(assistant_message, profile.message_length)
    
    # 🔥 НОВОЕ: Адаптивное форматирование
    from bot.services.formatting_service import format_bot_message
    assistant_message = format_bot_message(assistant_message, profile.message_length)
```

**Время:** 3-4 часа  
**Тестирование:** Сравнить ответы разной длины

---

## 📋 #5: Legacy Cleanup

**Проблема:** 150+ строк deprecated кода в `ChatGPT.py`

### Шаг 1: Удалить legacy код

**Файл:** `soul_bot/bot/functions/ChatGPT.py`

**Заменить функцию `get_assistant_response()` (lines 29-147):**

```python
async def get_assistant_response(user_id: int,
                                 prompt: str,
                                 assistant: str) -> str | None:
    """
    Получить ответ от ассистента через ChatCompletion API
    """
    try:
        return await openai_service.get_chat_completion(
            user_id=user_id,
            message=prompt,
            assistant_type=assistant
        )
    except Exception as e:
        logging.error(f"ChatCompletion API failed: {e}")
        await send_error(function='get_assistant_response', error=e)
        return None
```

**Удалить функцию `new_context()` (lines 150-181)** - больше не нужна

### Шаг 2: Удалить thread_id из БД

**Создать миграцию:** `soul_bot/database/migrations/003_remove_thread_ids.sql`

```sql
-- Удаляем устаревшие thread_id колонки (legacy Assistant API)
ALTER TABLE users DROP COLUMN IF EXISTS helper_thread_id;
ALTER TABLE users DROP COLUMN IF EXISTS sleeper_thread_id;
ALTER TABLE users DROP COLUMN IF EXISTS assistant_thread_id;
```

**Запустить:**
```bash
psql -U $POSTGRES_USER -d $POSTGRES_DB -f soul_bot/database/migrations/003_remove_thread_ids.sql
```

### Шаг 3: Удалить config_old.py (если есть)

```bash
rm soul_bot/config_old.py
```

**Время:** 30 минут  
**Экономия:** ~150 строк кода, ~3 колонки БД

---

## 🎯 Итоговый Timeline

| Неделя | Задачи | Время |
|--------|--------|-------|
| Неделя 1 | #1 (✅) + #2 + #3 | ~3ч |
| Неделя 2 | #4 + #5 | ~4ч |

**Total:** ~7 часов чистой разработки

**Рейтинг:**
- Сейчас: 7.5/10
- После Week 1: 8.5/10 (+1.0)
- После Week 2: 9.0/10 (+0.5)

---

## 📚 Документация

Создано:
- ✅ `DEEP_ANALYSIS_AND_RECOMMENDATIONS.md` - полный анализ (120+ рекомендаций)
- ✅ `АНАЛИЗ_РЕЗЮМЕ.md` - краткое резюме на русском
- ✅ `realtime_mood_detector.py` - готовый модуль (#1)
- ✅ `INTEGRATION_EXAMPLE_REALTIME_MOOD.md` - гайд по интеграции
- ✅ `QUICK_WINS_ROADMAP.md` - этот roadmap

---

## ✅ Next Steps

1. **Интегрировать realtime mood detector** (15 минут)
   - См. `INTEGRATION_EXAMPLE_REALTIME_MOOD.md`

2. **Реализовать context relevance check** (1-2 часа)
   - См. раздел #2

3. **Унифицировать UI настроек** (1 час)
   - См. раздел #3

4. **После этих 3 → протестировать** (1 час)

5. **Потом: adaptive formatting + legacy cleanup** (4 часа)

---

**Prepared by:** AI Analysis Agent  
**Status:** Ready to implement ✅

