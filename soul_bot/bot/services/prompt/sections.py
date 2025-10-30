"""
🎨 LEVEL 2: Prompt Sections для персонализированного system prompt

Каждая функция возвращает отформатированную секцию промпта.
Если данных нет - возвращает пустую строку.
"""
from typing import Optional


def render_style_section(style_instructions: str) -> str:
    """Секция настроек стиля (tone, personality, length)"""
    if not style_instructions:
        return ""
    return style_instructions


def render_base_instructions(base_instructions: str) -> str:
    """Базовые инструкции для ассистента"""
    if not base_instructions:
        return ""
    return f"""## 🤖 РОЛЬ И ЦЕЛЬ:
{base_instructions}"""


def render_user_info(user) -> str:
    """Информация о пользователе (имя, возраст, пол)"""
    if not user:
        return ""
    
    parts = []
    
    display_name = None
    if hasattr(user, 'real_name') and user.real_name:
        display_name = user.real_name
    elif hasattr(user, 'first_name') and user.first_name:
        display_name = user.first_name
    
    if display_name:
        parts.append(f"Имя: {display_name}")
    
    if hasattr(user, 'age') and user.age:
        parts.append(f"Возраст: {user.age}")
    
    if hasattr(user, 'gender') and user.gender:
        gender_map = {'male': 'Мужской', 'female': 'Женский', 'other': 'Другое'}
        parts.append(f"Пол: {gender_map.get(user.gender, user.gender)}")
    
    if not parts:
        return ""
    
    return f"""## 👤 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ:
{chr(10).join(parts)}"""


def render_patterns_section(profile) -> str:
    """
    Секция с выявленными паттернами пользователя
    
    LEVEL 2: Включает evidence (цитаты из диалогов)
    """
    if not profile or not profile.patterns:
        return ""
    
    patterns = profile.patterns.get('patterns', [])
    if not patterns:
        return ""
    
    # Берём топ-5 паттернов (сортировка по occurrences)
    top_patterns = sorted(
        patterns,
        key=lambda p: p.get('occurrences', 1),
        reverse=True
    )[:5]
    
    pattern_texts = []
    for pattern in top_patterns:
        title = pattern.get('title', 'Unknown')
        pattern_type = pattern.get('type', 'behavioral').upper()
        description = pattern.get('description', '')
        occurrences = pattern.get('occurrences', 1)
        confidence = pattern.get('confidence', 0.7)
        evidence = pattern.get('evidence', [])[:3]  # Макс 3 примера
        tags = pattern.get('tags', [])
        
        pattern_text = f"""**[{pattern_type}] {title}**
Описание: {description}
Частота: встречается {occurrences}x (уверенность {int(confidence * 100)}%)"""
        
        # 🎯 LEVEL 2: Добавляем evidence (конкретные цитаты)
        if evidence:
            evidence_lines = [f'  • "{quote}"' for quote in evidence]
            pattern_text += f"\n📝 Примеры из диалогов пользователя:\n{chr(10).join(evidence_lines)}"
        
        if tags:
            pattern_text += f"\nТеги: {', '.join(tags)}"
        
        pattern_texts.append(pattern_text)
    
    patterns_str = "\n\n".join(pattern_texts)
    
    return f"""## 🧠 Выявленные паттерны пользователя:

{patterns_str}

⚠️ ВАЖНО: Используй эти КОНКРЕТНЫЕ ПРИМЕРЫ из диалогов в своих ответах.
Формат: 'Помнишь, ты говорил: "[точная цитата]". Это проявление [паттерн]...'"""


def render_recent_messages_section(recent_user_messages: list[str]) -> str:
    """
    🔥 LEVEL 2 FIX: Секция с последними сообщениями пользователя
    
    Эта секция решает проблему Quote Hallucination:
    - GPT видит ТОЧНЫЕ последние фразы пользователя
    - Может цитировать только из этого списка (или из evidence выше)
    - Не придумывает цитаты
    """
    if not recent_user_messages:
        return ""
    
    numbered_messages = [
        f"{i+1}. \"{msg}\""
        for i, msg in enumerate(recent_user_messages)
    ]
    
    return f"""## 💬 ПОСЛЕДНИЕ СООБЩЕНИЯ ПОЛЬЗОВАТЕЛЯ (для точного цитирования):
{chr(10).join(numbered_messages)}

⚠️ КРИТИЧНОЕ ПРАВИЛО ЦИТИРОВАНИЯ:
- Если хочешь процитировать пользователя → используй ТОЛЬКО фразы из списка выше!
- Для примеров из прошлых разговоров → используй Evidence из секции "Паттерны" (с пометкой "В прошлых разговорах...")
- НИКОГДА не придумывай цитаты! Если точной фразы нет — перефразируй общий смысл без кавычек."""


def render_insights_section(profile) -> str:
    """Секция с инсайтами (глубокий анализ)"""
    if not profile or not profile.insights:
        return ""
    
    insights = profile.insights.get('insights', [])
    if not insights:
        return ""
    
    # Берём топ-3 инсайта (сортировка по priority)
    priority_map = {'high': 3, 'medium': 2, 'low': 1}
    top_insights = sorted(
        insights,
        key=lambda i: priority_map.get(i.get('priority', 'medium'), 2),
        reverse=True
    )[:3]
    
    insight_texts = []
    for insight in top_insights:
        title = insight.get('title', 'Unknown')
        description = insight.get('description', '')
        impact = insight.get('impact', 'neutral')
        recommendations = insight.get('recommendations', [])
        
        impact_emoji = {'positive': '✅', 'negative': '⚠️', 'neutral': 'ℹ️'}.get(impact, 'ℹ️')
        
        insight_text = f"""{impact_emoji} **{title}**
{description}"""
        
        if recommendations:
            recs = [f"  • {rec}" for rec in recommendations[:3]]
            insight_text += f"\nРекомендации:\n{chr(10).join(recs)}"
        
        insight_texts.append(insight_text)
    
    insights_str = "\n\n".join(insight_texts)
    
    return f"""## 💡 ИНСАЙТЫ (глубокий анализ):

{insights_str}"""


def render_emotional_state_section(profile) -> str:
    """Секция с текущим эмоциональным состоянием"""
    if not profile or not profile.emotional_state:
        return ""
    
    emotional_state = profile.emotional_state
    
    current_mood = emotional_state.get('current_mood', 'neutral')
    stress_level = emotional_state.get('stress_level', 'medium')
    energy_level = emotional_state.get('energy_level', 'medium')
    
    mood_emoji_map = {
        'slightly_down': '😔',
        'neutral': '😐',
        'good': '🙂',
        'energetic': '😄',
        'stressed': '😰'
    }
    
    mood_emoji = mood_emoji_map.get(current_mood, '😐')
    
    return f"""## 😊 ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ:
{mood_emoji} Настроение: {current_mood}
Стресс: {stress_level}
Энергия: {energy_level}

⚠️ Учитывай текущее состояние пользователя в своих ответах."""


def render_learning_preferences_section(profile) -> str:
    """Секция с learning preferences (что работает/не работает)"""
    if not profile or not profile.learning_preferences:
        return ""
    
    learning_prefs = profile.learning_preferences
    
    works_well = learning_prefs.get('works_well', [])
    doesnt_work = learning_prefs.get('doesnt_work', [])
    
    if not works_well and not doesnt_work:
        return ""
    
    parts = []
    
    if works_well:
        works_list = [f"  ✅ {item}" for item in works_well[:5]]
        parts.append(f"Что работает хорошо:\n{chr(10).join(works_list)}")
    
    if doesnt_work:
        doesnt_list = [f"  ❌ {item}" for item in doesnt_work[:5]]
        parts.append(f"Что НЕ работает:\n{chr(10).join(doesnt_list)}")
    
    return f"""## 🎓 LEARNING PREFERENCES:

{chr(10).join(parts)}

⚠️ Адаптируй свой подход основываясь на этих данных."""


def render_custom_instructions(profile) -> str:
    """Кастомные инструкции пользователя (если есть)"""
    if not profile or not hasattr(profile, 'custom_instructions'):
        return ""
    
    custom = profile.custom_instructions
    if not custom or not custom.strip():
        return ""
    
    return f"""## 📝 ДОПОЛНИТЕЛЬНЫЕ ИНСТРУКЦИИ ОТ ПОЛЬЗОВАТЕЛЯ:
{custom}"""


def render_meta_instructions(has_patterns: bool, has_insights: bool) -> str:
    """
    🎯 LEVEL 2: Мета-инструкции для GPT
    
    Объясняем GPT КАК использовать всю информацию выше
    """
    if not has_patterns and not has_insights:
        return ""
    
    instructions = []
    
    if has_patterns:
        instructions.append("""## 🎯 КАК ИСПОЛЬЗОВАТЬ ПРИМЕРЫ ИЗ ДИАЛОГОВ:

1. **Связывай текущее с прошлым:**
   - "Помнишь, ты говорил: '[цитата из Evidence]'. Сейчас ты снова..."
   - "В прошлых разговорах ты упоминал '[цитата]'. Вижу, что паттерн повторяется..."

2. **Показывай прогресс:**
   - "Раньше ты говорил '[старая цитата]', а сейчас '[новая цитата]'. Это прогресс!"
   - "Этот паттерн проявляется уже {occurrences} раз - значит, он важен для тебя."

3. **Используй клинические термины:**
   - Называй паттерны по их официальным названиям (Imposter Syndrome, Perfectionism)
   - Но объясняй простым языком с примерами""")
    
    if has_insights:
        instructions.append("""4. **Используй инсайты для глубины:**
   - Связывай несколько паттернов вместе
   - Предлагай конкретные рекомендации из инсайтов
   - Показывай cause-and-effect связи""")
    
    return "\n\n".join(instructions)



