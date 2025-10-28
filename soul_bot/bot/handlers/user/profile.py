from datetime import datetime
from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.user.start import menu_callback
from bot.keyboards.profile import (
    profile_menu, gender_menu, style_settings_menu,
    tone_menu, personality_menu, length_menu
)
from bot.keyboards.start import back, menu
from bot.loader import dp, bot
import database.repository.user as db_user
import database.repository.user_profile as db_user_profile
from bot.states.states import Update_user_info
from config import is_feature_enabled
from openai import AsyncOpenAI
from config import OPENAI_API_KEY
import json

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# ==========================================
# 🧠 КОМАНДА /MY_PROFILE (STAGE 3)
# ==========================================

def _clean_profile_for_display(profile_data: dict) -> dict:
    """
    Удалить embeddings и сократить данные для GPT форматирования
    
    Embeddings нужны только для similarity checks, не для форматирования!
    Каждый embedding = 1536 чисел = ~7.6KB → после 10 паттернов = 76KB!
    
    Args:
        profile_data: Сырые данные профиля
        
    Returns:
        Очищенные данные (БЕЗ embeddings, сокращённые evidence)
    """
    cleaned = profile_data.copy()
    
    # Очищаем patterns
    if 'patterns' in cleaned and cleaned['patterns']:
        cleaned_patterns = []
        for pattern in cleaned['patterns']:
            clean_pattern = {
                'type': pattern.get('type'),
                'title': pattern.get('title'),
                'description': pattern.get('description'),
                'evidence': pattern.get('evidence', [])[:2],  # Только 2 примера (не все!)
                'tags': pattern.get('tags', [])[:3],  # Топ-3 тега
                'confidence': pattern.get('confidence'),
                'occurrences': pattern.get('occurrences'),
                'first_detected': pattern.get('first_detected'),
                'last_detected': pattern.get('last_detected')
                # ❌ НЕ включаем: embedding, related_patterns (не нужны для display)
            }
            cleaned_patterns.append(clean_pattern)
        cleaned['patterns'] = cleaned_patterns
    
    # Очищаем insights (обычно уже без embeddings, но на всякий случай)
    if 'insights' in cleaned and cleaned['insights']:
        cleaned_insights = []
        for insight in cleaned['insights']:
            clean_insight = {
                'category': insight.get('category'),
                'title': insight.get('title'),
                'description': insight.get('description'),
                'impact': insight.get('impact'),
                'recommendations': insight.get('recommendations', [])[:3],  # Топ-3
                'priority': insight.get('priority')
                # ❌ НЕ включаем: derived_from (ID паттернов - не нужны юзеру)
            }
            cleaned_insights.append(clean_insight)
        cleaned['insights'] = cleaned_insights
    
    return cleaned


async def _format_profile_with_gpt(profile_data: dict) -> str:
    """
    Форматировать профиль через GPT-4 для красивого вывода
    
    Args:
        profile_data: Данные профиля (patterns, insights, mood, etc.)
        
    Returns:
        Красиво отформатированный текст на русском
    """
    prompt = f"""
Ты — дружелюбный ассистент, который помогает пользователю увидеть свой психологический профиль.

Перед тобой данные профиля пользователя в JSON формате. Твоя задача — представить эту информацию 
красиво, понятно и на русском языке.

ДАННЫЕ ПРОФИЛЯ:
{json.dumps(profile_data, ensure_ascii=False, indent=2)}

ИНСТРУКЦИИ:
1. Используй эмодзи для наглядности (🎨 🧠 💡 😊 🎓)
2. Структурируй информацию по блокам
3. Если данных нет — скажи что профиль ещё формируется
4. Будь дружелюбным и воодушевляющим
5. Паттерны и инсайты объясняй простым языком
6. ⚠️ ОБЯЗАТЕЛЬНО: Для каждого паттерна покажи ПРИМЕРЫ из диалогов (поле evidence)!
   Формат: "📝 <i>Примеры из ваших слов:</i>\n    • \"цитата1\"\n    • \"цитата2\""
7. Для настроения используй образные описания
8. Максимум 3000 символов (Telegram лимит)

ФОРМАТ ВЫВОДА:
```
🧠 <b>Ваш психологический профиль</b>

🎨 <b>Стиль общения:</b>
[описание стиля]

🧠 <b>Выявленные паттерны:</b>
- <b>Название паттерна</b> (частота: X)
  Описание паттерна...
  📝 <i>Примеры из ваших слов:</i>
    • "цитата из диалога 1"
    • "цитата из диалога 2"

💡 <b>Инсайты:</b>
[ключевые инсайты с рекомендациями]

😊 <b>Текущее состояние:</b>
[настроение, стресс, энергия]

🎓 <b>Что работает для вас:</b>
[learning preferences]

📊 <b>Статистика:</b>
[количество анализов, последний анализ]
```

Верни ТОЛЬКО отформатированный текст, без дополнительных комментариев.
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Дешевле для форматирования
            messages=[
                {"role": "system", "content": "Ты помогаешь форматировать психологические профили."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        formatted_text = response.choices[0].message.content
        return formatted_text
        
    except Exception as e:
        return f"⚠️ Ошибка форматирования профиля: {e}"


@dp.message(Command('my_profile'))
async def my_profile_command(message: Message):
    """
    Команда /my_profile - показать свой психологический профиль
    
    Форматирует профиль через GPT-4 для красивого отображения
    """
    user_id = message.from_user.id
    
    # Отправляем "печатаю..." пока GPT обрабатывает
    status_msg = await message.answer("🔄 Формирую ваш профиль...")
    
    try:
        # Получаем профиль
        profile = await db_user_profile.get_or_create(user_id)
        user = await db_user.get(user_id)
        
        # Собираем данные для GPT
        profile_data = {
            "style": {
                "tone": profile.tone_style,
                "personality": profile.personality,
                "message_length": profile.message_length
            },
            "patterns": profile.patterns.get('patterns', [])[-5:],  # Последние 5 (было 10)
            "insights": profile.insights.get('insights', [])[-3:],  # Последние 3 (было 5)
            "emotional_state": profile.emotional_state,
            "learning_preferences": profile.learning_preferences,
            "stats": {
                "analysis_count": profile.pattern_analysis_count,
                "last_analysis": profile.last_analysis_at.isoformat() if profile.last_analysis_at else None,
                "created_at": profile.created_at.isoformat()
            },
            "user_info": {
                "name": user.real_name,
                "age": user.age
            }
        }
        
        # ⚠️ FIX: Удаляем embeddings перед отправкой в GPT (экономим ~76KB!)
        cleaned_data = _clean_profile_for_display(profile_data)
        
        # Форматируем через GPT
        formatted_profile = await _format_profile_with_gpt(cleaned_data)
        
        # Удаляем "печатаю..."
        await status_msg.delete()
        
        # Отправляем профиль
        await message.answer(
            text=formatted_profile,
            parse_mode='HTML'
        )
        
    except Exception as e:
        await status_msg.delete()
        await message.answer(
            f"⚠️ Не удалось загрузить профиль: {e}\n\n"
            f"Попробуйте позже или обратитесь в поддержку."
        )


@dp.callback_query(F.data == 'view_psychological_profile')
async def view_psychological_profile_callback(call: CallbackQuery):
    """
    Callback для кнопки "Мой психологический профиль"
    
    Показывает детальный анализ через GPT-4
    """
    user_id = call.from_user.id
    
    # Отправляем "печатаю..." пока GPT обрабатывает
    await call.answer("🔄 Формирую профиль...", show_alert=False)
    
    try:
        # Получаем профиль
        profile = await db_user_profile.get_or_create(user_id)
        user = await db_user.get(user_id)
        
        # Собираем данные для GPT
        profile_data = {
            "style": {
                "tone": profile.tone_style,
                "personality": profile.personality,
                "message_length": profile.message_length
            },
            "patterns": profile.patterns.get('patterns', [])[-5:],  # Последние 5 (было 10)
            "insights": profile.insights.get('insights', [])[-3:],  # Последние 3 (было 5)
            "emotional_state": profile.emotional_state,
            "learning_preferences": profile.learning_preferences,
            "stats": {
                "analysis_count": profile.pattern_analysis_count,
                "last_analysis": profile.last_analysis_at.isoformat() if profile.last_analysis_at else None,
                "created_at": profile.created_at.isoformat()
            },
            "user_info": {
                "name": user.real_name,
                "age": user.age
            }
        }
        
        # ⚠️ FIX: Удаляем embeddings перед отправкой в GPT (экономим ~76KB!)
        cleaned_data = _clean_profile_for_display(profile_data)
        
        # Форматируем через GPT
        formatted_profile = await _format_profile_with_gpt(cleaned_data)
        
        # Удаляем старое сообщение и отправляем профиль
        await call.message.delete()
        await call.message.answer(
            text=formatted_profile,
            parse_mode='HTML'
        )
        
    except Exception as e:
        await call.answer(f"⚠️ Ошибка: {e}", show_alert=True)


@dp.callback_query(F.data == 'profile')
async def profile_callback(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    user = await db_user.get(user_id=user_id)

    sub_date = '❌' if user.sub_date < datetime.now() else f'{user.sub_date}'[:-10]

    text = f'👤 Ваш профиль, <code>{call.from_user.first_name}</code>\n' \
           f'├ Ваш ID: <code>{user_id}</code>\n' \
           f'├ Имя: <code>{user.real_name}</code>\n' \
           f'├ Возраст: <code>{user.age}</code>\n' \
           f'├ Пол: <code>{"Мужской" if user.gender else "Женский"}</code>\n'

    if user.sub_date > datetime.now():
        text += f'└ Подписка до: <code>{sub_date}</code>\n\n'
    else:
        text += (f'├ Ассистент: <code>{user.helper_requests}</code>\n'
                 f'├ Сонник: <code>{user.sleeper_requests}</code>\n'
                 f'├ Анализ личности: <code>{user.assistant_requests}</code>\n'
                 f'└ Подписка до: <code>{sub_date}</code>\n\n')

    text += f'+3 дня подписки за приведенного друга: <code>https://t.me/SoulnearBot?start={user_id}</code>'
    try:
        await call.message.delete()
        await call.message.answer(text=text,
                                  reply_markup=profile_menu)

    except:
        await call.answer()


@dp.callback_query(F.data == 'update_user_info')
async def update_user_info_start(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        await call.answer()

    await state.set_state(Update_user_info.real_name)

    m = await call.message.answer(text='Введите ваше настоящее имя: ',
                                  reply_markup=back)

    await state.update_data(is_profile=True,
                            message_id=m.message_id)


@dp.message(Update_user_info.real_name)
async def update_user_real_name(message: Message, state: FSMContext):
    real_name = message.text

    await message.delete()

    if len(real_name) > 32:
        return

    data = await state.get_data()

    await bot.delete_message(chat_id=message.chat.id,
                             message_id=data['message_id'])

    m = await message.answer(text='Сколько тебе полных лет? ',
                             reply_markup=back)

    await state.update_data(real_name=real_name,
                            message_id=m.message_id)

    await state.set_state(Update_user_info.age)


@dp.message(Update_user_info.age)
async def update_user_age(message: Message, state: FSMContext):
    age = int(message.text)
    await message.delete()

    if age < 0 or age > 100:
        return

    data = await state.get_data()

    await bot.delete_message(chat_id=message.chat.id,
                             message_id=data['message_id'])

    await state.update_data(age=age)
    await message.answer(text='Твой пол?',
                         reply_markup=gender_menu)


@dp.callback_query(F.data.startswith('gender'))
async def update_user_gender(call: CallbackQuery, state: FSMContext):
    gender = bool(int(call.data.split()[1]))
    data = await state.get_data()

    await db_user.update_info(user_id=call.from_user.id,
                              real_name=data['real_name'],
                              age=data['age'],
                              gender=gender)
    
    # ⚠️ FIX: Очищаем state ПЕРЕД menu_callback, чтобы избежать race condition
    await state.clear()
    
    if data['is_profile']:
        await profile_callback(call, state)
    else:
        await menu_callback(call, state)


# ==========================================
# 🎨 НАСТРОЙКИ СТИЛЯ (Stage 2)
# ==========================================

@dp.callback_query(F.data == 'style_settings')
async def style_settings_callback(call: CallbackQuery, state: FSMContext):
    """Показать меню настроек стиля"""
    if not is_feature_enabled('ENABLE_STYLE_SETTINGS'):
        await call.answer("⚠️ Настройки стиля временно недоступны", show_alert=True)
        return
    
    user_id = call.from_user.id
    profile = await db_user_profile.get_or_create(user_id)
    
    # Маппинг для красивого отображения
    tone_map = {
        'formal': '🎩 Формальный',
        'friendly': '😊 Дружелюбный',
        'sarcastic': '😏 Ироничный',
        'motivating': '🔥 Мотивирующий'
    }
    
    personality_map = {
        'mentor': '🧙‍♂️ Мудрый наставник',
        'friend': '👥 Поддерживающий друг',
        'coach': '💪 Строгий коуч'
    }
    
    length_map = {
        'brief': '⚡ Кратко',
        'medium': '📝 Средне',
        'detailed': '📚 Подробно'
    }
    
    text = (
        f'🎨 <b>Настройки стиля общения</b>\n\n'
        f'Текущие настройки:\n'
        f'├ Тон: <code>{tone_map.get(profile.tone_style, profile.tone_style)}</code>\n'
        f'├ Личность: <code>{personality_map.get(profile.personality, profile.personality)}</code>\n'
        f'└ Длина ответов: <code>{length_map.get(profile.message_length, profile.message_length)}</code>\n\n'
        f'💡 <i>Изменения применяются сразу ко всем ассистентам</i>'
    )
    
    try:
        await call.message.delete()
        await call.message.answer(text=text, reply_markup=style_settings_menu)
    except:
        await call.answer()


@dp.callback_query(F.data == 'change_tone')
async def change_tone_callback(call: CallbackQuery):
    """Показать меню выбора тона"""
    text = (
        '🎭 <b>Выбери тон общения:</b>\n\n'
        '🎩 <b>Формальный</b> - профессиональный и деловой\n'
        '😊 <b>Дружелюбный</b> - тёплый и поддерживающий\n'
        '😏 <b>Ироничный</b> - с лёгким сарказмом\n'
        '🔥 <b>Мотивирующий</b> - вдохновляющий и энергичный'
    )
    
    try:
        await call.message.edit_text(text=text, reply_markup=tone_menu)
    except:
        await call.answer()


@dp.callback_query(F.data.startswith('tone_'))
async def set_tone_callback(call: CallbackQuery):
    """Установить выбранный тон"""
    tone = call.data.replace('tone_', '')
    user_id = call.from_user.id
    
    await db_user_profile.update_style(user_id, tone_style=tone)
    
    tone_names = {
        'formal': 'Формальный',
        'friendly': 'Дружелюбный',
        'sarcastic': 'Ироничный',
        'motivating': 'Мотивирующий'
    }
    
    await call.answer(f"✅ Тон изменён на {tone_names.get(tone, tone)}", show_alert=True)
    await style_settings_callback(call, None)


@dp.callback_query(F.data == 'change_personality')
async def change_personality_callback(call: CallbackQuery):
    """Показать меню выбора личности"""
    text = (
        '👤 <b>Выбери личность ассистента:</b>\n\n'
        '🧙‍♂️ <b>Мудрый наставник</b> - делится опытом и мудростью\n'
        '👥 <b>Поддерживающий друг</b> - всегда рядом и понимает\n'
        '💪 <b>Строгий коуч</b> - фокус на результатах и действиях'
    )
    
    try:
        await call.message.edit_text(text=text, reply_markup=personality_menu)
    except:
        await call.answer()


@dp.callback_query(F.data.startswith('personality_'))
async def set_personality_callback(call: CallbackQuery):
    """Установить выбранную личность"""
    personality = call.data.replace('personality_', '')
    user_id = call.from_user.id
    
    await db_user_profile.update_style(user_id, personality=personality)
    
    personality_names = {
        'mentor': 'Мудрый наставник',
        'friend': 'Поддерживающий друг',
        'coach': 'Строгий коуч'
    }
    
    await call.answer(f"✅ Личность изменена на {personality_names.get(personality, personality)}", show_alert=True)
    await style_settings_callback(call, None)


@dp.callback_query(F.data == 'change_length')
async def change_length_callback(call: CallbackQuery):
    """Показать меню выбора длины ответов"""
    text = (
        '📏 <b>Выбери длину ответов:</b>\n\n'
        '⚡ <b>Кратко</b> - 1-2 коротких абзаца\n'
        '📝 <b>Средне</b> - 3-4 структурированных абзаца\n'
        '📚 <b>Подробно</b> - 5-7 абзацев с примерами'
    )
    
    try:
        await call.message.edit_text(text=text, reply_markup=length_menu)
    except:
        await call.answer()


@dp.callback_query(F.data.startswith('length_'))
async def set_length_callback(call: CallbackQuery):
    """Установить выбранную длину"""
    length = call.data.replace('length_', '')
    user_id = call.from_user.id
    
    await db_user_profile.update_style(user_id, message_length=length)
    
    length_names = {
        'ultra_brief': 'Очень коротко (2-3 предложения)',
        'brief': 'Кратко (1-2 абзаца)',
        'medium': 'Средне (3-4 абзаца)',
        'detailed': 'Подробно (5-7 абзацев)'
    }
    
    await call.answer(f"✅ Длина ответов изменена на: {length_names.get(length, length)}", show_alert=True)
    await style_settings_callback(call, None)
