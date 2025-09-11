from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# COSTS = [
#     {'amount': 1111, 'month': 1},
#     {'amount': 2999, 'month': 3},
#     {'amount': 5555, 'month': 6},
#     {'amount': 11111, 'month': 12},
# ]
# Выбор периода подписки
sub_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='1 месяц — 1 111 ₽', callback_data='pay 0')],
    [InlineKeyboardButton(text='3 месяца — 2 999 ₽', callback_data='pay 1')],
    [InlineKeyboardButton(text='6 месяцев — 5 555 ₽', callback_data='pay 2')],
    [InlineKeyboardButton(text='12 месяцев — 11 111 ₽', callback_data='pay 3')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]
])


def pay_menu(pay_url: str, pay_id: str, months: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💳 Оплатить', url=pay_url)],
        [InlineKeyboardButton(text='✅ Подтвердить оплату', callback_data=f'check_pay {pay_id} {months}')],
        [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')],
    ])
