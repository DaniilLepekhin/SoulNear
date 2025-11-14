import base64
import os
import random
import re
import string
from datetime import datetime

from aiogram.fsm.context import FSMContext

import database.repository.user as db_user
from bot.functions.speech import convert_voice, transcribe_audio
from bot.keyboards.premium import sub_menu
from bot.keyboards.start import start
from bot.loader import bot
import uuid
from aiogram.enums import ChatAction
from aiogram.types import Message, FSInputFile
import bot.keyboards.practice as keyboards
import bot.text as texts
from utils.date_helpers import add_months

from bot.functions.ChatGPT import get_assistant_response, generate_audio, analyse_photo
from bot.states.states import Update_user_info
from config import ADMINS


async def send_error(function, error):
    try:
        await bot.send_message(chat_id=73744901,
                               text=f'⚠️ALARM!⚠️\n'
                                    f'{function} \n\n{error}')
    except:
        pass


def generate_string(size=16):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(size))


# Экранирует специальные символы для MarkdownV2
def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Форматирование для MarkdownV2
def format_response_with_headers(res):
    if not res:
        return res

    # Если ответ уже содержит HTML-разметку, не экранируем её повторно
    if any(tag in res for tag in ("<b", "<i", "<u", "<a", "<code", "<pre")):
        return res

    lines = res.split("\n")
    formatted_lines = []

    for line in lines:
        if re.match(r"^\d+\.\s", line) or re.match(r"^- ", line):
            match = re.match(r"^(\d+\.\s[^:—]+)([:—].*)", line)
            if match:
                title = escape_html(match.group(1))
                rest = escape_html(match.group(2))
                formatted_lines.append(f"<b>{title}</b>{rest}")
            else:
                formatted_lines.append(escape_html(line))
        else:
            formatted_lines.append(escape_html(line))

    return "\n".join(formatted_lines)


def percent(*values):
    values = [int(val) if val is not None else 0 for val in values]

    total = sum(values)

    if total == 0:
        return tuple([0] * len(values))

    return tuple(round((val / total) * 100, 2) for val in values)


async def check_user_info(message: Message, state: FSMContext):
    user = await db_user.get(user_id=message.chat.id)

    # ✅ FIX: Check if user exists
    if user is None:
        return False

    if user.real_name is None:
        current_state = await state.get_state()
        if current_state == Update_user_info.real_name.state:
            return False

        await state.update_data(is_profile=False)
        await message.answer(texts.greet,
                             reply_markup=start,
                             disable_web_page_preview=True,
                             parse_mode='HTML')
        return False

    return True


async def check_sub(user_id: int):
    if user_id in ADMINS:
        return True

    user = await db_user.get(user_id=user_id)
    
    # ✅ FIX: Check if user exists
    if user is None:
        return False

    sub = user.sub_date >= datetime.now()

    if not sub:
        await bot.send_message(chat_id=user_id,
                               text=texts.limit_content_text,
                               reply_markup=sub_menu,
                               parse_mode='html')

    return sub


async def check_sub_assistant(user_id: int, assistant: str) -> bool:
    if user_id in ADMINS:
        return True

    user = await db_user.get(user_id=user_id)

    # ✅ FIX: Check if user exists
    if user is None:
        return False

    # ✅ NEW: Check free messages for helper assistant
    if assistant == 'helper' and user.free_messages_count > 0:
        return True

    sub = user.sub_date >= datetime.now()

    if not sub:
        fallback_attr = {
            'helper': 'helper_requests',
            'sleeper': 'sleeper_requests',
            'assistant': 'assistant_requests',
            'relationships': 'assistant_requests',
            'money': 'assistant_requests',
            'confidence': 'assistant_requests',
        }.get(assistant)

        if fallback_attr and getattr(user, fallback_attr, 0) > 0:
            sub = True

    if not sub:
        await bot.send_message(chat_id=user_id,
                               text=texts.limit_assistant_text,
                               reply_markup=sub_menu,
                               parse_mode='html')

    return sub


USERS_QUERY = []


def add_user(user_id: int):
    global USERS_QUERY
    USERS_QUERY.append(user_id)


def remove_user(user_id: int):
    global USERS_QUERY
    try:
        USERS_QUERY.remove(user_id)
    except:
        pass


def is_waiting(user_id: int) -> bool:
    global USERS_QUERY

    if user_id in USERS_QUERY:
        return True

    return False


async def voice_answer(message: Message, assistant: str):
    user_id = message.from_user.id

    if is_waiting(user_id=user_id):
        await message.answer('⏳ Обрабатываю ваш предыдущий запрос. Пожалуйста, подождите.')
        return

    if not await check_sub(user_id=user_id):
        return

    add_user(user_id)
    try:

        await bot.send_chat_action(user_id, action=ChatAction.RECORD_VOICE)

        gen_message = await message.answer(texts.gen_wait)

        filename = str(uuid.uuid4())
        file_name_full = f"./voice/{filename}.ogg"
        file_name_full_converted = f"./ready/{filename}.wav"

        try:
            file_info = await message.bot.get_file(message.voice.file_id)
            await message.bot.download_file(file_info.file_path, file_name_full)
        except Exception as e:
            remove_user(user_id)
            print(f"Ошибка при скачивании файла: {e}")
            await message.answer("Ошибка при скачивании файла. Пожалуйста, попробуйте ещё раз.")
            await gen_message.delete()
            return

        convert_voice(file_name_full, file_name_full_converted)
        text = await transcribe_audio(file_name_full_converted)

        res_text = await get_assistant_response(user_id, text, assistant)
        if not res_text:
            remove_user(user_id)
            return await gen_message.edit_text(
                texts.gen_error,
                reply_markup=keyboards.to_menu
            )

        await bot.send_chat_action(user_id, action=ChatAction.UPLOAD_VOICE)

        res_voice = await generate_audio(res_text, user_id)
        if not res_voice:
            remove_user(user_id)
            return await gen_message.edit_text(
                texts.gen_error,
                reply_markup=keyboards.to_menu
            )
        try:
            await message.answer_voice(FSInputFile(res_voice))
            await gen_message.message.delete()

        except Exception as e:
            remove_user(user_id)
            print(f"Ошибка при скачивании файла: {e}")
            await gen_message.delete()
            return
    except Exception as e:
        print(e)
        remove_user(user_id)
    finally:
        for path in (file_name_full, file_name_full_converted):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


async def text_answer(message: Message, assistant: str):
    user_id = message.from_user.id

    if is_waiting(user_id=user_id):
        await message.answer('⏳ Обрабатываю ваш предыдущий запрос. Пожалуйста, подождите.')
        return

    if not await check_sub_assistant(user_id=user_id, assistant=assistant):
        return

    add_user(user_id)
    try:
        prompt = message.text

        gen_message = await message.answer(texts.gen_wait)
        res = await get_assistant_response(user_id, prompt, assistant)

        if not res:
            remove_user(user_id)
            return await gen_message.edit_text(
                texts.gen_error,
                reply_markup=keyboards.to_menu
            )

        formatted_text = format_response_with_headers(res)

        await gen_message.edit_text(
            text=formatted_text,
            parse_mode="HTML"
        )
    except Exception as e:
        print(e)

    remove_user(user_id)


async def photo_answer(message: Message):
    user_id = message.from_user.id

    if is_waiting(user_id=user_id):
        await message.answer('⏳ Обрабатываю ваш предыдущий запрос. Пожалуйста, подождите.')
        return

    if not await check_sub(user_id=user_id):
        return

    await bot.send_chat_action(user_id, action=ChatAction.TYPING)
    add_user(user_id)
    try:
        photo = message.photo[-1]

        file = await bot.get_file(photo.file_id)

        file_bytes = await bot.download_file(file.file_path)

        file_content = file_bytes.read()

        photo = base64.b64encode(file_content).decode('utf-8')

        photo_text = await analyse_photo(photo)

        # await message.answer(f'{photo_text}')

        prompt = (f'{message.caption}\n'
                  f'{photo_text}')

        gen_message = await message.answer(texts.gen_wait)

        res = await get_assistant_response(user_id, prompt, 'helper')

        if not res:
            remove_user(user_id)
            return await gen_message.edit_text(
                texts.gen_error,
                reply_markup=keyboards.to_menu
            )

        formatted_text = format_response_with_headers(res)

        await gen_message.edit_text(
            text=formatted_text,
            parse_mode="HTML"
        )
    except Exception as e:
        print(e)

    remove_user(user_id)
