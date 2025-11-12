from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import bot.text as texts
from bot.functions.other import check_sub_assistant, voice_answer, text_answer
from bot.handlers.user.start import menu_message_not_delete
from bot.loader import dp
from bot.states.states import get_prompt
from database.repository import conversation_history
from bot.keyboards.analysis import build_quiz_ready_keyboard


# Чат ассистентом по деньгам
@dp.callback_query(F.data == 'money')
async def money(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        await callback.answer()

    user_id = callback.from_user.id

    if await check_sub_assistant(user_id=user_id, assistant='money'):
        await state.clear()
        await state.set_state(get_prompt.money_prompt)

        # Очищаем контекст для money ассистента
        await conversation_history.clear_history(user_id=user_id, assistant_type='money')

        await callback.message.answer(
            texts.money,
            reply_markup=build_quiz_ready_keyboard('money'),
            parse_mode='html',
            protect_content=True
        )


# Прием промпта (гс)
@dp.message(F.voice, get_prompt.money_prompt)
async def money_voice(message: Message, state: FSMContext):
    await voice_answer(message, assistant='money')

    try:
        data = await state.get_data()
        question_count = data['question_count']

    except:
        question_count = 1

    if question_count < 12:
        await state.update_data(question_count=question_count + 1)
    else:
        await menu_message_not_delete(message)
        await state.clear()


# Приём сигнала "Готово" и обработка 10 вопросов-ответов*
@dp.message(get_prompt.money_prompt)
async def money_text(message: Message, state: FSMContext):
    await text_answer(message, assistant='money')

    try:
        data = await state.get_data()
        question_count = data['question_count']

    except:
        question_count = 1

    if question_count < 12:
        await state.update_data(question_count=question_count + 1)
    else:
        await menu_message_not_delete(message)
        await state.clear()
