"""
🎯 Quiz Question Generator (Stage 4 - MVP с расширяемостью)

Генерирует вопросы для квиза через GPT-4

Архитектура:
- MVP: Простая генерация по категории
- V2: Учёт профиля пользователя (параметр уже предусмотрен!)
- V3: Adaptive logic (параметр previous_answers тоже готов!)
"""
import logging
import json
from typing import Optional
from openai import AsyncOpenAI

from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# ==========================================
# 📋 КАТЕГОРИИ КВИЗОВ
# ==========================================

QUIZ_CATEGORIES = {
    "relationships": {
        "name": "Отношения",
        "description": "Паттерны в отношениях с людьми",
        "emoji": "❤️"
    },
    "work": {
        "name": "Работа и карьера",
        "description": "Профессиональные паттерны",
        "emoji": "💼"
    },
    "emotions": {
        "name": "Эмоции",
        "description": "Эмоциональные реакции и триггеры",
        "emoji": "😊"
    },
    "habits": {
        "name": "Привычки",
        "description": "Поведенческие паттерны",
        "emoji": "🔄"
    },
    "personality": {
        "name": "Личность",
        "description": "Черты характера и ценности",
        "emoji": "🧠"
    }
}


# ==========================================
# 🎯 ГЕНЕРАЦИЯ ВОПРОСОВ (MVP)
# ==========================================

async def generate_questions(
    category: str,
    count: int = 10,
    user_profile: Optional[dict] = None,  # ← V2: параметр готов!
    previous_answers: Optional[list[dict]] = None  # ← V3: параметр готов!
) -> list[dict]:
    """
    Сгенерировать вопросы для квиза
    
    Args:
        category: Категория квиза (relationships, work, etc.)
        count: Количество вопросов
        user_profile: Профиль пользователя (опционально, для V2)
        previous_answers: Предыдущие ответы (опционально, для V3 adaptive)
        
    Returns:
        Список вопросов в формате:
        [
            {
                "id": "q1",
                "text": "Как часто вы чувствуете одиночество?",
                "type": "scale",
                "options": ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"],
                "category": "emotions"
            }
        ]
    """
    try:
        # Получаем информацию о категории
        category_info = QUIZ_CATEGORIES.get(category, {"name": category, "description": ""})
        
        # ==========================================
        # 🔧 MVP: Базовый промпт
        # ==========================================
        prompt = f"""
You are a professional psychologist creating a psychological quiz.

CATEGORY: {category_info['name']}
DESCRIPTION: {category_info['description']}
QUESTIONS COUNT: {count}

Generate {count} insightful psychological questions for this category.

REQUIREMENTS:
1. Questions should be deep and meaningful (not superficial)
2. Mix of question types: scale (1-5), multiple_choice, text
3. Questions should help identify behavioral patterns
4. Use clear, professional language
5. Each question should reveal something important

QUESTION TYPES:
- scale: 5-point scale (Никогда/Редко/Иногда/Часто/Постоянно)
- multiple_choice: 3-5 options
- text: Open-ended question

Return JSON:
{{
  "questions": [
    {{
      "id": "q1",
      "text": "Как часто вы чувствуете одиночество в присутствии других людей?",
      "type": "scale",
      "options": ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"]
    }},
    {{
      "id": "q2",
      "text": "Что помогает вам справляться со стрессом?",
      "type": "multiple_choice",
      "options": ["Общение", "Одиночество", "Физическая активность", "Творчество", "Другое"]
    }},
    {{
      "id": "q3",
      "text": "Опишите ситуацию, когда вы чувствовали себя наиболее комфортно в последнее время",
      "type": "text",
      "options": []
    }}
  ]
}}
"""
        
        # ==========================================
        # 🔧 V2: Добавляем контекст профиля (если есть)
        # ==========================================
        if user_profile and user_profile.get('patterns'):
            patterns_summary = "\n".join([
                f"- {p.get('title', 'Паттерн')}"
                for p in user_profile['patterns'][:3]
            ])
            
            prompt += f"""

EXISTING USER PATTERNS (адаптируй вопросы с учётом этого):
{patterns_summary}
"""
        
        # ==========================================
        # 🔧 V3: Adaptive logic (если есть предыдущие ответы)
        # ==========================================
        if previous_answers:
            last_answers = "\n".join([
                f"Q: {a.get('question_id')} → A: {a.get('value')}"
                for a in previous_answers[-2:]  # Последние 2 ответа
            ])
            
            prompt += f"""

PREVIOUS ANSWERS (адаптируй следующие вопросы на основе этих ответов):
{last_answers}

Make next questions more specific based on these answers.
"""
        
        # Генерируем через GPT-4
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Дешевле для генерации вопросов
            messages=[
                {"role": "system", "content": "You are an expert psychologist creating insightful quizzes."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        questions = result.get('questions', [])
        
        # Добавляем category к каждому вопросу
        for q in questions:
            q['category'] = category
        
        logger.info(f"Generated {len(questions)} questions for category '{category}'")
        
        return questions
        
    except Exception as e:
        logger.error(f"Failed to generate questions: {e}")
        
        # Fallback: возвращаем базовые вопросы
        return _get_fallback_questions(category, count)


def _get_fallback_questions(category: str, count: int) -> list[dict]:
    """
    Fallback вопросы на случай ошибки GPT
    
    Args:
        category: Категория
        count: Количество вопросов
        
    Returns:
        Базовые вопросы
    """
    fallback = {
        "relationships": [
            {
                "id": "q1",
                "text": "Как часто вы чувствуете поддержку от близких людей?",
                "type": "scale",
                "options": ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"],
                "category": "relationships"
            },
            {
                "id": "q2",
                "text": "Как вы обычно реагируете на конфликты?",
                "type": "multiple_choice",
                "options": ["Избегаю", "Агрессивно защищаюсь", "Ищу компромисс", "Молчу", "Ухожу"],
                "category": "relationships"
            }
        ],
        "emotions": [
            {
                "id": "q1",
                "text": "Как часто вы чувствуете тревогу без явной причины?",
                "type": "scale",
                "options": ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"],
                "category": "emotions"
            }
        ]
    }
    
    # Возвращаем fallback или дефолтные вопросы
    return fallback.get(category, fallback["emotions"])[:count]


# ==========================================
# 🎨 ФОРМАТИРОВАНИЕ ВОПРОСА ДЛЯ TELEGRAM
# ==========================================

def format_question_for_telegram(question: dict, current: int, total: int) -> str:
    """
    Форматировать вопрос для отображения в Telegram
    
    Args:
        question: Объект вопроса
        current: Текущий номер
        total: Всего вопросов
        
    Returns:
        Отформатированный текст
    """
    category_info = QUIZ_CATEGORIES.get(question.get('category', 'personality'))
    emoji = category_info.get('emoji', '🧠')
    
    text = f"{emoji} <b>Вопрос {current}/{total}</b>\n\n"
    text += f"{question['text']}\n\n"
    
    # Добавляем hint в зависимости от типа
    if question['type'] == 'scale':
        text += "📊 <i>Выберите значение по шкале</i>"
    elif question['type'] == 'multiple_choice':
        text += "☑️ <i>Выберите один вариант</i>"
    elif question['type'] == 'text':
        text += "✍️ <i>Напишите свой ответ</i>"
    
    return text

