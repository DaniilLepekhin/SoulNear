"""
Скрипт для загрузки видео в Telegram и получения file_id
Запустить на сервере: docker exec soulnear_bot python3 upload_menu_video.py
"""
import asyncio
from aiogram import Bot
from aiogram.types import FSInputFile
from config import BOT_TOKEN, ADMINS

async def main():
    bot = Bot(token=BOT_TOKEN)
    try:
        # Отправляем видео админу чтобы получить file_id
        # Укажи путь к скачанному видео
        video_path = "/app/menu_video.mp4"

        # Проверяем существование файла
        import os
        if not os.path.exists(video_path):
            print(f"❌ Файл {video_path} не найден!")
            print("Инструкция:")
            print("1. Скачай видео из https://t.me/mate_bot_open/8314")
            print("2. Загрузи его на сервер: docker cp menu_video.mp4 soulnear_bot:/app/menu_video.mp4")
            print("3. Запусти: docker exec soulnear_bot python3 upload_menu_video.py")
            return

        print("📤 Загружаю видео в Telegram...")
        video = FSInputFile(video_path)
        message = await bot.send_video(
            chat_id=ADMINS[0],
            video=video,
            caption="Видео для главного меню"
        )

        file_id = message.video.file_id
        print(f"\n✅ Успех! Video file_id:")
        print(f"\n{file_id}\n")
        print(f"Замени в start.py строку:")
        print(f'    video="https://t.me/mate_bot_open/8314"')
        print(f"на:")
        print(f'    video="{file_id}"')

    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
