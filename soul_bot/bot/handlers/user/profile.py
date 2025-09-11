from datetime import datetime
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.user.start import menu_callback
from bot.keyboards.profile import profile_menu, gender_menu
from bot.keyboards.start import back, menu
from bot.loader import dp, bot
import database.repository.user as db_user
from bot.states.states import Update_user_info


@dp.callback_query(F.data == 'profile')
async def profile_callback(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    user = await db_user.get(user_id=user_id)

    sub_date = '❌' if user.sub_date < datetime.now() else f'{user.sub_date}'[:-10]

    text = f'👤 Ваш профиль, <code>{call.from_user.first_name}</code>\n' \
           f'├ Ваш ID: <code>{user_id}</code>\n' \
           f'├ Имя: <code>{user.real_name}</code>\n' \
           f'├ Возраст: <code>{user.age}</code>\n' \
           f'├ Пол: <code>{"Мужской" if user.gender else "Женский"}</code>\n'

    if user.sub_date > datetime.now():
        text += f'└ Подписка до: <code>{sub_date}</code>\n\n'
    else:
        text += (f'├ Ассистент: <code>{user.helper_requests}</code>\n'
                 f'├ Сонник: <code>{user.sleeper_requests}</code>\n'
                 f'├ Анализ личности: <code>{user.assistant_requests}</code>\n'
                 f'└ Подписка до: <code>{sub_date}</code>\n\n')

    text += f'+3 дня подписки за приведенного друга: <code>https://t.me/SoulnearBot?start={user_id}</code>'
    try:
        await call.message.delete()
        await call.message.answer(text=text,
                                  reply_markup=profile_menu)

    except:
        await call.answer()


@dp.callback_query(F.data == 'update_user_info')
async def update_user_info_start(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        await call.answer()

    await state.set_state(Update_user_info.real_name)

    m = await call.message.answer(text='Введите ваше настоящее имя: ',
                                  reply_markup=back)

    await state.update_data(is_profile=True,
                            message_id=m.message_id)


@dp.message(Update_user_info.real_name)
async def update_user_real_name(message: Message, state: FSMContext):
    real_name = message.text

    await message.delete()

    if len(real_name) > 32:
        return

    data = await state.get_data()

    await bot.delete_message(chat_id=message.chat.id,
                             message_id=data['message_id'])

    m = await message.answer(text='Сколько тебе полных лет? ',
                             reply_markup=back)

    await state.update_data(real_name=real_name,
                            message_id=m.message_id)

    await state.set_state(Update_user_info.age)


@dp.message(Update_user_info.age)
async def update_user_age(message: Message, state: FSMContext):
    age = int(message.text)
    await message.delete()

    if age < 0 or age > 100:
        return

    data = await state.get_data()

    await bot.delete_message(chat_id=message.chat.id,
                             message_id=data['message_id'])

    await state.update_data(age=age)
    await message.answer(text='Твой пол?',
                         reply_markup=gender_menu)


@dp.callback_query(F.data.startswith('gender'))
async def update_user_gender(call: CallbackQuery, state: FSMContext):
    gender = bool(int(call.data.split()[1]))
    data = await state.get_data()

    await db_user.update_info(user_id=call.from_user.id,
                              real_name=data['real_name'],
                              age=data['age'],
                              gender=gender)
    if data['is_profile']:
        await profile_callback(call, state)
    else:
        await menu_callback(call, state)

    await state.clear()
