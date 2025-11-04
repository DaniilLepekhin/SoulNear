#!/bin/bash
# Запуск продакшн бота

set -e

echo "🚀 Запуск Soul Bot (PRODUCTION)"

cd "$(dirname "$0")/../soul_bot"

# Проверяем наличие .env.prod
if [ ! -f ".env.prod" ]; then
    echo "❌ Файл .env.prod не найден!"
    echo "Скопируй .env.example -> .env.prod и заполни токены"
    exit 1
fi

# Активируем виртуальное окружение (если есть)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Запуск с продакшн конфигом
export ENV=prod
python bot.py


