from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


analysis_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🤍 Близость', callback_data='relationships')],
    [InlineKeyboardButton(text='💸 Деньги', callback_data='money')],
    [InlineKeyboardButton(text='🌿 Предназначение', callback_data='confidence')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]
])
