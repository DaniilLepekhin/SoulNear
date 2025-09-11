import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '7838929567:AAELlItbyGN8KvzeYdY-28id6Fhtf6Zn0PY')  # тест

TEST = True

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your_openai_api_key_here')
ELEVEN_LABS_KEY = os.getenv('ELEVEN_LABS_KEY', 'your_eleven_labs_key_here')
HELPER_ID = os.getenv('HELPER_ID', 'your_helper_assistant_id_here')
SOULSLEEP_ID = os.getenv('SOULSLEEP_ID', 'your_soulsleep_assistant_id_here')
#Ассистенты по анализу
RELATIONSHIPS_ID = os.getenv('RELATIONSHIPS_ID', 'your_relationships_assistant_id_here')
MONEY_ID = os.getenv('MONEY_ID', 'your_money_assistant_id_here')
CONFIDENCE_ID = os.getenv('CONFIDENCE_ID', 'your_confidence_assistant_id_here')
FEARS_ID = os.getenv('FEARS_ID', 'your_fears_assistant_id_here')

#Юкасса
SHOP_ID = int(os.getenv('SHOP_ID', '476767'))
SECRET_KEY = os.getenv('SECRET_KEY', 'your_yookassa_secret_key_here')

POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'your_postgres_password_here')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'soul_test_bot')

ADMINS = [580613548, 946195257, 73744901]
