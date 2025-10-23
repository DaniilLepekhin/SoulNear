"""
Рефакторенная версия config.py с поддержкой множественных окружений.
"""
import os
from dotenv import load_dotenv

# Определяем окружение (prod/test/dev)
ENV = os.getenv('ENV', 'prod')

# Загружаем соответствующий .env файл (override=True для перезагрузки)
env_file = f'.env.{ENV}'
if os.path.exists(env_file):
    load_dotenv(env_file, override=True)
    print(f"🚀 Загружен конфиг: {env_file}")
else:
    # Fallback на обычный .env
    load_dotenv(override=True)
    print(f"⚠️  Файл {env_file} не найден, загружен .env")

# Telegram Bot
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError(f"BOT_TOKEN не найден в {env_file}!")

TEST = os.getenv('TEST', 'false').lower() == 'true'

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError(f"OPENAI_API_KEY не найден в {env_file}!")

# OpenAI Assistants
HELPER_ID = os.getenv('HELPER_ID', 'your_helper_assistant_id_here')
SOULSLEEP_ID = os.getenv('SOULSLEEP_ID', 'your_soulsleep_assistant_id_here')

# Ассистенты по анализу
RELATIONSHIPS_ID = os.getenv('RELATIONSHIPS_ID', 'your_relationships_assistant_id_here')
MONEY_ID = os.getenv('MONEY_ID', 'your_money_assistant_id_here')
CONFIDENCE_ID = os.getenv('CONFIDENCE_ID', 'your_confidence_assistant_id_here')
FEARS_ID = os.getenv('FEARS_ID', 'your_fears_assistant_id_here')

# Юкасса
SHOP_ID = int(os.getenv('SHOP_ID', '476767'))
SECRET_KEY = os.getenv('SECRET_KEY', 'your_yookassa_secret_key_here')

# PostgreSQL
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
if not POSTGRES_PASSWORD:
    raise ValueError(f"POSTGRES_PASSWORD не найден в {env_file}!")

POSTGRES_DB = os.getenv('POSTGRES_DB')
if not POSTGRES_DB:
    raise ValueError(f"POSTGRES_DB не найден в {env_file}!")

# Admins
ADMINS = [580613548, 946195257, 73744901, 389209990]

# Опциональные ключи (для расширенных фич)
ELEVEN_LABS_KEY = os.getenv('ELEVEN_LABS_KEY')

# Лог текущей конфигурации (для отладки)
if __name__ == '__main__':
    print(f"\n📋 Текущая конфигурация ({ENV}):")
    print(f"  BOT_TOKEN: {'*' * 10}{BOT_TOKEN[-10:] if BOT_TOKEN else 'НЕТ'}")
    print(f"  TEST: {TEST}")
    print(f"  POSTGRES_DB: {POSTGRES_DB}")
    print(f"  OPENAI_API_KEY: {'*' * 10}{OPENAI_API_KEY[-10:] if OPENAI_API_KEY else 'НЕТ'}")
    print(f"  HELPER_ID: {HELPER_ID}")

