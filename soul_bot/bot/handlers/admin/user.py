import time
from datetime import datetime

from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import bot.keyboards.admin as kba
from bot.functions.other import percent
from bot.loader import dp, bot
from bot.states.states import User_info, User_update_sub
from config import ADMINS
import database.repository.user as db_user
import database.repository.statistic_day as db_statistic_day
from database.models import User


@dp.callback_query(F.data == 'user_info_start')
async def user_info_start(call: CallbackQuery, state: FSMContext):
    await call.answer()

    m = await call.message.answer(text='Введите ид пользователя:',
                                  reply_markup=kba.cancel)

    await state.set_state(User_info.user_id)

    await state.update_data(message_id=m.message_id)


def user_info_text(user: User) -> str:
    sub_date = '❌' if user.sub_date < datetime.now() else f'{user.sub_date}'[:-10]

    return f'ID <code>{user.user_id}</code>\n' \
           f'Имя: <code>{user.name}</code>\n' \
           f'Никнейм: <code>@{user.username}</code>\n' \
           f'Зарегался: <code>{str(user.reg_date)[:-7]}</code>\n' \
           f'Был замечен: <code>{str(user.active_date)[:-7]}</code>\n' \
           f'Подписка до: <code>{sub_date}</code>\n'


@dp.message(User_info.user_id)
async def user_info_user_id_message(message: Message, state: FSMContext):
    user_id = message.text

    if not user_id.isdigit():
        await message.delete()
        return

    user_id = int(user_id)
    if user_id < 0 or user_id > 9223372036854775807:
        await message.delete()
        return

    user = await db_user.get(user_id)

    if not user:
        await message.answer('Такого пользователя нет.')
        return

    data = await state.get_data()
    await bot.delete_message(chat_id=message.chat.id, message_id=data['message_id'])

    await message.delete()

    await message.answer(text=user_info_text(user=user),
                         reply_markup=kba.user_menu(user_id))
    await state.clear()


@dp.callback_query(F.data.startswith('user_change_sub'))
async def user_change_sub_start(call: CallbackQuery, state: FSMContext):
    user_id = int(call.data.split()[1])
    type_ = int(call.data.split()[2])

    await state.update_data(user_id=user_id)
    await state.update_data(type=type_)

    await state.set_state(User_update_sub.value)

    match type_:
        case 0:
            type_ = 'дней'
        case 1:
            type_ = 'недель'
        case 2:
            type_ = 'месяцев'

    m = await call.message.answer(text=f'Введите кол-во {type_}: ',
                                  reply_markup=kba.cancel)

    await state.update_data(message_id=m.message_id)


@dp.message(User_update_sub.value)
async def user_update_sub(message: Message, state: FSMContext):
    value = message.text

    if not value.isdigit():
        await message.delete()
        return

    data = await state.get_data()
    user_id = data['user_id']
    value = int(value)

    match data['type']:
        case 0:
            await db_user.update_sub_date(user_id=user_id,
                                          days=value)
        case 1:
            await db_user.update_sub_date(user_id=user_id,
                                          weeks=value)
        case 2:
            await db_user.update_sub_date(user_id=user_id,
                                          months=value)

    await message.delete()
    await bot.delete_message(chat_id=message.chat.id, message_id=data['message_id'])

    await message.answer('Успешно!')

    user = await db_user.get(user_id)
    
    # ✅ FIX: Check if user exists
    if user is None:
        await message.answer("❌ Ошибка: пользователь не найден")
        await state.clear()
        return

    await message.answer(text=user_info_text(user=user),
                         reply_markup=kba.user_menu(user_id))

    await state.clear()
