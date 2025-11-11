from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import bot.text as texts
from bot.services.quiz_service import generator


def get_quiz_intro_text(category: str) -> str | None:
    mapping = {
        'relationships': texts.relationships,
        'money': texts.money,
        'purpose': texts.purpose,
    }
    return mapping.get(category)


def build_quiz_entry_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{info['emoji']} {info['name']}",
                callback_data=f"quiz_category_{category_id}"
            )
        ]
        for category_id, info in generator.QUIZ_CATEGORIES.items()
    ]
    buttons.append([InlineKeyboardButton(text='🏠 Меню', callback_data='quiz_go_menu')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_quiz_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🏠 Меню', callback_data='quiz_go_menu')]
    ])

