#!/bin/bash
# Скрипт для запуска тестов

set -e  # Останавливаться при ошибках

echo "🧪 Запуск тестов Soul Bot..."

# Активируем виртуальное окружение (если есть)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Устанавливаем зависимости для тестов (если нужно)
if [ "$1" == "--install" ]; then
    echo "📦 Установка зависимостей..."
    pip install -r requirements-test.txt
fi

# Типы запуска
case "$1" in
    "unit")
        echo "⚡ Запуск unit тестов..."
        pytest tests/unit/ -v
        ;;
    "integration")
        echo "🔗 Запуск integration тестов..."
        pytest tests/integration/ -v
        ;;
    "smoke")
        echo "💨 Запуск smoke тестов..."
        pytest tests/smoke/ -v -x  # -x = остановиться на первой ошибке
        ;;
    "coverage")
        echo "📊 Запуск с coverage..."
        pytest --cov=bot --cov=database --cov-report=html --cov-report=term
        echo "📁 HTML отчёт: htmlcov/index.html"
        ;;
    "quick")
        echo "⚡ Быстрая проверка (только unit + smoke)..."
        pytest tests/unit/ tests/smoke/ -v
        ;;
    *)
        echo "🎯 Запуск всех тестов..."
        pytest -v
        ;;
esac

echo "✅ Тесты завершены!"

