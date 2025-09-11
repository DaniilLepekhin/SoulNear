import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN', '7859607180:AAEApf_CfaTe5-HVc9eHNd1CGLSAEOjoGN0')
CHAT_ID = int(os.getenv('CHAT_ID', '-1002631450291'))
ADMINS = [580613548, 946195257, 73744901]

POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'your_postgres_password_here')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'soul_support')
