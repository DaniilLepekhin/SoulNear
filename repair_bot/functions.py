import asyncio
import os
import keyboard as kb
from config import ADMINS
from loader import bot
from aiogram.types import FSInputFile

MAX = 50 * 1024 * 1022  # 49.9mb
BUF = 1 * 1024 * 1024 * 1024  # 1gb


def execute(command):
    try:
        return os.popen(command).read()

    except Exception as e:
        return f'Ошибка: {e}'


async def execute_and_send(command, message):
    try:
        info = execute(command)

        if len(info) > 4096:
            for x in range(0, len(info), 4096):
                await message.answer(info[x:x + 4096], reply_markup=kb.close())
        else:
            await message.answer(info, reply_markup=kb.close())

    except Exception as e:
        await message.answer(str(e), reply_markup=kb.close())


async def send_message_to_admins(text, disable_notification=True):
    for a in ADMINS:
        try:
            asyncio.get_event_loop().create_task(send_message_wrapper(a, text,
                                                                      disable_notification=disable_notification))
        except Exception as e:
            print(e)


async def send_message_wrapper(admin, text, disable_notification=True):
    try:
        await bot.send_message(chat_id=admin, text=text,
                               disable_notification=disable_notification,
                               reply_markup=kb.close())
    except Exception as e:
        # await bot.send_message(chat_id=73744901,
        #                        text=str(e))
        print(e)


async def send_file_wrapper(admin, file, disable_notification=True):
    try:
        await bot.send_document(chat_id=admin,
                                document=FSInputFile(file),
                                disable_notification=disable_notification)
    except Exception as e:
        # await bot.send_message(chat_id=73744901,
        #                        text=str(e))
        print(e)


async def send_file_to_admins(file):
    tasks = []

    if os.stat(file).st_size >= MAX:
        parts = divide_file(file)

        for i in range(1, parts + 1):
            for a in ADMINS:
                await send_file_wrapper(a, file + '.%03d' % i)

        # await asyncio.gather(*tasks)

        for i in range(1, parts + 1):
            os.remove(file + '.%03d' % i)

    else:
        for a in ADMINS:
            tasks.append(send_file_wrapper(a, file))

        await asyncio.gather(*tasks)

    os.remove(file)


async def send_file(chat_id, file, disable_notification=True):
    if os.stat(file).st_size >= MAX:
        parts = divide_file(file)
        tasks = []

        for i in range(1, parts + 1):
            tasks.append(send_file_wrapper(admin=chat_id,
                                           file=file + '.%03d' % i,
                                           disable_notification=disable_notification))
        await asyncio.gather(*tasks)

        for i in range(1, parts + 1):
            os.remove(file + '.%03d' % i)

    else:
        await send_file_wrapper(admin=chat_id,
                                file=file,
                                disable_notification=disable_notification)
    os.remove(file)


def divide_file(file):
    chapters = 1
    uglybuf = ''

    with open(file, 'rb') as src:

        while True:
            tgt = open(file + '.%03d' % chapters, 'wb')
            written = 0

            while written < MAX:

                if len(uglybuf) > 0:
                    tgt.write(uglybuf)

                tgt.write(src.read(min(BUF, MAX - written)))
                written += min(BUF, MAX - written)
                uglybuf = src.read(1)

                if len(uglybuf) == 0:
                    break

            tgt.close()

            if len(uglybuf) == 0:
                break

            chapters += 1

    return chapters
