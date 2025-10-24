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
    # ==========================================
    # 🚩 FEATURE FLAG: ChatCompletion API
    # ==========================================
    # Если включен новый API - используем его
    if is_feature_enabled('USE_CHAT_COMPLETION'):
        try:
            return await openai_service.get_chat_completion(
                user_id=user_id,
                message=prompt,
                assistant_type=assistant
            )
        except Exception as e:
            logging.error(f"ChatCompletion API failed, falling back to Assistant API: {e}")
            # Если новый API упал - падаем на старый (fallback)
    
    # ==========================================
    # 📜 СТАРАЯ ЛОГИКА (Assistant API)
    # ==========================================
    user = await db_user.get(user_id=user_id)

    match assistant:
        case 'helper':
            assistant_id = HELPER_ID
        case 'sleeper':
            assistant_id = SOULSLEEP_ID
        case 'relationships':
            assistant_id = RELATIONSHIPS_ID
        case 'money':
            assistant_id = MONEY_ID
        case 'confidence':
            assistant_id = CONFIDENCE_ID
        case 'fears':
            assistant_id = FEARS_ID
    if assistant == 'helper':
        thread_id = user.helper_thread_id if user.helper_thread_id else await new_context(user_id=user_id,
                                                                                          assistant=assistant)
        asyncio.get_event_loop().create_task(db_statistic_day.increment('helper'))

    elif assistant == 'sleeper':
        thread_id = user.sleeper_thread_id if user.sleeper_thread_id else await new_context(user_id=user_id,
                                                                                            assistant=assistant)
        asyncio.get_event_loop().create_task(db_statistic_day.increment('sleeper'))

    else:
        thread_id = user.assistant_thread_id if user.assistant_thread_id else await new_context(user_id=user_id,
                                                                                                assistant=assistant)
        asyncio.get_event_loop().create_task(db_statistic_day.increment('assistant'))

    await client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=[
            {
                "type": "text",
                "text": prompt
            }
        ]
    )

    try:
        run = await client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id,
            model='gpt-4-turbo-preview'
        )

    except Exception as e:
        asyncio.get_event_loop().create_task(db_statistic_day.increment('bad_requests'))
        asyncio.get_event_loop().create_task(send_error(function='get_assistant_response',
                                                        error=e))

        return None

    # Получение сообщений в потоке
    max_attempts = 5
    attempt = 0
    while attempt < max_attempts:
        try:
            while run.status != 'completed':
                if run.status == 'failed':
                    await client.beta.threads.messages.create(
                        thread_id=thread_id,
                        role="user",
                        content=[
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    )
                    run = await client.beta.threads.runs.create(
                        thread_id=thread_id,
                        assistant_id=assistant_id,
                        model='gpt-4-turbo-preview'
                    )
                    attempt += 1
                    if attempt >= max_attempts:
                        asyncio.get_event_loop().create_task(send_error(function='get_assistant_response',
                                                                        error='Достигнут максимальный лимит попыток. Прерывание.'))
                        asyncio.get_event_loop().create_task(db_statistic_day.increment('bad_requests'))
                        return None
                    break
                run = await client.beta.threads.runs.get(run_id=run.id)
            if run.status == 'completed':
                break
        except Exception as e:
            asyncio.get_event_loop().create_task(send_error(function='get_assistant_response',
                                                            error=e))
            asyncio.get_event_loop().create_task(db_statistic_day.increment('bad_requests'))

            return None

    messages = await client.beta.threads.messages.list(thread_id=thread_id)
    messages = messages.data

    assistant_messages = [msg for msg in messages if msg.role == 'assistant']

    if not assistant_messages:
        asyncio.get_event_loop().create_task(db_statistic_day.increment('bad_requests'))
        asyncio.get_event_loop().create_task(send_error(function='get_assistant_response',
                                                        error="Не удалось получить ответ от ассистента."))
        return None

    last_message = assistant_messages[0]
    response_text = last_message.content[0].text.value if isinstance(last_message.content, list) else ""

    asyncio.get_event_loop().create_task(db_statistic_day.increment('good_requests'))

    asyncio.get_event_loop().create_task(db_user.decrement_requests(user_id=user_id, assistant=assistant))

    return response_text.replace('*', '').replace('#', '').strip()


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
