import asyncio
import os
import logging

from openai import AsyncOpenAI

from bot.loader import bot
from config import OPENAI_API_KEY, HELPER_ID, SOULSLEEP_ID, RELATIONSHIPS_ID, MONEY_ID, CONFIDENCE_ID, FEARS_ID, is_feature_enabled
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
    # ==========================================
    # 🚩 FEATURE FLAG: ChatCompletion API
    # ==========================================
    if is_feature_enabled('USE_CHAT_COMPLETION'):
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
    
    # ==========================================
    # ⚠️ LEGACY: Assistant API (DEPRECATED)
    # ==========================================
    # Если USE_CHAT_COMPLETION=false, используем старый API
    # НО: этот код устарел и будет удалён в будущем
    logging.warning("⚠️ Using deprecated Assistant API. Please enable USE_CHAT_COMPLETION flag.")
    
    user = await db_user.get(user_id=user_id)
    
    # Определяем assistant_id по типу
    assistant_ids = {
        'helper': HELPER_ID,
        'sleeper': SOULSLEEP_ID,
        'relationships': RELATIONSHIPS_ID,
        'money': MONEY_ID,
        'confidence': CONFIDENCE_ID,
        'fears': FEARS_ID
    }
    assistant_id = assistant_ids.get(assistant, HELPER_ID)
    
    # Получаем или создаём thread_id
    if assistant == 'helper':
        thread_id = user.helper_thread_id or await new_context(user_id, assistant)
        asyncio.get_event_loop().create_task(db_statistic_day.increment('helper'))
    elif assistant == 'sleeper':
        thread_id = user.sleeper_thread_id or await new_context(user_id, assistant)
        asyncio.get_event_loop().create_task(db_statistic_day.increment('sleeper'))
    else:
        thread_id = user.assistant_thread_id or await new_context(user_id, assistant)
        asyncio.get_event_loop().create_task(db_statistic_day.increment('assistant'))
    
    try:
        # Отправляем сообщение в thread
        await client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=[{"type": "text", "text": prompt}]
        )
        
        # Запускаем ассистент
        run = await client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id,
            model='gpt-4-turbo-preview'
        )
        
        # Ожидаем завершения (с retry логикой)
        max_attempts = 5
        for attempt in range(max_attempts):
            if run.status == 'completed':
                break
            elif run.status == 'failed':
                logging.warning(f"Run failed, retrying ({attempt + 1}/{max_attempts})...")
                await client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=[{"type": "text", "text": prompt}]
                )
                run = await client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                    model='gpt-4-turbo-preview'
                )
            else:
                await asyncio.sleep(1)
                run = await client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        
        if run.status != 'completed':
            raise Exception(f"Run did not complete after {max_attempts} attempts")
        
        # Получаем ответ
        messages = await client.beta.threads.messages.list(thread_id=thread_id)
        assistant_messages = [msg for msg in messages.data if msg.role == 'assistant']
        
        if not assistant_messages:
            raise Exception("No assistant messages found")
        
        response_text = assistant_messages[0].content[0].text.value
        
        # Статистика
        asyncio.get_event_loop().create_task(db_statistic_day.increment('good_requests'))
        asyncio.get_event_loop().create_task(db_user.decrement_requests(user_id=user_id, assistant=assistant))
        
        return response_text.replace('*', '').replace('#', '').strip()
        
    except Exception as e:
        logging.error(f"Assistant API error: {e}")
        asyncio.get_event_loop().create_task(db_statistic_day.increment('bad_requests'))
        asyncio.get_event_loop().create_task(send_error(function='get_assistant_response', error=e))
        return None


async def new_context(user_id: int, assistant: str) -> str:
    thread = await client.beta.threads.create()
    thread_id = thread.id

    if assistant == 'helper':
        await db_user.update_helper_thread(user_id=user_id, thread_id=thread_id)
        user = await db_user.get(user_id=user_id)

        text = f'Имя пользователя: {user.real_name}\n' \
               f'Возраст: {user.age}\n' \
               f'Пол: {"Мужской" if user.gender else "Женский"}\n' \
               f'Используй эту информацию при общении с пользователем. ' \
               f'На это сообщение не надо отвечать'
        await client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=[
                {
                    "type": "text",
                    "text": text
                }
            ]
        )


    elif assistant == 'sleeper':
        await db_user.update_sleeper_thread(user_id=user_id, thread_id=thread_id)
    else:
        await db_user.update_assistant_thread(user_id=user_id, thread_id=thread_id)

    return thread_id


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
