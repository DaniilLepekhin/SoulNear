"""
Скрипт для получения file_id видео из публичного канала
Запускать на сервере: docker exec soulnear_bot python3 get_video_file_id.py
"""
import asyncio
from aiogram import Bot
from config import BOT_TOKEN

async def main():
    bot = Bot(token=BOT_TOKEN)
    try:
        # Пробуем получить file_id
        # Вариант 1: используем copy_message
        # Отправим в saved messages (можно использовать любой chat_id где бот админ)

        print("Для получения file_id нужно:")
        print("1. Перешли видео из https://t.me/mate_bot_open/8314 боту @SoulnearBot в личку")
        print("2. Бот выведет file_id в ответ")
        print("\nИли используй этот код в handlers:")
        print("""
@dp.message(F.video)
async def get_video_file_id(message: Message):
    await message.answer(f"Video file_id: {message.video.file_id}")
""")

    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
