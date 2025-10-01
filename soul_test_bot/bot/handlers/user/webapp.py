from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from bot.loader import dp
import database.repository.user as db_user


@dp.message(Command('webapp'))
async def webapp_command(message: Message):
    """Handler for /webapp command - opens SoulNear WebApp"""
    user_id = message.from_user.id

    # Create WebApp button
    webapp_url = "https://soulnear.daniillepekhin.com"  # URL where webapp will be hosted

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧘 Открыть SoulNear App",
                    web_app=WebAppInfo(url=webapp_url)
                )
            ],
            [
                InlineKeyboardButton(
                    text="❓ Что такое WebApp?",
                    callback_data="webapp_info"
                )
            ]
        ]
    )

    webapp_text = """
🌟 <b>Добро пожаловать в SoulNear WebApp!</b>

Откройте полнофункциональное приложение прямо в Telegram:

🏠 <b>Главная</b> - отслеживайте свое настроение
🎤 <b>Голосовой ассистент</b> - общайтесь с Soul Near
🧘 <b>Практики</b> - медитации и упражнения
👤 <b>Профиль</b> - ваши достижения

<i>Нажмите кнопку ниже, чтобы запустить приложение</i>
    """

    await message.answer(
        text=webapp_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    # Update user activity
    await db_user.update_active(user_id=user_id)


@dp.callback_query(F.data == 'webapp_info')
async def webapp_info_callback(callback):
    """Provide information about WebApp functionality"""

    info_text = """
❓ <b>Что такое Telegram WebApp?</b>

WebApp - это полноценное веб-приложение, которое работает внутри Telegram:

✅ <b>Удобство</b> - не нужно устанавливать отдельное приложение
✅ <b>Быстрота</b> - мгновенный доступ к функциям
✅ <b>Безопасность</b> - все данные защищены Telegram
✅ <b>Синхронизация</b> - работа связана с вашим аккаунтом

<b>В SoulNear WebApp доступно:</b>
• Интерактивный календарь настроений
• Голосовое общение с ассистентом
• Библиотека медитаций и практик
• Персональная статистика
• Система достижений

<i>Просто нажмите "Открыть SoulNear App" и наслаждайтесь!</i>
    """

    await callback.answer()
    await callback.message.edit_text(
        text=info_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🧘 Открыть SoulNear App",
                        web_app=WebAppInfo(url="https://soulnear.daniillepekhin.com")
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="◀️ Назад",
                        callback_data="webapp_back"
                    )
                ]
            ]
        ),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == 'webapp_back')
async def webapp_back_callback(callback):
    """Go back to main webapp message"""

    webapp_text = """
🌟 <b>Добро пожаловать в SoulNear WebApp!</b>

Откройте полнофункциональное приложение прямо в Telegram:

🏠 <b>Главная</b> - отслеживайте свое настроение
🎤 <b>Голосовой ассистент</b> - общайтесь с Soul Near
🧘 <b>Практики</b> - медитации и упражнения
👤 <b>Профиль</b> - ваши достижения

<i>Нажмите кнопку ниже, чтобы запустить приложение</i>
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧘 Открыть SoulNear App",
                    web_app=WebAppInfo(url="https://soulnear.daniillepekhin.com")
                )
            ],
            [
                InlineKeyboardButton(
                    text="❓ Что такое WebApp?",
                    callback_data="webapp_info"
                )
            ]
        ]
    )

    await callback.answer()
    await callback.message.edit_text(
        text=webapp_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.message(lambda message: message.web_app_data is not None)
async def webapp_data_handler(message: Message):
    """Handle data from WebApp"""
    try:
        # Get data from WebApp
        web_app_data = message.web_app_data.data
        user_id = message.from_user.id

        # Parse JSON data
        import json
        data = json.loads(web_app_data)

        action = data.get("action")
        payload = data.get("data", {})
        timestamp = data.get("timestamp")

        if action == "mood_selected":
            mood = payload.get("mood", "неизвестно")
            await message.answer(
                f"😊 <b>Настроение сохранено!</b>\n\n"
                f"💭 Вы выбрали: {mood}\n"
                f"📅 Время: {timestamp}\n\n"
                f"✨ Отлично! Продолжайте отслеживать свое настроение в SoulNear!",
                parse_mode="HTML"
            )
            
        elif action == "chat_message":
            user_message = payload.get("message", "")
            await message.answer(
                f"💬 <b>Сообщение получено!</b>\n\n"
                f"📝 Ваше сообщение: \"{user_message}\"\n"
                f"🤖 Soul Near готов помочь вам с этим вопросом!\n\n"
                f"💡 Ответ будет сформирован в приложении.",
                parse_mode="HTML"
            )
            
        elif action == "voice_recording_started":
            await message.answer(
                f"🎤 <b>Голосовая запись началась!</b>\n\n"
                f"🗣️ Говорите четко и спокойно\n"
                f"⏱️ Soul Near внимательно слушает...",
                parse_mode="HTML"
            )
            
        elif action == "voice_recording_stopped":
            await message.answer(
                f"✅ <b>Голосовая запись завершена!</b>\n\n"
                f"🔄 Обрабатываем ваше сообщение...\n"
                f"💭 Скоро получите ответ в приложении!",
                parse_mode="HTML"
            )
            
        elif action == "dreams_analysis_opened":
            await message.answer(
                f"🌙 <b>Анализ снов</b>\n\n"
                f"✨ Функция анализа снов скоро будет доступна!\n"
                f"🔮 Soul Near изучает ваши сновидения для лучшего понимания подсознания.",
                parse_mode="HTML"
            )
            
        elif action == "personality_analysis_opened":
            await message.answer(
                f"🧠 <b>Анализ личности</b>\n\n"
                f"🔬 Функция анализа личности в разработке!\n"
                f"📊 Soul Near создаст детальный профиль вашей личности.",
                parse_mode="HTML"
            )
            
        else:
            await message.answer(
                f"✅ <b>Данные получены из WebApp!</b>\n\n"
                f"🎯 Действие: {action}\n"
                f"📊 Данные обрабатываются...\n"
                f"🚀 SoulNear работает для вас!",
                parse_mode="HTML"
            )

        # Update user activity
        await db_user.update_active(user_id=user_id)

    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка обработки данных</b>\n\n"
            f"🔧 Произошла техническая ошибка при обработке данных из приложения.\n"
            f"💡 Попробуйте еще раз или обратитесь в поддержку.\n\n"
            f"📝 Код ошибки: {str(e)[:50]}...",
            parse_mode="HTML"
        )
