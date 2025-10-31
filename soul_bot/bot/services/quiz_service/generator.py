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

async def generate_adaptive_question(
    category: str,
    question_number: int,
    previous_answers: list[dict],
    user_profile: Optional[dict] = None
) -> dict:
    """
    🆕 V2: Генерировать АДАПТИВНЫЙ вопрос на основе предыдущих ответов
    
    ЛОГИКА:
    - Questions 1-3: Baseline (establish foundation)
    - Questions 4-8: Adaptive (dig into contradictions from 1-3)
    - Questions 9-11: Deep dive (focus on biggest contradiction)
    
    Args:
        category: Категория квиза
        question_number: Номер текущего вопроса (1-based)
        previous_answers: Все предыдущие ответы с вопросами
        user_profile: Профиль пользователя (опционально)
        
    Returns:
        Один адаптивный вопрос (dict)
    """
    try:
        # Анализируем предыдущие ответы
        contradictions = _detect_answer_contradictions(previous_answers)
        
        # Формируем context для GPT
        answers_text = "\n".join([
            f"Q{i+1}: {a['question_text']}\nA: {a['answer_value']}"
            for i, a in enumerate(previous_answers)
        ])
        
        # Определяем focus (что копать)
        if question_number <= 3:
            focus_instruction = "Ask foundational baseline question to establish core patterns."
        elif question_number <= 8 and contradictions:
            focus_instruction = f"Dig into this contradiction: {contradictions[0]}"
        elif contradictions:
            focus_instruction = f"Deep dive: force user to confront their biggest contradiction: {contradictions[0]}"
        else:
            focus_instruction = "Explore emotional intensity peak from previous answers."
        
        prompt = f"""
Generate NEXT adaptive quiz question (#{question_number}) based on user's PREVIOUS answers.

CATEGORY: {category}
QUESTION NUMBER: {question_number}/11

PREVIOUS ANSWERS:
{answers_text}

DETECTED CONTRADICTIONS:
{chr(10).join(f"- {c}" for c in contradictions) if contradictions else "None yet (baseline phase)"}

YOUR TASK: {focus_instruction}

QUESTION MUST:
1. Reference previous answer if relevant (e.g. "You said X earlier, but...")
2. Go DEEPER not surface
3. Create cognitive dissonance (make them think "hmm...")
4. Be specific not generic

RETURN JSON (single question):
{{
  "id": "q{question_number}",
  "text": "Question text (can reference 'You mentioned X...' if digging into contradiction)",
  "type": "scale|choice|open",
  "options": ["option1", "option2", ...] if type != "open"
}}

EXAMPLES:

❌ GENERIC (BAD):
"How do you feel about relationships?" (boring, they answered this already!)

✅ ADAPTIVE (GOOD):
"You said you have many close friends. How often do you share your REAL feelings with them?"
(↑ digs into potential contradiction: many friends vs emotional intimacy)
"""
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at designing adaptive psychological assessments."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5
        )
        
        question = json.loads(response.choices[0].message.content)
        question['category'] = category
        
        logger.info(f"✅ Generated adaptive question #{question_number}")
        return question
        
    except Exception as e:
        logger.error(f"Adaptive question generation failed: {e}")
        # Fallback: generate basic question
        return {
            "id": f"q{question_number}",
            "text": "Tell me more about this topic.",
            "type": "open",
            "category": category
        }


def _detect_answer_contradictions(answers: list[dict]) -> list[str]:
    """
    🆕 V2: Детектировать противоречия в ответах пользователя
    
    LOGIC (simple heuristics - можно улучшить через GPT):
    - Ищем несовместимые ответы (high X + low Y когда X и Y должны коррелировать)
    - Выявляем denial patterns
    - Находим aspirational vs reality gaps
    
    Args:
        answers: Список ответов с вопросами
        
    Returns:
        Список противоречий (строки)
        
    Examples:
        >>> answers = [
        ...     {"question_text": "Do you have many friends?", "answer_value": "Yes, many"},
        ...     {"question_text": "How often do you feel lonely?", "answer_value": "Very often"}
        ... ]
        >>> _detect_answer_contradictions(answers)
        ["Says 'many friends' but feels lonely very often → surface connections"]
    """
    contradictions = []
    
    # Для начала простая keyword-based detection
    # В будущем можно улучшить через GPT/embeddings
    
    answers_text = [
        (a['question_text'].lower(), a['answer_value'].lower())
        for a in answers
    ]
    
    # CONTRADICTION 1: Many friends + lonely
    has_friends = any('friend' in q and ('many' in a or 'yes' in a or 'a lot' in a) 
                      for q, a in answers_text)
    feels_lonely = any(('lonely' in q or 'alone' in q) and ('often' in a or 'yes' in a or 'very' in a)
                       for q, a in answers_text)
    
    if has_friends and feels_lonely:
        contradictions.append(
            "User claims to have many friends but feels lonely often. "
            "Possible surface-level connections avoiding true intimacy."
        )
    
    # CONTRADICTION 2: Work-life balance claim + overwork reality
    claims_balance = any('balance' in q and ('yes' in a or 'good' in a) 
                        for q, a in answers_text)
    works_long_hours = any(('hours' in q or 'time' in q) and any(h in a for h in ['10', '11', '12', 'много'])
                           for q, a in answers_text)
    
    if claims_balance and works_long_hours:
        contradictions.append(
            "User claims work-life balance but works excessive hours. "
            "Possible denial of burnout or rationalization."
        )
    
    # CONTRADICTION 3: High self-criticism + claims confidence
    is_critical = any(('mistake' in q or 'criticize' in q or 'judge' in q) and ('often' in a or 'yes' in a)
                     for q, a in answers_text)
    claims_confident = any(('confident' in q or 'believe' in q) and ('yes' in a or 'very' in a)
                          for q, a in answers_text)
    
    if is_critical and claims_confident:
        contradictions.append(
            "User claims confidence but highly self-critical. "
            "Possible impostor syndrome or perfectionism masking insecurity."
        )
    
    # Limit to top 2 contradictions для фокуса
    return contradictions[:2]


async def generate_questions(
    category: str,
    count: int = 8,  # 🔥 UPGRADE: Снижаем до 8 базовых вопросов (+ 2-3 адаптивных = 10-11 total)
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
        # 🔧 V2: Добавляем контекст профиля (UPGRADE!)
        # ==========================================
        if user_profile and user_profile.get('patterns'):
            # Сортируем по частоте (occurrences) - самые "горячие" паттерны
            patterns = sorted(
                user_profile['patterns'],
                key=lambda p: p.get('occurrences', 0),
                reverse=True
            )[:3]  # Топ-3
            
            patterns_summary = "\n".join([
                f"- {p.get('title', 'Паттерн')} (confidence: {p.get('confidence', 0):.0%}, occurrences: {p.get('occurrences', 0)})\n"
                f"  Description: {p.get('description', 'N/A')[:100]}"
                for p in patterns
            ])
            
            prompt += f"""

🎯 EXISTING USER PATTERNS FROM CHAT HISTORY:
{patterns_summary}

INSTRUCTIONS FOR ADAPTATION:
1. Generate questions that EXPLORE these patterns deeper
2. Add questions to VALIDATE if these patterns are accurate
3. Look for RELATED or COMPLEMENTARY patterns
4. Prioritize patterns with high occurrences (more frequent = more important)
5. DON'T just repeat what we already know - dig deeper!
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
    import html
    
    category_info = QUIZ_CATEGORIES.get(question.get('category', 'personality'))
    emoji = category_info.get('emoji', '🧠')
    
    # 🔥 НОВОЕ: Визуальный прогресс-бар
    progress = current / total
    filled = int(progress * 10)  # 10 сегментов
    bar = "█" * filled + "░" * (10 - filled)
    percentage = int(progress * 100)
    
    # Экранируем HTML в тексте вопроса (GPT может вернуть HTML теги)
    safe_question_text = html.escape(question['text'])
    
    text = f"{emoji} <b>Вопрос {current}/{total}</b>\n"
    text += f"{bar} {percentage}%\n\n"
    text += f"{safe_question_text}\n\n"
    
    # Добавляем hint в зависимости от типа
    if question['type'] == 'scale':
        text += "📊 <i>Выберите значение по шкале</i>"
    elif question['type'] == 'multiple_choice':
        text += "☑️ <i>Выберите один вариант</i>"
    elif question['type'] == 'text':
        text += "✍️ <i>Напишите свой ответ</i>"
    
    return text

