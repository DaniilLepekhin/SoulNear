import asyncio
import os
import logging

from openai import AsyncOpenAI

from bot.loader import bot
from config import OPENAI_API_KEY
import database.repository.user as db_user
import database.repository.statistic_day as db_statistic_day

# Новый сервис с ChatCompletion API
from bot.services import openai_service

client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
)


async def send_error(function, error):
    try:
        await bot.send_message(chat_id=73744901,
                               text=f'⚠️ALARM!⚠️\n'
                                    f'{function} \n\n{error}')
    except:
        pass


async def get_assistant_response(user_id: int,
                                 prompt: str,
                                 assistant: str) -> str | None:
    """
    Получить ответ от ассистента через ChatCompletion API
    
    Args:
        user_id: Telegram ID пользователя
        prompt: Сообщение пользователя
        assistant: Тип ассистента (helper, sleeper, etc.)
        
    Returns:
        Ответ ассистента или None при ошибке
    """
    try:
        return await openai_service.get_chat_completion(
            user_id=user_id,
            message=prompt,
            assistant_type=assistant
        )
    except Exception as e:
        logging.error(f"ChatCompletion API failed: {e}")
        await send_error(function='get_assistant_response', error=e)
        return None


async def generate_audio(voiceover_text, user_id):
    response = await client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=voiceover_text,
    )

    user_dir = f'bot/media/voices/{user_id}/'
    os.makedirs(user_dir, exist_ok=True)

    audio_files = [f for f in os.listdir(user_dir) if f.startswith("audio")]
    audio_numbers = [
        int(f.split('audio')[1].split('.wav')[0]) for f in audio_files if f.endswith(".wav")
    ]

    next_number = max(audio_numbers, default=0) + 1

    output_file = os.path.join(user_dir, f'audio{next_number}.wav')
    response.stream_to_file(output_file)

    logging.info(f"Аудиофайл сохранён: {output_file}")
    return output_file


async def analyse_photo(photo: str) -> str:
    response = await client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text",
                     "text": "Разбери скришот и отправь текст в виде последовательного диалога, "
                             "оформи в виде реплик с указанием участников. Выведи как: 'диалог:[ТЕКСТ ДИАЛОГА]'"},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{photo}",
                    },
                ],
            }
        ],
    )
    return response.output_text
