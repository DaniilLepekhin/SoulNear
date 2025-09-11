from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# COSTS = [
#     {'amount': 290, 'month': 1},
#     {'amount': 880, 'month': 3},
#     {'amount': 1700, 'month': 6},
# ]
# Выбор периода подписки
sub_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='1 месяц/290 ₽', callback_data='pay 0')],
    [InlineKeyboardButton(text='3 месяца/880 ₽', callback_data='pay 1')],
    [InlineKeyboardButton(text='🔥6 месяцев/1700 ₽🔥', callback_data='pay 2')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]
])


def pay_menu(pay_url: str, pay_id: str, months: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💳 Оплатить', url=pay_url)],
        [InlineKeyboardButton(text='✅ Подтвердить оплату', callback_data=f'check_pay {pay_id} {months}')],
        [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')],
    ])
