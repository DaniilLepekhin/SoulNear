import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import bot.text as texts
from bot.functions.other import check_sub_assistant, voice_answer, text_answer
from bot.loader import dp
from bot.states.states import get_prompt
import bot.keyboards.practice as keyboards

logger = logging.getLogger(__name__)


@dp.callback_query(F.data == 'soulsleep')
async def soulsleep(callback: CallbackQuery, state: FSMContext):

    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning("Failed to delete sleeper menu message: %s", e)
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
    await voice_answer(message=message, assistant='sleeper')


# Приём промпта (текст)
@dp.message(get_prompt.soulsleep_prompt)
async def soulsleep_text(message: Message, state: FSMContext):
    await text_answer(message=message, assistant='sleeper')
