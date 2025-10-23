from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from config import BOT_TOKEN, TEST
from database.storage import MyStorage
import os

# Используем кастомный API сервер только если указан в .env
CUSTOM_API_SERVER = os.getenv('TELEGRAM_API_SERVER')

if CUSTOM_API_SERVER and not TEST:
    # Кастомный API сервер (например, для обхода блокировок)
    session = AiohttpSession(api=TelegramAPIServer.from_base(CUSTOM_API_SERVER))
    bot = Bot(token=BOT_TOKEN, session=session, default=DefaultBotProperties(parse_mode='HTML'))
else:
    # Стандартный Telegram API (по умолчанию)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

dp = Dispatcher(storage=MyStorage(), bot=bot)
