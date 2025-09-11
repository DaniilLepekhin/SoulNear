from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔒 Принять и продолжить', callback_data='menu')]
])

menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💬 Чат с SOUL.near GPT', callback_data='support')],
    [InlineKeyboardButton(text='👤 Анализ личности', callback_data='analysis')],
    [InlineKeyboardButton(text='💤 Сны', callback_data='soulsleep')],

    [InlineKeyboardButton(text='🧘 Практики', callback_data='media_categories practices'),
     InlineKeyboardButton(text='🗝 Видео', callback_data='media_categories videos')],

    [InlineKeyboardButton(text='⚙️ Профиль', callback_data='profile')],
    [InlineKeyboardButton(text='❓ FAQ', url='https://telegra.ph/FAQ-dlya-bota-SOULnear-10-22')]
])

back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]
])