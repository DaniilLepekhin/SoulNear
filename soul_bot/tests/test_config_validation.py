"""
Тесты для валидации конфигурации
Проверяем, что env файлы работают корректно
"""
import os
import sys
import pytest
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfigValidation:
    """Тесты конфигурации"""
    
    def test_env_files_exist(self):
        """Проверка наличия .env файлов"""
        base_path = Path(__file__).parent.parent
        
        assert (base_path / '.env.example').exists(), ".env.example должен существовать"
        
        # Эти файлы должны быть созданы пользователем
        if not (base_path / '.env.prod').exists():
            pytest.skip(".env.prod не создан (скопируй из .env.example)")
        
        if not (base_path / '.env.test').exists():
            pytest.skip(".env.test не создан (скопируй из .env.example)")
    
    
    def test_prod_config_loads(self):
        """Тест загрузки продакшн конфига"""
        os.environ['ENV'] = 'prod'
        
        # Перезагружаем конфиг
        import importlib
        if 'config' in sys.modules:
            importlib.reload(sys.modules['config'])
        else:
            import config
        
        # Проверяем базовые переменные
        assert hasattr(config, 'BOT_TOKEN'), "BOT_TOKEN должен быть определён"
        assert hasattr(config, 'POSTGRES_DB'), "POSTGRES_DB должен быть определён"
    
    
    def test_test_config_loads(self):
        """Тест загрузки тестового конфига"""
        os.environ['ENV'] = 'test'
        
        # Перезагружаем конфиг
        import importlib
        import config
        importlib.reload(config)
        
        # Проверяем, что TEST флаг установлен
        assert config.TEST == True, "В тестовом окружении TEST должен быть True"
        assert config.POSTGRES_DB == 'soul_test_bot', "Должна использоваться тестовая БД"


class TestEnvironmentSeparation:
    """Тесты разделения окружений"""
    
    def test_different_databases(self):
        """Проверяем, что prod и test используют разные БД"""
        from dotenv import dotenv_values
        
        base_path = Path(__file__).parent.parent
        
        prod_env = dotenv_values(base_path / '.env.prod')
        test_env = dotenv_values(base_path / '.env.test')
        
        if not prod_env or not test_env:
            pytest.skip(".env файлы не созданы")
        
        prod_db = prod_env.get('POSTGRES_DB', 'soul_bot')
        test_db = test_env.get('POSTGRES_DB', 'soul_test_bot')
        
        assert prod_db != test_db, "Prod и Test должны использовать РАЗНЫЕ БД!"
        assert test_db == 'soul_test_bot', "Тестовая БД должна называться soul_test_bot"
    
    
    def test_test_flag_different(self):
        """Проверяем, что флаг TEST отличается"""
        from dotenv import dotenv_values
        
        base_path = Path(__file__).parent.parent
        
        prod_env = dotenv_values(base_path / '.env.prod')
        test_env = dotenv_values(base_path / '.env.test')
        
        if not prod_env or not test_env:
            pytest.skip(".env файлы не созданы")
        
        prod_test = prod_env.get('TEST', 'false').lower()
        test_test = test_env.get('TEST', 'true').lower()
        
        assert prod_test == 'false', "В prod TEST должен быть false"
        assert test_test == 'true', "В test TEST должен быть true"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

