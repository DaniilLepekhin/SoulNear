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
from typing import Optional
from openai import AsyncOpenAI

from config import OPENAI_API_KEY
from bot.services import pattern_analyzer
import database.repository.user_profile as db_user_profile

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
You are a psychological DETECTIVE analyzing quiz results.

MISSION: DON'T classify ("they're anxious") - REVEAL what they CAN'T see!

═══════════════════════════════════════════════════════════════════
🎯 QUIZ DATA
═══════════════════════════════════════════════════════════════════

CATEGORY: {category}

ANSWERS:
{qa_text}

═══════════════════════════════════════════════════════════════════
🔍 YOUR TASK: FIND THE HIDDEN (3-Step Framework)
═══════════════════════════════════════════════════════════════════

STEP 1: DETECT CONTRADICTIONS
─────────────────────────────────────────────────────────────────
Look for answers that CONFLICT with each other.

EXAMPLES:
✓ Q1: "I have many friends" + Q7: "I feel lonely often" 
  → Contradiction: Surrounded but isolated
  → Insight: Surface connections, avoiding depth

✓ Q2: "I work 12 hours daily" + Q5: "I maintain work-life balance"
  → Contradiction: Denial of burnout
  → Insight: Rationalizing unsustainable behavior

LOOK FOR:
- Self-contradictory answers (says A, says opposite B)
- Denial patterns (claims X but data shows ¬X)
- Aspirational vs reality gap

STEP 2: UNCOVER HIDDEN DYNAMIC  
─────────────────────────────────────────────────────────────────
What DRIVES the behavior? What's the REAL fear?

DON'T say: "They procrastinate"
SAY: "Procrastination protects them from facing inadequacy fears"

FRAMEWORK: Surface behavior → Hidden fear → Core need

EXAMPLE from quiz:
Answers show: Perfectionism + fear of judgment + isolation
Hidden dynamic: "Uses perfectionism to JUSTIFY not sharing work. 
                Real fear: being seen as real self = rejection.
                Perfectionism is ARMOR, not standard."

STEP 3: IDENTIFY BLOCKED RESOURCE
─────────────────────────────────────────────────────────────────
Every pattern = DISTORTED STRENGTH

"Many friends but lonely" → Socialability (strength!)
BUT used for quantity not quality (misdirected)

"Works 12h/day" → Strong work ethic (power!)
BUT directed against self (burnout) not for self (growth)

TASK: How can they REDIRECT this resource?

═══════════════════════════════════════════════════════════════════
📤 RETURN FORMAT (JSON)
═══════════════════════════════════════════════════════════════════

{{
  "patterns": [
    {{
      "type": "behavioral|emotional|cognitive",
      "title": "Clinical term in English (e.g. Loneliness Among People)",
      
      "description": "Surface-level observation from quiz answers",
      
      "contradiction": "What CONTRADICTION exists? 'Says X in Q1 but Y in Q5, revealing...'",
      
      "hidden_dynamic": "What DRIVES this? 'Real fear is [X]. Dynamic: behavior serves to [protect/avoid/control] by...'",
      
      "blocked_resource": "Hidden strength. 'Shows [quality] but directed against/away from self. Could redirect by...'",
      
      "evidence": ["Quote from answer 1", "Quote from answer 2"],
      "tags": ["quiz-derived", "{category}"],
      "confidence": 0.7-1.0
    }}
  ]
}}

═══════════════════════════════════════════════════════════════════
✅ QUALITY CHECKLIST
═══════════════════════════════════════════════════════════════════

Before returning JSON, verify:

1. ✓ Found at least ONE contradiction in answers?
2. ✓ Hidden_dynamic explains WHY (not just describes WHAT)?
3. ✓ Blocked_resource shows STRENGTH not just problem?
4. ✓ Evidence = EXACT quotes from quiz answers?
5. ✓ Title = established term (Imposter Syndrome, not "self-doubt")?
6. ✓ Would user think "Whoa, how did you know that?"?

═══════════════════════════════════════════════════════════════════
🎯 EXAMPLES: DEPTH vs SURFACE
═══════════════════════════════════════════════════════════════════

❌ SURFACE (BAD):
Title: "Social anxiety"
Description: "User feels nervous in social situations"

WHY BAD: User already knows this!

✅ DEPTH (GOOD):
Title: "Loneliness Among People"
Contradiction: "Q2: 'I have 10+ close friends' + Q8: 'I feel lonely daily' 
               → Keeping everyone at surface to avoid vulnerability"
Hidden_dynamic: "Real fear: if I show real self, they'll leave. So I 
                collect people but never let them IN. Quantity shields 
                from quality."
Blocked_resource: "Strong social skills + desire for connection (power!) 
                  but used for ARMOR not INTIMACY. Redirect: choose 
                  ONE person, risk being real."

═══════════════════════════════════════════════════════════════════
🔥 REMEMBER YOUR MISSION
═══════════════════════════════════════════════════════════════════

You're NOT generating quiz summary. You're REVEALING blind spot.

User took this quiz hoping to learn something about themselves they 
DON'T already know. Give them that revelation.

DEPTH > CLASSIFICATION
INSIGHT > SUMMARY
REVELATION > DESCRIPTION

Now analyze.
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",  # Используем полную версию для качественного анализа
            messages=[
                {"role": "system", "content": "You are an expert psychologist analyzing quiz results."},
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
Based on these behavioral patterns, provide 3-5 practical recommendations.

CATEGORY: {category}

PATTERNS:
{patterns_summary}

Requirements:
1. Recommendations should be ACTIONABLE
2. Specific to the category
3. Not too generic
4. In Russian language
5. Brief (1-2 sentences each)

Return JSON:
{{
  "recommendations": [
    "Рекомендация 1",
    "Рекомендация 2",
    ...
  ]
}}
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",  # 🔥 UPGRADE: Используем GPT-4o для более глубоких рекомендаций
            messages=[
                {"role": "system", "content": "You are a supportive psychologist."},
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
    """Форматировать результаты квиза для отображения в Telegram."""
    import html

    category = results.get('category') or 'Квиз'
    patterns = results.get('new_patterns') or []
    recommendations = results.get('recommendations') or []

    header = f"🧠 <b>Разбор завершён</b> · {html.escape(category.title())}"
    sections: list[str] = [header]

    if patterns:
        pattern_blocks = ["🔥 <b>Главные паттерны</b>"]
        for pattern in patterns[:3]:
            pattern_blocks.append(_render_pattern_block(pattern))
        sections.append("\n".join(pattern_blocks))
    else:
        sections.append(
            "😶 Пока без ярко выраженных паттернов — это уже сигнал прислушаться к своим ощущениям."
        )

    if recommendations:
        rec_lines = ["📌 <b>Что попробовать</b>"]
        for rec in recommendations[:5]:
            rec_lines.append(f"• {html.escape(rec)}")
        sections.append("\n".join(rec_lines))

    sections.append("🪄 Если хочется копнуть глубже — напиши, продолжим раскатывать сюжет.")

    return "\n\n".join(sections)


def _render_pattern_block(pattern: dict) -> str:
    import html

    title = html.escape(pattern.get('title', 'Паттерн'))
    confidence = pattern.get('confidence', 0.0)
    stars = _confidence_to_stars(confidence)
    emoji = "✅" if confidence >= 0.7 else "⚠️"

    lines = [f"{emoji} <b>{title}</b> {stars}"]

    contradiction = pattern.get('contradiction')
    if contradiction:
        lines.append(f"⚡ <b>Противоречие:</b> {html.escape(contradiction)}")

    hidden_dynamic = pattern.get('hidden_dynamic')
    if hidden_dynamic:
        lines.append(f"🔍 <b>Скрытая динамика:</b> {html.escape(hidden_dynamic)}")

    blocked_resource = pattern.get('blocked_resource')
    if blocked_resource:
        lines.append(f"🔓 <b>Ресурс внутри:</b> {html.escape(blocked_resource)}")

    evidence = pattern.get('evidence') or []
    if evidence:
        lines.append("📝 Примеры:")
        for sample in evidence[:2]:
            lines.append(f"   • {html.escape(sample)}")

    return "\n".join(lines)

