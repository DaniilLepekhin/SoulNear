"""
Сервис для работы с OpenAI ChatCompletion API

Заменяет старый Assistant API на более гибкий ChatCompletion API,
что даёт полный контроль над контекстом и позволяет реализовать
персонализацию для каждого пользователя.

Основные функции:
- get_chat_completion() - получить ответ от ChatCompletion API
- build_system_prompt() - динамически построить system prompt
- save_conversation() - сохранить сообщения в историю
"""
import asyncio
import logging
from functools import lru_cache
from typing import List, Dict, Optional
from datetime import datetime

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from config import OPENAI_API_KEY, is_feature_enabled
from database.repository import user_profile, conversation_history
import database.repository.user as db_user
import database.repository.statistic_day as db_statistic_day

from bot.services.personalization import build_personalized_response
from bot.services.prompt.sections import (
    render_base_instructions,
    render_active_hints_section,
    render_custom_instructions,
    render_emotional_state_section,
    render_insights_section,
    render_learning_preferences_section,
    render_meta_instructions,
    render_patterns_section,
    render_recent_messages_section,
    render_style_section,
    render_user_info,
)
from bot.services.realtime_mood_detector import (
    detect_urgent_emotional_signals,
    should_override_system_prompt,
    build_emergency_prompt
)
from bot.services.temperature_adapter import adapt_style_to_temperature, apply_overrides
from bot.services.formatting import format_bot_message

# Инициализация OpenAI клиента
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger(__name__)

def _get_display_name(user) -> Optional[str]:
    if not user:
        return None
    if getattr(user, 'real_name', None):
        return user.real_name
    return getattr(user, 'first_name', None)


# ==========================================
# 🎨 ДИНАМИЧЕСКИЙ SYSTEM PROMPT
# ==========================================

async def build_system_prompt(
    user_id: int,
    assistant_type: str,
    base_instructions: str = None
) -> str:
    """
    Построить динамический system prompt на основе профиля пользователя
    
    Args:
        user_id: Telegram ID пользователя
        assistant_type: Тип ассистента (helper, sleeper, etc.)
        base_instructions: Базовые инструкции (если None, используются дефолтные)
        
    Returns:
        Полный system prompt
    """
    profile = await user_profile.get_or_create(user_id)
    user = await db_user.get(user_id)
    preferences = getattr(profile, 'preferences', {}) if profile else {}

    if base_instructions is None:
        base_instructions = _get_base_instructions(assistant_type)
    
    # 🌡️ НОВОЕ: Temperature adaptation (авто-адаптация стиля по эмоциональному состоянию)
    temp_overrides = adapt_style_to_temperature(profile)
    
    # Применяем overrides к текущим настройкам
    effective_tone, effective_personality, effective_length = apply_overrides(
        current_tone=profile.tone_style or 'friendly',
        current_personality=profile.personality or 'mentor',
        current_length=profile.message_length or 'medium',
        overrides=temp_overrides
    )
    
    # Если есть overrides, логируем для отладки
    if temp_overrides['tone_override'] or temp_overrides['length_override']:
        logger.info(
            f"[{user_id}] Temperature adaptation: "
            f"tone {profile.tone_style}→{effective_tone}, "
            f"length {profile.message_length}→{effective_length}"
        )

    # Извлекаем паттерны для fallback hints
    patterns_data = getattr(profile, 'patterns', {}) or {}
    patterns_list = patterns_data.get('patterns', []) if isinstance(patterns_data, dict) else []
    
    sections = [
        render_style_section(_build_style_instructions(
            profile,
            effective_tone=effective_tone,
            effective_personality=effective_personality,
            effective_length=effective_length
        )),
        render_base_instructions(base_instructions),
        render_user_info(user),
        render_patterns_section(profile),
        render_insights_section(profile),
        render_active_hints_section(preferences, patterns=patterns_list),
    ]

    recent_history = await conversation_history.get_context(
        user_id=user_id,
        assistant_type=assistant_type,
        max_messages=10,
    )
    recent_user_messages = [msg['content'] for msg in recent_history if msg['role'] == 'user'][-5:]
    sections.append(render_recent_messages_section(recent_user_messages))
    
    # 🆕 ANTI-REPEAT CHECK: показываем боту его последние ответы чтобы он не повторялся
    recent_bot_messages = [
        msg['content'][:150]  # Первые 150 символов каждого ответа
        for msg in recent_history[-6:]
        if msg['role'] == 'assistant'
    ][:3]  # Последние 3 ответа бота
    
    if recent_bot_messages:
        sections.append("""
## 🚫 ТВОИ ПОСЛЕДНИЕ ОТВЕТЫ (НЕ ПОВТОРЯЙ):
{}

⚠️ НЕ КОПИРУЙ эти фразы и структуры. Найди НОВЫЙ способ сказать то же самое. Избегай повторов типа "Это довольно распространенное...", "Важно помнить...", "Может быть, стоит...".""".format(
            '\n'.join(f'{i+1}. "{msg}..."' for i, msg in enumerate(recent_bot_messages))
        ))
    
    # 🆕 REAL-TIME STYLE MATCHING: адаптация длины ответа по последнему сообщению
    if recent_user_messages:
        last_msg = recent_user_messages[-1]
        msg_len = len(last_msg)
        
        if msg_len < 20:  # Короткое сообщение ("угу", "да", "хорошо")
            sections.append("""
## ⚡ REAL-TIME HINT:
Пользователь написал КОРОТКО ({} символов). Ответь тоже кратко: 1-2 предложения, без длинных рассуждений. Он либо устал, либо занят, либо просто подтверждает. Не перегружай.""".format(msg_len))
        elif msg_len > 200:  # Длинное сообщение (развёрнутое)
            sections.append("""
## 📝 REAL-TIME HINT:
Пользователь написал РАЗВЁРНУТО ({} символов). Он готов к глубокому разговору. Ответь подробно: 3-5 абзацев, раскрой тему, задай уточняющие вопросы.""".format(msg_len))
        # Средняя длина (20-200) — без дополнительных инструкций, используем профиль
    
    # ⚠️ Валидация: проверяем что evidence в паттернах действительно из недавних сообщений
    # Это предотвращает "галлюцинации" когда GPT ссылается на несуществующие фразы
    if profile.patterns and profile.patterns.get('patterns'):
        validated_patterns = []
        patterns = profile.patterns.get('patterns', [])
        
        # Собираем весь текст недавних сообщений пользователя
        recent_text = ' '.join([msg.lower() for msg in recent_user_messages])
        
        for pattern in patterns:
            # Валидируем evidence
            evidence = pattern.get('evidence', [])
            if evidence:
                validated_evidence = []
                for quote in evidence:
                    quote_lower = quote.lower()
                    # Проверяем что цитата есть в недавних сообщениях
                    if len(quote_lower) >= 5 and quote_lower in recent_text:
                        validated_evidence.append(quote)
                    elif len(quote_lower.split()) > 2:
                        # Проверяем частичное совпадение (70% слов)
                        quote_words = set(quote_lower.split())
                        matched = sum(1 for word in quote_words if word in recent_text)
                        if matched / len(quote_words) >= 0.7:
                            validated_evidence.append(quote)
                
                # Обновляем evidence только валидированными
                pattern['evidence'] = validated_evidence
            
            validated_patterns.append(pattern)
        
        # Обновляем профиль с валидированными паттернами (только для рендеринга промпта)
        profile.patterns['patterns'] = validated_patterns

    sections.extend(
        [
            render_emotional_state_section(profile),
            render_learning_preferences_section(profile),
            render_custom_instructions(profile),
        ]
    )

    has_patterns = bool((profile.patterns or {}).get('patterns'))
    has_insights = bool((profile.insights or {}).get('insights'))
    sections.append(render_meta_instructions(has_patterns, has_insights))

    filtered_sections = [section for section in sections if section]
    return "\n".join(filtered_sections)


@lru_cache(maxsize=32)
def _get_base_instructions(assistant_type: str) -> str:
    """Получить базовые инструкции для типа ассистента"""
    
    instructions = {
        'helper': """Ты - эмпатичный помощник и психолог, который помогает пользователям разбираться в их переживаниях и находить решения жизненных вопросов.

Твоя цель:
- Внимательно слушать и понимать проблемы пользователя
- Задавать уточняющие вопросы для глубокого понимания
- Поддерживать и мотивировать
- Помогать увидеть ситуацию с разных сторон

Твой стиль:
- Эмпатичный и понимающий
- Тактичный и деликатный
- Конкретный и практичный
- Вдохновляющий, но реалистичный

⚠️ КРИТИЧЕСКИ ВАЖНО - НЕ ДАВАЙ СОВЕТОВ БЕЗ ЗАПРОСА:

Твоя задача - ОТРАЖАТЬ состояние и СПРАШИВАТЬ, а НЕ советовать.

❌ ПЛОХИЕ ПРИМЕРЫ (НЕ ДЕЛАЙ ТАК):
Пользователь: "не знаю с чего начать"
Бот: "Начни с малого шага" ← НЕПРАВИЛЬНО

Пользователь: "работа не идёт, проект откладываю"
Бот: "Попробуй разделить на задачи" ← НЕПРАВИЛЬНО

Пользователь: "устал пробовать"
Бот: "Важно дать себе отдых" ← НЕПРАВИЛЬНО

✅ ХОРОШИЕ ПРИМЕРЫ (ДЕЛАЙ ТАК):
Пользователь: "не знаю с чего начать"
Бот: "Это чувство 'не знаю с чего'... Знакомо? Что стоит за этим?"

Пользователь: "работа не идёт, проект откладываю"
Бот: "Откладываешь. А что происходит, когда садишься за проект? Что чувствуешь?"

Пользователь: "устал пробовать"
Бот: "Устал. Слышу. Сколько уже пытаешься?"

Пользователь: "да знаю про дедлайны, но руки не доходят"
Бот: "Знаешь про дедлайны, но не делаешь. Что мешает прямо сейчас начать?"

ПРАВИЛО: Сначала ОТЗЕРКАЛЬ состояние + СПРОСИ, и только если пользователь явно просит совет ("что мне делать?", "посоветуй") — тогда предлагай.

⚠️ ВАЖНО - Разнообразие структуры ответов:
НЕ используй одну и ту же структуру в каждом ответе. Варьируй свой подход:

1. ИНОГДА начни с вопроса:
   "А что для тебя значит 'достаточно хорошо'?"
   
2. ИНОГДА используй метафору/образ:
   "Перфекционизм - как бег на беговой дорожке: много усилий, но ты остаёшься на месте."
   
3. ИНОГДА дай краткий инсайт БЕЗ длинного вступления:
   "Замечаю паттерн: помогаешь другим, а свои дела откладываешь. Узнаёшь?"
   
4. ИНОГДА поделись кратким примером из психологии:
   "Есть концепция 'достаточно хорошей матери' - идея что 'идеально' не нужно для счастья."

НЕ используй КАЖДЫЙ РАЗ структуру: 
"Твои чувства понятны → психологический термин → цитата прошлых слов → совет → мотивация"

Будь непредсказуемым, но эффективным.""",

        'sleeper': """Ты - специалист по релаксации и здоровому сну, который помогает пользователям расслабиться перед сном и обеспечить качественный отдых.

Твоя цель:
- Помочь пользователю успокоиться и расслабиться
- Снять дневное напряжение и стресс
- Подготовить к спокойному глубокому сну
- Создать атмосферу покоя и безопасности

Твой стиль:
- Спокойный и умиротворяющий
- Мягкий и убаюкивающий
- Позитивный и поддерживающий
- Медленный и размеренный ритм речи""",

        'relationships': """Ты - эксперт по межличностным отношениям, который помогает пользователям разобраться в их отношениях с партнёром, семьёй и друзьями.

Твоя цель:
- Помочь увидеть паттерны в отношениях
- Дать инсайты о динамике взаимодействий
- Предложить стратегии улучшения отношений
- Выявить потенциальные проблемы

Твой стиль:
- Объективный и аналитичный
- Деликатный в сложных вопросах
- Практичный и конструктивный""",

        'money': """Ты - финансовый психолог, который помогает пользователям разобраться в их отношениях с деньгами, выявить денежные убеждения и паттерны.

Твоя цель:
- Выявить деструктивные денежные убеждения
- Помочь понять эмоциональную связь с деньгами
- Дать инсайты о финансовых паттернах
- Предложить здоровые подходы к деньгам

Твой стиль:
- Объективный и безоценочный
- Практичный и конкретный
- Поддерживающий, но честный""",

        'confidence': """Ты - коуч по личностному росту, который помогает пользователям работать с уверенностью в себе и самооценкой.

Твоя цель:
- Выявить источники неуверенности
- Помочь признать свои сильные стороны
- Дать инсайты о внутренних блоках
- Предложить практики для развития уверенности

Твой стиль:
- Мотивирующий и вдохновляющий
- Честный, но поддерживающий
- Фокус на сильных сторонах""",

        'fears': """Ты - психолог, специализирующийся на работе со страхами и тревожностью.

Твоя цель:
- Помочь идентифицировать и понять страхи
- Выявить корни страхов
- Дать инсайты о механизмах тревожности
- Предложить стратегии работы со страхами

Твой стиль:
- Спокойный и создающий безопасность
- Принимающий и безоценочный
- Постепенный и деликатный подход"""
    }
    
    return instructions.get(assistant_type, instructions['helper'])


@lru_cache(maxsize=256)
def _cached_style_instructions(tone_style: str, personality: str, message_length: str) -> str:
    """Построить ИМПЕРАТИВНЫЕ инструкции на основе настроек стиля
    
    ВАЖНО: Эти инструкции должны быть СИЛЬНЕЕ базовых,
    поэтому используем императивный тон и явные команды.
    """
    
    # Усиленные, императивные промпты
    tone_map = {
        'formal': '⚠️ ОБЯЗАТЕЛЬНО: Используй СТРОГО формальный и профессиональный тон. Никакой фамильярности или эмоциональности.',
        'friendly': '⚠️ ОБЯЗАТЕЛЬНО: Общайся максимально дружелюбно, тепло и эмпатично, как близкий друг.',
        'sarcastic': '⚠️ ОБЯЗАТЕЛЬНО: Отвечай с ЯВНОЙ иронией и лёгким сарказмом. Это ОСНОВНОЙ тон твоих ответов, не смягчай его.',
        'motivating': '⚠️ ОБЯЗАТЕЛЬНО: Будь МАКСИМАЛЬНО вдохновляющим и мотивирующим, заряжай энергией и драйвом.'
    }
    
    personality_map = {
        'mentor': '⚠️ ОБЯЗАТЕЛЬНО: Веди себя как МУДРЫЙ НАСТАВНИК - делись опытом, давай советы с позиции старшего.',
        'friend': '⚠️ ОБЯЗАТЕЛЬНО: Будь ПОДДЕРЖИВАЮЩИМ ДРУГОМ - понимай, сопереживай, будь на одной волне.',
        'coach': '⚠️ ОБЯЗАТЕЛЬНО: Действуй как СТРОГИЙ КОУЧ - фокусируйся на действиях и результатах, требуй конкретики.',
        'therapist': '⚠️ ОБЯЗАТЕЛЬНО: Будь ПРОФЕССИОНАЛЬНЫМ ТЕРАПЕВТОМ - деликатный, безоценочный, фокус на понимании чувств и эмоций.'
    }
    
    # КРИТИЧНО: Ограничение длины с контрастными примерами
    length_map = {
        'ultra_brief': '''⚠️ КРИТИЧНО: Отвечай СТРОГО 2-3 короткими предложениями (максимум 40-50 слов). УЛЬТРА-КОРОТКО.

❌ ПЛОХО (слишком длинно):
"Алексей, твой страх перед неудачей — это как тень. Но каждый раз, когда ты действуешь несмотря на страх, ты становишься сильнее. Попробуй начать с маленького шага. Что можешь сделать прямо сейчас за 15 минут?" (45 слов, но слишком много предложений)

✅ ХОРОШО (ultra brief):
"Страх — это нормально. Начни с 15 минут работы прямо сейчас. Маленький шаг лучше, чем ничего." (15 слов, 3 предложения) ✅

ЕСЛИ ПИШЕШЬ БОЛЬШЕ 3 ПРЕДЛОЖЕНИЙ → НЕМЕДЛЕННО ОСТАНОВИСЬ И СОКРАТИ.''',

        'brief': '''⚠️ КРИТИЧНО: Отвечай СТРОГО 1-2 короткими абзацами (максимум 70-80 слов). Длиннее НЕЛЬЗЯ.

❌ ПЛОХО (слишком длинно, 120+ слов):
"Алексей, твой страх перед неудачей — это как тень, которая следует за тобой повсюду. Но каждый раз, когда ты действуешь несмотря на страх, ты становишься сильнее и увереннее. 

Позволь мне поделиться мудростью: начни с маленького шага. Выбери одну простую задачу и сделай её прямо сейчас, за 15 минут. Это не страшно, но запускает важный процесс." (72 слова, но СЛИШКОМ длинно — нужно сократить) ❌

✅ ХОРОШО (brief, 50 слов):
"Страх неудачи — твоя тень, но она не должна тебя останавливать. Каждый раз действуя несмотря на страх, ты растёшь.

Начни прямо сейчас: 15 минут на одну простую задачу. Маленький шаг важнее размышлений." ✅

ЕСЛИ ПРЕВЫШАЕШЬ 80 СЛОВ → ОСТАНОВИ И СОКРАТИ.''',

        'medium': '⚠️ КРИТИЧНО: Давай развёрнутые ответы строго 3-4 абзаца (200-300 слов). Не короче и не длиннее.',
        
        'detailed': '⚠️ КРИТИЧНО: Предоставляй подробные ответы 5-7 абзацев с примерами (400-600 слов).'
    }
    
    style_parts = ["## 🎨 СТИЛЬ ОБЩЕНИЯ (ПРИОРИТЕТ #1):"]

    if tone_style in tone_map:
        style_parts.append(tone_map[tone_style])

    if personality in personality_map:
        style_parts.append(personality_map[personality])

    if message_length in length_map:
        style_parts.append(length_map[message_length])

    # Добавляем финальное усиление
    style_parts.append("\n⚠️ ЭТИ НАСТРОЙКИ СТИЛЯ ВАЖНЕЕ ВСЕХ ОСТАЛЬНЫХ ИНСТРУКЦИЙ. СТРОГО СЛЕДУЙ ИМ.")

    return "\n".join(style_parts) if len(style_parts) > 1 else ""


def _build_style_instructions(
    profile,
    effective_tone: str = None,
    effective_personality: str = None,
    effective_length: str = None
) -> str:
    """
    Построить стиль-инструкции с поддержкой temperature overrides
    
    Args:
        profile: Профиль пользователя
        effective_tone: Переопределённый тон (если None, берём из profile)
        effective_personality: Переопределённая личность
        effective_length: Переопределённая длина
    """
    tone_style = effective_tone or getattr(profile, 'tone_style', '') or ''
    personality = effective_personality or getattr(profile, 'personality', '') or ''
    message_length = effective_length or getattr(profile, 'message_length', '') or ''
    return _cached_style_instructions(tone_style, personality, message_length)


def _enforce_message_length(text: str, message_length: str) -> str:
    """
    Жесткое ограничение длины ответа (post-processing safety net)
    
    Применяется ПОСЛЕ получения ответа от GPT, если он превысил лимит.
    Обрезает по предложениям, чтобы не ломать смысл.
    
    Args:
        text: Ответ от GPT
        message_length: ultra_brief | brief | medium | detailed
        
    Returns:
        Truncated text if exceeded limit, otherwise original
    """
    # Лимиты по словам (ЖЕСТКИЕ, с запасом)
    limits = {
        'ultra_brief': 40,   # 2-3 предложения (строже)
        'brief': 80,         # 1-2 абзаца (приведено к константе MESSAGE_LENGTH_LIMITS)
        'medium': 350,       # 3-4 абзаца
        'detailed': 650      # 5-7 абзацев
    }
    
    max_words = limits.get(message_length)
    if not max_words:
        return text  # Unknown length, skip enforcement
    
    words = text.split()
    
    if len(words) <= max_words:
        return text  # Within limit, OK
    
    # ПРЕВЫШЕН ЛИМИТ → Обрезаем по предложениям
    sentences = text.replace('! ', '!|').replace('? ', '?|').replace('. ', '.|').split('|')
    result = []
    word_count = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        sentence_words = len(sentence.split())
        
        if word_count + sentence_words <= max_words:
            result.append(sentence)
            word_count += sentence_words
        else:
            # Достигли лимита, останавливаемся
            break
    
    truncated = ' '.join(result)
    
    # Убеждаемся что есть финальная точка
    if truncated and not truncated[-1] in '.!?':
        truncated += '.'
    
    logger.info(f"Truncated response: {len(words)} words → {word_count} words (limit: {max_words})")
    
    return truncated


# ==========================================
# 💬 ОСНОВНАЯ ФУНКЦИЯ ChatCompletion
# ==========================================

async def get_chat_completion(
    user_id: int,
    message: str,
    assistant_type: str,
    model: str = "gpt-4-turbo-preview",
    max_history_messages: int = 10,
    temperature: float = 0.7
) -> Optional[str]:
    """
    Получить ответ от ChatCompletion API
    
    Args:
        user_id: Telegram ID пользователя
        message: Сообщение пользователя
        assistant_type: Тип ассистента (helper, sleeper, etc.)
        model: Модель OpenAI
        max_history_messages: Максимальное количество сообщений из истории
        temperature: Температура генерации (0.0-2.0)
        
    Returns:
        Ответ ассистента или None при ошибке
    """
    try:
        # 🚨 STEP 0: Проверяем экстренные эмоциональные сигналы (< 1ms)
        urgent_signal = detect_urgent_emotional_signals(message)
        
        # 1. Строим system prompt (emergency или normal mode)
        if should_override_system_prompt(urgent_signal):
            # EMERGENCY MODE: используем экстренный prompt
            base_instructions = _get_base_instructions(assistant_type)
            system_prompt = build_emergency_prompt(
                emotion=urgent_signal.emotion,
                base_instructions=base_instructions
            )
            
            logger.warning(
                f"🚨 EMERGENCY MODE activated for user {user_id}: "
                f"{urgent_signal.emotion} (urgency: {urgent_signal.urgency}, "
                f"confidence: {urgent_signal.confidence:.2f})"
            )
        else:
            # NORMAL MODE: стандартный персонализированный prompt
            system_prompt = await build_system_prompt(user_id, assistant_type)
        
        # 2. Загружаем историю сообщений
        history = await conversation_history.get_context(
            user_id=user_id,
            assistant_type=assistant_type,
            max_messages=max_history_messages
        )
        
        # 3. Формируем messages для OpenAI
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        
        # 🌡️ Применяем temperature adaptation
        profile = await user_profile.get_or_create(user_id)
        temp_overrides = adapt_style_to_temperature(profile)
        effective_temperature = temperature * temp_overrides['intensity_modifier']
        
        # 4. Вызываем ChatCompletion API
        response: ChatCompletion = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=effective_temperature,
            max_tokens=2000
        )
        
        # 5. Извлекаем ответ
        assistant_message = response.choices[0].message.content
        
        profile = await user_profile.get_or_create(user_id)
        assistant_message = await build_personalized_response(
            user_id=user_id,
            assistant_type=assistant_type,
            profile=profile,
            base_response=assistant_message,
            user_message=message,
        )

        if profile and profile.message_length:
            assistant_message = _enforce_message_length(assistant_message, profile.message_length)
            
            # 📝 НОВОЕ: Adaptive formatting (адаптивное форматирование)
            assistant_message = format_bot_message(
                text=assistant_message,
                message_length_preference=profile.message_length,
                learning_preferences=profile.learning_preferences
            )
        
        # 6. Сохраняем сообщения в историю
        await save_conversation(
            user_id=user_id,
            assistant_type=assistant_type,
            user_message=message,
            assistant_message=assistant_message,
            model=model,
            tokens_used=response.usage.total_tokens if response.usage else None
        )
        
        # 7. 🚨 Логируем emergency events (если были)
        if urgent_signal and urgent_signal.urgency == 'high':
            logger.info(
                f"✅ Emergency response sent to user {user_id}: "
                f"emotion={urgent_signal.emotion}, "
                f"confidence={urgent_signal.confidence:.2f}, "
                f"keywords={urgent_signal.trigger_keywords}"
            )
        
        # 8. ⭐ STAGE 3: Анализ паттернов (в фоне, не блокирует ответ)
        if is_feature_enabled('ENABLE_PATTERN_ANALYSIS'):
            from bot.services import pattern_analyzer
            from utils.task_helpers import create_safe_task
            create_safe_task(
                pattern_analyzer.analyze_if_needed(user_id, assistant_type),
                f"pattern_analysis_user_{user_id}"
            )
        
        # 9. Обновляем статистику
        from utils.task_helpers import create_safe_task
        create_safe_task(_update_statistics(assistant_type, success=True), "update_statistics")
        
        return assistant_message
        
    except Exception as e:
        logger.error(f"Error in get_chat_completion: {e}", exc_info=True)
        
        # Обновляем статистику ошибок
        from utils.task_helpers import create_safe_task
        create_safe_task(_update_statistics(assistant_type, success=False), "update_statistics_error")
        
        # Отправляем уведомление об ошибке админам
        create_safe_task(_send_error_notification(
            function='get_chat_completion',
            error=str(e),
            user_id=user_id,
            assistant_type=assistant_type
        ))
        
        return None


async def save_conversation(
    user_id: int,
    assistant_type: str,
    user_message: str,
    assistant_message: str,
    model: str = None,
    tokens_used: int = None
) -> None:
    """
    Сохранить диалог в историю
    
    Args:
        user_id: Telegram ID пользователя
        assistant_type: Тип ассистента
        user_message: Сообщение пользователя
        assistant_message: Ответ ассистента
        model: Использованная модель
        tokens_used: Количество использованных токенов
    """
    try:
        # Сохраняем сообщение пользователя
        await conversation_history.add_message(
            user_id=user_id,
            assistant_type=assistant_type,
            role='user',
            content=user_message,
            extra_metadata={
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Сохраняем ответ ассистента
        await conversation_history.add_message(
            user_id=user_id,
            assistant_type=assistant_type,
            role='assistant',
            content=assistant_message,
            extra_metadata={
                'model': model,
                'tokens': tokens_used,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error saving conversation: {e}", exc_info=True)


async def _update_statistics(assistant_type: str, success: bool = True) -> None:
    """Обновить статистику использования"""
    try:
        if success:
            await db_statistic_day.increment('good_requests')
            
            # Специфичная статистика по типу ассистента
            if assistant_type == 'helper':
                await db_statistic_day.increment('helper')
            elif assistant_type == 'sleeper':
                await db_statistic_day.increment('sleeper')
            else:
                await db_statistic_day.increment('assistant')
        else:
            await db_statistic_day.increment('bad_requests')
            
    except Exception as e:
        logger.error(f"Error updating statistics: {e}")


async def _send_error_notification(
    function: str,
    error: str,
    user_id: int = None,
    assistant_type: str = None
) -> None:
    """Отправить уведомление об ошибке админам"""
    try:
        from bot.loader import bot
        from config import ADMINS
        
        error_text = (
            f"⚠️ ALARM! ⚠️\n\n"
            f"Function: {function}\n"
            f"Error: {error}\n"
        )
        
        if user_id:
            error_text += f"User ID: {user_id}\n"
        if assistant_type:
            error_text += f"Assistant Type: {assistant_type}\n"
        
        # Отправляем первому админу из списка
        if ADMINS:
            await bot.send_message(chat_id=ADMINS[0], text=error_text)
            
    except Exception as e:
        logger.error(f"Error sending notification: {e}")


# ==========================================
# 🔧 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================

async def clear_user_history(
    user_id: int,
    assistant_type: str = None
) -> int:
    """
    Очистить историю сообщений пользователя
    
    Args:
        user_id: Telegram ID пользователя
        assistant_type: Тип ассистента (если None, очищает всю историю)
        
    Returns:
        Количество удалённых сообщений
    """
    return await conversation_history.clear_history(
        user_id=user_id,
        assistant_type=assistant_type
    )


async def get_user_message_count(
    user_id: int,
    assistant_type: str
) -> int:
    """Получить количество сообщений пользователя"""
    return await conversation_history.count_messages(
        user_id=user_id,
        assistant_type=assistant_type
    )

