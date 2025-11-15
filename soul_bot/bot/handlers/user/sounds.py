import logging
from aiogram import F
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    FSInputFile,
    CallbackQuery,
    InputMediaAudio
)

import bot.functions.Pictures as Pictures
from bot.loader import dp

logger = logging.getLogger(__name__)

"""version1"""

sounds = [
    {"name": "Macadamia", "id": "CQACAgIAAxkBAAIaWme6IHocOTKeWabBMRFMAo30j0RxAAIUcQACMpLRSTh0TJb9ws2pNgQ", "num": "01",
     "duration": "227"},
    {"name": "New Horizons", "id": "CQACAgIAAxkBAAIaXGe6IJtFfe3ZnHnTn72SEbEHtJ_kAAIZcQACMpLRSQm3SlOEcP70NgQ",
     "num": "02", "duration": "141"},
    {"name": "Sunny Way", "id": "CQACAgIAAxkBAAIaXme6ILRQFjmomRTaU3S_LweBO4KcAAIbcQACMpLRScrLXVN5ihmENgQ", "num": "03",
     "duration": "323"},
    {"name": "Seven Wonders", "id": "CQACAgIAAxkBAAIaYGe6IMFSka-PeboFTY749cTdqO1YAAIdcQACMpLRSTfG0XkQqWr5NgQ",
     "num": "04", "duration": "185"},
    {"name": "The Flow", "id": "CQACAgIAAxkBAAIaYme6INjiJa78R71Tgilz1cHoVNE5AAIecQACMpLRSZnku-mQlkNgNgQ", "num": "05",
     "duration": "318"},
    {"name": "Immersion", "id": "CQACAgIAAxkBAAIaZGe6IO62dHDYLfZ6ApYx5JAO5IB6AAIfcQACMpLRSU0Hq8D0hVztNgQ", "num": "06",
     "duration": "226"},
    {"name": "Spring", "id": "CQACAgIAAxkBAAIaZme6IPo_U0KLRwhniaCdH6PHbdq1AAIgcQACMpLRSRyrUTuiVBMDNgQ", "num": "07",
     "duration": "212"},
    {"name": "Rainbow", "id": "CQACAgIAAxkBAAIaaGe6IQkaE72Z22xs5phmwjNnD-OfAAIjcQACMpLRSXmo6_o-tdlNNgQ", "num": "08",
     "duration": "273"},
    {"name": "Blissful", "id": "CQACAgIAAxkBAAIaame6IRhI9YHGUNDzGXdyYXjTlOBfAAIlcQACMpLRSdMBcbkGn_SqNgQ", "num": "09",
     "duration": "314"},
    {"name": "Ocean Inside", "id": "CQACAgIAAxkBAAIabGe6IR--hH94dPduMd_xOVWwW9HiAAImcQACMpLRSUS6P8YcBJJWNgQ",
     "num": "10", "duration": "152"},
    {"name": "Gravity", "id": "CQACAgIAAxkBAAIabme6ITnuagYXIOA-x5dEkW1BqOtxAAIqcQACMpLRSXiK8U0F0yHjNgQ", "num": "11",
     "duration": "186"},
    {"name": "Cappadocia", "id": "CQACAgIAAxkBAAIacGe6IU0FqF8GNMKuUAxzCEFcsCSEAAIucQACMpLRSYay1XS2zvn7NgQ", "num": "12",
     "duration": "246"},
    {"name": "Reggae", "id": "CQACAgIAAxkBAAIacme6IWWKZbY-7FQG6aQ3p0QS2LWiAAIxcQACMpLRSYlpu2L73SnvNgQ", "num": "13",
     "duration": "192"},
    {"name": "Macadamia Remix", "id": "CQACAgIAAxkBAAIadGe6IXuMKffmitJKgPE4YjVuCql9AAI0cQACMpLRSXqbQKD9N4c9NgQ",
     "num": "14", "duration": "271"},
    {"name": "Sunny Way Remix", "id": "CQACAgIAAxkBAAIadme6IYc32RhDe3f-n1eaeYAccwj9AAI2cQACMpLRSXwwwGBfYacZNgQ",
     "num": "15", "duration": "312"},
    {"name": "Breath of Spring Remix", "id": "CQACAgIAAxkBAAIaeGe6IY5EARlEtekD_9KAxuK1iEcGAAI3cQACMpLRSVTbvohBGOngNgQ",
     "num": "16", "duration": "211"},
    {"name": "Ocean Inside Remix", "id": "CQACAgIAAxkBAAIaeme6IaGK7nwa_UEJ3HxRIzkwr_NHAAI6cQACMpLRSXm8c2FvvzFSNgQ",
     "num": "17", "duration": "311"},
    {"name": "J. Remix", "id": "CQACAgIAAxkBAAIafGe6Iax5rwOE8jZe_8IIPcRPoSHrAAI8cQACMpLRSd60kiEAAcn2UTYE", "num": "18",
     "duration": "226"},
]

PAGE_SIZE = 18


# Клавиатура плейлиста ханга
async def sounds_hang_kb(index: int):
    buttons = []

    if index > 0:
        buttons.append(InlineKeyboardButton(text="⬅", callback_data=f"page_{index - 1}"))
    if index < len(sounds) - 1:
        buttons.append(InlineKeyboardButton(text="➡", callback_data=f"page_{index + 1}"))

    return InlineKeyboardMarkup(inline_keyboard=[buttons])


# Отображение плейлиста ханга
@dp.callback_query(F.data == 'sounds')
async def sounds_menu(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning("Failed to delete sounds menu message: %s", e)
    await callback.answer()

    msg_pic = FSInputFile(Pictures.hang_pic)

    await callback.message.answer_photo(photo=msg_pic,
                                        protect_content=True,
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                            [InlineKeyboardButton(text="↩️", callback_data="menu")]
                                        ]))

    index = 0
    await callback.message.answer_audio(
        (sounds[index]["id"]),
        reply_markup=await sounds_hang_kb(index),
        protect_content=True
    )


# Листать страницы меню
@dp.callback_query(F.data.startswith('page_'))
async def change_page(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])

    await callback.message.edit_media(
        media=InputMediaAudio(media=sounds[index]["id"]),
        reply_markup=await sounds_hang_kb(index),
        protect_content=True
    )
