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
Analyze quiz answers and extract behavioral/emotional patterns.

CATEGORY: {category}

QUIZ ANSWERS:
{qa_text}

Tasks:
1. Find 2-3 significant patterns from these answers
2. Each pattern should be specific and actionable
3. DON'T just repeat the answers - find UNDERLYING patterns

Return JSON:
{{
  "patterns": [
    {{
      "type": "behavioral|emotional|cognitive",
      "title": "Short pattern title (5-7 words)",
      "description": "Detailed description",
      "evidence": ["quote from answer 1", "quote from answer 2"],
      "tags": ["tag1", "tag2"],
      "confidence": 0.0-1.0
    }}
  ]
}}
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
    """
    Форматировать результаты квиза для отображения в Telegram
    
    Args:
        results: Результаты анализа
        user_id: ID пользователя
        
    Returns:
        Красиво отформатированный текст
    """
    # Используем GPT для форматирования (как в /my_profile)
    prompt = f"""
Format quiz results in a friendly, encouraging way for the user.

RESULTS:
{json.dumps(results, ensure_ascii=False, indent=2)}

Requirements:
1. Use emojis (🎯, 💡, ⭐, etc.)
2. Be supportive and encouraging
3. Highlight key patterns WITH confidence visualization:
   - Show confidence as stars: ⭐⭐⭐⭐⭐ (95%+), ⭐⭐⭐⭐ (80-94%), ⭐⭐⭐ (60-79%), ⭐⭐ (40-59%)
   - Add confidence percentage in parentheses
   - Example: "✅ Perfectionism (confidence: 95%) ⭐⭐⭐⭐⭐"
   - Use ⚠️ for patterns with confidence < 70%
4. Present recommendations clearly
5. In Russian
6. Max 2000 characters
7. Format like:
   🧠 Выявленные паттерны:
   
   ✅ Pattern Name (confidence: 85%) ⭐⭐⭐⭐
      "Description here..."
   
   💡 Рекомендации:
   - Recommendation 1
   - Recommendation 2

Return formatted text (not JSON, just text).
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a supportive psychologist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Results formatting failed: {e}")
        
        # Fallback форматирование с confidence
        text = "🎉 <b>Квиз завершён!</b>\n\n"
        
        # Паттерны с confidence
        patterns = results.get('new_patterns', [])
        if patterns:
            text += "🧠 <b>Выявленные паттерны:</b>\n\n"
            for p in patterns[:3]:
                confidence = p.get('confidence', 0.7)
                confidence_viz = _confidence_to_stars(confidence)
                emoji = "✅" if confidence >= 0.7 else "⚠️"
                title = p.get('title', 'Паттерн')
                description = p.get('description', '')[:150]
                
                text += f"{emoji} <b>{title}</b> {confidence_viz}\n"
                text += f"   {description}...\n\n"
        
        # Рекомендации
        recommendations = results.get('recommendations', [])
        if recommendations:
            text += "💡 <b>Рекомендации:</b>\n"
            for i, rec in enumerate(recommendations[:5], 1):
                text += f"{i}. {rec}\n"
        
        return text

