from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

profile_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🛠 Изменить информацию', callback_data='update_user_info')],
    [InlineKeyboardButton(text='💳 Подписка', callback_data='premium')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]

])

gender_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='👩 Женский', callback_data='gender 0')],
    [InlineKeyboardButton(text='🧔‍♂️ Мужской', callback_data='gender 1')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]
])
