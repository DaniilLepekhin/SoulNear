from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import bot.keyboards.admin as kba
from bot.loader import dp, bot
from bot.states.states import Add_add
import database.repository.ads as db_ad


@dp.callback_query(F.data == 'ads_menu')
async def ads_menu_callback(call: CallbackQuery, state: FSMContext):
    ads = await db_ad.get_all()

    if ads:
        await call.message.answer('Имя | Ссылка | Переходов | Пользователей', reply_markup=kba.ads_menu(ads, 0))
        await call.answer()
    else:
        await state.set_state(Add_add.name)

        m = await call.message.answer('Введите название реферальной рекламы:', reply_markup=kba.cancel)
        await state.update_data(message_id=m.message_id)


@dp.callback_query(F.data.startswith('ads_change_page'))
async def ads_change_page(call: CallbackQuery):
    page = int(call.data.split()[1])

    if page < 0:
        await call.answer()
        return

    ads = await db_ad.get_all()
    len_ads = len(ads)
    pages = len_ads // 10

    if pages <= page:
        await call.answer()
        return

    await call.message.edit_text(text='Рефералы', reply_markup=kba.ads_menu(ads, page))


@dp.callback_query(F.data.startswith('send_ad'))
async def send_ad(call: CallbackQuery):
    ad_id = int(call.data.split()[1])
    ad = await db_ad.get(ad_id)

    try:
        cost_user = ad.cost / ad.users
    except ZeroDivisionError:
        cost_user = 0
    try:
        cost_view = ad.cost / ad.views
    except ZeroDivisionError:
        cost_view = 0

    await call.message.answer(
        f"""ID <code>{ad.id}</code>
Имя: <code>{ad.name}</code>
Ссылка:
<code>https://t.me/SoulnearBot?start={ad.link}</code>

👀 Переходов: <code>{ad.views}</code>
👥 Юзеров: <code>{ad.users}</code>
🤑 Заработано: <code>{ad.earn} руб</code>

– Че по деньгам?
💵 Цена: <code>{ad.cost}</code>
🪙 Цена перехода: <code>{cost_view}</code>
💎 Цена пользователя: <code>{cost_user}</code> руб""",
        reply_markup=kba.cancel)
    await call.answer()


@dp.callback_query(F.data == 'add_ad')
async def add_ad_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(Add_add.name)

    m = await call.message.answer('Введите название реферальной рекламы:', reply_markup=kba.cancel)
    await state.update_data(message_id=m.message_id)
    await call.answer()


@dp.message(Add_add.name)
async def add_ad_name(message: Message, state: FSMContext):
    await state.set_state(Add_add.cost)
    data = await state.get_data()

    m = await message.answer('Введите стоимость рекламы:', reply_markup=kba.cancel)
    await bot.delete_message(message.chat.id, data['message_id'])

    await state.update_data(message_id=m.message_id,
                            name=message.text)
    await message.delete()


@dp.message(Add_add.cost)
async def add_ad_cost(message: Message, state: FSMContext):
    if message.text.isdigit():
        data = await state.get_data()
        await bot.delete_message(message.chat.id, data['message_id'])

        link = await db_ad.new(name=data['name'],
                             cost=int(message.text))

        if link is not None:
            await message.answer(f'Успешно!\n'
                                 f'Линк: <code>https://t.me/SoulnearBot?start={link}</code>',
                                 reply_markup=kba.cancel)

            ads = await db_ad.get_all()
            await message.answer('Имя | Ссылка | Переходов | Пользователей', reply_markup=kba.ads_menu(ads, 0))

            await state.clear()

    await message.delete()
