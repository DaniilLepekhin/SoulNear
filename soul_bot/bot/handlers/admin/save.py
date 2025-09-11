import os
from aiogram import F
from aiogram.enums import ChatAction
from aiogram.types import CallbackQuery, FSInputFile
from bot.loader import dp, bot
import database.repository.user as db_user


@dp.callback_query(F.data == 'send_active_file')
async def send_active_file_callback(call: CallbackQuery):
    await call.answer()
    await bot.send_chat_action(call.message.chat.id, action=ChatAction.UPLOAD_DOCUMENT)

    users = await db_user.get_all_active_users_id()

    with open('users.txt', 'w') as file:
        for user_id in users:
            file.write(f"{user_id}\n")

    await call.message.answer_document(document=FSInputFile('users.txt'))
    os.remove('users.txt')
