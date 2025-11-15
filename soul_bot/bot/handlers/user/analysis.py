import logging
from aiogram import F
from aiogram.types import CallbackQuery
import bot.text as texts
import bot.keyboards.analysis as analysis_kb
from bot.loader import dp

logger = logging.getLogger(__name__)


# Чат с ChatGPT
@dp.callback_query(F.data == 'analysis')
async def analysis(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning("Failed to delete analysis message: %s", e)

    await callback.message.answer(
        text=texts.analysis,
        reply_markup=analysis_kb.analysis_menu,
        parse_mode='html')
