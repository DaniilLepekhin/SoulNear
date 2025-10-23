#!/usr/bin/env python3
"""
Простой скрипт для проверки рефакторинга
Проверяет, что оба режима (prod/test) работают корректно
"""

import os
import sys

def test_config_load(env_name):
    """Тестируем загрузку конфига"""
    print(f"\n{'='*60}")
    print(f"🧪 Тестируем окружение: {env_name.upper()}")
    print('='*60)
    
    # Устанавливаем ENV
    os.environ['ENV'] = env_name
    
    # Перезагружаем config если он уже был импортирован
    if 'config' in sys.modules:
        import importlib
        importlib.reload(sys.modules['config'])
    
    # Импортируем
    import config
    
    # Проверяем
    checks = []
    
    # 1. ENV переменная
    expected_env = env_name
    actual_env = config.ENV if hasattr(config, 'ENV') else 'unknown'
    checks.append(('ENV', expected_env, actual_env, expected_env == actual_env))
    
    # 2. TEST флаг
    expected_test = (env_name == 'test')
    actual_test = config.TEST
    checks.append(('TEST', expected_test, actual_test, expected_test == actual_test))
    
    # 3. POSTGRES_DB
    expected_db = 'soul_test_bot' if env_name == 'test' else 'soul_bot'
    actual_db = config.POSTGRES_DB
    checks.append(('POSTGRES_DB', expected_db, actual_db, expected_db == actual_db))
    
    # 4. BOT_TOKEN существует
    has_token = bool(config.BOT_TOKEN and config.BOT_TOKEN != 'your_bot_token_here')
    checks.append(('BOT_TOKEN', 'установлен', 'установлен' if has_token else 'НЕ УСТАНОВЛЕН', has_token))
    
    # 5. OPENAI_API_KEY существует
    has_openai = bool(config.OPENAI_API_KEY and config.OPENAI_API_KEY != 'your_openai_api_key_here')
    checks.append(('OPENAI_API_KEY', 'установлен', 'установлен' if has_openai else 'НЕ УСТАНОВЛЕН', has_openai))
    
    # Выводим результаты
    all_passed = True
    for check_name, expected, actual, passed in checks:
        status = '✅' if passed else '❌'
        print(f"{status} {check_name:20} | Ожидалось: {expected:20} | Получено: {actual}")
        if not passed:
            all_passed = False
    
    return all_passed


def main():
    """Основная функция"""
    print("🚀 Проверка рефакторинга SoulBot")
    print("Проверяем, что prod и test окружения работают корректно\n")
    
    # Тест 1: Prod окружение
    prod_passed = test_config_load('prod')
    
    # Тест 2: Test окружение  
    test_passed = test_config_load('test')
    
    # Итоги
    print(f"\n{'='*60}")
    print("📊 ИТОГИ:")
    print('='*60)
    print(f"{'✅' if prod_passed else '❌'} Production окружение: {'PASSED' if prod_passed else 'FAILED'}")
    print(f"{'✅' if test_passed else '❌'} Test окружение: {'PASSED' if test_passed else 'FAILED'}")
    
    if prod_passed and test_passed:
        print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Рефакторинг успешен!")
        print("\n✨ Теперь можно:")
        print("   - Запустить prod: ENV=prod python bot.py")
        print("   - Запустить test: ENV=test python bot.py")
        print("   - Или использовать скрипты: ./scripts/run_prod.sh и ./scripts/run_test.sh")
        return 0
    else:
        print("\n⚠️  НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОШЛИ!")
        print("   Проверьте .env.prod и .env.test файлы")
        return 1


if __name__ == '__main__':
    sys.exit(main())


