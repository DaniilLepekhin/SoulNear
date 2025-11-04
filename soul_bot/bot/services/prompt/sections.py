"""
🎨 LEVEL 2: Prompt Sections для персонализированного system prompt

Каждая функция возвращает отформатированную секцию промпта.
Если данных нет - возвращает пустую строку.
"""
from typing import Optional

from bot.services.pattern_context_filter import (
    detect_topic_from_message,
    get_relevant_patterns_for_chat,
)
from bot.services.text_formatting import (
    get_topic_emoji,
    localize_pattern_title,
    localize_pattern_type,
    safe_shorten,
)


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


def render_patterns_section_contextual(
    profile,
    user_message: Optional[str] = None,
    current_topic: Optional[str] = None,
) -> str:
    """Context-aware pattern rendering for the system prompt."""

    if not profile or not profile.patterns:
        return ""

    patterns = profile.patterns.get('patterns', [])
    if not patterns:
        return ""

    detected_topic = current_topic
    if not detected_topic and user_message:
        detected_topic = detect_topic_from_message(user_message)

    relevant_patterns = get_relevant_patterns_for_chat(
        patterns=patterns,
        user_message=user_message or "",
        detected_topic=detected_topic,
        max_patterns=5,
    )

    if not relevant_patterns:
        # fallback — берём топ по встречаемости
        relevant_patterns = sorted(
            patterns,
            key=lambda p: p.get('occurrences', 1),
            reverse=True,
        )[:3]

    context_labels = {
        'relationships': 'отношения',
        'money': 'деньги',
        'work': 'работа',
        'purpose': 'предназначение',
        'confidence': 'уверенность',
        'fears': 'страхи',
        'self': 'самоопределение',
    }

    pattern_blocks: list[str] = []
    for pattern in relevant_patterns:
        title = localize_pattern_title(pattern.get('title'))
        pattern_type = localize_pattern_type(pattern.get('type'))
        occurrences = pattern.get('occurrences', 1)
        confidence_pct = int((pattern.get('confidence') or 0.7) * 100)
        evidence = pattern.get('evidence', [])[:3]
        primary_context = pattern.get('primary_context')

        block_lines = [f"🧩 <b>{title}</b> · уверенность {confidence_pct}%", ""]

        if pattern_type:
            block_lines.append(f"Тип: {pattern_type}")
            block_lines.append("")
        block_lines.append(f"Частота: повторяется {occurrences} раз")
        block_lines.append("")

        contradiction = safe_shorten(pattern.get('contradiction'), 180)
        if contradiction:
            block_lines.append(f"🔁 Противоречие: {contradiction}")
            block_lines.append("")

        hidden_dynamic = safe_shorten(pattern.get('hidden_dynamic'), 180)
        if hidden_dynamic:
            block_lines.append(f"🎭 Динамика: {hidden_dynamic}")
            block_lines.append("")

        blocked_resource = safe_shorten(pattern.get('blocked_resource'), 160)
        if blocked_resource:
            block_lines.append(f"💎 Ресурс: {blocked_resource}")
            block_lines.append("")

        if primary_context:
            context_label = context_labels.get(primary_context, primary_context)
            block_lines.append(f"🌿 Контекст: {context_label}")
            block_lines.append("")

        if evidence:
            quotes = [safe_shorten(quote, 140) for quote in evidence if quote]
            clean_quotes = [quote for quote in quotes if quote]
            if clean_quotes:
                quote_lines = [f"  • «{quote}»" for quote in clean_quotes]
                block_lines.append("📝 Примеры:")
                block_lines.extend(quote_lines)
                block_lines.append("")

        while block_lines and block_lines[-1] == "":
            block_lines.pop()

        pattern_blocks.append("\n".join(block_lines))

    patterns_str = "\n\n".join(pattern_blocks)

    topic_label = context_labels.get(detected_topic, detected_topic or 'текущая тема')

    topic_emoji = get_topic_emoji(detected_topic, "🧩")

    return f"""## {topic_emoji} Паттерны по теме «{topic_label}»

{patterns_str}

⚠️ Используй цитаты из блоков «📝 Примеры» и явно связывай их с текущим вопросом пользователя."""


def render_patterns_section(profile) -> str:
    return render_patterns_section_contextual(profile)


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
        f"{i+1}. «{msg}»"
        for i, msg in enumerate(recent_user_messages)
    ]

    return f"""## 💬 Последние сообщения пользователя

{chr(10).join(numbered_messages)}

⚠️ Цитируй только из этого списка.
Если нужна ссылка на прошлые диалоги — используй evidence из секции «Паттерны» и явно говори, что это пример из истории."""


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
        title = insight.get('title', 'Инсайт')
        description = safe_shorten(insight.get('description'), 220)
        impact = insight.get('impact', 'neutral')
        recommendations = insight.get('recommendations', [])
        
        # 🆕 V2 FIELDS: Глубокие инсайты
        the_system = safe_shorten(insight.get('the_system'), 220)
        the_blockage = safe_shorten(insight.get('the_blockage'), 220)
        the_way_out = safe_shorten(insight.get('the_way_out'), 220)
        why_this_matters = safe_shorten(insight.get('why_this_matters'), 220)
        
        impact_emoji = {'positive': '✅', 'negative': '⚠️', 'neutral': 'ℹ️'}.get(impact, 'ℹ️')
        
        insight_text = f"""{impact_emoji} **{title}**"""
        
        # V2: Используем новые поля если есть, иначе старый формат
        if the_system or the_blockage or the_way_out:
            # НОВЫЙ ФОРМАТ (глубокий анализ)
            if the_system:
                insight_text += f"\n\n🔄 Система: {the_system}"
            if the_blockage:
                insight_text += f"\n\n🚧 Блокировка: {the_blockage}"
            if the_way_out:
                insight_text += f"\n\n🛤️ Путь вперед: {the_way_out}"
            if why_this_matters:
                insight_text += f"\n\n💎 Почему это важно: {why_this_matters}"
        else:
            # СТАРЫЙ ФОРМАТ (backward compatibility)
            if description:
                insight_text += f"\n{description}"
            if recommendations:
                recs = [f"  • {rec}" for rec in recommendations[:3]]
                insight_text += f"\nРекомендации:\n{chr(10).join(recs)}"
        
        insight_texts.append(insight_text)
    
    insights_str = "\n\n".join(insight_texts)
    
    return f"""## 💡 Главные инсайты

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
    mood_labels = {
        'slightly_down': 'уставшее',
        'neutral': 'ровное',
        'good': 'поднятое',
        'energetic': 'энергичное',
        'stressed': 'на взводе'
    }
    stress_labels = {
        'low': 'низкий',
        'medium': 'средний',
        'high': 'высокий',
        'critical': 'критический'
    }
    energy_labels = {
        'low': 'мало',
        'medium': 'сбалансировано',
        'high': 'много'
    }

    mood_emoji = mood_emoji_map.get(current_mood, '😐')
    mood_label = mood_labels.get(current_mood, current_mood)
    stress_label = stress_labels.get(stress_level, stress_level)
    energy_label = energy_labels.get(energy_level, energy_level)

    return f"""## 😊 Эмоциональное состояние
{mood_emoji} Настроение: {mood_label}
☁️ Стресс: {stress_label}
⚡ Энергия: {energy_label}

⚠️ Подстраивай тон и скорость ответа под это состояние."""


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
        works_list = [
            f"• {safe_shorten(item, 160)}"
            for item in works_well[:5]
            if item
        ]
        parts.append("✅ Подходит пользователю:\n" + chr(10).join(works_list))

    if doesnt_work:
        doesnt_list = [
            f"• {safe_shorten(item, 160)}"
            for item in doesnt_work[:5]
            if item
        ]
        parts.append("⚠️ Не заходит:\n" + chr(10).join(doesnt_list))

    return f"""## 🎓 Как подстраиваться под пользователя

{chr(10).join(parts)}

⚠️ Учитывай эти сигналы в следующем ответе и не возвращайся к «не работает» без объяснения."""


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
        instructions.append("""## 🎯 Как опираться на прошлый опыт

1. **Соединяй настоящее и историю.**
   - «Помнишь, ты говорил: "[цитата из evidence]" — сейчас звучит то же чувство».
   - «В прошлых разговорах ты упоминал "[цитата]" — петля повторяется». 

2. **Отмечай движение и прогресс.**
   - «Раньше ты говорил "[старая цитата]", а сегодня уже "[новая цитата]"».
   - «Этот паттерн звучал несколько раз — значит, тема для тебя важная».

3. **Называй паттерн по-русски и поясняй смысл.**
   - Используй дружеские формулировки («Синдром самозванца», «Страх отказа») и коротко объясняй, что это значит для пользователя.
   - Не прячься за диагнозами — говори живым языком, ссылайся на цитаты.""")
    
    if has_insights:
        instructions.append("""## 💡 Как использовать инсайты
   - Связывай несколько паттернов в одну цепочку, показывай причину и следствие.
   - Предлагай шаги из инсайтов, объясняя зачем они нужны именно этому человеку.
   - Подсвечивай выгоду изменений и цену бездействия.""")
    
    return "\n\n".join(instructions)


def render_active_hints_section(preferences: Optional[dict], patterns: list = None) -> str:
    """Секция с активными response hints, которые нужно использовать в ближайшем ответе."""

    if not preferences:
        preferences = {}

    hints = preferences.get('active_response_hints') or []
    pending = [
        hint for hint in hints
        if isinstance(hint, dict) and (hint.get('status') in (None, 'pending'))
    ]

    # 🆕 FALLBACK для новых пользователей (< 3 паттернов)
    if not pending:
        patterns = patterns or []
        if len(patterns) < 3:
            return """## 🎯 Идеи для первого отклика

Пользователь только знакомится с ботом. Темы, которые стоит мягко отразить:
- Страх начала: «не знаю с чего начать» → назови сомнение, уточни, что мешает сделать первый шаг.
- Застревание: «всё как в замкнутом круге» → опиши цикл, спроси где он чувствует повтор.
- Потеря смысла: «а зачем всё это?» → аккуратно подсвети пустоту, спроси что раньше давало опору.
- Прокрастинация: «откладываю дела» → отзеркаль избегание, спроси что он чувствует в момент выбора.
- Самокритика: «я плохой/слабый» → отметь суровый внутренний голос, спроси откуда он знаком.

⚠️ Работай с одной темой за раз, задавай уточняющий вопрос и не торопись советовать."""
        return ""

    lines = []
    for idx, hint in enumerate(pending[:3], start=1):
        text = (hint.get('hint') or '').strip()
        if not text:
            continue

        source = hint.get('source') or {}
        source_label = source.get('title') or source.get('type') or 'hint'
        lines.append(f"{idx}. \"{text}\" — источник: {source_label}")

    if not lines:
        return ""

    return (
        "## 🎯 Активные зеркала для следующего ответа\n"
        + "\n".join(lines)
        + "\n\n⚠️ Вплети хотя бы одно зеркало: перефразируй по-своему, привяжи к текущему сообщению и заверши вопросом или паузой."
    )



