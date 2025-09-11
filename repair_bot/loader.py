from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN

bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode='HTML'),
    )

storage = MemoryStorage()

dp = Dispatcher(storage=storage)
