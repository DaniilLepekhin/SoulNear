from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import bot.text as texts
from bot.functions.other import check_sub_assistant, voice_answer, text_answer
from bot.handlers.user.start import menu_message_not_delete
from bot.loader import dp
from bot.states.states import get_prompt
import bot.keyboards.practice as keyboards
from database.repository import conversation_history


# Чат ассистентом по отношениям
@dp.callback_query(F.data == 'relationships')
async def relationships(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        await callback.answer()

    user_id = callback.from_user.id

    if await check_sub_assistant(user_id=user_id, assistant='relationships'):
        await state.clear()
        await state.set_state(get_prompt.relationships_prompt)

        # Очищаем контекст для relationships ассистента
        await conversation_history.clear(user_id=user_id, assistant_type='relationships')

        await callback.message.answer(
            texts.relationships,
            reply_markup=keyboards.to_menu,
            parse_mode='html',
            protect_content=True
        )


# Прием промпта (гс)
@dp.message(F.voice, get_prompt.relationships_prompt)
async def relationships_voice(message: Message, state: FSMContext):
    await voice_answer(message, assistant='relationships')

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
@dp.message(get_prompt.relationships_prompt)
async def relationships_text(message: Message, state: FSMContext):
    await text_answer(message, assistant='relationships')

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
