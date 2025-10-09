#!/usr/bin/env python3
"""
Скрипт для миграции аудио файлов из Telegram в S3
"""
import os
import asyncio
import httpx
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv('/home/soulnear_api/.env')

# Telegram Bot
BOT_TOKEN = os.getenv('BOT_TOKEN')

# S3 Configuration
S3_ENDPOINT = 'https://s3.ru1.storage.beget.cloud'
S3_BUCKET = '08b73313bdeb-osnova'
S3_ACCESS_KEY = '9P05IY2460QVK7DVWKQH'
S3_SECRET_KEY = 'V8p2okf0cyscPa9lz5DSrc7DPycFDymseIOJlCXg'
S3_PUBLIC_URL = 'https://storage.daniillepekhin.com'

# Database
from urllib.parse import quote_plus
DB_PASSWORD = quote_plus(os.getenv('POSTGRES_PASSWORD', ''))
DB_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{DB_PASSWORD}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

# Ханг музыка из app.py
HANG_MUSIC = [
    {"name": "Macadamia", "id": "CQACAgIAAxkBAAIaWme6IHocOTKeWabBMRFMAo30j0RxAAIUcQACMpLRSTh0TJb9ws2pNgQ", "duration": "3:47"},
    {"name": "New Horizons", "id": "CQACAgIAAxkBAAIaXGe6IJtFfe3ZnHnTn72SEbEHtJ_kAAIZcQACMpLRSQm3SlOEcP70NgQ", "duration": "2:21"},
    {"name": "Sunny Way", "id": "CQACAgIAAxkBAAIaXme6ILRQFjmomRTaU3S_LweBO4KcAAIbcQACMpLRScrLXVN5ihmENgQ", "duration": "5:23"},
    {"name": "Seven Wonders", "id": "CQACAgIAAxkBAAIaYGe6IMFSka-PeboFTY749cTdqO1YAAIdcQACMpLRSTfG0XkQqWr5NgQ", "duration": "3:05"},
    {"name": "The Flow", "id": "CQACAgIAAxkBAAIaYme6INjiJa78R71Tgilz1cHoVNE5AAIecQACMpLRSZnku-mQlkNgNgQ", "duration": "5:18"},
    {"name": "Immersion", "id": "CQACAgIAAxkBAAIaZGe6IO62dHDYLfZ6ApYx5JAO5IB6AAIfcQACMpLRSU0Hq8D0hVztNgQ", "duration": "3:46"},
    {"name": "Spring", "id": "CQACAgIAAxkBAAIaZme6IPo_U0KLRwhniaCdH6PHbdq1AAIgcQACMpLRSRyrUTuiVBMDNgQ", "duration": "3:32"},
    {"name": "Rainbow", "id": "CQACAgIAAxkBAAIaaGe6IQkaE72Z22xs5phmwjNnD-OfAAIjcQACMpLRSXmo6_o-tdlNNgQ", "duration": "4:33"},
    {"name": "Blissful", "id": "CQACAgIAAxkBAAIaame6IRhI9YHGUNDzGXdyYXjTlOBfAAIlcQACMpLRSdMBcbkGn_SqNgQ", "duration": "5:14"},
    {"name": "Ocean Inside", "id": "CQACAgIAAxkBAAIabGe6IR--hH94dPduMd_xOVWwW9HiAAImcQACMpLRSUS6P8YcBJJWNgQ", "duration": "2:32"},
    {"name": "Gravity", "id": "CQACAgIAAxkBAAIabme6ITnuagYXIOA-x5dEkW1BqOtxAAIqcQACMpLRSXiK8U0F0yHjNgQ", "duration": "3:06"},
    {"name": "Cappadocia", "id": "CQACAgIAAxkBAAIacGe6IU0FqF8GNMKuUAxzCEFcsCSEAAIucQACMpLRSYay1XS2zvn7NgQ", "duration": "4:06"},
    {"name": "Reggae", "id": "CQACAgIAAxkBAAIacme6IWWKZbY-7FQG6aQ3p0QS2LWiAAIxcQACMpLRSYlpu2L73SnvNgQ", "duration": "3:12"},
    {"name": "Macadamia Remix", "id": "CQACAgIAAxkBAAIadGe6IXuMKffmitJKgPE4YjVuCql9AAI0cQACMpLRSXqbQKD9N4c9NgQ", "duration": "4:31"},
    {"name": "Sunny Way Remix", "id": "CQACAgIAAxkBAAIadme6IYc32RhDe3f-n1eaeYAccwj9AAI2cQACMpLRSXwwwGBfYacZNgQ", "duration": "5:12"},
    {"name": "Breath of Spring Remix", "id": "CQACAgIAAxkBAAIaeGe6IY5EARlEtekD_9KAxuK1iEcGAAI3cQACMpLRSVTbvohBGOngNgQ", "duration": "3:31"},
    {"name": "Ocean Inside Remix", "id": "CQACAgIAAxkBAAIaeme6IaGK7nwa_UEJ3HxRIzkwr_NHAAI6cQACMpLRSXm8c2FvvzFSNgQ", "duration": "5:11"},
    {"name": "J. Remix", "id": "CQACAgIAAxkBAAIafGe6Iax5rwOE8jZe_8IIPcRPoSHrAAI8cQACMpLRSd60kiEAAcn2UTYE", "duration": "3:46"},
]

async def download_from_telegram(file_id: str) -> bytes:
    """Скачивает файл из Telegram"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Получаем file_path
        response = await client.get(
            f'https://api.telegram.org/bot{BOT_TOKEN}/getFile',
            params={'file_id': file_id}
        )
        data = response.json()

        if not data.get('ok'):
            raise Exception(f"Failed to get file info: {data}")

        file_path = data['result']['file_path']
        file_url = f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}'

        # Скачиваем файл
        print(f"  Downloading from Telegram: {file_path}")
        response = await client.get(file_url)
        return response.content

def upload_to_s3(file_content: bytes, file_name: str, content_type: str = 'audio/mpeg') -> str:
    """Загружает файл в S3 и возвращает публичный URL"""
    import requests
    from requests_aws4auth import AWS4Auth

    s3_key = f'soulnear/audio/{file_name}'
    print(f"  Uploading to S3: {s3_key}")

    # Используем requests с AWS4Auth для Beget S3
    auth = AWS4Auth(S3_ACCESS_KEY, S3_SECRET_KEY, 'ru-1', 's3')
    url = f'{S3_ENDPOINT}/{S3_BUCKET}/{s3_key}'

    headers = {
        'Content-Type': content_type
    }

    response = requests.put(url, data=file_content, headers=headers, auth=auth)

    if response.status_code not in [200, 201]:
        raise Exception(f"Upload failed: {response.status_code} - {response.text}")

    # Возвращаем публичный URL
    public_url = f'{S3_PUBLIC_URL}/{s3_key}'
    return public_url

def upload_to_s3_video(file_content: bytes, file_name: str) -> str:
    """Загружает видео в S3 и возвращает публичный URL"""
    import requests
    from requests_aws4auth import AWS4Auth

    s3_key = f'soulnear/video/{file_name}'
    print(f"  Uploading to S3: {s3_key}")

    # Используем requests с AWS4Auth для Beget S3
    auth = AWS4Auth(S3_ACCESS_KEY, S3_SECRET_KEY, 'ru-1', 's3')
    url = f'{S3_ENDPOINT}/{S3_BUCKET}/{s3_key}'

    headers = {
        'Content-Type': 'video/mp4'
    }

    response = requests.put(url, data=file_content, headers=headers, auth=auth)

    if response.status_code not in [200, 201]:
        raise Exception(f"Upload failed: {response.status_code} - {response.text}")

    # Возвращаем публичный URL
    public_url = f'{S3_PUBLIC_URL}/{s3_key}'
    return public_url

async def migrate_media_files():
    """Основная функция миграции"""
    print("🚀 Starting media migration to S3...")

    # Подключаемся к БД
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        # Добавляем колонку file_url если её нет
        print("\n📋 Adding file_url column to medias table...")
        try:
            conn.execute(text("ALTER TABLE medias ADD COLUMN file_url TEXT"))
            conn.commit()
            print("  ✅ Column added")
        except Exception as e:
            conn.rollback()  # Откатываем транзакцию
            if 'already exists' in str(e):
                print("  ℹ️  Column already exists")
            else:
                print(f"  ⚠️  Error: {e}")

        # Получаем все медиа файлы (аудио и видео) из БД
        result = conn.execute(text("""
            SELECT id, name, media_id, media_type
            FROM medias
            WHERE media_type IN ('audio', 'video') AND media_id IS NOT NULL
        """))

        media_files = result.fetchall()
        print(f"\n📦 Found {len(media_files)} media files in database")
        print(f"📦 Found {len(HANG_MUSIC)} hang music tracks")
        print(f"📦 Total: {len(media_files) + len(HANG_MUSIC)} files to migrate\n")

        # Миграция файлов из БД
        for idx, row in enumerate(media_files, 1):
            media_id, name, file_id, media_type = row

            print(f"[{idx}/{len(media_files) + len(HANG_MUSIC)}] Processing DB {media_type}: {name}")

            try:
                # Скачиваем из Telegram
                file_content = await download_from_telegram(file_id)

                # Генерируем имя файла
                safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_name = safe_name.replace(' ', '_')

                if media_type == 'video':
                    file_name = f"{media_id}_{safe_name}.mp4"
                    public_url = upload_to_s3_video(file_content, file_name)
                else:
                    file_name = f"{media_id}_{safe_name}.mp3"
                    public_url = upload_to_s3(file_content, file_name)

                # Обновляем БД
                conn.execute(
                    text("UPDATE medias SET file_url = :url WHERE id = :id"),
                    {"url": public_url, "id": media_id}
                )
                conn.commit()

                print(f"  ✅ Success: {public_url}\n")

            except Exception as e:
                print(f"  ❌ Error: {e}\n")
                continue

        # Миграция Ханг музыки
        for idx, track in enumerate(HANG_MUSIC, len(media_files) + 1):
            name = track['name']
            file_id = track['id']

            print(f"[{idx}/{len(media_files) + len(HANG_MUSIC)}] Processing Hang Music: {name}")

            try:
                # Скачиваем из Telegram
                file_content = await download_from_telegram(file_id)

                # Генерируем имя файла
                safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_name = safe_name.replace(' ', '_')
                file_name = f"hang_{safe_name}.mp3"

                # Загружаем в S3
                public_url = upload_to_s3(file_content, file_name)

                print(f"  ✅ Success: {public_url}\n")

                # Сохраняем URL для последующего обновления app.py
                track['s3_url'] = public_url

            except Exception as e:
                print(f"  ❌ Error: {e}\n")
                continue

    # Выводим обновленный массив HANG_MUSIC с S3 URLs
    print("\n" + "="*60)
    print("📝 Updated HANG_MUSIC array (copy to app.py):")
    print("="*60)
    print("HANG_MUSIC = [")
    for track in HANG_MUSIC:
        if 's3_url' in track:
            print(f'    {{"name": "{track["name"]}", "url": "{track["s3_url"]}", "duration": "{track["duration"]}"}},')
    print("]")
    print("="*60)

    print("\n🎉 Migration completed!")

if __name__ == '__main__':
    asyncio.run(migrate_media_files())
