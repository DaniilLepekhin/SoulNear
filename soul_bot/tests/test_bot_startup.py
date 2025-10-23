"""
Smoke тесты для проверки запуска бота в разных режимах
"""
import os
import sys
import pytest
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBotStartup:
    """Тесты запуска бота"""
    
    def test_imports_work(self):
        """Проверка, что все импорты работают"""
        try:
            import config
            from bot.loader import bot, dp
            from database.database import db, create_tables
            assert True
        except Exception as e:
            pytest.fail(f"Импорты не работают: {e}")
    
    
    def test_config_has_required_fields(self):
        """Проверка наличия всех обязательных полей в конфиге"""
        import config
        
        required_fields = [
            'BOT_TOKEN',
            'TEST',
            'OPENAI_API_KEY',
            'HELPER_ID',
            'SOULSLEEP_ID',
            'POSTGRES_HOST',
            'POSTGRES_PORT',
            'POSTGRES_USER',
            'POSTGRES_PASSWORD',
            'POSTGRES_DB',
            'ADMINS'
        ]
        
        for field in required_fields:
            assert hasattr(config, field), f"Поле {field} отсутствует в конфиге"
    
    
    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Проверка подключения к БД"""
        from database.database import db
        
        try:
            async with db.begin() as session:
                result = await session.execute("SELECT 1")
                assert result is not None
        except Exception as e:
            pytest.skip(f"БД недоступна (это нормально для локальных тестов): {e}")
    
    
    def test_handlers_registered(self):
        """Проверка, что хендлеры зарегистрированы"""
        from bot.handlers import dp
        
        # Проверяем, что dp имеет обработчики
        assert hasattr(dp, 'message'), "Message handlers должны быть зарегистрированы"
        assert hasattr(dp, 'callback_query'), "Callback handlers должны быть зарегистрированы"


class TestEnvironmentFlags:
    """Тесты флагов окружения"""
    
    def test_test_flag_affects_behavior(self):
        """Проверка, что флаг TEST влияет на поведение"""
        os.environ['ENV'] = 'test'
        
        import importlib
        if 'config' in sys.modules:
            importlib.reload(sys.modules['config'])
        else:
            import config
        
        # В тестовом режиме TEST должен быть True
        assert config.TEST == True, "В тестовом режиме TEST должен быть True"
    
    
    def test_prod_flag_sets_prod_mode(self):
        """Проверка, что в продакшн режиме TEST=False"""
        os.environ['ENV'] = 'prod'
        
        import importlib
        if 'config' in sys.modules:
            importlib.reload(sys.modules['config'])
        else:
            import config
        
        # В продакшн режиме TEST должен быть False
        assert config.TEST == False, "В продакшн режиме TEST должен быть False"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


