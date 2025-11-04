#!/bin/bash
# Запуск тестового бота

set -e

echo "🧪 Запуск Soul Bot (TEST)"

cd "$(dirname "$0")/../soul_bot"

# Проверяем наличие .env.test
if [ ! -f ".env.test" ]; then
    echo "❌ Файл .env.test не найден!"
    echo "Скопируй .env.example -> .env.test и заполни токены"
    exit 1
fi

# Активируем виртуальное окружение (если есть)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Запуск с тест конфигом
export ENV=test
python bot.py


