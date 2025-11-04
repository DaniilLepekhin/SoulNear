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
from bot.services.pattern_context_filter import get_relevant_patterns_for_quiz

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


# ==========================================
# 🔠 ВСПОМОГАТЕЛЬНЫЕ КОНСТАНТЫ И ХЕЛПЕРЫ
# ==========================================

_OPEN_QUESTION_KEYWORDS = {
    "если бы",
    "как бы",
    "что бы",
    "что для тебя",
    "что это изменило",
    "что это изменит",
    "что это значит",
    "что для тебя значит",
    "почему",
    "зачем",
    "расскажи",
    "опиши",
    "поделись",
    "что почувствовал",
    "что чувствовал",
    "что чувствуешь",
    "как ты",
    "как измени",
    "как повлия",
    "что случилось",
    "что изменится",
}

_FOLLOWUP_LIKELY_KEYWORDS = {
    "если бы",
    "как бы",
    "как изменило",
    "как изменило бы",
    "как это изменило",
    "как это повлияло",
    "что бы это значило",
    "что ты сделал",
    "что бы ты сделал",
}

_SCALE_EMOJI_KEYWORDS = [
    ("никогда", "⭕"),
    ("редко", "🟡"),
    ("иногда", "🟠"),
    ("часто", "🔴"),
    ("постоянно", "🔥"),
    ("совсем не", "⭕"),
    ("почти не", "🟡"),
    ("иногда", "🟠"),
    ("частенько", "🔴"),
    ("практически всегда", "🔥"),
]

_DEFAULT_SCALE_BASE_OPTIONS = [
    "Никогда",
    "Редко",
    "Иногда",
    "Часто",
    "Постоянно",
]

_GENERIC_MULTIPLE_CHOICE_FALLBACK = [
    "Начал(а) бы менять своё поведение",
    "Скорее оставил(а) всё как есть",
    "Обратился(ась) бы за помощью или советом",
    "Испытал(а) бы тревогу и сомнения",
]


def _is_open_question(text: str) -> bool:
    """Определяет, требует ли вопрос развёрнутого ответа."""

    if not text:
        return False

    normalized = text.lower()

    if len(normalized) > 140:  # длинные вопросы почти всегда открытые
        return True

    if normalized.count("?") >= 2:
        return True

    if any(keyword in normalized for keyword in _OPEN_QUESTION_KEYWORDS):
        return True

    if any(keyword in normalized for keyword in _FOLLOWUP_LIKELY_KEYWORDS):
        return True

    # Если вопрос заканчивается вопросительным знаком и содержит местоимения "как",
    # "что" вместе с глаголами размышления — считаем открытым.
    if normalized.rstrip().endswith("?") and any(
        phrase in normalized
        for phrase in ("как", "что", "зачем", "почему")
    ) and any(
        verb in normalized
        for verb in ("думаешь", "чувствуешь", "видишь", "реагируешь", "воспринимаешь")
    ):
        return True

    return False


def _decorate_scale_options(options: list[str]) -> list[str]:
    """Добавляет эмодзи к вариантам шкалы, если их ещё нет."""

    decorated: list[str] = []
    for original in options or []:
        option = original.strip()
        lower_option = option.lower()
        emoji = None
        for keyword, icon in _SCALE_EMOJI_KEYWORDS:
            if keyword in lower_option:
                emoji = icon
                break
        if emoji and not option.startswith(emoji):
            decorated.append(f"{emoji} {option}")
        else:
            decorated.append(option)
    if decorated:
        return decorated

    # Если список пустой, возвращаем стандартную шкалу с эмодзи
    default_icons = ["⭕", "🟡", "🟠", "🔴", "🔥"]
    return [f"{icon} {label}" for icon, label in zip(default_icons, _DEFAULT_SCALE_BASE_OPTIONS)]


_DEFAULT_SCALE_OPTIONS = _decorate_scale_options(_DEFAULT_SCALE_BASE_OPTIONS)


def _fallback_question_for_type(
    question: dict,
    *,
    category: str,
    desired_type: str,
) -> dict:
    """Создаёт fallback-вопрос нужного типа, если GPT не справился."""

    base_text = (question.get("text") or "").strip()
    preface = question.get("preface")
    question_id = question.get("id")

    if desired_type == "scale":
        fallback_text = (
            f"Насколько для тебя верно утверждение: «{base_text.rstrip('?')}»?"
            if base_text
            else "Насколько тебе знакомо это состояние?"
        )
        fallback = {
            "id": question_id,
            "text": fallback_text,
            "type": "scale",
            "category": category,
            "options": list(_DEFAULT_SCALE_OPTIONS),
        }
        if preface:
            fallback["preface"] = preface
        return fallback

    if desired_type == "multiple_choice":
        fallback_options = list(_GENERIC_MULTIPLE_CHOICE_FALLBACK)
        fallback = {
            "id": question_id,
            "text": base_text or "Какой вариант тебе ближе?",
            "type": "multiple_choice",
            "category": category,
            "options": fallback_options,
        }
        if preface:
            fallback["preface"] = preface
        return fallback

    fallback = dict(question)
    fallback["category"] = category
    fallback["type"] = desired_type
    if desired_type == "text":
        fallback["options"] = []
    return fallback


async def _regenerate_question_with_type(
    *,
    question: dict,
    category: str,
    desired_type: str,
    previous_answers: list[dict],
) -> dict:
    """Просит GPT переформулировать вопрос под нужный тип и возвращает нормализованный результат."""

    import asyncio

    category_info = QUIZ_CATEGORIES.get(
        category,
        {
            "name": category,
            "description": "",
            "tone_hint": "Разговаривай честно и по-человечески.",
        },
    )

    answers_text = "\n".join(
        [
            f"Q{i + 1}: {answer.get('question_text', '')}\nA: {answer.get('answer_value', '')}"
            for i, answer in enumerate(previous_answers[-3:])
        ]
    ) or "— пользователь пока ничего не рассказал."

    original_text = (question.get("text") or "").strip()
    preface = question.get("preface") or ""

    prompt = f"""
Тебе нужно переписать вопрос квиза под формат "{desired_type}".

Категория: {category_info['name']}
Описание: {category_info['description']}
Тон: {category_info.get('tone_hint', 'Будь честным, тёплым и точным.')}

Исходный вопрос:
\"\"\"{original_text}\"\"\"

Preface (если пусто — можешь опустить):
\"\"\"{preface}\"\"\"

Последние ответы пользователя:
{answers_text}

Правила:
- Сохрани смысл вопроса, но подбери форму "{desired_type}".
- Если тип = "scale" — сформулируй утверждение, к которому человек может отнестись по шкале из 5 пунктов.
- Если тип = "multiple_choice" — дай 3-4 осмысленных варианта, отражающих разные реакции или стратегии.
- Если тип = "text" — задай глубокий открытый вопрос.
- Пиши по-русски.

Верни JSON вида:
{{
  "question": {{
    "text": "...",
    "type": "{desired_type}",
    "options": ["...", "..."] (если тип не text),
    "preface": "..." (опционально, до 100 символов)
  }}
}}
"""

    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты психолог, который задаёт точные вопросы и строго следует формату.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.4,
            ),
            timeout=20.0,
        )

        data = json.loads(response.choices[0].message.content)
        new_question = data.get("question")
        if not isinstance(new_question, dict):
            raise ValueError("GPT returned invalid question structure")

        new_question.setdefault("type", desired_type)
        new_question.setdefault("category", category)
        if preface and not new_question.get("preface"):
            new_question["preface"] = preface

        normalized = _normalize_question_list([new_question], category)
        if normalized:
            return normalized[0]
        raise ValueError("Normalization returned empty result")

    except asyncio.TimeoutError:
        logger.warning(
            "⏱ Question regeneration timed out (category=%s, desired=%s). Using fallback.",
            category,
            desired_type,
        )
    except Exception as err:  # noqa: BLE001
        logger.error(
            "Question regeneration failed (category=%s, desired=%s): %s",
            category,
            desired_type,
            err,
        )

    fallback = _fallback_question_for_type(
        question,
        category=category,
        desired_type=desired_type,
    )
    normalized = _normalize_question_list([fallback], category)
    return normalized[0] if normalized else fallback

# Стартовые "крючки" для пользователей без истории
# Включают сценарные вопросы + разные типы для вовлечения
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
            "id": "seed_rel_2_scenario",
            "text": "Представь: твой партнёр забыл про важную для тебя дату. Что первое приходит в голову?",
            "type": "multiple_choice",
            "category": "relationships",
            "options": [
                "Он/она меня не ценит",
                "Бывает, ничего страшного",
                "Я сделаю вид что не заметил(а)",
                "Спрошу что случилось"
            ],
            "preface": "Сценарий"
        },
        {
            "id": "seed_rel_3",
            "text": "Когда в последний раз ты позволял(а) себе быть по-настоящему уязвимым(ой) рядом с близким человеком? Что случилось потом?",
            "type": "text",
            "category": "relationships"
        },
    ],
    "money": [
        {
            "id": "seed_money_1_scenario",
            "text": "Ты на кассе, карта не проходит, за тобой очередь. Первая реакция?",
            "type": "multiple_choice",
            "category": "money",
            "options": [
                "Паника и стыд",
                "Спокойно достаю другую карту",
                "Злюсь на банк/судьбу",
                "Смущённо извиняюсь"
            ],
            "preface": "Говорим про деньги так, как говорили бы на кухне ночью."
        },
        {
            "id": "seed_money_2",
            "text": "Представь что тебе сегодня перечислили сумму, которая закрывает все базовые нужды на год. Что первое приходит в голову — радость, тревога или что-то ещё?",
            "type": "text",
            "category": "money"
        },
        {
            "id": "seed_money_3",
            "text": "Вспомни самый сильный детский эпизод, связанный с деньгами. Как он влияет на твои решения сейчас?",
            "type": "text",
            "category": "money"
        },
    ],
    "purpose": [
        {
            "id": "seed_purpose_1",
            "text": "Когда ты в последний раз ловил(а) ощущение: \"я точно не там, где должен быть\"? Что стало триггером?",
            "type": "text",
            "category": "purpose",
            "preface": "Копаем туда, куда обычно не доходят руки."
        },
        {
            "id": "seed_purpose_2_scenario",
            "text": "Друг спрашивает: 'А ты чего в жизни хочешь?' Что отвечаешь?",
            "type": "multiple_choice",
            "category": "purpose",
            "options": [
                "Знаю точно, начинаю рассказывать",
                "Смущаюсь, говорю что-то общее",
                "Злюсь что спрашивают",
                "Не знаю что ответить"
            ]
        },
        {
            "id": "seed_purpose_3",
            "text": "Какое твоё решение за последние пару лет больше всего похоже на компромисс с собой?",
            "type": "text",
            "category": "purpose"
        },
    ],
}

TARGET_QUESTION_COUNT = 10


# ==========================================
# 🎯 ГЕНЕРАЦИЯ ВОПРОСОВ (MVP)
# ==========================================

async def _validate_and_fix_question_type(
    question: dict,
    previous_answers: list[dict],
    *,
    category: str,
) -> dict:
    """Проверяет тип вопроса и при необходимости перегенерирует его под другой тип."""

    import random

    if not previous_answers or len(previous_answers) < 2:
        return question

    recent_types = [answer.get("question_type", "text") for answer in previous_answers[-3:]]
    current_type = question.get("type", "text")
    question_text = question.get("text", "")

    # Если подряд уже 2 открытых вопроса, пытаемся сменить тип
    if (
        len(recent_types) >= 2
        and recent_types[-2:] == ["text", "text"]
        and current_type == "text"
    ):
        if _is_open_question(question_text):
            logger.info(
                "💡 Validation: keeping open question despite streak (text='%s')",
                question_text[:80],
            )
        else:
            desired_pool = [t for t in ["scale", "multiple_choice"] if t != recent_types[-1]] or [
                "scale",
                "multiple_choice",
            ]
            desired_type = random.choice(desired_pool)
            logger.warning(
                "⚠️ Validation: forcing type change text → %s (streak detected)",
                desired_type,
            )
            return await _regenerate_question_with_type(
                question=question,
                category=category,
                desired_type=desired_type,
                previous_answers=previous_answers,
            )

    # Если давно не было открытых вопросов, можно оставить как есть
    if (
        len(recent_types) >= 3
        and all(t != "text" for t in recent_types)
        and current_type != "text"
    ):
        logger.info(
            "💡 Validation: detected long non-text streak (recent=%s).", recent_types
        )

    return question


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
        # 🔥 SEMANTIC ANALYSIS: Анализируем предыдущие ответы через GPT
        contradictions = await _detect_contradictions_via_gpt(previous_answers, category)
        
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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 CRITICAL: MIX QUESTION TYPES!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use these 3 types strategically:
- "text" (20-30%): Deep exploration, open-ended
- "scale" (40-50%): Frequency/intensity (5 points: Никогда → Постоянно)
- "multiple_choice" (20-30%): Quick decisions (3-4 options)

⚠️ AVOID asking 3+ "text" questions in a row (user fatigue!)
✅ ALTERNATE between types for better engagement

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RETURN JSON (single question):
{{
  "id": "q{question_number}",
  "text": "Question text in Russian (reference user's answers when useful)",
  "type": "text|scale|multiple_choice",
  "options": ["option1", "option2", ...] if type != "text",
  "preface": "Optional short hook before the question"
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLES (each type):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ BAD (all text):
Q1: "Расскажите о ваших отношениях" (text)
Q2: "Опишите ваши страхи" (text)
Q3: "Что вас беспокоит?" (text)
→ User exhausted by Q3!

✅ GOOD (mixed types):

1. TYPE "text" (open-ended exploration):
{{
  "id": "q1",
  "text": "Ты сказал что у тебя много друзей. Когда в последний раз ты плакал при ком-то из них?",
  "type": "text",
  "preface": "Копаем глубже"
}}

2. TYPE "scale" (frequency/intensity):
{{
  "id": "q2",
  "text": "Как часто ты чувствуешь одиночество, даже когда вокруг люди?",
  "type": "scale",
  "options": ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"]
}}

3. TYPE "multiple_choice" (quick decision):
{{
  "id": "q3",
  "text": "Когда партнёр не отвечает несколько часов, что первое приходит в голову?",
  "type": "multiple_choice",
  "options": [
    "Он/она меня игнорирует",
    "Просто занят(а), ничего страшного",
    "Может что-то случилось?",
    "Я написал(а) что-то не то?"
  ]
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REMEMBER: Generate question in RUSSIAN. Mix types. Reference previous answers when possible.
"""
        
        # ✅ TIER 1: Add timeout to GPT call (20 seconds)
        import asyncio
        
        response = await asyncio.wait_for(
            client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at designing adaptive psychological assessments."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5
            ),
            timeout=20.0  # ✅ TIER 1: 20 second timeout for GPT
        )
        
        question = json.loads(response.choices[0].message.content)
        question['category'] = category
        
        # 🔥 VALIDATION: Force mix question types if needed
        question = await _validate_and_fix_question_type(
            question,
            previous_answers,
            category=category,
        )

        normalized = _normalize_question_list([question], category)
        if normalized:
            final_question = normalized[0]
        else:
            final_question = question
        
        logger.info(
            "✅ Generated adaptive question #%s (type: %s)",
            question_number,
            final_question.get('type'),
        )
        return final_question
        
    except asyncio.TimeoutError:
        logger.warning(f"⏱ Adaptive question generation timed out after 20s - using fallback")
        # ✅ TIER 1: Fallback при timeout - генерируем базовый вопрос
        fallback = {
            "id": f"q{question_number}",
            "text": "Расскажи больше об этой теме.",
            "type": "text",
            "category": category
        }
        return _normalize_question_list([fallback], category)[0]
    except Exception as e:
        logger.error(f"Adaptive question generation failed: {e}")
        # Fallback: generate basic question
        fallback = {
            "id": f"q{question_number}",
            "text": "Расскажи больше об этой теме.",
            "type": "text",
            "category": category
        }
        return _normalize_question_list([fallback], category)[0]


async def _detect_contradictions_via_gpt(answers: list[dict], category: str) -> list[str]:
    """
    🔥 V2: Детектировать СКРЫТЫЕ противоречия через GPT (semantic analysis)
    
    Находит не очевидные (many friends + lonely), а СКРЫТЫЕ:
    - "Говоришь что любишь людей, но все хобби одиночные"
    - "Хочешь стабильности, но меняешь работу каждый год"
    
    Args:
        answers: Список ответов с вопросами
        category: Категория квиза (для контекста)
        
    Returns:
        Список противоречий (1-3 самых интересных)
    """
    if not answers or len(answers) < 2:
        # Мало данных для анализа
        return []
    
    # Формируем контекст для GPT
    answers_text = "\n".join([
        f"Q{i+1}: {a['question_text']}\nA: {a['answer_value']}"
        for i, a in enumerate(answers)
    ])
    
    prompt = f"""
You are a psychological DETECTIVE finding HIDDEN contradictions in quiz answers.

CATEGORY: {category}

ANSWERS:
{answers_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR TASK: Find SUBTLE, NON-OBVIOUS contradictions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ DON'T find OBVIOUS contradictions:
"Says has many friends + feels lonely" (user already knows!)
"Claims work-life balance + works 12 hours" (too surface!)

✅ DO find SUBTLE patterns:
"Says values relationships deeply + all hobbies are solitary → avoiding intimacy"
"Wants stability + changes jobs yearly without external reason → fear of commitment"
"Claims to be open + avoids vulnerability in every example → trust issues masked as openness"

LOOK FOR:
- Actions that contradict stated values
- Patterns that reveal hidden fears/motivations
- Aspirational identity vs actual behavior
- What they DON'T say (avoidance patterns)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return JSON (1-3 contradictions):
{{
  "contradictions": [
    {{
      "summary": "Short description (1 sentence)",
      "evidence": ["Quote from answer 1", "Quote from answer 2"],
      "insight": "What this REALLY means (hidden dynamic)"
    }}
  ]
}}

If NO subtle contradictions found, return empty array.
QUALITY over QUANTITY: Better 1 good insight than 3 obvious ones.
"""
    
    try:
        # ✅ TIER 1: Add timeout to GPT call (20 seconds)
        import asyncio
        
        response = await asyncio.wait_for(
            client.chat.completions.create(
            model="gpt-4o-mini",  # Fast & cheap для mid-quiz analysis
            messages=[
                {"role": "system", "content": "You find hidden psychological patterns that users don't see."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3  # Low temperature для более deterministic
            ),
            timeout=20.0  # ✅ TIER 1: 20 second timeout for GPT
        )
        
        result = json.loads(response.choices[0].message.content)
        contradictions_data = result.get('contradictions', [])
        
        # Извлекаем summaries для использования в follow-up вопросах
        contradictions = [c['summary'] for c in contradictions_data if c.get('summary')]
        
        logger.info(f"🔍 GPT found {len(contradictions)} subtle contradictions")
        return contradictions[:2]  # Limit to top 2
        
    except asyncio.TimeoutError:
        logger.warning(f"⏱ GPT contradiction detection timed out after 20s - using fallback")
        # ✅ TIER 1: Fallback при timeout
        return _detect_answer_contradictions_keyword_fallback(answers)
    except Exception as e:
        logger.error(f"GPT contradiction detection failed: {e}")
        # Fallback на keyword-based
        return _detect_answer_contradictions_keyword_fallback(answers)


def _detect_answer_contradictions_keyword_fallback(answers: list[dict]) -> list[str]:
    """
    Fallback: Keyword-based detection если GPT недоступен
    """
    contradictions = []
    
    answers_text = [
        (a['question_text'].lower(), a['answer_value'].lower())
        for a in answers
    ]
    
    # Простые heuristics (топ 2-3 самых частых)
    has_friends = any('friend' in q and ('many' in a or 'yes' in a or 'a lot' in a) 
                      for q, a in answers_text)
    feels_lonely = any(('lonely' in q or 'alone' in q) and ('often' in a or 'yes' in a or 'very' in a)
                       for q, a in answers_text)
    
    if has_friends and feels_lonely:
        contradictions.append(
            "Claims many friends but feels lonely often → possible surface-level connections"
        )
    
    return contradictions[:2]


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

        # 1. Крючки на прогрев — для новых людей берём больше (3), для тёплой базы меньше (1-2)
        seed_pack = _clone_seed_questions(category)
        if not user_profile or not user_profile.get("patterns"):
            # Новые пользователи: даём 3 seed вопроса (включая сценарный)
            questions.extend(seed_pack[:3])
        else:
            # Пользователи с историей: 1-2 вопроса в зависимости от количества паттернов
            patterns_count = len(user_profile.get("patterns", []))
            seed_count = 1 if patterns_count >= 3 else 2
            questions.extend(seed_pack[:seed_count])

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

    relevant_patterns = get_relevant_patterns_for_quiz(
        patterns=patterns,
        category=category,
        max_patterns=2,
    )

    probes: list[dict] = []
    for pattern in relevant_patterns:
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

        if question_type in {"scale"}:
            if not question.get("options"):
                question["options"] = list(_DEFAULT_SCALE_OPTIONS)
            else:
                question["options"] = _decorate_scale_options(question["options"])
        elif question_type in {"multiple_choice"}:
            if not question.get("options"):
                question["options"] = list(_GENERIC_MULTIPLE_CHOICE_FALLBACK)
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
    relevant_patterns = get_relevant_patterns_for_quiz(
        patterns=patterns,
        category=category,
        max_patterns=3,
    )

    if relevant_patterns:
        patterns_summary = "\n".join(
            [
                f"- {item.get('title', 'Паттерн')} (confidence {item.get('confidence', 0):.0%})"
                for item in relevant_patterns
            ]
        )
    else:
        patterns_summary = "— данных нет, считай пользователя белым листом."

    prompt = f"""
Ты — психолог, который ведёт глубинный квиз в формате живого диалога. 

КАТЕГОРИЯ: {category_info['name']}
ОПИСАНИЕ: {category_info['description']}
ТОН: {category_info.get('tone_hint', 'Будь честным, тёплым и точным.')} 

Уже прозвучало:
{asked_questions_text}

Ответы пользователя:
{answers_text}

Известные паттерны (релевантные теме "{category_info['name']}"):
{patterns_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Тебе нужно придумать {needed} следующих вопросов.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ПРАВИЛА:
1. Пиши по-русски, разговорно, без канцелярита
2. Если есть за что зацепиться — ссылайся на ответы: «Ты сказал…», «Ты отметил…»
3. Копай противоречия, скрытые мотивы, заблокированные ресурсы
4. Избегай банальных «Как часто…» — будь конкретнее!
5. Можно добавить "preface" — короткий крючок (до 100 символов)
6. Не повторяй темы уже заданных вопросов

🎯 КРИТИЧНО: ЧЕРЕДУЙ ТИПЫ ВОПРОСОВ!

Используй 3 типа:
- "text" (20-30%): Глубокое исследование, открытый ответ
- "scale" (40-50%): Частота/интенсивность (5 точек: Никогда → Постоянно)
- "multiple_choice" (20-30%): Быстрые решения (3-4 варианта)

⚠️ ВАЖНО: НЕ делай 3+ "text" вопроса подряд (усталость пользователя)!
✅ ЧЕРЕДУЙ типы для лучшего вовлечения

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПРИМЕРЫ (каждый тип):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ТИП "text" (открытый ответ):
{{
  "id": "dyn_1",
  "text": "С кем бы ты рискнул поделиться тем, что сейчас переживаешь, если выбрать только одного человека?",
  "type": "text",
  "options": [],
  "preface": "Копаем глубже"
}}

ТИП "scale" (шкала частоты):
{{
  "id": "dyn_2",
  "text": "Как часто ты ловишь себя на мысли: 'Я недостаточно хорош'?",
  "type": "scale",
  "options": ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"]
}}

ТИП "multiple_choice" (выбор из вариантов):
{{
  "id": "dyn_3",
  "text": "Когда тебе делают комплимент, что происходит первым?",
  "type": "multiple_choice",
  "options": [
    "Неловко, ищу что ответить",
    "Сразу обесцениваю ('Да ладно, это ерунда')",
    "Радуюсь и благодарю",
    "Подозреваю что-то ('А зачем он это сказал?')"
  ]
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ВЕРНИ JSON:
{{
  "questions": [
    {{
      "id": "dyn_X",
      "text": "...",
      "type": "text|scale|multiple_choice",
      "options": [...] если type != "text",
      "preface": "..." (опционально)
    }}
  ]
}}

ПОМНИ: Чередуй типы! Пиши по-русски. Ссылайся на ответы пользователя где уместно.
"""

    try:
        # ✅ TIER 1: Add timeout to GPT call (20 seconds)
        import asyncio
        
        response = await asyncio.wait_for(
            client.chat.completions.create(
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
            ),
            timeout=20.0  # ✅ TIER 1: 20 second timeout for GPT
        )
        data = json.loads(response.choices[0].message.content)
        generated = data.get("questions", [])
    except asyncio.TimeoutError:
        logger.warning(f"⏱ Dynamic quiz batch generation timed out after 20s")
        return []  # ✅ TIER 1: Fallback - пустой массив
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
        Отформатированный текст (HTML разметка)
    """
    import html
    
    category_info = QUIZ_CATEGORIES.get(question.get('category', 'relationships'), {})
    emoji = category_info.get('emoji', '🧠')
    safe_question_text = html.escape(question.get('text', ''))
    preface = question.get('preface')
    question_type = question.get('type', 'text')

    # ✨ TIER 2: Улучшенное форматирование - больше воздуха
    # Показываем прогресс, чтобы человек понимал, сколько осталось
    if total:
        header = f"{emoji} <b>Вопрос {current} из {total}</b>"  # ✨ "из" вместо "/" для читаемости
    else:
        header = f"{emoji} <b>Вопрос {current}</b>"

    body_parts: list[str] = [header, ""]  # Пустая строка для отступа

    # Preface (если есть) — курсивом, отдельной строкой
    if preface:
        body_parts.append(f"<i>{html.escape(preface)}</i>")
        body_parts.append("")  # ✨ TIER 2: Дополнительный отступ после preface

    # Сам вопрос — жирным
    body_parts.append(f"<b>{safe_question_text}</b>")
    body_parts.append("")  # Отступ перед инструкцией

    # Дополнительный прогресс-индикатор ближе к финалу
    if total and total - current <= 3 and total - current >= 1:
        remaining = total - current
        if remaining == 1:
            remaining_text = "Остался 1 вопрос"
        elif remaining < 5:
            remaining_text = f"Осталось {remaining} вопроса"
        else:
            remaining_text = f"Осталось {remaining} вопросов"
        body_parts.append(f"⏳ <i>{remaining_text}</i>")
        body_parts.append("")

    # Инструкция в зависимости от типа (элегантная, не техническая)
    if question_type == 'scale':
        body_parts.append("📊 <i>Выбери точку на шкале:</i>")
        # Показываем preview шкалы
        options = question.get('options', [])
        if options and len(options) == 5:
            body_parts.append(f"<i>{options[0]} → {options[-1]}</i>")
    
    elif question_type == 'multiple_choice':
        body_parts.append("☑️ <i>Выбери вариант, который откликается:</i>")
    
    else:  # text
        body_parts.append("✍️ <i>Напиши что думаешь, можно войсом</i> 🎙️")

    return "\n".join(body_parts)

