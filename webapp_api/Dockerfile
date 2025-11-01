# Dockerfile for SoulNear WebApp API
FROM python:3.11-slim

WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код API
COPY . .

# Expose порт
EXPOSE 8888

# Запускаем Quart приложение
CMD ["python", "app.py"]

