from datetime import datetime
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.user.start import menu_callback
from bot.keyboards.profile import (
    profile_menu, gender_menu, style_settings_menu,
    tone_menu, personality_menu, length_menu
)
from bot.keyboards.start import back, menu
from bot.loader import dp, bot
import database.repository.user as db_user
import database.repository.user_profile as db_user_profile
from bot.states.states import Update_user_info
from config import is_feature_enabled


@dp.callback_query(F.data == 'profile')
async def profile_callback(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    user = await db_user.get(user_id=user_id)

    sub_date = '❌' if user.sub_date < datetime.now() else f'{user.sub_date}'[:-10]

    text = f'👤 Ваш профиль, <code>{call.from_user.first_name}</code>\n' \
           f'├ Ваш ID: <code>{user_id}</code>\n' \
           f'├ Имя: <code>{user.real_name}</code>\n' \
           f'├ Возраст: <code>{user.age}</code>\n' \
           f'├ Пол: <code>{"Мужской" if user.gender else "Женский"}</code>\n'

    if user.sub_date > datetime.now():
        text += f'└ Подписка до: <code>{sub_date}</code>\n\n'
    else:
        text += (f'├ Ассистент: <code>{user.helper_requests}</code>\n'
                 f'├ Сонник: <code>{user.sleeper_requests}</code>\n'
                 f'├ Анализ личности: <code>{user.assistant_requests}</code>\n'
                 f'└ Подписка до: <code>{sub_date}</code>\n\n')

    text += f'+3 дня подписки за приведенного друга: <code>https://t.me/SoulnearBot?start={user_id}</code>'
    try:
        await call.message.delete()
        await call.message.answer(text=text,
                                  reply_markup=profile_menu)

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
    if data['is_profile']:
        await profile_callback(call, state)
    else:
        await menu_callback(call, state)

    await state.clear()


# ==========================================
# 🎨 НАСТРОЙКИ СТИЛЯ (Stage 2)
# ==========================================

@dp.callback_query(F.data == 'style_settings')
async def style_settings_callback(call: CallbackQuery, state: FSMContext):
    """Показать меню настроек стиля"""
    if not is_feature_enabled('ENABLE_STYLE_SETTINGS'):
        await call.answer("⚠️ Настройки стиля временно недоступны", show_alert=True)
        return
    
    user_id = call.from_user.id
    profile = await db_user_profile.get_or_create(user_id)
    
    # Маппинг для красивого отображения
    tone_map = {
        'formal': '🎩 Формальный',
        'friendly': '😊 Дружелюбный',
        'sarcastic': '😏 Ироничный',
        'motivating': '🔥 Мотивирующий'
    }
    
    personality_map = {
        'mentor': '🧙‍♂️ Мудрый наставник',
        'friend': '👥 Поддерживающий друг',
        'coach': '💪 Строгий коуч'
    }
    
    length_map = {
        'brief': '⚡ Кратко',
        'medium': '📝 Средне',
        'detailed': '📚 Подробно'
    }
    
    text = (
        f'🎨 <b>Настройки стиля общения</b>\n\n'
        f'Текущие настройки:\n'
        f'├ Тон: <code>{tone_map.get(profile.tone_style, profile.tone_style)}</code>\n'
        f'├ Личность: <code>{personality_map.get(profile.personality, profile.personality)}</code>\n'
        f'└ Длина ответов: <code>{length_map.get(profile.message_length, profile.message_length)}</code>\n\n'
        f'💡 <i>Изменения применяются сразу ко всем ассистентам</i>'
    )
    
    try:
        await call.message.delete()
        await call.message.answer(text=text, reply_markup=style_settings_menu)
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
        'coach': 'Строгий коуч'
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
        'brief': 'Кратко',
        'medium': 'Средне',
        'detailed': 'Подробно'
    }
    
    await call.answer(f"✅ Длина ответов изменена на {length_names.get(length, length)}", show_alert=True)
    await style_settings_callback(call, None)
