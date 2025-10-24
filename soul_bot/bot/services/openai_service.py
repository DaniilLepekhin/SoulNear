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
from typing import List, Dict, Optional
from datetime import datetime

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from config import OPENAI_API_KEY, is_feature_enabled
from database.repository import user_profile, conversation_history
import database.repository.user as db_user
import database.repository.statistic_day as db_statistic_day

# Инициализация OpenAI клиента
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger(__name__)


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
    # Получаем профиль пользователя
    profile = await user_profile.get_or_create(user_id)
    user = await db_user.get(user_id)
    
    # Базовые инструкции по типу ассистента
    if base_instructions is None:
        base_instructions = _get_base_instructions(assistant_type)
    
    # Строим промпт по частям
    prompt_parts = [base_instructions]
    
    # ==========================================
    # ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ
    # ==========================================
    if user:
        user_info = []
        if user.real_name:
            user_info.append(f"Имя пользователя: {user.real_name}")
        if user.age:
            user_info.append(f"Возраст: {user.age}")
        if user.gender is not None:
            gender = "мужской" if user.gender else "женский"
            user_info.append(f"Пол: {gender}")
        
        if user_info:
            prompt_parts.append("\n## 👤 О пользователе:\n" + "\n".join(user_info))
    
    # ==========================================
    # НАСТРОЙКИ СТИЛЯ
    # ==========================================
    style_instructions = _build_style_instructions(profile)
    if style_instructions:
        prompt_parts.append(style_instructions)
    
    # ==========================================
    # ПАТТЕРНЫ И ИНСАЙТЫ
    # ==========================================
    patterns = profile.patterns.get('patterns', [])
    if patterns and len(patterns) > 0:
        # Берём последние 5 паттернов
        recent_patterns = patterns[-5:]
        patterns_text = "\n".join([
            f"- {p.get('description', 'Без описания')}"
            for p in recent_patterns
        ])
        prompt_parts.append(
            f"\n## 🧠 Выявленные паттерны пользователя:\n{patterns_text}\n"
            "Учитывай эти паттерны в своих ответах."
        )
    
    insights = profile.insights.get('insights', [])
    if insights and len(insights) > 0:
        # Берём последние 3 инсайта
        recent_insights = insights[-3:]
        insights_text = "\n".join([
            f"- {i.get('insight', 'Без описания')}"
            for i in recent_insights
        ])
        prompt_parts.append(
            f"\n## 💡 Ключевые инсайты:\n{insights_text}\n"
            "Используй эти инсайты для более глубокого понимания пользователя."
        )
    
    # ==========================================
    # ДОПОЛНИТЕЛЬНЫЕ ПРЕДПОЧТЕНИЯ
    # ==========================================
    custom_instructions = profile.preferences.get('custom_instructions')
    if custom_instructions:
        prompt_parts.append(
            f"\n## ⚙️ Дополнительные инструкции:\n{custom_instructions}"
        )
    
    # Объединяем все части
    full_prompt = "\n".join(prompt_parts)
    
    return full_prompt


def _get_base_instructions(assistant_type: str) -> str:
    """Получить базовые инструкции для типа ассистента"""
    
    instructions = {
        'helper': """Ты - эмпатичный помощник и психолог, который помогает пользователям разбираться в их переживаниях и находить решения жизненных вопросов.

Твоя цель:
- Внимательно слушать и понимать проблемы пользователя
- Задавать уточняющие вопросы для глубокого понимания
- Давать практичные советы и рекомендации
- Поддерживать и мотивировать
- Помогать увидеть ситуацию с разных сторон

Твой стиль:
- Эмпатичный и понимающий
- Тактичный и деликатный
- Конкретный и практичный
- Вдохновляющий, но реалистичный""",

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


def _build_style_instructions(profile) -> str:
    """Построить инструкции на основе настроек стиля"""
    
    tone_map = {
        'formal': 'Используй формальный и профессиональный тон.',
        'friendly': 'Общайся дружелюбно и тепло, как с другом.',
        'sarcastic': 'Можешь использовать лёгкую иронию и сарказм (но осторожно).',
        'motivating': 'Будь вдохновляющим и мотивирующим, заряжай энергией.'
    }
    
    personality_map = {
        'mentor': 'Веди себя как мудрый наставник, делящийся опытом.',
        'friend': 'Будь как поддерживающий друг, который всегда рядом.',
        'coach': 'Действуй как строгий, но справедливый коуч, фокусирующийся на результатах.'
    }
    
    length_map = {
        'brief': 'Отвечай кратко и по существу (1-2 короткихабзаца).',
        'medium': 'Давай развёрнутые, но структурированные ответы (3-4 абзаца).',
        'detailed': 'Предоставляй подробные и глубокие ответы с примерами (5-7 абзацев).'
    }
    
    style_parts = ["\n## 🎨 Стиль общения:"]
    
    if profile.tone_style in tone_map:
        style_parts.append(tone_map[profile.tone_style])
    
    if profile.personality in personality_map:
        style_parts.append(personality_map[profile.personality])
    
    if profile.message_length in length_map:
        style_parts.append(length_map[profile.message_length])
    
    return "\n".join(style_parts) if len(style_parts) > 1 else ""


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
        # 1. Строим system prompt
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
        
        # 4. Вызываем ChatCompletion API
        response: ChatCompletion = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )
        
        # 5. Извлекаем ответ
        assistant_message = response.choices[0].message.content
        
        # 6. Сохраняем сообщения в историю
        await save_conversation(
            user_id=user_id,
            assistant_type=assistant_type,
            user_message=message,
            assistant_message=assistant_message,
            model=model,
            tokens_used=response.usage.total_tokens if response.usage else None
        )
        
        # 7. Обновляем статистику
        asyncio.create_task(_update_statistics(assistant_type, success=True))
        
        return assistant_message
        
    except Exception as e:
        logger.error(f"Error in get_chat_completion: {e}", exc_info=True)
        
        # Обновляем статистику ошибок
        asyncio.create_task(_update_statistics(assistant_type, success=False))
        
        # Отправляем уведомление об ошибке админам
        asyncio.create_task(_send_error_notification(
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

