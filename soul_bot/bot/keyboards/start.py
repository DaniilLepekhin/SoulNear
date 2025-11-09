from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

_QUIZ_CATEGORY_BUTTONS = [
    ('relationships', '🤍 Отношения'),
    ('money', '💸 Деньги'),
    ('purpose', '🌿 Предназначение'),
]

start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔒 Принять и продолжить', callback_data='menu')]
])

menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💬 Чат с SOUL.near GPT', callback_data='support')],
    [InlineKeyboardButton(text='👤 Анализ личности', callback_data='analysis')],
    [InlineKeyboardButton(text='🧠 Психологический квиз', callback_data='quiz_start')],
    [InlineKeyboardButton(text='💤 Сны', callback_data='soulsleep')],

    [InlineKeyboardButton(text='🧘 Практики', callback_data='media_categories practices'),
     InlineKeyboardButton(text='🗝 Видео', callback_data='media_categories videos')],

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

quiz_offer = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=label, callback_data=f'quiz_category_{category}')]
    for category, label in _QUIZ_CATEGORY_BUTTONS
] + [
    [InlineKeyboardButton(text='🏠 Главное меню', callback_data='menu')]
])