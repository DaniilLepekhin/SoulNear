#!/bin/bash

# Скрипт для валидации .env файла перед запуском Docker

set -e

ENV=${ENV:-prod}
ENV_FILE=".env.${ENV}"

echo "🔍 Проверка конфигурации: ${ENV_FILE}"

if [ ! -f "${ENV_FILE}" ]; then
    echo "❌ Файл ${ENV_FILE} не найден!"
    echo "💡 Создайте его командой: cp .env.example ${ENV_FILE}"
    exit 1
fi

# Функция проверки переменной
check_var() {
    local var_name=$1
    local var_value=$(grep "^${var_name}=" "${ENV_FILE}" | cut -d '=' -f2-)
    
    if [ -z "${var_value}" ] || [[ "${var_value}" == *"your_"* ]] || [[ "${var_value}" == *"_here"* ]]; then
        echo "❌ ${var_name} не заполнен или содержит placeholder"
        return 1
    else
        echo "✅ ${var_name}"
        return 0
    fi
}

# Обязательные переменные
REQUIRED_VARS=(
    "BOT_TOKEN"
    "OPENAI_API_KEY"
    "POSTGRES_PASSWORD"
)

# Опциональные, но важные переменные
OPTIONAL_VARS=(
    "HELPER_ID"
    "SOULSLEEP_ID"
    "POSTGRES_DB"
)

echo ""
echo "📋 Обязательные переменные:"
ERRORS=0

for var in "${REQUIRED_VARS[@]}"; do
    if ! check_var "$var"; then
        ((ERRORS++))
    fi
done

echo ""
echo "📋 Опциональные переменные:"

for var in "${OPTIONAL_VARS[@]}"; do
    check_var "$var" || true
done

echo ""

if [ $ERRORS -gt 0 ]; then
    echo "❌ Найдено $ERRORS ошибок. Заполните все обязательные переменные!"
    echo "💡 Отредактируйте файл: nano ${ENV_FILE}"
    exit 1
else
    echo "✅ Все обязательные переменные заполнены!"
    echo "🚀 Можно запускать: make up"
    exit 0
fi

