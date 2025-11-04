# 🎯 Context Filter Fix: Summary

**Date:** November 3, 2025  
**Issue:** Bot упоминает паттерны про отношения когда пользователь говорит про деньги

---

## 🐛 Проблема

**Кейс:**
```
Пользователь: проходит квиз про отношения → получает паттерн "Страх потери интереса"
Пользователь: "У меня постоянно нет денег"
Бот: "Ты писал: 'Страх быть отвергнутым... девушка меня оставит' ← WTF?!"
```

**Root Cause:**
1. `_select_primary_pattern()` НЕ использовал контекстную фильтрацию
2. `_is_personalization_relevant()` НЕ проверял `context_weights`
3. Паттерн выбирался ТОЛЬКО по frequency, игнорируя релевантность теме

---

## ✅ Решение

### 1. Интегрирована контекстная фильтрация в `_select_primary_pattern()`

**Файл:** `bot/services/personalization/engine.py`

```python
def _select_primary_pattern(
    patterns: List[dict],
    user_message: str = "",
    detected_topic: Optional[str] = None
):
    # 🎯 Step 1: Filter by context relevance
    if user_message:
        relevant_patterns = get_relevant_patterns_for_chat(
            patterns=patterns,
            user_message=user_message,
            detected_topic=detected_topic,
            max_patterns=5
        )
    
    # 🏆 Step 2: Sort by frequency & confidence
    # 📝 Step 3: Return first with evidence
```

**Что изменилось:**
- ✅ Сначала фильтруем паттерны по релевантности теме
- ✅ Среди релевантных выбираем по frequency
- ✅ Fallback на все паттерны если ничего не нашлось

### 2. Добавлена проверка `context_weights` в `_is_personalization_relevant()`

```python
def _is_personalization_relevant(
    user_message: str,
    primary_pattern: dict,
    detected_topic: Optional[str] = None
):
    # 🎯 0. Check context_weights FIRST
    if primary_pattern:
        context_weights = primary_pattern.get('context_weights', {})
        if context_weights:
            topic = detected_topic or detect_topic_from_message(user_message)
            relevance = context_weights.get(topic, 0.0)
            
            if relevance < 0.3:  # Threshold: 30%
                return False  # Skip personalization!
    
    # 1. Emotional content? → ALWAYS relevant
    # 2. Pattern keywords present? → relevant
    # ... rest of checks
```

**Что изменилось:**
- ✅ **ПЕРВЫМ** проверяется `context_weights`
- ✅ Если релевантность < 30% → персонализация не применяется
- ✅ Эмоциональный контент все равно персонализируется

### 3. Передача `user_message` и `detected_topic`

**В `build_personalized_response()`:**
```python
# Detect topic once
detected_topic = detect_topic_from_message(user_message)

# Use in pattern selection
primary_pattern = _select_primary_pattern(
    patterns=patterns,
    user_message=user_message,
    detected_topic=detected_topic
)

# Use in relevance check
is_relevant = _is_personalization_relevant(
    user_message=user_message,
    primary_pattern=primary_pattern,
    detected_topic=detected_topic
)
```

---

## 🧪 Тесты

**Добавлен новый тест:** `test_personalize_response_skips_irrelevant_pattern`

```python
profile.patterns = [
    {
        'title': 'Страх потери интереса',
        'context_weights': {
            'relationships': 1.0,
            'money': 0.1  # Very low!
        }
    }
]

result = await build_personalized_response(
    user_message='У меня постоянно нет денег'
)

# ✅ Should NOT mention relationship pattern
assert 'Страх быть отвергнутым' not in result
assert 'девушка' not in result
```

**Результаты:**
```
tests/unit/test_personalize_response.py ............... PASSED
tests/unit/test_pattern_context_filter.py ............. PASSED
```

---

## 🎯 Логика выбора паттерна

**Теперь:**
```
1. get_relevant_patterns_for_chat()
   ├─ Detect topic from message ("money", "relationships", etc)
   ├─ Score each pattern by context_weights
   └─ Return top-5 relevant patterns

2. _select_primary_pattern()
   ├─ Sort by (occurrences, confidence)
   └─ Return first with evidence

3. _is_personalization_relevant()
   ├─ Check context_weights[topic] >= 0.3
   ├─ Check emotional keywords
   ├─ Check pattern keywords
   └─ Return True/False
```

**Было:**
```
1. _select_primary_pattern()
   ├─ Sort ALL patterns by occurrences
   └─ Return first with evidence
   
2. _is_personalization_relevant()
   ├─ Check emotional keywords
   ├─ Check pattern keywords
   └─ Return True/False (но без context_weights!)
```

---

## 📊 Изменения в коде

**Файлы:**
- ✅ `bot/services/personalization/engine.py` - основные изменения
- ✅ `tests/unit/test_personalize_response.py` - новый тест
- ✅ `tests/unit/test_openai_service.py` - fix индентации

**Статистика:**
- `engine.py`: +80 строк (улучшенная логика + docstrings)
- `test_personalize_response.py`: +46 строк (новый тест)

**Импорты:**
```python
from bot.services.pattern_context_filter import (
    get_relevant_patterns_for_chat,
    detect_topic_from_message,
)
```

---

## 🚀 Эффект

**До:**
```
User: "У меня нет денег"
Bot: "Ты писал: 'девушка меня оставит' — это проявление Страх потери интереса"
→ WTF момент! 😱
```

**После:**
```
User: "У меня нет денег"
Bot: "Давай разберемся с твоими финансами. Что именно тебя беспокоит?"
→ Релевантный ответ! ✅
```

**Когда персонализация ВСЕ ЕЩЕ применяется:**
- Эмоциональное сообщение: "Чувствую тревогу из-за денег" → может упомянуть паттерн
- Ключевые слова паттерна: "Боюсь что девушка уйдет" → упомянет паттерн про отношения
- Высокая релевантность: context_weights[topic] >= 0.3

**Когда персонализация пропускается:**
- Низкая релевантность: context_weights[topic] < 0.3
- Factual question: "Сколько стоит биткоин?"
- Very short: "Ок"

---

## ✅ Checklist

- [x] Интегрирована контекстная фильтрация в `_select_primary_pattern()`
- [x] Добавлена проверка `context_weights` в `_is_personalization_relevant()`
- [x] Передается `user_message` и `detected_topic` во все функции
- [x] Добавлен тест для кейса "relationship pattern + money message"
- [x] Все существующие тесты проходят
- [x] Нет конфликтов в промптах
- [x] Docstrings обновлены
- [x] Логирование добавлено

---

**Status:** ✅ Ready for merge  
**Breaking Changes:** None  
**Backward Compatible:** Yes (fallback если `context_weights` отсутствует)

