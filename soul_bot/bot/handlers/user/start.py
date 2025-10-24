import asyncio
from datetime import datetime, timedelta
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    FSInputFile,
    CallbackQuery
)

import bot.functions.Pictures as Pictures
import bot.text as texts
from bot.functions.ChatGPT import new_context
from bot.functions.other import check_user_info
from bot.keyboards.premium import sub_menu
from bot.loader import dp, bot
from bot.states.states import get_prompt, Update_user_info
from bot.keyboards.start import menu as menu_keyboard, start
import database.repository.user as db_user
import database.repository.ads as db_ads
from config import TEST

# MENU_VIDEO - file_id для видео меню (если доступен)
# Если видео недоступно, бот отправит текст вместо видео
MENU_VIDEO = 'BAACAgIAAxkBAAI6cGg4w8Vk5fnwf7A-9jUr3Q6WmfGOAAJ6dAACEmXISc7N8yQYdufxNgQ'


@dp.message(CommandStart())
async def start_message(message: Message):
    user_id = message.from_user.id

    link = None if message.text == '/start' else message.text.split()[1]

    if link:
        if not link.isdigit():
            ref = await db_ads.get_by_link(link=link)
            if ref:
                await db_ads.increment_views(ad_id=ref.id)

    if not await db_user.is_exist(user_id=user_id):

        await db_user.new(user_id=message.from_user.id,
                          name=message.from_user.first_name,
                          username=message.from_user.username,
                          ref=link,
                          sub_date=datetime.now())

        if link:
            if not link.isdigit():
                ref = await db_ads.get_by_link(link=link)
                if ref:
                    await db_ads.increment_users(ad_id=ref.id)
            else:
                await db_user.update_sub_date(user_id=int(link),
                                              days=3)
                await bot.send_message(chat_id=int(link),
                                       text='🎉 +3 дня к подписки за приведенного друга!')

    await message.answer(text=texts.greet,
                         reply_markup=start,
                         disable_web_page_preview=True)


@dp.message(Command('menu'))
async def menu_message(message: Message, state: FSMContext):
    try:
        if TEST:
            await message.answer(text=texts.menu,
                                 reply_markup=menu_keyboard)
        else:
            await message.answer_video(video=MENU_VIDEO,
                                       caption=texts.menu,
                                       reply_markup=menu_keyboard)
    except Exception as e:
        # Если видео недоступно, отправляем просто текст
        await message.answer(text=texts.menu,
                             reply_markup=menu_keyboard)
    
    try:
        await message.delete()
    except:
        pass


@dp.message(Command('deletecontext'))
async def delete_context_message(message: Message, state: FSMContext):
    user_id = message.from_user.id

    await state.set_state(get_prompt.helper_prompt)

    msg = await message.answer("Очищаю контекст...")
    try:
        await new_context(user_id, 'helper')
        await msg.edit_text(
            "Контекст удален. Теперь вы с SOUL.near можете сосредоточиться на текущей теме, не отвлекаясь на предыдущие обсуждения."
        )
    except Exception as e:
        await message.answer("Контекст не очищен.")
        print(f"Ошибка в deletecontext: {e}")


@dp.message(Command('settings'))
async def settings_message(message: Message):
    """Команда /settings - быстрый доступ к настройкам стиля"""
    from bot.handlers.user.profile import style_settings_callback
    from bot.keyboards.profile import style_settings_menu
    from config import is_feature_enabled
    import database.repository.user_profile as db_user_profile
    
    if not is_feature_enabled('ENABLE_STYLE_SETTINGS'):
        await message.answer("⚠️ Настройки стиля временно недоступны")
        return
    
    user_id = message.from_user.id
    profile = await db_user_profile.get_or_create(user_id)
    
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
    
    await message.answer(text=text, reply_markup=style_settings_menu)


@dp.callback_query(F.data == 'menu')
async def menu_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Произошла ошибка при попытке удаления сообщения: {e}")
        await callback.answer()

    if not await check_user_info(message=callback.message, state=state):
        return

    try:
        if TEST:
            await callback.message.answer(text=texts.menu,
                                          reply_markup=menu_keyboard)
        else:
            await callback.message.answer_video(video=MENU_VIDEO,
                                                caption=texts.menu,
                                                reply_markup=menu_keyboard)
    except Exception as e:
        # Если видео недоступно (wrong file identifier), отправляем просто текст
        print(f"Ошибка при отправке видео: {e}")
        await callback.message.answer(text=texts.menu,
                                      reply_markup=menu_keyboard)


async def menu_message_not_delete(message: Message):
    try:
        if TEST:
            await message.answer(text=texts.menu,
                                 reply_markup=menu_keyboard)
        else:
            await message.answer_video(video=MENU_VIDEO,
                                       caption=texts.menu,
                                       reply_markup=menu_keyboard)
    except Exception as e:
        # Если видео недоступно, отправляем просто текст
        print(f"Ошибка при отправке видео: {e}")
        await message.answer(text=texts.menu,
                             reply_markup=menu_keyboard)
