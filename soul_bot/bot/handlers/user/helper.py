import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import bot.text as texts
from bot.functions.other import check_sub_assistant, voice_answer, text_answer, photo_answer, check_user_info
from bot.loader import dp
from bot.states.states import get_prompt, Update_user_info
from database.repository import conversation_history
import bot.keyboards.practice as keyboards
import database.repository.user as db_user
from datetime import datetime
from bot.services.error_notifier import report_exception

logger = logging.getLogger(__name__)


async def _check_and_decrease_free_messages(message: Message) -> bool:
    """
    Проверить и уменьшить счётчик бесплатных сообщений.
    Возвращает True если можно продолжить, False если лимит исчерпан.
    """
    user_id = message.from_user.id
    user = await db_user.get(user_id)

    # Если нет бесплатных сообщений или есть подписка - пропускаем
    if user.free_messages_count <= 0 or user.sub_date >= datetime.now():
        return True

    # Уменьшить счетчик
    new_count = user.free_messages_count - 1
    await db_user.update(user_id=user_id, free_messages_count=new_count)

    # Предупреждение на последнем сообщении
    if new_count == 1:
        await message.answer(
            "⚠️ <b>У тебя осталось одно сообщение.</b>\n\n"
            "<i>Если хочешь продолжить без лимитов — можно открыть полную версию.</i>",
            parse_mode='HTML'
        )

    # Оффер после окончания
    elif new_count == 0:
        await _offer_subscription(message)
        return False  # НЕ обрабатывать сообщение

    return True


async def _offer_subscription(message: Message):
    """Предложить подписку после окончания бесплатных сообщений"""
    from bot.keyboards.premium import sub_menu

    await message.answer(
        "<b>Твои 5 бесплатных сообщений закончились</b> 💫\n\n"
        "<i>Если хочется глубже или просто иметь место, где тебя слышат — полная версия открыта.</i>\n\n"
        "Там безлимитные диалоги, разборы и практики.",
        reply_markup=sub_menu,
        parse_mode='HTML'
    )

    # Запустить retention
    await _schedule_retention_start(message.from_user.id)


async def _schedule_retention_start(user_id: int):
    """Запланировать начало retention цепочки"""
    # Устанавливаем начальное состояние для retention
    # Устанавливаем last_retention_sent=now() чтобы первое сообщение пришло через 2 дня
    await db_user.update(
        user_id=user_id,
        last_retention_message=0,
        last_retention_sent=datetime.now(),
        retention_paused=False
    )


# Чат с ChatGPT
# При нажатии кнопки проверка статуса подписки пользователя
@dp.callback_query(F.data == 'support')
async def support(callback: CallbackQuery, state: FSMContext):

    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning("Failed to delete helper menu message for user %s: %s", callback.from_user.id, e)
        await callback.answer()

    user_id = callback.from_user.id

    if await check_sub_assistant(user_id=user_id, assistant='helper'):
        await state.set_state(get_prompt.helper_prompt)
        await callback.message.answer(
            texts.support,
            reply_markup=keyboards.to_menu,
            parse_mode='html',
            protect_content=True)


@dp.callback_query(F.data == 'clear_context')
async def clear_context(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    await state.set_state(get_prompt.helper_prompt)

    try:
        await conversation_history.clear_history(user_id, 'helper')
    except Exception as exc:  # pragma: no cover - defensive
        await callback.answer("Не удалось очистить контекст 😔", show_alert=True)
        logger.exception("Failed to clear helper context for user %s via button", user_id)
        await report_exception(
            "helper.clear_context",
            exc,
            event=callback,
            extras={"user_id": user_id},
        )
        return

    await callback.answer("Контекст очищен ✨", show_alert=False)
    await callback.message.answer(
        "🧹 Контекст очищен. Расскажи, что сейчас важно.",
        protect_content=True
    )


@dp.message(F.photo, get_prompt.helper_prompt)
async def handle_photo(message: Message, state: FSMContext):
    if not await check_user_info(message=message, state=state):
        return

    # Проверить и уменьшить счётчик бесплатных сообщений
    if not await _check_and_decrease_free_messages(message):
        return

    await photo_answer(message)


# Прием промпта (гс)
@dp.message(F.voice, get_prompt.helper_prompt)
async def handle_voice(message: Message, state: FSMContext):
    if not await check_user_info(message=message, state=state):
        return

    # Проверить и уменьшить счётчик бесплатных сообщений
    if not await _check_and_decrease_free_messages(message):
        return

    await voice_answer(message=message, assistant='helper')


# Приём промпта (текст)
@dp.message(get_prompt.helper_prompt)
async def handle_text(message: Message, state: FSMContext):
    if not await check_user_info(message=message, state=state):
        return

    # Проверить и уменьшить счётчик бесплатных сообщений
    if not await _check_and_decrease_free_messages(message):
        return

    await text_answer(message=message, assistant='helper')


