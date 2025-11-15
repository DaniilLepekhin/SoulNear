import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import bot.text as texts
from bot.functions.other import check_sub_assistant, voice_answer, text_answer, photo_answer, check_user_info
from bot.loader import dp
from bot.states.states import get_prompt, Update_user_info
from database.repository import conversation_history
import bot.keyboards.practice as keyboards
from bot.services.error_notifier import report_exception

logger = logging.getLogger(__name__)


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

    await photo_answer(message)


# Прием промпта (гс)
@dp.message(F.voice, get_prompt.helper_prompt)
async def handle_voice(message: Message, state: FSMContext):
    if not await check_user_info(message=message, state=state):
        return
    await voice_answer(message=message, assistant='helper')


# Приём промпта (текст)
@dp.message(get_prompt.helper_prompt)
async def handle_text(message: Message, state: FSMContext):
    if not await check_user_info(message=message, state=state):
        return
    await text_answer(message=message, assistant='helper')


