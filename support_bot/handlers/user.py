from aiogram import types
from config import CHAT_ID
from loader import dp, bot
import database.controllers.user as User


@dp.message()
async def support(message: types.Message):
    if message.from_user.is_bot:
        return

    if message.chat.is_forum:
        user = await User.get_by_topic(message.message_thread_id)

        await bot.copy_message(chat_id=user.user_id,
                               from_chat_id=CHAT_ID,
                               message_id=message.message_id)
        return

    chat_id = message.chat.id

    if chat_id != CHAT_ID:
        user = await User.get(user_id=chat_id)

        if not user:
            topic = await bot.create_forum_topic(chat_id=CHAT_ID,
                                                 name=f'{message.from_user.full_name} | {message.chat.id}')
            await User.new(user_id=chat_id,
                           topic_id=topic.message_thread_id)

            await bot.copy_message(from_chat_id=chat_id,
                                   message_id=message.message_id,
                                   chat_id=CHAT_ID,
                                   message_thread_id=topic.message_thread_id)

            await bot.send_message(chat_id=CHAT_ID,
                                   message_thread_id=topic.message_thread_id,
                                   text='Привет, я бот обратной связи проекта SOUL.near!\n'
                                        'Отвечать будут настоящие люди\n'
                                        'Что Вас интересует?')

            await message.answer('Привет, я бот обратной связи проекта SOUL.near!\n'
                                 'Отвечать будут настоящие люди\n'
                                 'Что Вас интересует?')

        else:
            await bot.copy_message(from_chat_id=chat_id,
                                   message_id=message.message_id,
                                   chat_id=CHAT_ID,
                                   message_thread_id=user.topic_id)
