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
import uuid
from typing import Optional
from openai import AsyncOpenAI

from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# ==========================================
# 📋 КАТЕГОРИИ КВИЗОВ (v2)
# ==========================================

QUIZ_CATEGORIES = {
    "relationships": {
        "name": "Отношения",
        "description": "Глубинные сценарии близости, привязанности и границ",
        "emoji": "❤️",
        "tone_hint": "Разговаривай как близкий друг, который не боится назвать вещи своими именами.",
    },
    "money": {
        "name": "Деньги",
        "description": "Денежные убеждения, ценность себя и сценарии из детства",
        "emoji": "💰",
        "tone_hint": "Звучит как честный коуч: бережно, но без самообмана.",
    },
    "purpose": {
        "name": "Предназначение",
        "description": "Внутренние противоречия между желаниями, страхами и траекторией жизни",
        "emoji": "🧭",
        "tone_hint": "Диалог как с наставником, который видит твой потенциал глубже, чем ты сам.",
    },
}


# Стартовые "крючки" для пользователей без истории (2 вопроса на категорию)
SEED_QUESTIONS: dict[str, list[dict]] = {
    "relationships": [
        {
            "id": "seed_rel_1",
            "text": "Если честно, что в ваших отношениях (или их отсутствии) сейчас ощущается самым напряжённым?",
            "type": "text",
            "category": "relationships",
            "preface": "Сейчас без шума и формальностей."
        },
        {
            "id": "seed_rel_2",
            "text": "Когда в последний раз вы позволяли себе быть по-настоящему уязвимыми рядом с близким человеком? Что случилось потом?",
            "type": "text",
            "category": "relationships"
        },
    ],
    "money": [
        {
            "id": "seed_money_1",
            "text": "Представьте, что вам сегодня перечислили сумму, которая закрывает все базовые нужды. Что первое приходит в голову — радость, тревога или что-то ещё?",
            "type": "text",
            "category": "money",
            "preface": "Говорим про деньги так, как говорили бы на кухне ночью."
        },
        {
            "id": "seed_money_2",
            "text": "Вспомните самый сильный детский эпизод, связанный с деньгами. Как он влияет на ваши решения сейчас?",
            "type": "text",
            "category": "money"
        },
    ],
    "purpose": [
        {
            "id": "seed_purpose_1",
            "text": "Когда вы в последний раз ловили ощущение: "
                    "\"я точно не там, где должен быть\"? Что стало триггером?",
            "type": "text",
            "category": "purpose",
            "preface": "Копаем туда, куда обычно не доходят руки."
        },
        {
            "id": "seed_purpose_2",
            "text": "Какое ваше решение за последние пару лет больше всего похоже на компромисс с собой?",
            "type": "text",
            "category": "purpose"
        },
    ],
}

TARGET_QUESTION_COUNT = 10


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
        
        category_info = QUIZ_CATEGORIES.get(
            category,
            {
                "name": category,
                "description": "",
                "tone_hint": "Разговаривай честно и по-человечески.",
            },
        )

        # Формируем context для GPT
        answers_text = "\n".join([
            f"Q{i+1}: {a['question_text']}\nA: {a['answer_value']}"
            for i, a in enumerate(previous_answers)
        ])

        branch_question = _pick_branch_question(contradictions, previous_answers, category, question_number)
        if branch_question:
            logger.info(
                "🎯 Branch question served (category=%s, number=%s, id=%s)",
                category,
                question_number,
                branch_question["id"],
            )
            return branch_question
        
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

CATEGORY: {category_info['name']}
CATEGORY CONTEXT: {category_info['description']}
VOICE INSTRUCTIONS: {category_info.get('tone_hint', 'Будь честным, тёплым и точным.')}
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
  "text": "Question text (reference user's answers when useful)",
  "type": "scale|choice|open",
  "options": ["option1", "option2", ...] if type != "open",
  "preface": "Optional short hook before the question"
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

    # CONTRADICTION 4: Loves spending yet feels guilty about money
    enjoys_spending = any(
        ('spend' in q or 'тратить' in q or 'трачу' in a) and any(word in a for word in ['love', 'люблю', 'нравится'])
        for q, a in answers_text
    )
    feels_guilty_spending = any(
        ('guilt' in a or 'вину' in a or 'стыд' in a)
        for _, a in answers_text
    )

    if enjoys_spending and feels_guilty_spending:
        contradictions.append(
            "Enjoys spending money but immediately feels guilt → unresolved scarcity beliefs."
        )

    # CONTRADICTION 5: States clear vision yet claims lacking direction (purpose)
    says_no_direction = any(
        ('direction' in q or 'куда' in q or 'purpose' in q or 'предназначение' in q)
        and any(word in a for word in ['не знаю', 'stuck', 'застрял'])
        for q, a in answers_text
    )
    articulates_goal = any(
        ('goal' in q or 'мечта' in q or 'хочу' in q) and any(word in a for word in ['точно знаю', 'clearly', 'совершенно ясно'])
        for q, a in answers_text
    )

    if says_no_direction and articulates_goal:
        contradictions.append(
            "Claims to lack direction yet articulates a clear goal → action paralysis masking fear of change."
        )
     
    # Limit to top 2 contradictions для фокуса
    return contradictions[:2]


def _pick_branch_question(
    contradictions: list[str],
    previous_answers: list[dict],
    category: str,
    question_number: int,
) -> dict | None:
    """Lightweight branching: return scripted follow-up when contradiction matches a heuristic"""
    if question_number <= 3 or not contradictions:
        return None

    contradiction_blob = " ".join(contradictions).lower()
    last_answer = previous_answers[-1]['answer_value'] if previous_answers else ""

    if "friend" in contradiction_blob and "lonely" in contradiction_blob:
        return {
            "id": f"branch_lonely_{question_number}",
            "text": (
                "Ты пишешь, что вокруг много людей, но ощущение одиночества остаётся. "
                "С кем бы ты рискнул поделиться тем, что сейчас переживаешь, если выбрать только одного человека?"
            ),
            "type": "open",
            "category": category,
        }

    if "balance" in contradiction_blob and ("hour" in contradiction_blob or "overwork" in contradiction_blob):
        return {
            "id": f"branch_burnout_{question_number}",
            "text": (
                "Ты говоришь, что контролируешь баланс, но график звучит как марафон. "
                "Что произойдёт, если ты действительно отключишься от работы хотя бы на один вечер?"
            ),
            "type": "open",
            "category": category,
        }

    if "confidence" in contradiction_blob and ("critical" in contradiction_blob or "mask" in contradiction_blob):
        return {
            "id": f"branch_confidence_{question_number}",
            "text": (
                "Ты описал высокую уверенность, но продолжаешь разносить себя за ошибки. "
                "Какое самое страшное последствие, если ты признаешь себе, что имеешь право на промахи?"
            ),
            "type": "open",
            "category": category,
        }

    if last_answer and "не доверяю" in last_answer.lower():
        return {
            "id": f"branch_trust_{question_number}",
            "text": (
                "Ты ответил, что почти никому не доверяешь. "
                "Когда в последний раз ты позволял себе быть уязвимым и что из этого вышло?"
            ),
            "type": "open",
            "category": category,
        }

    return None


async def generate_questions(
    category: str,
    count: int = 3,
    user_profile: Optional[dict] = None,
    previous_answers: Optional[list[dict]] = None
) -> list[dict]:
    """Сформировать первые вопросы живого квиз-диалога."""
    try:
        category_info = QUIZ_CATEGORIES.get(
            category,
            {
                "name": category,
                "description": "",
                "emoji": "🧠",
                "tone_hint": "Говори по-человечески."
            },
        )

        target_count = min(max(count, 3), TARGET_QUESTION_COUNT)
        questions: list[dict] = []

        # 1. Крючки на прогрев — для новых людей берём два, для тёплой базы достаточно одного.
        seed_pack = _clone_seed_questions(category)
        if not user_profile or not user_profile.get("patterns"):
            questions.extend(seed_pack[:2])
        else:
            questions.extend(seed_pack[:1])

        # 2. Быстро сверяем, жив ли прежний анализ.
        questions.extend(_build_profile_probe_questions(user_profile, category))

        questions = _normalize_question_list(questions, category)

        # 3. Остаток докидываем через GPT, чтобы не упасть в унылый тест.
        if len(questions) < target_count:
            remaining = target_count - len(questions)
            dynamic_questions = await _generate_dynamic_batch(
                category=category,
                category_info=category_info,
                needed=remaining,
                existing_questions=questions,
                user_profile=user_profile,
                previous_answers=previous_answers or [],
            )
            questions.extend(dynamic_questions)

        return questions[:target_count]

    except Exception as exc:
        logger.error("Failed to generate questions: %s", exc)
        return _get_fallback_questions(category, count)


# ===== Helper utilities for conversational quiz v2 =====

def _clone_seed_questions(category: str) -> list[dict]:
    seeds = SEED_QUESTIONS.get(category, [])
    try:
        # Быстрый deep copy без импортов copy.deepcopy
        return json.loads(json.dumps(seeds))
    except Exception:
        return [dict(seed) for seed in seeds]


def _build_profile_probe_questions(
    user_profile: Optional[dict],
    category: str,
) -> list[dict]:
    if not user_profile:
        return []

    patterns = user_profile.get("patterns") or []
    if not patterns:
        return []

    sorted_patterns = sorted(
        patterns,
        key=lambda item: (
            item.get("occurrences", 0),
            item.get("confidence", 0.0),
        ),
        reverse=True,
    )[:2]

    probes: list[dict] = []
    for pattern in sorted_patterns:
        title = (pattern.get("title") or "").strip()
        if not title:
            continue

        hidden_dynamic = (pattern.get("hidden_dynamic") or "").strip()
        description = (pattern.get("description") or "").strip()

        question_text = (
            f"Про паттерн «{title}»: {hidden_dynamic or description} "
            "Что из последней недели подтверждает или ломает этот сценарий?"
        ).strip()

        # Если описания нет — задаём более общий крючок.
        if not hidden_dynamic and not description:
            question_text = (
                f"Ты упоминал паттерн «{title}». Приведи свежую ситуацию, "
                "где он проявился сильнее всего?"
            )

        probes.append(
            {
                "id": f"profile_{uuid.uuid4().hex[:8]}",
                "text": question_text,
                "type": "text",
                "preface": "Хочу сверить прошлый вывод — скажи честно.",
                "category": category,
            }
        )

    return probes


def _normalize_question_list(questions: list[dict], category: str) -> list[dict]:
    normalized: list[dict] = []
    seen_ids: set[str] = set()

    for raw in questions:
        if not isinstance(raw, dict):
            continue

        question = dict(raw)
        question.setdefault("category", category)
        question_type = (question.get("type") or "text").lower()
        if question_type in {"open", "free_text"}:
            question_type = "text"
        elif question_type in {"choice"}:
            question_type = "multiple_choice"
        question["type"] = question_type

        if question_type in {"scale"} and not question.get("options"):
            question["options"] = [
                "Никогда",
                "Редко",
                "Иногда",
                "Часто",
                "Постоянно",
            ]
        elif question_type in {"multiple_choice"} and not question.get("options"):
            question["options"] = [
                "Скорее да",
                "Скорее нет",
                "Это зависит",
                "Не понимаю",
            ]
        elif question_type == "text":
            question.setdefault("options", [])

        question_id = question.get("id") or f"q_{uuid.uuid4().hex[:8]}"
        if question_id in seen_ids:
            question_id = f"q_{uuid.uuid4().hex[:8]}"
        question["id"] = question_id
        seen_ids.add(question_id)

        normalized.append(question)

    return normalized


async def _generate_dynamic_batch(
    *,
    category: str,
    category_info: dict,
    needed: int,
    existing_questions: list[dict],
    user_profile: Optional[dict],
    previous_answers: list[dict],
) -> list[dict]:
    if needed <= 0:
        return []

    asked_questions_text = "\n".join(
        [
            f"{idx + 1}. {question.get('text', '').strip()}"
            for idx, question in enumerate(existing_questions)
            if question.get("text")
        ]
    ) or "— ещё ничего не спрашивали."

    answers_text = "\n".join(
        [
            f"{idx + 1}. Q: {answer.get('question_text', answer.get('question_id', '??'))}\n   A: {answer.get('answer_value', answer.get('value', ''))}"
            for idx, answer in enumerate(previous_answers)
        ]
    ) or "— пользователь пока не отвечал."

    patterns = (user_profile or {}).get("patterns") or []
    patterns_summary = "\n".join(
        [
            f"- {item.get('title', 'Паттерн')} (confidence {item.get('confidence', 0):.0%})"
            for item in patterns[:3]
        ]
    ) or "— данных нет, считай пользователя белым листом."

    prompt = f"""
Ты — психолог, который ведёт глубинный квиз в формате живого диалога. Категория: {category_info['name']}.
Описание: {category_info['description']}
Тон: {category_info.get('tone_hint', 'Будь честным, тёплым и точным.')} 

Уже прозвучало:
{asked_questions_text}

Ответы пользователя:
{answers_text}

Известные паттерны:
{patterns_summary}

Тебе нужно придумать {needed} следующих вопросов.
Правила:
1. Пиши по-русски, разговорно, без канцелярита.
2. Если есть за что зацепиться — ссылайся на ответы пользователя: «Ты сказал…», «Ты отметил…».
3. Копай противоречия, скрытые мотивы, заблокированные ресурсы. Избегай банальных «Как часто…».
4. Авторизованные типы: text (открытый ответ), multiple_choice (3-4 варианта), scale (5 вариантов «Никогда» → «Постоянно»).
5. Можно добавить поле "preface" — короткий крючок перед вопросом (не более 100 символов).
6. Не повторяй темы уже заданных вопросов.

Верни JSON такого вида:
{{
  "questions": [
    {{
      "id": "dyn_1",
      "text": "…",
      "type": "text|multiple_choice|scale",
      "options": [],
      "preface": "…"  # опционально
    }}
  ]
}}
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You craft psychologically sharp, empathetic questions in Russian.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.6,
        )
        data = json.loads(response.choices[0].message.content)
        generated = data.get("questions", [])
    except Exception as err:
        logger.error("Dynamic quiz batch failed: %s", err)
        return []

    normalized = _normalize_question_list(generated, category)
    return normalized[:needed]


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
                "id": "fallback_rel_1",
                "text": "Что в текущих отношениях (или их отсутствии) сейчас больше всего царапает?",
                "type": "text",
                "category": "relationships",
            },
            {
                "id": "fallback_rel_2",
                "text": "Когда вы в последний раз показали партнёру или другу свою уязвимость? Чем всё закончилось?",
                "type": "text",
                "category": "relationships",
            },
        ],
        "money": [
            {
                "id": "fallback_money_1",
                "text": "Какая денежная ситуация из детства вспоминается первой, когда речь заходит о риске?",
                "type": "text",
                "category": "money",
            },
            {
                "id": "fallback_money_2",
                "text": "Как вы обычно реагируете на неожиданный крупный расход: зажимаетесь, игнорируете или ищете возможности?",
                "type": "multiple_choice",
                "options": [
                    "Зажимаюсь и экономлю на всём",
                    "Продолжаю жить как есть",
                    "Начинаю искать дополнительные доходы",
                    "Прошу помощи у близких",
                ],
                "category": "money",
            },
        ],
        "purpose": [
            {
                "id": "fallback_purpose_1",
                "text": "В какой момент последнего месяца вы почувствовали: «Я занимаюсь не тем»?",
                "type": "text",
                "category": "purpose",
            },
            {
                "id": "fallback_purpose_2",
                "text": "Если представить, что провал невозможен, какой шаг вы бы сделали в сторону своего интереса?",
                "type": "text",
                "category": "purpose",
            },
        ],
    }
    
    bucket = fallback.get(category, fallback["relationships"])
    return bucket[:count]


# ==========================================
# 🎨 ФОРМАТИРОВАНИЕ ВОПРОСА ДЛЯ TELEGRAM
# ==========================================

def format_question_for_telegram(question: dict, current: int, total: int) -> str:
    """
    Форматировать вопрос для отображения в Telegram
    
    Args:
        question: Объект вопроса
        current: Текущий номер (1-based)
        total: Всего вопросов
        
    Returns:
        Отформатированный текст
    """
    import html
    
    category_info = QUIZ_CATEGORIES.get(question.get('category', 'relationships'), {})
    emoji = category_info.get('emoji', '🧠')
    safe_question_text = html.escape(question.get('text', ''))
    preface = question.get('preface')

    label = f"({current}/{total})" if total else ""
    title_line = f"{label} {emoji}".strip()

    body_parts: list[str] = [title_line]

    if preface and safe_question_text and " " in safe_question_text:
        body_parts.append(f"<i>{html.escape(preface)}</i>")
        body_parts.append(f"<b>{safe_question_text}</b>")
    else:
        merged = " ".join(filter(None, (preface, safe_question_text))).strip()
        body_parts.append(f"<b>{html.escape(merged)}</b>")

    question_type = question.get('type')
    if question_type == 'scale':
        body_parts.append("📊 <i>Отметьте точку на шкале</i>")
    elif question_type == 'multiple_choice':
        body_parts.append("☑️ <i>Выберите вариант</i>")
    else:
        body_parts.append("✍️ <i>Напишите свой ответ</i>")
        body_parts.append("🎙️ Можно ответить голосом — просто отправьте аудио.")

    return "\n".join(body_parts)

