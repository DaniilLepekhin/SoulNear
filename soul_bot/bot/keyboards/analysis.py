from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


analysis_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🤍 Близость', callback_data='relationships')],
    [InlineKeyboardButton(text='💸 Деньги', callback_data='money')],
    [InlineKeyboardButton(text='🌿 Предназначение', callback_data='confidence')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]
])


def build_quiz_ready_keyboard(category: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='↩️ Назад', callback_data='analysis'),
            InlineKeyboardButton(text='▶️ Начать', callback_data=f'quiz_category_{category}'),
        ]
    ])
