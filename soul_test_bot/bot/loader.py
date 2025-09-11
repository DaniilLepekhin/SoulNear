from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from config import BOT_TOKEN, TEST
from database.storage import MyStorage

if TEST:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
else:
    session = AiohttpSession(api=TelegramAPIServer.from_base('https://tgrasp.co'))

    bot = Bot(token=BOT_TOKEN, session=session, default=DefaultBotProperties(parse_mode='HTML'))

dp = Dispatcher(storage=MyStorage(), bot=bot)
