import asyncio
import logging
from datetime import datetime
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import bot.text as texts
from bot.functions.other import check_user_info
from database.repository import conversation_history
from bot.keyboards.premium import sub_menu
from bot.loader import dp, bot
from bot.states.states import get_prompt, Update_user_info
from bot.keyboards.start import menu as menu_keyboard, start
from bot.services.quiz_ui import get_quiz_intro_text
from bot.handlers.user.quiz import launch_quiz_for_category_from_message
import database.repository.user as db_user
import database.repository.ads as db_ads
import database.repository.deeplink_event as db_deeplink_event
from config import ADMINS
from bot.services.error_notifier import report_exception

logger = logging.getLogger(__name__)

LEGACY_QUIZ_DEEPLINK_PREFIX = 'quiz_'
QUIZ_DEEPLINK_ALIASES = {
    'analysis_relationships_ads': 'relationships',
    'analysis_money_ads': 'money',
    'analysis_purpose_ads': 'purpose',
}


async def send_menu_with_video(message: Message):
    """Send main menu with video from public channel"""
    video_file_id = "BAACAgIAAxkBAAJfJWkWtqGD6TzSH15gz5k25qNfe9MpAAJ4igACpV-wSJePx5AcgfxyNgQ"

    try:
        await message.answer_video(
            video=video_file_id,
            caption=texts.menu,
            reply_markup=menu_keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error sending menu with video: {e}")
        # Fallback to text-only menu
        await message.answer(
            text=texts.menu,
            reply_markup=menu_keyboard,
            disable_web_page_preview=True,
            parse_mode='HTML'
        )


def _resolve_quiz_deeplink(raw_link: str | None) -> str | None:
    if not raw_link:
        return None

    normalized = raw_link.strip()
    category = QUIZ_DEEPLINK_ALIASES.get(normalized)
    if category:
        return category

    if normalized.startswith(LEGACY_QUIZ_DEEPLINK_PREFIX):
        candidate = normalized[len(LEGACY_QUIZ_DEEPLINK_PREFIX):]
        if get_quiz_intro_text(candidate):
            return candidate

    return None


async def finalize_deeplink_event(state: FSMContext, quiz_session_id: int | None) -> None:
    if not quiz_session_id:
        return

    data = await state.get_data()
    event_id = data.get('deeplink_event_id')
    if not event_id:
        return

    await db_deeplink_event.attach_quiz(event_id, quiz_session_id)
    await state.update_data(deeplink_event_id=None, pending_quiz_category=None)


async def launch_deeplink_quiz(message: Message, state: FSMContext, category: str) -> int | None:
    intro_text = get_quiz_intro_text(category)
    if intro_text:
        display_text = (
            f"{intro_text}\n\n"
            "<b>Нажми «Начать», чтобы перейти к вопросам.</b>"
        )
    else:
        display_text = (
            "<b>🧠 Квиз готов</b>\n"
            "<i>Нажми «Начать», чтобы перейти к вопросам.</i>"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='▶️ Начать',
                    callback_data=f'deeplink_quiz_start:{category}',
                ),
                InlineKeyboardButton(
                    text='🏠 Меню',
                    callback_data='quiz_go_menu',
                ),
            ]
        ]
    )

    sent = await message.answer(
        display_text,
        reply_markup=keyboard,
        disable_web_page_preview=True,
        parse_mode='HTML',
    )

    await state.update_data(
        pending_quiz_category=category,
    )

    return sent.message_id


@dp.callback_query(F.data.startswith('deeplink_quiz_start:'))
async def deeplink_quiz_start_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    parts = callback.data.split(':', 1)
    if len(parts) != 2 or not parts[1]:
        await callback.message.answer("⚠️ Не удалось определить квиз.")
        return

    category = parts[1]

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    quiz_session_id = await launch_quiz_for_category_from_message(callback.message, state, category)
    await finalize_deeplink_event(state, quiz_session_id)

@dp.callback_query(F.data == 'start_accept')
async def start_accept_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    try:
        await callback.message.delete()
    except Exception:
        pass

    data = await state.get_data()
    pending_category = data.get('pending_quiz_category')

    user = await db_user.get(user_id=callback.from_user.id)
    if user and user.real_name:
        if pending_category:
            await launch_deeplink_quiz(callback.message, state, pending_category)
        else:
            await send_menu_with_video(callback.message)
        return

    prompt = await callback.message.answer(
        "Перед тем как мы начнём, расскажи немного о себе.\n\n"
        "📍 <b>Шаг 1 из 3 — Имя</b>\n\n"
        "<i>Напиши, как мне к тебе обращаться.</i>",
        parse_mode='HTML',
    )

    await state.set_state(Update_user_info.real_name)
    await state.update_data(is_profile=False,
                            message_id=prompt.message_id)


@dp.message(CommandStart())
async def start_message(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id

    parts = (message.text or '').split(maxsplit=1)
    link = parts[1].strip() if len(parts) > 1 else None

    pending_category = _resolve_quiz_deeplink(link)
    if pending_category:
        await state.update_data(pending_quiz_category=pending_category)
    if link and not link.isdigit():
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

    if pending_category:
        raw_link = link or pending_category
        event_id = await db_deeplink_event.create(
            user_id=user_id,
            raw_link=raw_link,
            resolved_category=pending_category,
        )
        await state.update_data(deeplink_event_id=event_id)

    await message.answer(text=texts.greet,
                         reply_markup=start,
                         disable_web_page_preview=True,
                         parse_mode='HTML')


@dp.message(Command('menu'))
async def menu_message(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text.startswith('/'):
        data = await state.get_data()
        if data.get('pending_quiz_category'):
            await state.update_data(pending_quiz_category=None)
    else:
        if await _maybe_send_pending_quiz(message, state):
            try:
                await message.delete()
            except:
                pass
            return

    if not await check_user_info(message=message, state=state):
        return

    await send_menu_with_video(message)

    try:
        await message.delete()
    except:
        pass


async def _maybe_send_pending_quiz(message: Message, state: FSMContext) -> bool:
    data = await state.get_data()
    pending_category = data.get('pending_quiz_category')

    if not pending_category:
        return False

    await launch_deeplink_quiz(message, state, pending_category)
    return True


@dp.message(Command('deletecontext'))
async def delete_context_message(message: Message, state: FSMContext):
    user_id = message.from_user.id

    await state.set_state(get_prompt.helper_prompt)

    msg = await message.answer("Очищаю контекст...")
    try:
        # Очищаем историю через новый API (ChatCompletion)
        await conversation_history.clear_history(user_id, 'helper')
        await msg.edit_text(
            "✅ Контекст удален. Теперь вы с SOUL.near можете сосредоточиться на текущей теме, не отвлекаясь на предыдущие обсуждения."
        )
    except Exception as e:
        await msg.edit_text("❌ Ошибка при очистке контекста.")
        logger.exception("Failed to clear helper context for user %s", user_id)
        await report_exception(
            "start.delete_context",
            e,
            event=message,
            extras={"user_id": user_id},
        )


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
        logger.warning("Failed to delete menu message for user %s: %s", callback.from_user.id, e)
        await callback.answer()

    if not await check_user_info(message=callback.message, state=state):
        await callback.answer()
        return

    if await _maybe_send_pending_quiz(callback.message, state):
        await callback.answer()
        return

    await send_menu_with_video(callback.message)


async def menu_message_not_delete(message: Message):
    await send_menu_with_video(message)


# Тестовая команда для быстрого тестирования цепочки (только для админов)
@dp.message(Command('test_gift'))
async def test_gift_command(message: Message):
    """Тестирование предложения подарка"""
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return

    # Сброс флагов для теста
    await db_user.update(
        user_id=user_id,
        free_messages_offered=False,
        free_messages_activated=False,
        free_messages_count=0
    )

    # Импортируем функцию
    from bot.handlers.user.quiz import _offer_free_messages_or_menu

    await _offer_free_messages_or_menu(message, user_id)


@dp.message(Command('test_subscription'))
async def test_subscription_command(message: Message):
    """Тестирование оффера подписки"""
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return

    # Установить флаг активации для теста
    await db_user.update(
        user_id=user_id,
        free_messages_activated=True
    )

    # Импортируем функцию
    from bot.handlers.user.quiz import _offer_free_messages_or_menu

    await _offer_free_messages_or_menu(message, user_id)
