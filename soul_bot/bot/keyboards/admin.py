import math
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Ad

menu = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='🤝 Реклама', callback_data='ads_menu'),
            InlineKeyboardButton(text='💾 Выгрузка', callback_data='send_active_file')
        ],
        [
            InlineKeyboardButton(text='📨 Рассылка', callback_data='mailing_start'),
            InlineKeyboardButton(text='👤 Пользователи', callback_data='user_info_start')
        ],
        [
            InlineKeyboardButton(text='♻ Обновить', callback_data='panel_refresh'),
            InlineKeyboardButton(text='🔄 Обновить', callback_data='panel_refresh_message')
        ],
        [
            InlineKeyboardButton(text='Закрыть', callback_data='cancel')
        ]
    ])


def ads_menu(ads: list[Ad], page: int) -> InlineKeyboardMarkup:
    keyboard_buttons = []

    len_ads = len(ads)
    pages = math.ceil(len_ads / 10)

    limit = 0
    for i in range(page * 10, len_ads):
        id = ads[i].id
        name = ads[i].name
        link = ads[i].link
        views = ads[i].views
        users = ads[i].users

        keyboard_buttons.append([
            InlineKeyboardButton(text=f"{name} | {link} | {views} | {users}", callback_data=f'send_ad {id}')
        ])

        limit += 1
        if limit > 9:
            break

    left = InlineKeyboardButton(text='<<', callback_data=f'ads_change_page {page - 1}')
    center = InlineKeyboardButton(text=f'{page + 1}/{pages}', callback_data=f'none')
    right = InlineKeyboardButton(text='>>', callback_data=f'ads_change_page {page + 1}')

    keyboard_buttons.append([left, center, right])

    keyboard_buttons.append([InlineKeyboardButton(text=' ➕ Добавить', callback_data=f'add_ad')])

    keyboard_buttons.append([InlineKeyboardButton(text='Закрыть', callback_data=f'cancel')])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    return keyboard


def mailing_stop(id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Остановить', callback_data=f'mailing_stop {id}')
        ]
    ])

    return keyboard


cancel = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='❌ Отмена', callback_data='cancel'),
    ],
])

mail_accept = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='✅ Да', callback_data='mail_accept')
    ],
    [
        InlineKeyboardButton(text='❌ Отмена', callback_data='cancel')
    ]
])


def user_menu(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Добавить месяц', callback_data=f'user_change_sub {user_id} 2')
        ],
        [
            InlineKeyboardButton(text='Добавить неделю', callback_data=f'user_change_sub {user_id} 1')
        ],
        [
            InlineKeyboardButton(text='Добавить день', callback_data=f'user_change_sub {user_id} 0')
        ],
        [
            InlineKeyboardButton(text='❌ Закрыть', callback_data='cancel')
        ]
    ])
