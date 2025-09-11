from aiogram import F
from aiogram.types import CallbackQuery
import bot.text as texts
import bot.keyboards.analysis as analysis_kb
from bot.loader import dp


# Чат с ChatGPT
@dp.callback_query(F.data == 'analysis')
async def analysis(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    await callback.message.answer(
        text=texts.analysis,
        reply_markup=analysis_kb.analysis_menu,
        parse_mode='html')
