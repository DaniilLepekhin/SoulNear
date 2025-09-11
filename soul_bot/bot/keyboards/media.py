from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.models.media_category import Media_category
from database.models.media import Media


def categories_menu(categories: list[Media_category]) -> InlineKeyboardMarkup:
    keyboard = []

    for category in categories:
        if category.name == '🚪 Введение':
            keyboard.append([InlineKeyboardButton(text='🎧 Ханг музыка',
                                                  callback_data='sounds')])

    for category in categories:
        keyboard.append([InlineKeyboardButton(text=category.name,
                                              callback_data=f'media_category {category.id}')])

    keyboard.append([InlineKeyboardButton(text='↩️ Назад', callback_data='menu')])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def medias_menu(medias: list[Media], category: str) -> InlineKeyboardMarkup:
    keyboard = []
    for media in medias:
        keyboard.append([InlineKeyboardButton(text=media.name,
                                              callback_data=f'media_file {media.id}')])

    keyboard.append([InlineKeyboardButton(text='↩️ Назад', callback_data=f'media_categories {category}')])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def media_menu(category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='↩️ Назад', callback_data=f'media_category {category_id}')]
    ])
