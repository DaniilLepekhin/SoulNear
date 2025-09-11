from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import BOTS


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='🤖 Боты', callback_data='bots')
        ],
        [
            InlineKeyboardButton(text='💾 Бэкап базы', callback_data='server_backup_bd'),
            InlineKeyboardButton(text='🔄 Перезагрузить сервант', callback_data='server_reboot'),
        ],
    ])


def bots_menu():
    buttons = []

    for i, bot in enumerate(BOTS):
        buttons.append([InlineKeyboardButton(text=bot['name'], callback_data=f'bot_menu {i}')])

    buttons.append([InlineKeyboardButton(text='Закрыть', callback_data='close')])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def bot_menu(i):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='🔄 Перезагрузить', callback_data=f'bot_reload {i}'),
            InlineKeyboardButton(text='💾 Выгрузка Базы', callback_data=f'bot_bd {i}')
        ],
        [
            InlineKeyboardButton(text='🛠 Логи', callback_data=f'bot_logs {i}'),
            InlineKeyboardButton(text='Закрыть', callback_data='close')
        ]
    ])


def close():

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Закрыть', callback_data='close'),
        ]
    ])


def confirm_(name):

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Да', callback_data=f'confirm_{name}'),
        ],
        [
            InlineKeyboardButton(text='Закрыть', callback_data=f'close')
        ]
    ])
