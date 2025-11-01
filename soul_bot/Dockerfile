# Dockerfile for SoulNear Telegram Bot
FROM python:3.11-slim

# Устанавливаем зависимости системы (для pydub и других либ)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код бота
COPY . .

# Создаем директорию для логов
RUN mkdir -p /app/logs

# Запускаем бота
CMD ["python", "bot.py"]

