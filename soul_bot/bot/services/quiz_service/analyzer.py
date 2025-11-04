"""
🔍 Quiz Results Analyzer (Stage 4 - переиспользуем Stage 3)

Анализирует ответы квиза и обновляет профиль пользователя

Архитектура:
- Модульная (не монолит!)
- Переиспользуем pattern_analyzer из Stage 3
- Легко расширяется для deep analysis в V2
"""
import logging
import json
from openai import AsyncOpenAI

from config import OPENAI_API_KEY
from bot.services import pattern_analyzer
import database.repository.user_profile as db_user_profile
from bot.services.text_formatting import (
    get_topic_emoji,
    localize_pattern_title,
    safe_shorten,
)

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# ==========================================
# 🧠 ANALYZE_QUIZ_RESULTS (МОДУЛЬНАЯ СТРУКТУРА)
# ==========================================

async def analyze_quiz_results(
    user_id: int,
    quiz_session: dict,
    category: str
) -> dict:
    """
    Анализировать результаты квиза
    
    Args:
        user_id: ID пользователя
        quiz_session: Объект сессии с ответами
        category: Категория квиза
        
    Returns:
        Результаты анализа:
        {
            "new_patterns": [...],
            "insights": [...],
            "recommendations": [...],
            "confidence": 0.85
        }
    """
    try:
        # 1. Извлекаем ответы (модуль)
        answers = _extract_answers(quiz_session)
        
        # 2. Генерируем паттерны через GPT-4 (модуль)
        new_patterns = await _generate_patterns_from_quiz(answers, category)
        
        # 3. Переиспользуем pattern_analyzer из Stage 3!
        await _update_profile_with_patterns(user_id, new_patterns)
        
        # 4. Генерируем рекомендации (модуль)
        recommendations = await _generate_recommendations(new_patterns, category)
        
        # 5. Формируем результат
        result = {
            "new_patterns": new_patterns,
            "recommendations": recommendations,
            "confidence": _calculate_confidence(answers),
            "category": category
        }
        
        logger.info(f"Quiz analysis complete for user {user_id}: {len(new_patterns)} patterns")
        
        return result
        
    except Exception as e:
        logger.error(f"Quiz analysis failed: {e}")
        return {
            "new_patterns": [],
            "recommendations": [],
            "confidence": 0.0,
            "error": str(e)
        }


# ==========================================
# 📊 МОДУЛЬ: ИЗВЛЕЧЕНИЕ ОТВЕТОВ
# ==========================================

def _extract_answers(quiz_session: dict) -> list[dict]:
    """
    Извлечь ответы из сессии
    
    Args:
        quiz_session: Объект сессии
        
    Returns:
        Список ответов с вопросами
    """
    questions = quiz_session.get('data', {}).get('questions', [])
    answers = quiz_session.get('data', {}).get('answers', [])
    
    # Объединяем вопросы и ответы
    result = []
    for answer in answers:
        question = next(
            (q for q in questions if q['id'] == answer['question_id']),
            None
        )
        
        if question:
            result.append({
                "question_text": question['text'],
                "question_type": question['type'],
                "answer_value": answer['value'],
                "answered_at": answer.get('answered_at')
            })
    
    return result


# ==========================================
# 🧠 МОДУЛЬ: ГЕНЕРАЦИЯ ПАТТЕРНОВ
# ==========================================

async def _generate_patterns_from_quiz(
    answers: list[dict],
    category: str
) -> list[dict]:
    """
    Сгенерировать паттерны на основе ответов квиза
    
    Args:
        answers: Список ответов с вопросами
        category: Категория квиза
        
    Returns:
        Список паттернов (без embeddings, их добавит pattern_analyzer)
    """
    # Формируем контекст для GPT
    qa_text = "\n".join([
        f"Q: {a['question_text']}\nA: {a['answer_value']}"
        for a in answers
    ])
    
    prompt = f"""
Ты — психолог-расследователь, говоришь только по-русски. Тебя попросили разобрать результаты квиза и найти скрытые динамики, которые человек сам не замечает.

═════════ ВХОДНЫЕ ДАННЫЕ ═════════
Категория: {category}

Ответы пользователя (формат Q/A):
{qa_text}

═════════ ЧТО СДЕЛАТЬ ═════════
1. Найди 1–3 ключевых паттерна. Каждый паттерн обязан строиться вокруг противоречия в ответах.
2. Для каждого паттерна опиши:
   • Название на русском (без клиники, живое формулирование)
   • Короткое описание того, что видно на поверхности
   • Противоречие: какие ответы конфликтуют и что это показывает
   • Скрытую динамику: какой страх/потребность управляет поведением
   • Заблокированный ресурс: какая сила уже есть, но направлена против себя, и как её перенаправить
   • Два точных цитирования из ответов (без переработки)
   • Уверенность (0.7–1.0)

3. Всё формулируй простым разговорным русским, будто объясняешь другу. Никаких англицизмов, клинических терминов и «наблюдается тенденция». Только живой язык.

═════════ ФОРМАТ ОТВЕТА ═════════
Верни JSON:
{{
  "patterns": [
    {{
      "type": "behavioral|emotional|cognitive",
      "title": "Короткое русское название",
      "description": "Что видно на поверхности (рус.)",
      "contradiction": "Какое противоречие нашли (рус.)",
      "hidden_dynamic": "В чём скрытая динамика (рус.)",
      "blocked_resource": "Какая сила скрыта и как её перенаправить (рус.)",
      "evidence": ["Цитата 1", "Цитата 2"],
      "tags": ["quiz-derived", "{category}"],
      "confidence": 0.7
    }}
  ]
}}

Требования к качеству:
• Все значения (кроме type/tags) строго на русском.
• Противоречие должно ссылаться на конкретные ответы.
• Скрытая динамика объясняет «почему», а не «что».
• Заблокированный ресурс показывает силу и способ её развернуть.
• После прочтения человек должен подумать: «Нифига себе, это про меня».

Если противоречий нет, придумай наименее очевидный паттерн, но честно объясни, что данных мало.
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",  # Используем полную версию для качественного анализа
            messages=[
                {"role": "system", "content": """
 Ты мой друг, который знает меня 10 лет и видит паттерны, которые я сам не замечаю.
 
 Говори прямо, без терапевтического языка:
 ❌ "У вас наблюдается низкая самоэффективность с элементами избегания"
 ✅ "Ты не веришь что справишься, да? Каждый раз находишь причину почему 'не получится'."
 
 ❌ "Паттерн избегания конфронтации с тенденцией к подавлению эмоций"
 ✅ "Ты убегаешь от конфликтов, заметил? Лучше проглотить, чем выяснять."
 
 ТВОЯ ЗАДАЧА: Найти то, что человек сам не видит. Показать blind spot. 
 Не классифицировать ("you're anxious"), а REVEAL скрытую динамику.
 
 Без канцелярита. Без абстракций. Называй вещи своими именами.
 Всегда отвечай по-русски.
 """},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.4
        )
        
        result = json.loads(response.choices[0].message.content)
        patterns = result.get('patterns', [])
        
        return patterns
        
    except Exception as e:
        logger.error(f"Pattern generation failed: {e}")
        return []


# ==========================================
# 💾 МОДУЛЬ: ОБНОВЛЕНИЕ ПРОФИЛЯ
# ==========================================

async def _update_profile_with_patterns(user_id: int, new_patterns: list[dict]):
    """
    Обновить профиль пользователя с новыми паттернами
    
    ⚡ ПЕРЕИСПОЛЬЗУЕМ pattern_analyzer из Stage 3!
    
    Args:
        user_id: ID пользователя
        new_patterns: Новые паттерны (без embeddings)
    """
    # Получаем профиль
    profile = await db_user_profile.get_or_create(user_id)
    existing_patterns = profile.patterns.get('patterns', [])
    
    # Используем _add_patterns_with_dedup из pattern_analyzer
    # (он автоматически добавит embeddings и проверит дубликаты!)
    from bot.services.pattern_analyzer import _add_patterns_with_dedup
    
    await _add_patterns_with_dedup(user_id, new_patterns, existing_patterns)
    
    logger.info(f"Profile updated with {len(new_patterns)} patterns from quiz")


# ==========================================
# 💡 МОДУЛЬ: ГЕНЕРАЦИЯ РЕКОМЕНДАЦИЙ
# ==========================================

async def _generate_recommendations(
    patterns: list[dict],
    category: str
) -> list[str]:
    """
    Сгенерировать рекомендации на основе паттернов
    
    Args:
        patterns: Выявленные паттерны
        category: Категория квиза
        
    Returns:
        Список рекомендаций для пользователя
    """
    if not patterns:
        return ["Продолжайте общаться с ботом для более точных рекомендаций"]
    
    patterns_summary = "\n".join([
        f"- {p.get('title', 'Паттерн')}: {p.get('description', '')}"
        for p in patterns
    ])
    
    prompt = f"""
Ты — мой близкий друг и ментор. На основе выявленных паттернов подскажи 3–5 конкретных шагов, которые человек может сделать в ближайшие дни.

Категория: {category}

Паттерны:
{patterns_summary}

Требования:
1. Пиши только по-русски, разговорно и по делу.
2. Каждая рекомендация = конкретное действие (что сделать, как, когда).
3. Избегай общих фраз типа «развивайте осознанность».
4. Учитывай категорию и найденные противоречия.
5. Длина одной рекомендации — не больше двух предложений.

Верни JSON:
{{
  "recommendations": [
    "Шаг 1 (рус.)",
    "Шаг 2 (рус.)"
  ]
}}
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",  # 🔥 UPGRADE: Используем GPT-4o для более глубоких рекомендаций
            messages=[
                {"role": "system", "content": "Ты эмпатичный наставник, который говорит только по-русски и даёт очень практичные советы."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        recommendations = result.get('recommendations', [])
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Recommendations generation failed: {e}")
        return ["Продолжайте практики самопознания"]


# ==========================================
# 📊 МОДУЛЬ: РАСЧЁТ CONFIDENCE
# ==========================================

def _confidence_to_stars(confidence: float) -> str:
    """
    Преобразовать confidence (0.0-1.0) в звёздочки
    
    Args:
        confidence: Уверенность от 0.0 до 1.0
        
    Returns:
        Строка со звёздочками: "⭐⭐⭐⭐⭐ (95%)"
    """
    percentage = int(confidence * 100)
    
    if percentage >= 95:
        stars = "⭐⭐⭐⭐⭐"
    elif percentage >= 80:
        stars = "⭐⭐⭐⭐"
    elif percentage >= 60:
        stars = "⭐⭐⭐"
    elif percentage >= 40:
        stars = "⭐⭐"
    else:
        stars = "⭐"
    
    return f"{stars} ({percentage}%)"


def _calculate_confidence(answers: list[dict]) -> float:
    """
    Рассчитать уверенность в результатах
    
    Факторы:
    - Количество ответов
    - Полнота ответов (не пропущены ли)
    - Наличие text ответов (более информативные)
    
    Args:
        answers: Список ответов
        
    Returns:
        Confidence score (0.0 - 1.0)
    """
    if not answers:
        return 0.0
    
    # Базовая уверенность от количества
    base_confidence = min(len(answers) / 10.0, 1.0)
    
    # Бонус за text ответы
    text_answers = len([a for a in answers if a.get('question_type') == 'text'])
    text_bonus = min(text_answers * 0.1, 0.2)
    
    # Штраф за пустые ответы
    empty_answers = len([a for a in answers if not a.get('answer_value')])
    empty_penalty = empty_answers * 0.1
    
    confidence = base_confidence + text_bonus - empty_penalty
    
    return max(0.0, min(confidence, 1.0))


# ==========================================
# 🎨 ФОРМАТИРОВАНИЕ РЕЗУЛЬТАТОВ ДЛЯ TELEGRAM
# ==========================================

async def format_results_for_telegram(
    results: dict,
    user_id: int
) -> str:
    """
    Форматировать результаты квиза для Telegram
    
    Стиль: Разговор с другом, который знает тебя 10 лет
    """
    import html

    category_code = (results.get('category') or 'общие')
    category_labels = {
        'relationships': 'отношения',
        'money': 'деньги',
        'purpose': 'предназначение',
        'confidence': 'уверенность',
        'fears': 'страхи',
        'sleep': 'сны',
        'stress': 'стресс',
    }
    category_label = category_labels.get(str(category_code).lower(), str(category_code))
    patterns = results.get('new_patterns') or []
    recommendations = results.get('recommendations') or []

    topic_emoji = get_topic_emoji(category_code, "💬")
    sections: list[str] = [
        f"{topic_emoji} Я собрал краткий разбор по теме «{html.escape(category_label)}»."
    ]

    if patterns:
        pattern_blocks: list[str] = []
        for idx, pattern in enumerate(patterns[:3], 1):
            title = html.escape(localize_pattern_title(pattern.get('title')))
            confidence = pattern.get('confidence', 0.0)
            stars = _confidence_to_stars(confidence)
            block_lines = [
                f"🧩 <b>{idx}. {title}</b> {stars}",
                "",
            ]

            contradiction = pattern.get('contradiction')
            if contradiction:
                short_contradiction = safe_shorten(contradiction, 180)
                if short_contradiction:
                    block_lines.append(f"🔁 <b>Петля:</b> {html.escape(short_contradiction)}")
                    block_lines.append("")

            hidden_dynamic = pattern.get('hidden_dynamic')
            if hidden_dynamic:
                short_dynamic = safe_shorten(hidden_dynamic, 180)
                if short_dynamic:
                    block_lines.append(f"🎭 <b>Динамика:</b> {html.escape(short_dynamic)}")
                    block_lines.append("")

            blocked_resource = pattern.get('blocked_resource')
            if blocked_resource:
                short_resource = safe_shorten(blocked_resource, 160)
                if short_resource:
                    block_lines.append(f"💎 <b>Ресурс:</b> {html.escape(short_resource)}")
                    block_lines.append("")

            evidence = pattern.get('evidence') or []
            if evidence:
                sample = safe_shorten(evidence[0], 140)
                if sample:
                    block_lines.append(f'<i>«{html.escape(sample)}»</i>')
                    block_lines.append("")

            while block_lines and block_lines[-1] == "":
                block_lines.pop()

            pattern_blocks.append("\n".join(block_lines))

        sections.append("\n\n".join(pattern_blocks))
    
    else:
        sections.append("🧩 Пока без ярких паттернов — продолжим диалог, чтобы услышать больше контекста.")

    if recommendations:
        rec_lines = ["🪷 <b>Что попробовать</b>", ""]
        for idx, rec in enumerate(recommendations[:3], 1):
            short_rec = safe_shorten(rec, 150)
            if short_rec:
                rec_lines.append(f"<b>Шаг {idx}.</b> {html.escape(short_rec)}")
                rec_lines.append("")

        while rec_lines and rec_lines[-1] == "":
            rec_lines.pop()

        sections.append("\n".join(rec_lines))

    sections.append("🤍 Выбери один шаг и напиши, как пойдёт. Я помогу отследить изменения.")

    return "\n\n".join([line for line in sections if line and line.strip()])

