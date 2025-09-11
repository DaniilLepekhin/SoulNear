import datetime
import time

from aiogram import F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import bot.keyboards.admin as kba
from bot.functions.other import percent
from bot.loader import dp
from config import ADMINS
import database.repository.user as db_user
import database.repository.statistic_day as db_statistic_day
from bot.states.states import Media


async def text_panel() -> str:
    start = time.time()
    users, block_users, active_users = await db_user.panel()

    today = await db_statistic_day.get_today()
    yesterday = await db_statistic_day.get_yesterday()

    alive_users = users - block_users

    (alive_percent,
     block_percent) = percent(alive_users,
                              block_users)
    (today_new_percent,
     today_block_percent) = percent(today.new_users,
                                    today.block_users)
    (today_new_sarafan_percent,
     today_new_refs_percent,
     today_new_ads_percent) = percent(today.sarafan,
                                      today.refs,
                                      today.ads)
    (today_good_percent,
     today_bad_percent) = percent(today.good_requests,
                                  today.bad_requests)
    (today_assistant_percent,
     today_helper_percent,
     today_sleeper_percent) = percent(today.assistant,
                                      today.helper,
                                      today.sleeper)
    (yesterday_new_percent,
     yesterday_block_percent) = percent(yesterday.new_users,
                                        yesterday.block_users)
    (yesterday_good_percent,
     yesterday_bad_percent) = percent(yesterday.good_requests,
                                      yesterday.bad_requests)
    (yesterday_assistant_percent,
     yesterday_helper_percent,
     yesterday_sleeper_percent) = percent(yesterday.assistant,
                                          yesterday.helper,
                                          yesterday.sleeper)
    (yesterday_new_sarafan_percent,
     yesterday_new_refs_percent,
     yesterday_new_ads_percent) = percent(yesterday.sarafan,
                                          yesterday.refs,
                                          yesterday.ads)

    return (f'📊 Юзеров: <code>{users}</code>\n'
            f'📍 Актив: <code>{active_users}</code>\n\n'
            f'🟢 Живых: <code>{alive_users} ({alive_percent}%)</code>\n'
            f'🔴 Остановок: <code>{block_users} ({block_percent}%)</code>\n\n'
            f'Сегодня:\n'
            f'📈 Регистраций: <code>{today.new_users} ({today_new_percent}%)</code>\n'
            f' └ 📻 Сарафан: <code>{today.sarafan} ({today_new_sarafan_percent}%)</code>\n'
            f' └ 🔗 Рефки: <code>{today.refs} ({today_new_refs_percent}%)</code>\n'
            f' └ 🤝 Реклама: <code>{today.ads} ({today_new_ads_percent}%)</code>\n'
            f'🩸 Остановки: <code>{today.block_users} ({today_block_percent}%)</code>\n'
            f'🔙 Вернулись: <code>{today.return_users}</code>\n'
            f'💰 Деньги: <code>{today.earn}</code>\n'
            f'🔹 Успешно: <code>{today.good_requests} ({today_good_percent}%)</code>\n'
            f'🔻 Ошибка: <code>{today.bad_requests} ({today_bad_percent}%)</code>\n'
            f'🆘 Помощник:<code> {today.helper} ({today_helper_percent}%)</code>\n'
            f'🤔 Ассистент: <code>{today.assistant} ({today_assistant_percent}%)</code>\n'
            f'💤 Соник: <code>{today.sleeper} ({today_sleeper_percent}%)</code>\n'
            f'🦞 Клац-клац: <code>{today.events}</code>\n\n'
            f'Вчера:\n'
            f'📈 Регистраций: <code>{yesterday.new_users} ({yesterday_new_percent}%)</code>\n'
            f' └ 📻 Сарафан: <code>{yesterday.sarafan} ({yesterday_new_sarafan_percent}%)</code>\n'
            f' └ 🔗 Рефки: <code>{yesterday.refs} ({yesterday_new_refs_percent}%)</code>\n'
            f' └ 🤝 Реклама: <code>{yesterday.ads} ({yesterday_new_ads_percent}%)</code>\n'
            f'🩸 Остановки: <code>{yesterday.block_users} ({yesterday_block_percent}%)</code>\n'
            f'🔙 Вернулись: <code>{yesterday.return_users}</code>\n'
            f'💰 Деньги: <code>{yesterday.earn}</code>\n'
            f'🔹 Успешно: <code>{yesterday.good_requests} ({yesterday_good_percent}%)</code>\n'
            f'🔻 Ошибка: <code>{yesterday.bad_requests} ({yesterday_bad_percent}%)</code>\n'
            f'🆘 Помощник: <code>{yesterday.helper} ({yesterday_helper_percent}%)</code>\n'
            f'🤔 Ассистент: <code>{yesterday.assistant} ({yesterday_assistant_percent}%)</code>\n'
            f'💤 Соник: <code>{yesterday.sleeper} ({yesterday_sleeper_percent}%)</code>\n'
            f'🦞 Клац-клац: <code>{yesterday.events}</code>\n\n'
            f'⌛️ <code>{round(time.time() - start, 3)}</code> сек.')


@dp.message(Command('admin'))
async def admin(message: Message):
    user_id = message.chat.id

    if user_id in ADMINS:
        await message.answer(text=await text_panel(), reply_markup=kba.menu, parse_mode='html')


@dp.callback_query(F.data == 'panel_refresh_message')
async def panel_refresh(call: CallbackQuery):
    await call.message.answer(await text_panel(), reply_markup=kba.menu, parse_mode='html')
    await call.answer()


@dp.callback_query(F.data == 'panel_refresh')
async def panel_callback(call: CallbackQuery):
    try:
        await call.message.edit_text(text=await text_panel(), reply_markup=kba.menu, parse_mode='html')
    except:
        await call.answer()


@dp.callback_query(F.data == 'cancel')
async def cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()

    await call.message.delete()


@dp.message(Command('media'))
async def media_start(message: Message, state: FSMContext):
    await state.set_state(Media.get)
    await message.answer('Пришлите медиа')


@dp.message(Media.get)
async def media_get(message: Message, state: FSMContext):
    if message.photo:
        await message.answer(str(message.photo[-1].file_id))
    elif message.video:
        await message.answer(str(message.video.file_id))
    elif message.audio:
        await message.answer(str(message.audio.file_id))
    await state.clear()