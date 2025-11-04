from datetime import datetime
import html

from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.user.start import menu_callback
from bot.keyboards.profile import (
    profile_menu, gender_menu, style_settings_menu,
    tone_menu, personality_menu, length_menu,
    build_style_settings_menu_v2
)
from bot.keyboards.start import back, menu
from bot.loader import dp, bot
import database.repository.user as db_user
import database.repository.user_profile as db_user_profile
from bot.states.states import Update_user_info
from config import is_feature_enabled
from bot.services.text_formatting import (
    localize_pattern_title,
    safe_shorten,
)


# Telegram message length limit
MAX_MESSAGE_LENGTH = 4096


# ==========================================
# 🧠 КОМАНДА /MY_PROFILE (STAGE 3)
# ==========================================

async def _send_long_message(message: Message, text: str, parse_mode: str = 'HTML'):
    """
    Отправка длинного сообщения, разбивая его на части если нужно.
    
    Telegram имеет лимит 4096 символов на сообщение.
    Если текст длиннее - разбиваем на части по разделителям (двойной перевод строки).
    
    Args:
        message: Исходное сообщение для ответа
        text: Текст для отправки
        parse_mode: Режим парсинга (HTML, Markdown)
    """
    if len(text) <= MAX_MESSAGE_LENGTH:
        await message.answer(text, parse_mode=parse_mode)
        return
    
    # Разбиваем по двойным переводам строки (параграфы)
    parts = text.split('\n\n')
    current_part = ""
    part_number = 1
    total_parts = (len(text) // MAX_MESSAGE_LENGTH) + 1
    
    for paragraph in parts:
        # Если добавление параграфа превысит лимит - отправляем текущую часть
        if len(current_part) + len(paragraph) + 2 > MAX_MESSAGE_LENGTH:
            if current_part:
                header = f"📄 <b>Часть {part_number}/{total_parts}</b>\n\n" if part_number > 1 or total_parts > 1 else ""
                await message.answer(header + current_part, parse_mode=parse_mode)
                part_number += 1
                current_part = ""
        
        # Добавляем параграф к текущей части
        if current_part:
            current_part += "\n\n" + paragraph
        else:
            current_part = paragraph
    
    # Отправляем остаток
    if current_part:
        header = f"📄 <b>Часть {part_number}/{total_parts}</b>\n\n" if part_number > 1 or total_parts > 1 else ""
        await message.answer(header + current_part, parse_mode=parse_mode)

STYLE_TONE_LABELS = {
    'friendly': 'дружелюбный',
    'formal': 'формальный',
    'sarcastic': 'ироничный',
    'motivating': 'мотивирующий',
}

STYLE_PERSONALITY_LABELS = {
    'mentor': 'наставник',
    'friend': 'друг',
    'coach': 'коуч',
    'therapist': 'терапевт',
}

STYLE_LENGTH_LABELS = {
    'ultra_brief': 'очень короткие',
    'brief': 'краткие',
    'medium': 'средние',
    'detailed': 'подробные',
}

MOOD_LABELS = {
    'positive': 'поднятое',
    'slightly_positive': 'ровное',
    'neutral': 'нейтральное',
    'slightly_down': 'уставшее',
    'negative': 'подавленное',
}

STRESS_LABELS = {
    'low': 'низкий',
    'medium': 'средний',
    'high': 'высокий',
    'critical': 'критический',
}

ENERGY_LABELS = {
    'low': 'мало',
    'medium': 'сбалансировано',
    'high': 'много',
}

def _shorten(text: str | None, limit: int = 160) -> str:
    """Сохранён для обратной совместимости с тестами и использует safe_shorten."""

    return safe_shorten(text, limit)


def _format_patterns_section(patterns: list[dict]) -> str:
    if not patterns:
        return ""

    lines: list[str] = ["🧩 <b>Главные паттерны</b>", ""]
    for pattern in patterns[:3]:
        title = html.escape(localize_pattern_title(pattern.get('title')))
        confidence = int((pattern.get('confidence') or 0) * 100)
        lines.append(f"• <b>{title}</b> · уверенность {confidence}%")

        contradiction = safe_shorten(pattern.get('contradiction'), 160)
        if contradiction:
            lines.append(f"  🔁 {html.escape(contradiction)}")

        hidden_dynamic = safe_shorten(pattern.get('hidden_dynamic'), 160)
        if hidden_dynamic:
            lines.append(f"  🎭 {html.escape(hidden_dynamic)}")

        resource = safe_shorten(pattern.get('blocked_resource'), 150)
        if resource:
            lines.append(f"  💎 {html.escape(resource)}")

        evidence = pattern.get('evidence') or []
        if evidence:
            snippet = safe_shorten(evidence[0], 140)
            if snippet:
                lines.append(f"  📝 <i>«{html.escape(snippet)}»</i>")

        lines.append("")

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)


def _format_insights_section(insights: list[dict]) -> str:
    if not insights:
        return ""

    lines: list[str] = ["💡 <b>Инсайты</b>"]
    for insight in insights[:3]:
        title = html.escape(insight.get('title', 'Инсайт'))
        lines.append(f"• <b>{title}</b>")

        description = safe_shorten(insight.get('description'), 220)
        if description:
            lines.append(f"  {html.escape(description)}")

        recs = insight.get('recommendations') or []
        if recs:
            lines.append(f"  👉 Что попробовать:")
            for rec in recs[:2]:
                snippet = safe_shorten(rec, 160)
                if snippet:
                    lines.append(f"    – {html.escape(snippet)}")

        lines.append("")

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)


def _format_emotional_state_section(emotional_state: dict) -> str:
    if not emotional_state:
        return ""

    mood = MOOD_LABELS.get((emotional_state.get('current_mood') or '').lower())
    stress = STRESS_LABELS.get((emotional_state.get('stress_level') or '').lower())
    energy = ENERGY_LABELS.get((emotional_state.get('energy_level') or '').lower())

    lines = ["😊 <b>Текущее состояние</b>"]
    if mood:
        lines.append(f"• Настроение: {mood}")
    if stress:
        lines.append(f"• Стресс: {stress}")
    if energy:
        lines.append(f"• Энергия: {energy}")

    return "\n".join(lines) if len(lines) > 1 else ""


def _format_learning_section(preferences: dict) -> str:
    if not preferences:
        return ""

    works = preferences.get('works_well') or []
    doesnt = preferences.get('doesnt_work') or []
    if not works and not doesnt:
        return ""

    lines = ["🎓 <b>Что помогает</b>"]
    if works:
        lines.append("• Работает:")
        for item in works[:3]:
            snippet = safe_shorten(item, 160)
            if snippet:
                lines.append(f"  – {html.escape(snippet)}")
    if doesnt:
        lines.append("• Не работает:")
        for item in doesnt[:3]:
            snippet = safe_shorten(item, 160)
            if snippet:
                lines.append(f"  – {html.escape(snippet)}")

    return "\n".join(lines)


def _format_profile_compact(profile, user) -> str:
    sections: list[str] = []

    header_lines = ["🧠 <b>Психологический профиль</b>"]
    user_meta = []
    if user.real_name:
        user_meta.append(f"Имя: {html.escape(user.real_name)}")
    if user.age:
        user_meta.append(f"Возраст: {user.age}")
    if user_meta:
        header_lines.append("\n".join(user_meta))
    sections.append("\n".join(header_lines))

    patterns = (profile.patterns or {}).get('patterns', []) if getattr(profile, 'patterns', None) else []
    patterns_block = _format_patterns_section(patterns)
    if patterns_block:
        sections.append(patterns_block)
    else:
        sections.append("🧩 Пока нет выявленных паттернов — продолжайте диалог, чтобы бот понял вас глубже.")

    insights = (profile.insights or {}).get('insights', []) if getattr(profile, 'insights', None) else []
    insights_block = _format_insights_section(insights)
    if insights_block:
        sections.append(insights_block)

    state_block = _format_emotional_state_section(getattr(profile, 'emotional_state', {}) or {})
    if state_block:
        sections.append(state_block)

    learning_block = _format_learning_section(getattr(profile, 'learning_preferences', {}) or {})
    if learning_block:
        sections.append(learning_block)

    return "\n\n".join([block for block in sections if block])


@dp.message(Command('my_profile'))
async def my_profile_command(message: Message):
    """
    Команда /my_profile - показать свой психологический профиль
    
    Форматирует профиль через GPT-4 для красивого отображения
    """
    user_id = message.from_user.id
    
    # Отправляем "печатаю..." пока GPT обрабатывает
    status_msg = await message.answer("🔄 Формирую ваш профиль...")
    
    try:
        profile = await db_user_profile.get_or_create(user_id)
        user = await db_user.get(user_id)
        
        # ✅ FIX: Check if user exists
        if user is None:
            await status_msg.edit_text("❌ Ошибка: пользователь не найден")
            return
        
        formatted_profile = _format_profile_compact(profile, user)
        
        # Удаляем "печатаю..." (с защитой от ошибки если уже удалено)
        try:
            await status_msg.delete()
        except Exception:
            pass  # Игнорируем если сообщение уже удалено
        
        # Отправляем профиль (разбиваем если слишком длинный)
        await _send_long_message(message, formatted_profile)
        
    except Exception as e:
        try:
            await status_msg.delete()
        except Exception:
            pass
        await message.answer(
            f"⚠️ Не удалось загрузить профиль: {e}\n\n"
            f"Попробуйте позже или обратитесь в поддержку."
        )


@dp.callback_query(F.data == 'view_psychological_profile')
async def view_psychological_profile_callback(call: CallbackQuery):
    """
    Callback для кнопки "Мой психологический профиль"
    
    Показывает детальный анализ без GPT, на основе текущих данных
    """
    user_id = call.from_user.id
    
    await call.answer("🔄 Формирую профиль...", show_alert=False)
    
    try:
        profile = await db_user_profile.get_or_create(user_id)
        user = await db_user.get(user_id)
        
        # ✅ FIX: Check if user exists
        if user is None:
            await call.answer("❌ Ошибка: пользователь не найден", show_alert=True)
            return
        
        formatted_profile = _format_profile_compact(profile, user)
        
        try:
            await call.message.delete()
        except Exception:
            pass
        
        await _send_long_message(call.message, formatted_profile)
        
    except Exception as e:
        await call.answer(f"⚠️ Ошибка: {e}", show_alert=True)


@dp.callback_query(F.data == 'profile')
async def profile_callback(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    user = await db_user.get(user_id=user_id)
    
    # ✅ FIX: Check if user exists
    if user is None:
        await call.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return
    
    profile_data = await db_user_profile.get_or_create(user_id)

    sub_date = '❌' if user.sub_date < datetime.now() else f'{user.sub_date}'[:-10]
    gender_label = "Не указан"
    if user.gender is True:
        gender_label = "Мужской"
    elif user.gender is False:
        gender_label = "Женский"

    info_lines = [
        "👤 <b>Ваш профиль</b>",
        "",
        f"ID: <code>{user_id}</code>",
        f"Имя: <code>{user.real_name or '—'}</code>",
        f"Возраст: <code>{user.age or '—'}</code>",
        f"Пол: <code>{gender_label}</code>",
    ]

    if user.sub_date > datetime.now():
        info_lines.append(f"Подписка активна до: <code>{sub_date}</code>")
    else:
        info_lines.append("Подписка: <code>не активна</code>")

    tone_label = STYLE_TONE_LABELS.get(profile_data.tone_style, 'по умолчанию')
    personality_label = STYLE_PERSONALITY_LABELS.get(profile_data.personality, 'универсальный')
    length_label = STYLE_LENGTH_LABELS.get(profile_data.message_length, 'средние')

    style_lines = [
        "🎨 <b>Стиль бота</b>",
        f"• Тон: {tone_label}",
        f"• Роль: {personality_label}",
        f"• Длина ответов: {length_label}",
    ]

    usage_lines = []
    if user.sub_date <= datetime.now():
        usage_lines = [
            "📈 <b>Статистика использования</b>",
            f"• Помощник: {user.helper_requests}",
            f"• Сонник: {user.sleeper_requests}",
            f"• Анализ личности: {user.assistant_requests}",
        ]

    referral = (
        "🔗 <b>Пригласите друга и получите +3 дня подписки</b>\n"
        f"https://t.me/SoulnearBot?start={user_id}"
    )

    sections = ["\n".join(info_lines), "\n".join(style_lines)]
    if usage_lines:
        sections.append("\n".join(usage_lines))
    sections.append(referral)

    text = "\n\n".join(sections)
    try:
        await call.message.delete()
        await call.message.answer(text=text,
                                  reply_markup=profile_menu,
                                  parse_mode='HTML')

    except:
        await call.answer()


@dp.callback_query(F.data == 'update_user_info')
async def update_user_info_start(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        await call.answer()

    await state.set_state(Update_user_info.real_name)

    m = await call.message.answer(text='Введите ваше настоящее имя: ',
                                  reply_markup=back)

    await state.update_data(is_profile=True,
                            message_id=m.message_id)


@dp.message(Update_user_info.real_name)
async def update_user_real_name(message: Message, state: FSMContext):
    real_name = message.text

    await message.delete()

    if len(real_name) > 32:
        return

    data = await state.get_data()

    await bot.delete_message(chat_id=message.chat.id,
                             message_id=data['message_id'])

    m = await message.answer(text='Сколько тебе полных лет? ',
                             reply_markup=back)

    await state.update_data(real_name=real_name,
                            message_id=m.message_id)

    await state.set_state(Update_user_info.age)


@dp.message(Update_user_info.age)
async def update_user_age(message: Message, state: FSMContext):
    age = int(message.text)
    await message.delete()

    if age < 0 or age > 100:
        return

    data = await state.get_data()

    await bot.delete_message(chat_id=message.chat.id,
                             message_id=data['message_id'])

    await state.update_data(age=age)
    await message.answer(text='Твой пол?',
                         reply_markup=gender_menu)


@dp.callback_query(F.data.startswith('gender'))
async def update_user_gender(call: CallbackQuery, state: FSMContext):
    gender = bool(int(call.data.split()[1]))
    data = await state.get_data()

    await db_user.update_info(user_id=call.from_user.id,
                              real_name=data['real_name'],
                              age=data['age'],
                              gender=gender)
    
    # ⚠️ FIX: Очищаем state ПЕРЕД menu_callback, чтобы избежать race condition
    await state.clear()
    
    if data['is_profile']:
        await profile_callback(call, state)
    else:
        await menu_callback(call, state)


# ==========================================
# 🎨 НАСТРОЙКИ СТИЛЯ (Stage 2)
# ==========================================

@dp.callback_query(F.data == 'style_settings')
async def style_settings_callback(call: CallbackQuery, state: FSMContext):
    """Показать меню настроек стиля (UNIFIED V2)"""
    if not is_feature_enabled('ENABLE_STYLE_SETTINGS'):
        await call.answer("⚠️ Настройки стиля временно недоступны", show_alert=True)
        return
    
    user_id = call.from_user.id
    profile = await db_user_profile.get_or_create(user_id)
    
    # Используем новое unified меню (всё на одном экране)
    keyboard = build_style_settings_menu_v2(
        current_tone=profile.tone_style,
        current_personality=profile.personality,
        current_length=profile.message_length
    )
    
    text = (
        f'🎨 <b>Настройки стиля общения</b>\n\n'
        f'Выбери параметры ниже 👇\n'
        f'Текущие отмечены галочкой ✓\n\n'
        f'💡 <i>Изменения применяются моментально</i>'
    )
    
    try:
        await call.message.delete()
        await call.message.answer(text=text, reply_markup=keyboard)
    except:
        await call.answer()


@dp.callback_query(F.data == 'change_tone')
async def change_tone_callback(call: CallbackQuery):
    """Показать меню выбора тона"""
    text = (
        '🎭 <b>Выбери тон общения:</b>\n\n'
        '🎩 <b>Формальный</b> - профессиональный и деловой\n'
        '😊 <b>Дружелюбный</b> - тёплый и поддерживающий\n'
        '😏 <b>Ироничный</b> - с лёгким сарказмом\n'
        '🔥 <b>Мотивирующий</b> - вдохновляющий и энергичный'
    )
    
    try:
        await call.message.edit_text(text=text, reply_markup=tone_menu)
    except:
        await call.answer()


@dp.callback_query(F.data.startswith('tone_'))
async def set_tone_callback(call: CallbackQuery):
    """Установить выбранный тон"""
    tone = call.data.replace('tone_', '')
    user_id = call.from_user.id
    
    await db_user_profile.update_style(user_id, tone_style=tone)
    
    tone_names = {
        'formal': 'Формальный',
        'friendly': 'Дружелюбный',
        'sarcastic': 'Ироничный',
        'motivating': 'Мотивирующий'
    }
    
    await call.answer(f"✅ Тон изменён на {tone_names.get(tone, tone)}", show_alert=True)
    await style_settings_callback(call, None)


@dp.callback_query(F.data == 'change_personality')
async def change_personality_callback(call: CallbackQuery):
    """Показать меню выбора личности"""
    text = (
        '👤 <b>Выбери личность ассистента:</b>\n\n'
        '🧙‍♂️ <b>Мудрый наставник</b> - делится опытом и мудростью\n'
        '👥 <b>Поддерживающий друг</b> - всегда рядом и понимает\n'
        '💪 <b>Строгий коуч</b> - фокус на результатах и действиях'
    )
    
    try:
        await call.message.edit_text(text=text, reply_markup=personality_menu)
    except:
        await call.answer()


@dp.callback_query(F.data.startswith('personality_'))
async def set_personality_callback(call: CallbackQuery):
    """Установить выбранную личность"""
    personality = call.data.replace('personality_', '')
    user_id = call.from_user.id
    
    await db_user_profile.update_style(user_id, personality=personality)
    
    personality_names = {
        'mentor': 'Мудрый наставник',
        'friend': 'Поддерживающий друг',
        'coach': 'Строгий коуч',
        'therapist': 'Терапевт'
    }
    
    await call.answer(f"✅ Личность изменена на {personality_names.get(personality, personality)}", show_alert=True)
    await style_settings_callback(call, None)


@dp.callback_query(F.data == 'change_length')
async def change_length_callback(call: CallbackQuery):
    """Показать меню выбора длины ответов"""
    text = (
        '📏 <b>Выбери длину ответов:</b>\n\n'
        '⚡ <b>Кратко</b> - 1-2 коротких абзаца\n'
        '📝 <b>Средне</b> - 3-4 структурированных абзаца\n'
        '📚 <b>Подробно</b> - 5-7 абзацев с примерами'
    )
    
    try:
        await call.message.edit_text(text=text, reply_markup=length_menu)
    except:
        await call.answer()


@dp.callback_query(F.data.startswith('length_'))
async def set_length_callback(call: CallbackQuery):
    """Установить выбранную длину"""
    length = call.data.replace('length_', '')
    user_id = call.from_user.id
    
    await db_user_profile.update_style(user_id, message_length=length)
    
    length_names = {
        'ultra_brief': 'Очень коротко (2-3 предложения)',
        'brief': 'Кратко (1-2 абзаца)',
        'medium': 'Средне (3-4 абзаца)',
        'detailed': 'Подробно (5-7 абзацев)'
    }
    
    await call.answer(f"✅ Длина ответов изменена на: {length_names.get(length, length)}", show_alert=True)
    await style_settings_callback(call, None)


# ==========================================
# 🚀 UNIFIED STYLE HANDLER (V2)
# ==========================================

@dp.callback_query(F.data.startswith('style_'))
async def unified_style_handler(call: CallbackQuery):
    """
    Универсальный handler для нового формата style_*
    
    Формат callback_data: style_{category}_{value}
    Примеры: style_tone_friendly, style_personality_mentor, style_length_medium
    """
    parts = call.data.split('_', 2)  # style, category, value
    if len(parts) != 3:
        await call.answer("❌ Ошибка формата", show_alert=True)
        return
    
    _, category, value = parts
    user_id = call.from_user.id
    
    # Обновляем профиль в зависимости от категории
    if category == 'tone':
        await db_user_profile.update_style(user_id, tone_style=value)
        names = {
            'formal': 'Формальный 🎩',
            'friendly': 'Дружелюбный 😊',
            'sarcastic': 'Ироничный 😏',
            'motivating': 'Мотивирующий 🔥'
        }
        message = f"Тон: {names.get(value, value)}"
    
    elif category == 'personality':
        await db_user_profile.update_style(user_id, personality=value)
        names = {
            'mentor': 'Наставник 🧙',
            'friend': 'Друг 👥',
            'coach': 'Коуч 💪',
            'therapist': 'Терапевт 🧘'
        }
        message = f"Личность: {names.get(value, value)}"
    
    elif category == 'length':
        await db_user_profile.update_style(user_id, message_length=value)
        names = {
            'ultra_brief': '⚡⚡',
            'brief': '⚡',
            'medium': '📝',
            'detailed': '📚'
        }
        message = f"Длина: {names.get(value, value)}"
    
    else:
        await call.answer("❌ Неизвестная категория", show_alert=True)
        return
    
    # Обновляем меню (перерисовываем с новыми галочками)
    profile = await db_user_profile.get_or_create(user_id)
    keyboard = build_style_settings_menu_v2(
        current_tone=profile.tone_style,
        current_personality=profile.personality,
        current_length=profile.message_length
    )
    
    try:
        await call.message.edit_reply_markup(reply_markup=keyboard)
        await call.answer(f"✅ {message}", show_alert=False)
    except:
        await call.answer(f"✅ {message}", show_alert=True)


@dp.callback_query(F.data == 'noop')
async def noop_handler(call: CallbackQuery):
    """Handler для кнопок-разделителей (noop = no operation)"""
    await call.answer()


# ==========================================
# ⚡ QUICK SWITCH PRESETS
# ==========================================

@dp.callback_query(F.data == 'style_presets')
async def style_presets_callback(call: CallbackQuery):
    """Показать меню быстрых пресетов"""
    if not is_feature_enabled('ENABLE_STYLE_SETTINGS'):
        await call.answer("⚠️ Настройки стиля временно недоступны", show_alert=True)
        return
    
    from bot.keyboards.profile import build_style_presets_menu
    
    keyboard = build_style_presets_menu()
    
    text = (
        f'⚡ <b>Быстрые пресеты стиля</b>\n\n'
        f'Выбери готовую комбинацию настроек для быстрого старта!\n\n'
        f'Каждый пресет это комбинация:\n'
        f'• Тон (формальный/дружелюбный/мотивирующий)\n'
        f'• Личность (коуч/друг/терапевт/наставник)\n'
        f'• Длина ответов (кратко/средне/подробно)\n\n'
        f'💡 <i>Изменения применяются моментально</i>'
    )
    
    try:
        await call.message.delete()
        await call.message.answer(text=text, reply_markup=keyboard)
    except:
        await call.answer()


@dp.callback_query(F.data.startswith('preset_'))
async def apply_preset_callback(call: CallbackQuery):
    """Применить пресет стиля"""
    if not is_feature_enabled('ENABLE_STYLE_SETTINGS'):
        await call.answer("⚠️ Настройки стиля временно недоступны", show_alert=True)
        return
    
    from bot.keyboards.profile import STYLE_PRESETS
    
    preset_id = call.data.replace('preset_', '')
    preset = STYLE_PRESETS.get(preset_id)
    
    if not preset:
        await call.answer("❌ Пресет не найден", show_alert=True)
        return
    
    user_id = call.from_user.id
    
    # Применяем все настройки сразу
    await db_user_profile.update_style(
        user_id,
        tone_style=preset['tone'],
        personality=preset['personality'],
        message_length=preset['length']
    )
    
    await call.answer(f"✅ Применён: {preset['name']}", show_alert=False)
    
    # Показываем обновлённое меню с галочкой
    from bot.keyboards.profile import build_style_presets_menu
    keyboard = build_style_presets_menu(current_preset_id=preset_id)
    
    text = (
        f'⚡ <b>Быстрые пресеты стиля</b>\n\n'
        f'✅ <b>Применён:</b> {preset["name"]}\n'
        f'<i>{preset["description"]}</i>\n\n'
        f'Настройки:\n'
        f'• Тон: <code>{preset["tone"]}</code>\n'
        f'• Личность: <code>{preset["personality"]}</code>\n'
        f'• Длина: <code>{preset["length"]}</code>\n\n'
        f'💡 <i>Можешь выбрать другой пресет или перейти к детальным настройкам</i>'
    )
    
    try:
        await call.message.edit_text(text=text, reply_markup=keyboard)
    except:
        await call.answer()
