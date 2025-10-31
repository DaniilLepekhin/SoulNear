# 🚀 Единый план улучшений SOUL.near Bot

**Дата:** 31 октября 2025  
**Источники:** Анализ 3 AI агентов + собственный аудит  
**Scope:** Telegram бот (веб-версия исключена)

---

## 📊 Консолидированный анализ

### Что все агенты нашли (консенсус):

✅ **UI настроек стиля требует упрощения** (5 тапов → 1 тап)  
✅ **Форматирование не адаптируется к длине/контексту**  
✅ **Персонализация слишком агрессивная** (не учитывает контекст)  
✅ **Квиз недостаточно адаптивный** (триггерится только раз)  
✅ **Legacy код не удалён** (Assistant API, config_old.py)

### Уникальные находки по агентам:

**Агент 1 (философ):**
- Иерархический анализ паттернов (surface → existential)
- Темповая адаптация общения
- Time-based tones (утро/вечер/ночь)

**Агент 2 (практик):**
- Готовый код улучшенного меню ✅
- Модуль formatting.py ✅

**Агент 3 (аудитор):**
- Magic numbers вместо констант (КРИТИЧНО!)
- conversation_metrics не используется
- learning_preferences теряет порядок (set → OrderedDict)
- therapist есть в constants, но не в UI
- Temperature режим (auto-адаптация стиля по mood)
- Quick switch пресеты

**Мой вклад:**
- Realtime mood detector для экстренных ситуаций
- Context relevance check для персонализации
- Emergency prompts для кризисов

---

## 🎯 UNIFIED PLAN (приоритеты)

---

## PHASE 1: РЕФАКТОРИНГ И ОЧИСТКА (Приоритет: 🔥 CRITICAL)

**Timeline:** 2-3 часа  
**Impact:** Code health 6/10 → 9/10

### 1.1 Удалить Legacy код ⏱️ 30 минут

**Файлы для удаления:**

```bash
# Полностью удалить
rm soul_bot/config_old.py
rm -rf webapp_test_bot/

# Markdown отчёты (архивировать или удалить)
rm soul_bot/STAGE_1_PROGRESS.md
rm soul_bot/STAGE_2_COMPLETE.md
rm soul_bot/STAGE_2_FIX.md
rm soul_bot/NEXT_STEPS.md
# (оставить только актуальные: README.md, TESTING.md)
```

**Рефакторинг:**

`soul_bot/bot/functions/ChatGPT.py` - удалить legacy Assistant API:

```python
# УДАЛИТЬ lines 59-147 (весь блок с feature flag)
async def get_assistant_response(user_id: int, prompt: str, assistant: str) -> str | None:
    """Получить ответ через ChatCompletion API (unified)"""
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

# УДАЛИТЬ функцию new_context() (lines 150-181)
```

**Миграция БД:**

```sql
-- soul_bot/database/migrations/003_remove_thread_ids.sql
ALTER TABLE users DROP COLUMN IF EXISTS helper_thread_id;
ALTER TABLE users DROP COLUMN IF EXISTS sleeper_thread_id;
ALTER TABLE users DROP COLUMN IF EXISTS assistant_thread_id;
```

**Экономия:** ~180 строк кода, 3 колонки БД

---

### 1.2 Magic Numbers → Константы ⏱️ 1 час

**Проблема (найдена Агентом 3):**

```python
# soul_bot/bot/services/pattern_analyzer.py:511-512
if message_count > 0 and message_count % 3 == 0:  # ← magic number!
    await quick_analysis(user_id, assistant_type)
if message_count > 0 and message_count % 20 == 0:  # ← magic number!
    await deep_analysis(user_id, assistant_type)
```

**Решение:**

`soul_bot/bot/services/constants.py` - добавить:

```python
# Pattern Analysis Frequencies
QUICK_ANALYSIS_FREQUENCY = 3  # messages
DEEP_ANALYSIS_FREQUENCY = 20  # messages
QUICK_ANALYSIS_MIN_MESSAGES = 4
DEEP_ANALYSIS_MIN_MESSAGES = 10

# Pattern Analysis Context Sizes
QUICK_ANALYSIS_CONTEXT_SIZE = 15  # messages
DEEP_ANALYSIS_CONTEXT_SIZE = 30  # messages

# Уже есть, но используются непоследовательно:
# QUICK_ANALYSIS_FREQUENCY = 5  ← КОНФЛИКТ! Исправить на 3 или использовать
```

**Обновить:**

`soul_bot/bot/services/pattern_analyzer.py`:

```python
from bot.services.constants import (
    QUICK_ANALYSIS_FREQUENCY,
    DEEP_ANALYSIS_FREQUENCY,
    QUICK_ANALYSIS_MIN_MESSAGES,
    DEEP_ANALYSIS_MIN_MESSAGES,
    QUICK_ANALYSIS_CONTEXT_SIZE,
    DEEP_ANALYSIS_CONTEXT_SIZE
)

async def quick_analysis(user_id: int, assistant_type: str = 'helper'):
    messages = await conversation_history.get_context(
        user_id=user_id,
        assistant_type=assistant_type,
        max_messages=QUICK_ANALYSIS_CONTEXT_SIZE  # вместо 15
    )
    
    if len(messages) < QUICK_ANALYSIS_MIN_MESSAGES:  # вместо 4
        logger.debug("Not enough messages for analysis")
        return
    # ...

async def analyze_if_needed(user_id: int, assistant_type: str = 'helper'):
    message_count = await conversation_history.count_messages(user_id, assistant_type)
    
    if message_count > 0 and message_count % QUICK_ANALYSIS_FREQUENCY == 0:
        await quick_analysis(user_id, assistant_type)
    
    if message_count > 0 and message_count % DEEP_ANALYSIS_FREQUENCY == 0:
        await deep_analysis(user_id, assistant_type)
```

**Impact:** Упрощает конфигурацию, устраняет баги

---

### 1.3 Cleanup неиспользуемых полей ⏱️ 30 минут

**Проблема (найдена Агентом 3):**

`conversation_metrics` объявлено в модели, добавлено в миграции, но **НЕ обновляется нигде**.

**Решение - Option A (рекомендуется):** Удалить поле

```sql
-- soul_bot/database/migrations/004_cleanup_unused_fields.sql
ALTER TABLE user_profiles DROP COLUMN IF EXISTS conversation_metrics;
```

`soul_bot/database/models/user_profile.py` - удалить:

```python
# УДАЛИТЬ:
# conversation_metrics: Mapped[dict] = mapped_column(JSONB, default=lambda: {...})
```

**Решение - Option B:** Начать использовать

```python
# soul_bot/bot/services/openai_service.py

async def save_conversation(...):
    # После сохранения сообщений
    await _update_conversation_metrics(user_id, assistant_type)

async def _update_conversation_metrics(user_id: int, assistant_type: str):
    """Обновить метрики общения"""
    profile = await user_profile.get_or_create(user_id)
    metrics = profile.conversation_metrics
    
    # Обновляем total_messages
    metrics['total_messages'] = metrics.get('total_messages', 0) + 1
    
    # Обновляем avg_session_length, most_discussed_topics, question_types
    # ...
    
    await user_profile.update_metrics(user_id, metrics)
```

**Рекомендация:** Option A (удалить), если не планируется использовать в ближайшие 2 недели.

---

### 1.4 Fix learning_preferences порядок ⏱️ 20 минут

**Проблема (найдена Агентом 3):**

```python
# soul_bot/bot/services/pattern_analyzer.py:465-472
works_well = set(learning_prefs.get('works_well', []))  # ← теряем порядок!
doesnt_work = set(learning_prefs.get('doesnt_work', []))

works_well.update(learning_data.get('works_well', []))
doesnt_work.update(learning_data.get('doesnt_work', []))

learning_prefs['works_well'] = list(works_well)[-10:]  # ← случайный порядок
learning_prefs['doesnt_work'] = list(doesnt_work)[-10:]
```

**Решение:**

```python
from collections import OrderedDict

async def _update_learning_preferences(user_id: int, learning_data: dict):
    """Обновить learning preferences (что работает/не работает)"""
    profile = await user_profile.get_or_create(user_id)
    learning_prefs = profile.learning_preferences
    
    # Используем OrderedDict для сохранения порядка (новые в конец)
    works_well = OrderedDict.fromkeys(learning_prefs.get('works_well', []))
    doesnt_work = OrderedDict.fromkeys(learning_prefs.get('doesnt_work', []))
    
    # Добавляем новые (дедупликация автоматическая)
    for item in learning_data.get('works_well', []):
        works_well[item] = None
    for item in learning_data.get('doesnt_work', []):
        doesnt_work[item] = None
    
    # Limit: последние 10 (самые свежие)
    learning_prefs['works_well'] = list(works_well.keys())[-10:]
    learning_prefs['doesnt_work'] = list(doesnt_work.keys())[-10:]
    
    # Сохраняем
    # ...
```

**Impact:** UI будет показывать свежие предпочтения первыми

---

## PHASE 2: UI/UX УЛУЧШЕНИЯ (Приоритет: 🔥 HIGH)

**Timeline:** 3-4 часа  
**Impact:** User satisfaction 6/10 → 9/10

### 2.1 Unified Style Settings Menu ⏱️ 1 час

**Проблема:** 5 тапов для изменения одной настройки

**Решение (готовый код от Агента 2):**

`soul_bot/bot/keyboards/profile.py` - использовать `build_style_settings_menu_v2()`:

```python
def build_style_settings_menu_v2(current_tone: str, current_personality: str, current_length: str):
    """
    Улучшенное меню настроек - ВСЁ в одном экране
    
    Формат callback_data: style_{category}_{value}
    Например: style_tone_friendly, style_personality_mentor
    """
    tone_buttons = [
        InlineKeyboardButton(
            text=f"{'✓ ' if current_tone == 'formal' else ''}🎩 Формальный",
            callback_data='style_tone_formal'
        ),
        InlineKeyboardButton(
            text=f"{'✓ ' if current_tone == 'friendly' else ''}😊 Дружелюбный",
            callback_data='style_tone_friendly'
        ),
    ]
    # ... аналогично для personality и length
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='━━━ ТОН ━━━', callback_data='noop')],
        tone_buttons,
        [InlineKeyboardButton(text='━━ ЛИЧНОСТЬ ━━', callback_data='noop')],
        personality_buttons,
        [InlineKeyboardButton(text='━━━ ДЛИНА ━━━', callback_data='noop')],
        length_buttons,
        [InlineKeyboardButton(text='↩️ Назад к профилю', callback_data='profile')]
    ])
```

**Обновить handlers:**

```python
@dp.callback_query(F.data.startswith('style_'))
async def update_style_inline(call: CallbackQuery):
    """Универсальный handler для всех настроек стиля"""
    _, category, value = call.data.split('_')  # style_tone_friendly
    
    user_id = call.from_user.id
    
    # Обновляем БД
    if category == 'tone':
        await db_user_profile.update_style(user_id, tone_style=value)
    elif category == 'personality':
        await db_user_profile.update_style(user_id, personality=value)
    elif category == 'length':
        await db_user_profile.update_style(user_id, message_length=value)
    
    # Обновляем меню (показываем галочки на новых значениях)
    profile = await db_user_profile.get_or_create(user_id)
    new_menu = build_style_settings_menu_v2(
        profile.tone_style,
        profile.personality,
        profile.message_length
    )
    
    await call.message.edit_reply_markup(reply_markup=new_menu)
    await call.answer("✅ Обновлено", show_alert=False)
```

**Результат:** 1 тап вместо 5 🎉

---

### 2.2 Quick Switch Пресеты ⏱️ 1.5 часа

**Идея (от Агента 3):** Добавить быстрые пресеты ("коучер + кратко", "друг + подробно")

**Реализация:**

`soul_bot/bot/keyboards/profile.py`:

```python
STYLE_PRESETS = {
    'coach_brief': {
        'name': '💪 Коуч (кратко)',
        'tone': 'motivating',
        'personality': 'coach',
        'length': 'brief'
    },
    'friend_detailed': {
        'name': '👥 Друг (подробно)',
        'tone': 'friendly',
        'personality': 'friend',
        'length': 'detailed'
    },
    'therapist_medium': {
        'name': '🧘 Терапевт (средне)',
        'tone': 'formal',
        'personality': 'therapist',  # ← добавляем therapist!
        'length': 'medium'
    },
    'mentor_balanced': {
        'name': '🧙 Мудрец (сбалансировано)',
        'tone': 'friendly',
        'personality': 'mentor',
        'length': 'medium'
    }
}

def build_style_presets_menu():
    """Меню быстрых пресетов"""
    buttons = [
        [InlineKeyboardButton(
            text=preset['name'],
            callback_data=f'preset_{preset_id}'
        )]
        for preset_id, preset in STYLE_PRESETS.items()
    ]
    
    buttons.append([
        InlineKeyboardButton(text='⚙️ Детальные настройки', callback_data='style_settings'),
        InlineKeyboardButton(text='↩️ Назад', callback_data='profile')
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
```

**Handler:**

```python
@dp.callback_query(F.data.startswith('preset_'))
async def apply_preset(call: CallbackQuery):
    """Применить пресет стиля"""
    preset_id = call.data.replace('preset_', '')
    preset = STYLE_PRESETS.get(preset_id)
    
    if not preset:
        await call.answer("Пресет не найден", show_alert=True)
        return
    
    user_id = call.from_user.id
    
    # Применяем все настройки сразу
    await db_user_profile.update_style(
        user_id,
        tone_style=preset['tone'],
        personality=preset['personality'],
        message_length=preset['length']
    )
    
    await call.answer(f"✅ Применён пресет: {preset['name']}", show_alert=False)
    
    # Возвращаем в профиль
    await profile_callback(call, None)
```

**Добавить therapist в UI:**

`soul_bot/bot/keyboards/profile.py`:

```python
personality_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧙‍♂️ Мудрый наставник', callback_data='personality_mentor')],
    [InlineKeyboardButton(text='👥 Поддерживающий друг', callback_data='personality_friend')],
    [InlineKeyboardButton(text='💪 Строгий коуч', callback_data='personality_coach')],
    [InlineKeyboardButton(text='🧘 Терапевт', callback_data='personality_therapist')],  # ← НОВОЕ
    [InlineKeyboardButton(text='↩️ Назад', callback_data='style_settings')]
])
```

**Обновить openai_service.py:**

```python
# soul_bot/bot/services/openai_service.py:218-221

personality_map = {
    'mentor': '⚠️ ОБЯЗАТЕЛЬНО: Веди себя как МУДРЫЙ НАСТАВНИК...',
    'friend': '⚠️ ОБЯЗАТЕЛЬНО: Будь ПОДДЕРЖИВАЮЩИМ ДРУГОМ...',
    'coach': '⚠️ ОБЯЗАТЕЛЬНО: Действуй как СТРОГИЙ КОУЧ...',
    'therapist': '⚠️ ОБЯЗАТЕЛЬНО: Будь ПРОФЕССИОНАЛЬНЫМ ТЕРАПЕВТОМ - деликатный, безоценочный, фокус на понимании чувств.'  # ← НОВОЕ
}
```

**Impact:** Быстрый выбор стиля за 1 клик

---

### 2.3 Прогресс-бар в квизе ⏱️ 30 минут

**Проблема:** Пользователь не видит прогресс

**Решение:**

`soul_bot/bot/services/quiz_service/generator.py`:

```python
def format_question_for_telegram(question: dict, current: int, total: int) -> str:
    """Форматировать вопрос для Telegram"""
    
    # Визуальный прогресс-бар
    progress = current / total
    filled = int(progress * 10)
    bar = "█" * filled + "░" * (10 - filled)
    percentage = int(progress * 100)
    
    text = f"""<b>Вопрос {current} из {total}</b>
{bar} {percentage}%

{question['text']}"""
    
    return text
```

**Результат:**
```
Вопрос 3 из 10
███░░░░░░░ 30%

Как часто вы чувствуете одиночество?
```

---

## PHASE 3: АЛГОРИТМИЧЕСКИЕ УЛУЧШЕНИЯ (Приоритет: 🔥 HIGH)

**Timeline:** 6-8 часов  
**Impact:** Bot intelligence 7.5/10 → 9.0/10

### 3.1 Realtime Mood Detector ⏱️ 15 минут (интеграция)

**Статус:** ✅ Код готов (`realtime_mood_detector.py`)

**Интеграция:** См. `INTEGRATION_EXAMPLE_REALTIME_MOOD.md`

```python
# soul_bot/bot/services/openai_service.py:366-368

try:
    # 🚨 STEP 0: Проверяем экстренные сигналы
    urgent_signal = detect_urgent_emotional_signals(message)
    
    # 1. Строим system prompt
    if should_override_system_prompt(urgent_signal):
        system_prompt = build_emergency_prompt(
            emotion=urgent_signal.emotion,
            base_instructions=_get_base_instructions(assistant_type)
        )
        logger.warning(f"🚨 EMERGENCY MODE: {urgent_signal.emotion}")
    else:
        system_prompt = await build_system_prompt(user_id, assistant_type)
```

**Impact:** Немедленная реакция на кризисы (9/10)

---

### 3.2 Context Relevance Check ⏱️ 1.5 часа

**Проблема:** Персонализация применяется даже к factual questions

**Решение:**

`soul_bot/bot/services/personalization/engine.py` - добавить ПЕРЕД line 131:

```python
async def _is_personalization_relevant(user_message: str, primary_pattern: dict) -> bool:
    """
    Проверяет релевантность паттерна к текущему сообщению
    
    Fast heuristic (< 5ms)
    """
    message_lower = user_message.lower()
    
    # 1. Factual questions → skip personalization
    factual_indicators = [
        'какая', 'какой', 'какое', 'сколько', 'когда', 'где', 
        'кто', 'что такое', 'как называется', 'почему', 'зачем'
    ]
    # Проверяем наличие question mark + factual indicator
    if '?' in user_message and any(ind in message_lower for ind in factual_indicators):
        # НО: если есть эмоциональный контекст → всё равно персонализируем
        emotional_keywords = ['чувствую', 'боюсь', 'тревожно', 'страшно', 'грустно']
        if not any(kw in message_lower for kw in emotional_keywords):
            return False
    
    # 2. Pattern keywords present? → relevant
    pattern_tags = primary_pattern.get('tags', [])
    if any(tag.lower() in message_lower for tag in pattern_tags):
        return True
    
    # 3. Emotional content? → relevant
    emotional_keywords = ['чувствую', 'грустно', 'тревожно', 'боюсь', 'злюсь', 
                          'не могу', 'страшно', 'тяжело', 'больно', 'одиноко']
    if any(kw in message_lower for kw in emotional_keywords):
        return True
    
    # 4. Very short message (< 5 words) → probably not emotional
    if len(user_message.split()) < 5:
        return False
    
    # 5. Default: apply personalization (conservative)
    return True
```

**Модифицировать `build_personalized_response()`:**

```python
async def build_personalized_response(...) -> str:
    # ... existing code ...
    
    primary_pattern = _select_primary_pattern(patterns)
    if not primary_pattern:
        return base_response
    
    # 🔥 НОВОЕ: Проверяем релевантность
    is_relevant = await _is_personalization_relevant(user_message, primary_pattern)
    
    if not is_relevant:
        logger.debug("[%s] personalization skipped: not relevant", user_id)
        return base_response
    
    # Остальная логика без изменений
    # ...
```

**Impact:** Устраняет неуместную персонализацию (8/10)

---

### 3.3 Temperature Режим (auto-адаптация стиля) ⏱️ 2 часа

**Идея (от Агента 3):** Авто-переключение стиля по mood/stress

**Реализация:**

`soul_bot/bot/services/temperature_adapter.py` (НОВЫЙ ФАЙЛ):

```python
"""
Temperature Adapter - авто-адаптация стиля по эмоциональному состоянию

Логика:
- Если stress_level = high → brief + supportive
- Если mood = energetic → motivating + medium
- Если mood = slightly_down → friendly + empathetic
"""

def adapt_style_to_temperature(profile) -> dict:
    """
    Адаптировать стиль на основе эмоционального состояния
    
    Returns:
        {
            'tone_override': Optional[str],
            'length_override': Optional[str],
            'intensity_modifier': float  # 0.5-1.5 (multiplier for temperature)
        }
    """
    emotional_state = profile.emotional_state
    
    stress_level = emotional_state.get('stress_level', 'medium')
    current_mood = emotional_state.get('current_mood', 'neutral')
    energy_level = emotional_state.get('energy_level', 'medium')
    
    overrides = {
        'tone_override': None,
        'length_override': None,
        'intensity_modifier': 1.0
    }
    
    # HIGH STRESS → краткость + поддержка
    if stress_level == 'high':
        overrides['length_override'] = 'brief'
        overrides['tone_override'] = 'friendly'  # убираем сарказм
        overrides['intensity_modifier'] = 0.7  # спокойнее
        
    # LOW ENERGY → короткие ответы
    elif energy_level == 'low':
        overrides['length_override'] = 'brief'
        overrides['intensity_modifier'] = 0.8
        
    # ENERGETIC → мотивация + драйв
    elif current_mood == 'energetic':
        overrides['tone_override'] = 'motivating'
        overrides['intensity_modifier'] = 1.3  # больше драйва
        
    # SLIGHTLY_DOWN → эмпатия + поддержка
    elif current_mood == 'slightly_down':
        overrides['tone_override'] = 'friendly'
        overrides['length_override'] = 'medium'  # больше слов поддержки
        overrides['intensity_modifier'] = 0.9
    
    return overrides
```

**Интеграция в openai_service.py:**

```python
# soul_bot/bot/services/openai_service.py

from bot.services.temperature_adapter import adapt_style_to_temperature

async def build_system_prompt(user_id: int, assistant_type: str, ...) -> str:
    profile = await user_profile.get_or_create(user_id)
    
    # 🔥 НОВОЕ: Temperature adaptation
    temp_overrides = adapt_style_to_temperature(profile)
    
    # Применяем overrides
    effective_tone = temp_overrides['tone_override'] or profile.tone_style
    effective_length = temp_overrides['length_override'] or profile.message_length
    
    # Строим style instructions с учётом overrides
    style_instructions = _cached_style_instructions(
        effective_tone,
        profile.personality,
        effective_length
    )
    
    # ... остальная логика
```

**Добавить в get_chat_completion():**

```python
# После line 385 (ChatCompletion.create):

# Применяем intensity modifier к temperature
temp_overrides = adapt_style_to_temperature(profile)
effective_temperature = temperature * temp_overrides['intensity_modifier']

response: ChatCompletion = await client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=effective_temperature,  # вместо просто temperature
    max_tokens=2000
)
```

**Impact:** Бот автоматически подстраивается под состояние (8/10)

---

### 3.4 Адаптивное форматирование (merge с Агентом 2) ⏱️ 2 часа

**Статус:** Агент 2 создал `formatting.py`, но нужен merge с моими идеями

**Финальная версия:**

`soul_bot/bot/services/formatting.py`:

```python
"""
Адаптивное форматирование ответов бота

Правила:
- Ultra brief (< 50 words): plain text
- Brief (50-100): minimal formatting (action verbs bold)
- Medium (100-300): structured (headers, lists)
- Detailed (300+): full formatting (sections, highlights)
"""

import re
from typing import Optional

def format_bot_message(
    text: str, 
    message_length_preference: str,
    learning_preferences: Optional[dict] = None
) -> str:
    """
    Адаптивное форматирование в зависимости от длины и предпочтений
    
    Args:
        text: Исходный текст
        message_length_preference: ultra_brief|brief|medium|detailed
        learning_preferences: Что работает/не работает для пользователя
    """
    word_count = len(text.split())
    
    # Проверяем learning preferences
    if learning_preferences:
        doesnt_work = learning_preferences.get('doesnt_work', [])
        
        # Если пользователь не любит списки → не форматируем их
        if 'списки' in doesnt_work or 'bullet points' in doesnt_work:
            return text  # оставить как есть
        
        # Если не любит bold → не выделяем
        if 'жирный текст' in doesnt_work or 'bold' in doesnt_work:
            return text
    
    # Форматирование по длине
    if word_count < 50:
        return text  # Ultra brief: no formatting
    
    elif word_count < 100:
        return _apply_minimal_formatting(text)
    
    elif word_count < 300:
        return _apply_medium_formatting(text)
    
    else:
        return _apply_detailed_formatting(text)


def _apply_minimal_formatting(text: str) -> str:
    """Brief: выделяем только action verbs"""
    action_verbs = [
        'начни', 'сделай', 'попробуй', 'выдели', 'запиши', 
        'подумай', 'прочитай', 'напиши', 'спроси'
    ]
    
    for verb in action_verbs:
        # Выделяем только в начале предложения или после переноса
        text = re.sub(
            rf'(^|\n)({verb})\b',
            r'\1<b>\2</b>',
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )
    
    return text


def _apply_medium_formatting(text: str) -> str:
    """Medium: структура + списки"""
    lines = text.split('\n')
    result = []
    
    # 1. Выделяем имя пользователя (если в начале)
    if lines and ',' in lines[0]:
        parts = lines[0].split(',', 1)
        if len(parts[0].split()) == 1:  # Одно слово → имя
            lines[0] = f"<b>{parts[0]}</b>,{parts[1]}"
    
    # 2. Конвертируем numbered lists в bullet points
    for line in lines:
        stripped = line.strip()
        
        # Numbered list
        if re.match(r'^\d+\.\s', stripped):
            line = '• ' + re.sub(r'^\d+\.\s', '', stripped)
        
        # Dash list
        elif stripped.startswith('- '):
            line = '• ' + stripped[2:]
        
        result.append(line)
    
    # 3. Выделяем ключевые фразы
    formatted = '\n'.join(result)
    
    # "Важно:", "Совет:", etc.
    key_phrases = ['важно', 'совет', 'рекомендация', 'помни', 'обрати внимание']
    for phrase in key_phrases:
        formatted = re.sub(
            rf'\b({phrase})\b:',
            r'<b>\1</b>:',
            formatted,
            flags=re.IGNORECASE
        )
    
    return formatted


def _apply_detailed_formatting(text: str) -> str:
    """Detailed: секции + полная структура"""
    
    # 1. Detect sections by keywords
    sections = {
        'паттерн': '🧠',
        'инсайт': '💡',
        'рекомендац': '📌',
        'примеры': '📝',
        'шаги': '🔢',
        'итого': '✅',
        'важно': '⚠️',
        'помни': '🎯'
    }
    
    formatted = text
    
    # Добавляем emojis к секциям
    for keyword, emoji in sections.items():
        # Находим строки начинающиеся с keyword (case-insensitive)
        formatted = re.sub(
            rf'^({keyword}.*?):\s*',
            rf'<b>{emoji} \1:</b>\n',
            formatted,
            flags=re.IGNORECASE | re.MULTILINE
        )
    
    # 2. Конвертируем списки
    lines = formatted.split('\n')
    result = []
    
    for line in lines:
        stripped = line.strip()
        
        # Numbered list → bullet
        if re.match(r'^\d+\.\s', stripped):
            line = '  • ' + re.sub(r'^\d+\.\s', '', stripped)
        
        # Dash list → bullet
        elif stripped.startswith('- '):
            line = '  • ' + stripped[2:]
        
        result.append(line)
    
    # 3. Выделяем цитаты
    formatted = '\n'.join(result)
    
    # "Ты говорил: 'цитата'" → italic для цитаты
    formatted = re.sub(
        r"'([^']+)'",
        r"<i>'\1'</i>",
        formatted
    )
    formatted = re.sub(
        r'"([^"]+)"',
        r'<i>"\1"</i>',
        formatted
    )
    
    return formatted
```

**Интеграция:**

```python
# soul_bot/bot/services/openai_service.py:404-406

if profile and profile.message_length:
    assistant_message = _enforce_message_length(assistant_message, profile.message_length)
    
    # 🔥 Адаптивное форматирование
    from bot.services.formatting import format_bot_message
    assistant_message = format_bot_message(
        text=assistant_message,
        message_length_preference=profile.message_length,
        learning_preferences=profile.learning_preferences
    )
```

**Impact:** Читаемость ответов +40% (7/10)

---

### 3.5 Улучшение Adaptive Quiz ⏱️ 2.5 часа

**Проблема 1 (найдена Агентом 3):** Триггерится только раз, не track'ает что уже спрашивали

**Решение:**

`soul_bot/bot/services/quiz/adaptive_quiz_service.py`:

```python
class AdaptiveQuizService:
    BRANCH_AFTER_QUESTION = 5
    MAX_BRANCHES = 2  # ← НОВОЕ: можно добавить вопросы дважды
    
    async def should_branch(self, session: QuizSession) -> bool:
        """Определить нужно ли добавить follow-up вопросы"""
        
        # Считаем сколько раз уже branched
        branch_count = getattr(session, 'branch_count', 0)
        
        # Можем branch максимум 2 раза (после Q5 и Q8)
        if branch_count >= self.MAX_BRANCHES:
            return False
        
        # Branch точки: Q5, Q8
        branch_points = [5, 8]
        if session.current_question_index not in branch_points:
            return False
        
        # Нужно минимум 3 новых ответа с прошлого branch
        answers_since_last_branch = len(session.answers) - getattr(session, 'last_branch_at', 0)
        if answers_since_last_branch < 3:
            return False
        
        return True
    
    async def get_adaptive_questions(self, session: QuizSession) -> list[dict]:
        """Main method: analyze patterns and generate follow-ups"""
        
        patterns = await self.analyze_patterns(session)
        
        # ... existing logic ...
        
        # 🔥 НОВОЕ: Track что уже спрашивали
        asked_patterns = getattr(session, 'asked_patterns', set())
        
        # Фильтруем паттерны которые уже спрашивали
        new_patterns = [
            p for p in strong_patterns
            if p.get('title') not in asked_patterns
        ]
        
        if not new_patterns:
            logger.info("All patterns already covered")
            return []
        
        # Генерируем вопросы для нового паттерна
        top_pattern = new_patterns[0]
        followups = await self.generate_followup_questions(top_pattern, session)
        
        # Обновляем tracking
        asked_patterns.add(top_pattern.get('title'))
        session.asked_patterns = asked_patterns
        session.branch_count = getattr(session, 'branch_count', 0) + 1
        session.last_branch_at = len(session.answers)
        
        return followups
```

**Проблема 2:** Не учитывает предыдущие квизы

**Решение:**

`soul_bot/bot/services/quiz_service/generator.py`:

```python
async def generate_questions(
    category: str,
    count: int = 8,
    user_profile: Optional[dict] = None,
    previous_answers: Optional[list[dict]] = None
) -> list[dict]:
    """
    Генерация вопросов с учётом профиля и истории
    """
    
    # Извлекаем существующие паттерны
    existing_patterns = []
    if user_profile:
        existing_patterns = user_profile.get('patterns', [])
    
    # 🔥 НОВОЕ: Анализируем какие темы уже well-understood
    well_understood_topics = []
    for pattern in existing_patterns:
        if pattern.get('occurrences', 0) > 5 and pattern.get('confidence', 0) > 0.8:
            # Паттерн хорошо понятен → избегаем повторных вопросов
            well_understood_topics.extend(pattern.get('tags', []))
    
    # Формируем prompt для GPT
    context = f"""
Category: {category}
User has {len(existing_patterns)} existing patterns.

Well-understood topics (avoid these): {', '.join(well_understood_topics[:5])}

Weak patterns (validate these):
{_format_weak_patterns(existing_patterns)}

Generate {count} questions that:
1. AVOID well-understood topics
2. EXPLORE gaps in understanding
3. VALIDATE weak patterns (confidence < 0.7)
4. DISCOVER new aspects
"""
    
    # ... existing GPT call ...
```

**Impact:** Квиз становится действительно адаптивным (8/10)

---

## PHASE 4: РАСШИРЕННЫЕ УЛУЧШЕНИЯ (Приоритет: MEDIUM)

**Timeline:** 8-10 часов  
**Impact:** Nice to have (6-7/10 each)

### 4.1 Иерархический анализ паттернов ⏱️ 3 часа

**Идея (от Агента 1):** surface → behavioral → emotional → existential

**Реализация:**

`soul_bot/bot/services/pattern_analyzer.py`:

```python
PATTERN_HIERARCHY = {
    'surface': {
        'depth': 1,
        'examples': ['I feel tired', 'Work is busy', 'Weather is bad']
    },
    'behavioral': {
        'depth': 2,
        'examples': ['Procrastination', 'Avoidance', 'Perfectionism']
    },
    'emotional': {
        'depth': 3,
        'examples': ['Fear of failure', 'Imposter syndrome', 'Anxiety']
    },
    'cognitive': {
        'depth': 3,
        'examples': ['Black-white thinking', 'Catastrophizing']
    },
    'existential': {
        'depth': 4,
        'examples': ['Life meaning', 'Purpose', 'Values conflict']
    }
}

async def _analyze_conversation_quick(messages, existing_patterns) -> dict:
    """Quick analysis with hierarchy detection"""
    
    prompt = f"""
Analyze conversation and detect patterns at MULTIPLE DEPTH LEVELS:

HIERARCHY:
1. Surface (depth=1): Observable facts, symptoms
2. Behavioral (depth=2): Repeated actions, habits
3. Emotional (depth=3): Underlying feelings, fears
4. Existential (depth=4): Deep values, life meaning

Current patterns: {existing_patterns}

Return JSON with hierarchy:
{{
  "new_patterns": [
    {{
      "title": "...",
      "type": "behavioral",
      "depth": 2,
      "parent_pattern": "surface_pattern_id",  # if derived from another
      "description": "..."
    }}
  ]
}}
"""
    # ... existing GPT call ...
```

**Визуализация в профиле:**

```
🧠 Паттерны (иерархия):

📍 Surface:
  • Усталость (5x)
  
  └─ 🔄 Behavioral:
     • Прокрастинация (8x)
     
     └─ 💭 Emotional:
        • Страх неудачи (3x)
        
        └─ 🌟 Existential:
           • Поиск смысла в работе (1x)
```

**Impact:** Глубокое понимание пользователя (7/10)

---

### 4.2 Темповая адаптация ⏱️ 2.5 часа

**Идея (от Агента 1):** Адаптация под response_time, message_length пользователя

**Реализация:**

`soul_bot/database/models/user_profile.py` - добавить:

```python
# Темп общения (добавить в модель)
communication_tempo: Mapped[dict] = mapped_column(
    JSONB,
    default=lambda: {
        "avg_response_time": None,  # seconds
        "avg_message_length": None,  # words
        "conversation_density": "medium",  # sparse|medium|dense
        "preferred_depth": "medium"  # surface|medium|deep
    }
)
```

**Трекинг:**

`soul_bot/bot/services/openai_service.py`:

```python
async def save_conversation(...):
    # ... existing code ...
    
    # 🔥 Track communication tempo
    await _update_communication_tempo(user_id, user_message, assistant_message)

async def _update_communication_tempo(user_id: int, user_message: str, assistant_message: str):
    """Обновить темп общения"""
    profile = await user_profile.get_or_create(user_id)
    tempo = profile.communication_tempo
    
    # Считаем длину сообщения пользователя
    user_words = len(user_message.split())
    
    # Обновляем среднюю длину (moving average)
    current_avg = tempo.get('avg_message_length') or user_words
    new_avg = (current_avg * 0.9) + (user_words * 0.1)  # exponential moving average
    tempo['avg_message_length'] = int(new_avg)
    
    # Определяем conversation_density
    if new_avg < 10:
        tempo['conversation_density'] = 'sparse'
    elif new_avg < 30:
        tempo['conversation_density'] = 'medium'
    else:
        tempo['conversation_density'] = 'dense'
    
    # Сохраняем
    await user_profile.update_tempo(user_id, tempo)
```

**Применение:**

```python
async def build_system_prompt(...):
    # ...
    tempo = profile.communication_tempo
    
    # Если пользователь пишет коротко → бот пишет коротко
    if tempo.get('conversation_density') == 'sparse':
        # Override length to brief
        effective_length = 'brief'
    elif tempo.get('conversation_density') == 'dense':
        # Пользователь любит подробности → можем detailed
        effective_length = 'detailed'
```

**Impact:** Бот подстраивается под темп (6/10)

---

### 4.3 Time-based tones ⏱️ 1.5 часа

**Идея (от Агента 1):** Ночь → успокаивающий, утро → мотивирующий

**Реализация:**

`soul_bot/bot/services/time_adapter.py` (НОВЫЙ ФАЙЛ):

```python
"""
Time-based tone adaptation
"""
from datetime import datetime
import pytz

def get_time_based_tone_modifier(user_timezone: str = 'Europe/Moscow') -> dict:
    """
    Определить модификатор тона на основе времени суток
    
    Returns:
        {
            'suggested_tone': Optional[str],
            'energy_modifier': float,  # 0.5-1.5
            'should_be_brief': bool
        }
    """
    # Получаем текущий час по timezone пользователя
    tz = pytz.timezone(user_timezone)
    now = datetime.now(tz)
    hour = now.hour
    
    # Night (22:00-06:00) → calming, brief
    if hour >= 22 or hour < 6:
        return {
            'suggested_tone': 'friendly',  # убираем сарказм
            'energy_modifier': 0.6,  # спокойнее
            'should_be_brief': True
        }
    
    # Morning (06:00-10:00) → motivating, energetic
    elif 6 <= hour < 10:
        return {
            'suggested_tone': 'motivating',
            'energy_modifier': 1.3,
            'should_be_brief': False
        }
    
    # Day (10:00-18:00) → normal
    elif 10 <= hour < 18:
        return {
            'suggested_tone': None,  # no override
            'energy_modifier': 1.0,
            'should_be_brief': False
        }
    
    # Evening (18:00-22:00) → reflective, medium
    else:
        return {
            'suggested_tone': 'friendly',
            'energy_modifier': 0.9,
            'should_be_brief': False
        }
```

**Интеграция:**

```python
# soul_bot/bot/services/openai_service.py

from bot.services.time_adapter import get_time_based_tone_modifier

async def build_system_prompt(...):
    # ...
    
    # 🔥 Time-based adaptation
    time_modifier = get_time_based_tone_modifier()
    
    # Применяем только если нет high stress (приоритет у temperature)
    if not temp_overrides['tone_override']:
        if time_modifier['suggested_tone']:
            effective_tone = time_modifier['suggested_tone']
        
        if time_modifier['should_be_brief']:
            effective_length = 'brief'
```

**Impact:** Бот адаптируется к времени суток (6/10)

---

## 📊 ИТОГОВЫЙ ROADMAP

### Quick Wins (Week 1): 6-8 часов

| Задача | Время | Impact | Priority |
|--------|-------|--------|----------|
| 1.1 Legacy cleanup | 30м | 6/10 | 🔥 |
| 1.2 Magic numbers → constants | 1ч | 7/10 | 🔥 |
| 1.3 Cleanup unused fields | 30м | 5/10 | 🔥 |
| 1.4 Fix learning_preferences | 20м | 6/10 | 🔥 |
| 2.1 Unified style menu | 1ч | 8/10 | 🔥 |
| 2.2 Quick switch presets | 1.5ч | 7/10 | 🔥 |
| 2.3 Quiz progress bar | 30м | 6/10 | MEDIUM |
| 3.1 Realtime mood detector | 15м | 9/10 | 🔥🔥🔥 |
| 3.2 Context relevance | 1.5ч | 8/10 | 🔥 |

**Total Week 1:** ~7.5 часов  
**Result:** 7.5/10 → 8.5/10

---

### Main Improvements (Week 2): 6-7 часов

| Задача | Время | Impact | Priority |
|--------|-------|--------|----------|
| 3.3 Temperature режим | 2ч | 8/10 | 🔥 |
| 3.4 Adaptive formatting | 2ч | 7/10 | 🔥 |
| 3.5 Improved adaptive quiz | 2.5ч | 8/10 | MEDIUM |

**Total Week 2:** ~6.5 часов  
**Result:** 8.5/10 → 9.0/10

---

### Advanced Features (Week 3-4): 8-10 часов

| Задача | Время | Impact | Priority |
|--------|-------|--------|----------|
| 4.1 Hierarchical patterns | 3ч | 7/10 | LOW |
| 4.2 Tempo adaptation | 2.5ч | 6/10 | LOW |
| 4.3 Time-based tones | 1.5ч | 6/10 | LOW |

**Total Week 3-4:** ~7 часов  
**Result:** 9.0/10 → 9.3/10

---

## 🎯 PRIORITIES SUMMARY

### MUST DO (Critical Path):

1. **Realtime mood detector** (15м) - 9/10 impact ← START HERE
2. **Legacy cleanup** (30м) - tech debt
3. **Magic numbers fix** (1ч) - code quality
4. **Unified style menu** (1ч) - UX pain point
5. **Context relevance** (1.5ч) - fixes annoying bug
6. **Quick switch presets** (1.5ч) - great UX
7. **Temperature режим** (2ч) - smart adaptation
8. **Adaptive formatting** (2ч) - readability

**Total:** ~10 часов → Рейтинг 7.5 → 9.0

---

### NICE TO HAVE (Phase 2):

9. Improved adaptive quiz (2.5ч)
10. Quiz progress bar (30м)
11. learning_preferences fix (20м)
12. cleanup unused fields (30м)

---

### FUTURE (Phase 3):

13. Hierarchical patterns (3ч)
14. Tempo adaptation (2.5ч)
15. Time-based tones (1.5ч)

---

## 🚀 QUICK START GUIDE

### Day 1 (2 часа):

```bash
# 1. Интегрировать realtime mood detector (15м)
# См. INTEGRATION_EXAMPLE_REALTIME_MOOD.md

# 2. Legacy cleanup (30м)
rm soul_bot/config_old.py
# Отредактировать ChatGPT.py (удалить lines 59-181)

# 3. Magic numbers → constants (1ч)
# Отредактировать pattern_analyzer.py
# Использовать QUICK_ANALYSIS_FREQUENCY из constants.py

# 4. Тестирование
pytest soul_bot/tests/unit/test_pattern_analyzer.py
```

### Day 2 (3 часа):

```bash
# 5. Unified style menu (1ч)
# Отредактировать bot/keyboards/profile.py
# Добавить build_style_settings_menu_v2()
# Обновить handlers в bot/handlers/user/profile.py

# 6. Context relevance check (1.5ч)
# Отредактировать bot/services/personalization/engine.py
# Добавить _is_personalization_relevant()

# 7. Quick switch presets (1.5ч)
# Добавить STYLE_PRESETS в profile.py
# Добавить therapist в personality_menu
```

### Day 3 (4 часа):

```bash
# 8. Temperature режим (2ч)
# Создать bot/services/temperature_adapter.py
# Интегрировать в openai_service.py

# 9. Adaptive formatting (2ч)
# Merge с кодом Агента 2 (formatting.py)
# Интегрировать в openai_service.py
```

**Total:** 3 дня × 3 часа = 9 часов  
**Result:** Bot 7.5/10 → 9.0/10 🎉

---

## 📝 ФАЙЛЫ ДЛЯ ИЗМЕНЕНИЯ

### Создать новые:

- ✅ `soul_bot/bot/services/realtime_mood_detector.py` (готов)
- `soul_bot/bot/services/temperature_adapter.py`
- `soul_bot/bot/services/time_adapter.py`
- `soul_bot/bot/services/formatting.py` (merge с версией Агента 2)
- `soul_bot/database/migrations/003_remove_thread_ids.sql`
- `soul_bot/database/migrations/004_cleanup_unused_fields.sql`

### Изменить существующие:

- `soul_bot/bot/functions/ChatGPT.py` (удалить legacy)
- `soul_bot/bot/services/pattern_analyzer.py` (constants, OrderedDict)
- `soul_bot/bot/services/openai_service.py` (интеграции)
- `soul_bot/bot/services/personalization/engine.py` (context relevance)
- `soul_bot/bot/keyboards/profile.py` (unified menu, presets, therapist)
- `soul_bot/bot/handlers/user/profile.py` (новые handlers)
- `soul_bot/bot/services/quiz/adaptive_quiz_service.py` (tracking)
- `soul_bot/bot/services/quiz_service/generator.py` (profile-aware)
- `soul_bot/bot/services/constants.py` (добавить константы)

### Удалить:

- `soul_bot/config_old.py`
- `webapp_test_bot/` (весь каталог)
- Markdown отчёты (опционально)

---

## ✅ ЧЕКЛИСТ ПЕРЕД СТАРТОМ

- [ ] Сделать backup БД
- [ ] Сделать git branch `feature/unified-improvements`
- [ ] Протестировать realtime_mood_detector.py (тесты уже есть ✅)
- [ ] Проверить что все feature flags включены в .env.test
- [ ] Подготовить тестовые кейсы для новых функций

---

## 🎓 LESSONS LEARNED

**От Агента 1 (философ):**
- Иерархический анализ - сильная концепция
- Темповая адаптация - хорошая идея
- НО: слишком амбициозный scope

**От Агента 2 (практик):**
- Готовый код - лучший вклад
- Unified menu - сразу можно использовать
- НО: узкий фокус (только UI)

**От Агента 3 (аудитор):**
- Конкретные баги с номерами строк - ЗО Л ОТО
- Magic numbers, conversation_metrics - критичные находки
- Temperature режим, quick switch - отличные идеи
- НО: саркастичный тон иногда отвлекает

**Мой вклад:**
- Realtime mood detector - уникальная фича
- Context relevance - фиксит реальную проблему
- Emergency prompts - могут спасти жизни

---

**Prepared by:** Consolidated AI Team  
**Ready to implement:** ✅ YES  
**Total effort:** ~16 часов (3 weeks)  
**Expected result:** 7.5/10 → 9.3/10

