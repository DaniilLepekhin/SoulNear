import os
from dotenv import load_dotenv

load_dotenv()

ADMINS = [580613548, 946195257, 73744901]
TOKEN = os.getenv('TOKEN', '7548056844:AAHH5W5myeaH_lLBbxW5RxqJiQwpd4wNNcg')
POSTGRES_PASS = os.getenv('POSTGRES_PASS', 'your_postgres_password_here')

BOTS = [
    {
        'name': 'Soul.near 🔮',
        'username': 'SoulnearBot',
        'token': os.getenv('SOUL_BOT_TOKEN', '7120474080:AAF9jNP4yveP-sQzuzlCwYsH_hYyGsqvEF0'),
        'bd_name': 'soul_bot',
        'daemon_name': 'soul_bot'
    },
    {
        'name': 'Soul.near TEST ⚠️',
        'username': 'Soulneartest_bot',
        'token': os.getenv('SOUL_TEST_BOT_TOKEN', '7838929567:AAELlItbyGN8KvzeYdY-28id6Fhtf6Zn0PY'),
        'bd_name': 'soul_test_bot',
        'daemon_name': 'soul_test_bot'
    },
    {
        'name': 'Soul.near Support 🗣 ',
        'username': 'SOULnearsupportbot',
        'token': os.getenv('SUPPORT_BOT_TOKEN', '7859607180:AAEApf_CfaTe5-HVc9eHNd1CGLSAEOjoGN0'),
        'bd_name': None,
        'daemon_name': 'soul_support_bot'
    },

]
