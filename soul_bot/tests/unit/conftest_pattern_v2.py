"""
Conftest для тестов pattern analyzer - настройка окружения
"""
import os
import sys

# Set test environment BEFORE any imports
os.environ['ENV_MODE'] = 'test'
os.environ['BOT_TOKEN'] = 'test_token'
os.environ['OPENAI_API_KEY'] = 'test_key'
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'

# Ensure soul_bot is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

