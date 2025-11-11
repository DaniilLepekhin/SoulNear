from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

_QUIZ_CATEGORY_BUTTONS = [
    ('relationships', '🤍 Отношения'),
    ('money', '💸 Деньги'),
    ('purpose', '🌿 Предназначение'),
]

start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Принять и продолжить', callback_data='start_accept')]
])

menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💬 Чат с Soul Near', callback_data='support')],
    [InlineKeyboardButton(text='🌙 Сны', callback_data='soulsleep')],
    [InlineKeyboardButton(text='🧩 Паттерны', callback_data='analysis')],
    [
        InlineKeyboardButton(text='🪷 Практики', callback_data='media_categories practices'),
        InlineKeyboardButton(text='🎥 Видео', callback_data='media_categories videos'),
    ],
    [InlineKeyboardButton(text='⚙️ Профиль', callback_data='profile')],
    [InlineKeyboardButton(text='❓ FAQ', url='https://telegra.ph/FAQ-dlya-bota-SOULnear-10-22')]
])

back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]
])

age_question = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🙈 Не важно', callback_data='age_skip')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]
])