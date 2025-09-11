import asyncio
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import bot.keyboards.admin as kba
from bot.loader import dp, bot
from bot.states.states import Mailing
from config import ADMINS
import database.repository.user as db_user



@dp.callback_query(F.data == 'mailing_start')
async def mail_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(Mailing.message)
    await call.message.answer('Пришлите сообщение', reply_markup=kba.cancel)
    await call.answer()


@dp.message(Mailing.message)
async def mail_message(message: Message, state: FSMContext):
    await state.update_data(message_id=message.message_id,
                            chat_id=message.chat.id,
                            reply_markup=message.reply_markup)

    await bot.copy_message(chat_id=message.chat.id,
                           message_id=message.message_id,
                           from_chat_id=message.chat.id,
                           reply_markup=message.reply_markup)

    await message.answer('Рассылать?', reply_markup=kba.mail_accept)


ALL = 0
GOOD = 0
BAD = 0


@dp.callback_query(F.data == 'mail_accept')
async def mail_accept(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    chat_id = data['chat_id']
    message_id = data['message_id']
    reply_markup = data['reply_markup']
    await call.message.answer('Рассылка начнется в течение минуты!')

    await state.clear()

    await call.message.delete()

    users = await db_user.get_all()

    global ALL
    ALL = len(users)

    delay = 0
    tasks = []
    asyncio.get_event_loop().create_task(admin_loader())

    for i, user in enumerate(users):
        delay += 0.04

        tasks.append(send_mail(user.user_id, delay, message_id, chat_id, reply_markup))

        if i % 100000 == 0:
            await asyncio.gather(*tasks)
            tasks = []
            delay = 0

    await asyncio.gather(*tasks)


async def send_mail(user_id, delay, message_id, chat_id, reply_markup):
    await asyncio.sleep(delay)

    try:
        await bot.copy_message(chat_id=user_id,
                               message_id=message_id,
                               from_chat_id=chat_id,
                               reply_markup=reply_markup)
        global GOOD
        GOOD += 1
    except Exception as e:
        await db_user.block(user_id=user_id)

        global BAD
        BAD += 1


async def admin_loader():
    loaders = []
    for a in ADMINS:
        try:
            loader = await bot.send_message(chat_id=a, text='Началась рассылка!')
            loaders.append(loader)

        except:
            pass

    prev_data = 0
    while True:
        global ALL
        users = ALL
        global GOOD
        alive = GOOD
        global BAD
        dead = BAD
        alive_dead = alive + dead
        kolvo = alive_dead - prev_data
        prev_data = alive_dead

        for loader in loaders:
            text3 = 'Доступно чатов - ' + str(users) + \
                    '\nОбработано - ' + str(alive_dead) + \
                    '\nУспешно - ' + str(alive) + \
                    '\nНе удачно - ' + str(dead) + \
                    '\n' + str(kolvo) + 'в сек'

            try:
                await asyncio.sleep(1)
                await loader.edit_text(text3)
            except Exception as e:
                print(e)

        if users == alive_dead:
            break

        await asyncio.sleep(1)

    text3 = '\nОбработано - ' + str(alive_dead) + \
            '\nУспешно - ' + str(alive) + \
            '\nНе удачно - ' + str(dead)

    for loader in loaders:
        await loader.answer('Закончилась рассылка!' + text3)
        await loader.delete()
