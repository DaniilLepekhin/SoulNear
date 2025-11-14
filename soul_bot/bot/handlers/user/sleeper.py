from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import bot.text as texts
from bot.functions.other import check_sub_assistant, voice_answer, text_answer
from bot.loader import dp
from bot.states.states import get_prompt
import bot.keyboards.practice as keyboards
from bot.handlers.user.helper import _check_and_decrease_free_messages


@dp.callback_query(F.data == 'soulsleep')
async def soulsleep(callback: CallbackQuery, state: FSMContext):

    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        await callback.answer()

    user_id = callback.from_user.id

    if await check_sub_assistant(user_id=user_id, assistant='sleeper'):
        await state.set_state(get_prompt.soulsleep_prompt)
        await callback.message.answer(
            texts.soulsleep,
            reply_markup=keyboards.to_menu,
            parse_mode='html',
            protect_content=True)


# Прием промпта (гс)
@dp.message(F.voice, get_prompt.soulsleep_prompt)
async def soulsleep_voice(message: Message, state: FSMContext):
    # Проверить и уменьшить счётчик бесплатных сообщений
    if not await _check_and_decrease_free_messages(message):
        return

    await voice_answer(message=message, assistant='sleeper')


# Приём промпта (текст)
@dp.message(get_prompt.soulsleep_prompt)
async def soulsleep_text(message: Message, state: FSMContext):
    # Проверить и уменьшить счётчик бесплатных сообщений
    if not await _check_and_decrease_free_messages(message):
        return

    await text_answer(message=message, assistant='sleeper')
