from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import bot.text as text
from bot.functions.payments import create, check
from bot.handlers.user.start import menu_message_not_delete
from bot.keyboards.premium import pay_menu, sub_menu
from bot.loader import dp
import database.repository.user as db_user
import database.repository.statistic_day as db_statistic_day
import database.repository.ads as db_ads

COSTS = [
    {'amount': 1111, 'month': 1},
    {'amount': 2999, 'month': 3},
    {'amount': 5555, 'month': 6},
    {'amount': 11111, 'month': 12},
]


@dp.callback_query(F.data == 'premium')
async def premium_callback(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        await callback.answer()

    await callback.message.answer(
        'Выберите подписку:',
        reply_markup=sub_menu
    )


@dp.callback_query(F.data.startswith('pay'))
async def subscription_callback(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        await callback.answer()

    user_id = callback.from_user.id
    data = int(callback.data.split()[1])

    amount, months = COSTS[data]['amount'], COSTS[data]['month']

    pay_url, pay_id = create(amount, user_id)

    await callback.message.answer(
        text.pay,
        reply_markup=pay_menu(pay_id=pay_id, months=months, pay_url=pay_url),
        parse_mode='html'
    )


@dp.callback_query(F.data.startswith('check_pay'))
async def check_pay(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    payment_id = callback.data.split()[1]

    if not await check(payment_id=payment_id):
        await callback.answer('❌ Счет не оплачен')
        return

    months = int(callback.data.split()[2])

    await db_user.update_sub_date(user_id=user_id,
                                  months=months)

    await callback.message.edit_text('Подписка продлена!')

    await menu_message_not_delete(callback.message)

    for cost in COSTS:
        if cost['month'] == months:
            await db_statistic_day.increment(column='earn', value=cost['amount'])

            user = await db_user.get(user_id=user_id)

            if user.ref:
                if not user.ref.isdigit():
                    await db_ads.update_earn(link=user.ref,
                                             value=cost['amount'],)

            return
