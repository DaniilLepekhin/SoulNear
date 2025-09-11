from config import POSTGRES_PASS, BOTS
from functions import *
from loader import dp
import keyboard as kb
from aiogram import types, F
from aiogram.filters import CommandStart, Command


@dp.message(CommandStart())
async def start_message(message: types.Message):
    if message.chat.id in ADMINS:
        await message.answer('Царь во дворца!', reply_markup=kb.main_menu())

        await message.delete()


@dp.message(Command('command'))
async def command_handler(message: types.Message):
    if message.chat.id in ADMINS:
        command = message.text.replace('/command', '')

        await execute_and_send(command, message)


@dp.callback_query(F.data == 'server_reboot')
async def server_reboot(call: types.CallbackQuery):
    await call.message.answer('Точьно?', reply_markup=kb.confirm_('server_reboot'))
    await call.answer()


@dp.callback_query(F.data == 'confirm_server_reboot')
async def server_reboot_confirm(call: types.CallbackQuery):
    await call.message.answer('Сервер перезагружается...', reply_markup=kb.close())
    await call.answer()

    execute('reboot')


@dp.callback_query(F.data == 'server_backup_bd')
async def server_backup_bd(call: types.CallbackQuery):
    await bot.send_chat_action(chat_id=call.message.chat.id, action='upload_document')
    await call.answer()

    execute(f'PGPASSWORD={POSTGRES_PASS} pg_dumpall -U postgres -h localhost --exclude-database postgres -f postgres.sql')

    await send_file(call.message.chat.id, 'postgres.sql')


@dp.callback_query(F.data == 'bots')
async def bots_callback(call: types.CallbackQuery):
    await call.message.answer('🤖 Боты', reply_markup=kb.bots_menu())


@dp.callback_query(F.data.startswith('bot_menu'))
async def bot_menu(call: types.CallbackQuery):
    i = int(call.data.split()[1])

    await call.message.answer(text=f'Имя: {BOTS[i]["name"]}\n'
                                   f'Ссылка: @{BOTS[i]["username"]}\n'
                                   f'Токен: <code>{BOTS[i]["token"]}</code>',
                              reply_markup=kb.bot_menu(i))

    await call.answer()


@dp.callback_query(F.data.startswith('bot_reload'))
async def bot_reload(call: types.CallbackQuery):
    i = int(call.data.split()[1])

    execute(f'systemctl restart {BOTS[i]["daemon_name"]}')

    await call.answer(f'{BOTS[i]["name"]} Перезагружен')


@dp.callback_query(F.data.startswith('bot_logs'))
async def bot_logs(call: types.CallbackQuery):
    i = int(call.data.split()[1])

    logs = execute(f'journalctl --unit={BOTS[i]["daemon_name"]}.service -n 1000 --no-pager')

    fname = f'{BOTS[i]["daemon_name"]}_logs.txt'

    with open(fname, 'w') as file:
        file.write(logs)

    await call.message.answer_document(open(fname, 'rb'))
    os.remove(fname)

    await call.answer()


@dp.callback_query(F.data.startswith('bot_bd'))
async def bot_bd(call: types.CallbackQuery):
    i = int(call.data.split()[1])
    await call.answer()

    if not BOTS[i]['bd_name']:
        return

    await bot.send_chat_action(chat_id=call.message.chat.id, action='upload_document')

    fname = f'{BOTS[i]["bd_name"]}.sql'

    execute(f'PGPASSWORD={POSTGRES_PASS} pg_dump -U postgres -h localhost -f {fname} {BOTS[i]["bd_name"]}')

    await send_file(call.message.chat.id, fname)

@dp.callback_query(F.data.startswith('close'))
async def close(call: types.CallbackQuery):
    await call.message.delete()
