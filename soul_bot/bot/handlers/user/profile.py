from datetime import datetime
import html
import json

from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.user.start import menu_callback
from bot.keyboards.profile import (
    profile_menu, gender_menu, style_settings_menu,
    tone_menu, personality_menu, length_menu,
    build_style_settings_menu_v2
)
from bot.keyboards.start import back, menu
from bot.loader import dp, bot
import database.repository.user as db_user
import database.repository.user_profile as db_user_profile
from bot.states.states import Update_user_info
from config import is_feature_enabled
from openai import AsyncOpenAI
from config import OPENAI_API_KEY

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Telegram message length limit
MAX_MESSAGE_LENGTH = 4096


# ==========================================
# 🧠 КОМАНДА /MY_PROFILE (STAGE 3)
# ==========================================

async def _send_long_message(message: Message, text: str, parse_mode: str = 'HTML'):
    """
    Отправка длинного сообщения, разбивая его на части если нужно.
    
    Telegram имеет лимит 4096 символов на сообщение.
    Если текст длиннее - разбиваем на части по разделителям (двойной перевод строки).
    
    Args:
        message: Исходное сообщение для ответа
        text: Текст для отправки
        parse_mode: Режим парсинга (HTML, Markdown)
    """
    if len(text) <= MAX_MESSAGE_LENGTH:
        await message.answer(text, parse_mode=parse_mode)
        return
    
    # Разбиваем по двойным переводам строки (параграфы)
    parts = text.split('\n\n')
    current_part = ""
    part_number = 1
    total_parts = (len(text) // MAX_MESSAGE_LENGTH) + 1
    
    for paragraph in parts:
        # Если добавление параграфа превысит лимит - отправляем текущую часть
        if len(current_part) + len(paragraph) + 2 > MAX_MESSAGE_LENGTH:
            if current_part:
                header = f"📄 <b>Часть {part_number}/{total_parts}</b>\n\n" if part_number > 1 or total_parts > 1 else ""
                await message.answer(header + current_part, parse_mode=parse_mode)
                part_number += 1
                current_part = ""
        
        # Добавляем параграф к текущей части
        if current_part:
            current_part += "\n\n" + paragraph
        else:
            current_part = paragraph
    
    # Отправляем остаток
    if current_part:
        header = f"📄 <b>Часть {part_number}/{total_parts}</b>\n\n" if part_number > 1 or total_parts > 1 else ""
        await message.answer(header + current_part, parse_mode=parse_mode)

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
        allowed_keys = {
            'type',
            'title',
            'description',
            'tags',
            'confidence',
            'occurrences',
            'first_detected',
            'last_detected',
            'contradiction',
            'hidden_dynamic',
            'blocked_resource',
            'auto_detected',
            'detection_score'
        }
        for pattern in cleaned['patterns']:
            seen_evidence = set()
            unique_evidence = []
            for raw_quote in pattern.get('evidence', []):
                if not raw_quote:
                    continue
                normalized = " ".join(raw_quote.strip().split())
                key = normalized.lower()
                if key in seen_evidence:
                    continue
                seen_evidence.add(key)
                unique_evidence.append(normalized)
            clean_pattern = {key: pattern.get(key) for key in allowed_keys if pattern.get(key) is not None}
            clean_pattern['evidence'] = unique_evidence[:2]  # Только 2 уникальных примера
            clean_pattern['tags'] = pattern.get('tags', [])[:3]  # Топ-3 тега
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


def _build_pattern_highlights(patterns: list[dict]) -> list[dict]:
    """Сформировать список паттернов с глубинными полями для отображения"""
    highlights: list[dict] = []
    for pattern in patterns or []:
        contradiction = pattern.get('contradiction')
        hidden_dynamic = pattern.get('hidden_dynamic')
        blocked_resource = pattern.get('blocked_resource')

        if not any([contradiction, hidden_dynamic, blocked_resource]):
            continue

        highlights.append(
            {
                'title': pattern.get('title', 'Pattern'),
                'frequency': pattern.get('occurrences'),
                'contradiction': contradiction,
                'hidden_dynamic': hidden_dynamic,
                'blocked_resource': blocked_resource,
            }
        )

    return highlights


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
1. Используй HTML-форматирование: заголовки через <b>, пояснения через <i>, списки с символом •.
2. Структурируй информацию по блокам и добавляй эмодзи (🎨 🧠 💡 😊 🎓) в заголовки.
3. Если данных нет — честно напиши, что профиль ещё формируется.
4. **ВАЖНО**: Тон живой, простой, как будто друг рассказывает. Без академических терминов (избегай слов типа "интроспекция", "экзистенциальный", "предусмотрительность"). Вместо них используй обычные слова: "смотришь внутрь себя", "вопрос смысла жизни", "умение планировать".
5. Для каждого паттерна обязательно показывай поля:
   • <b>Описание</b> — кратко, простыми словами, с фокусом на ощущениях пользователя.
   • <b>🔀 Противоречие</b> — из поля contradiction (перефразируй простым языком).
   • <b>🎭 Скрытая динамика</b> — из поля hidden_dynamic (объясни как будто другу).
   • <b>💎 Заблокированный ресурс</b> — из поля blocked_resource (покажи потенциал человека).
   • 📝 <i>Примеры из ваших слов:</i> + маркированный список цитат (макс 2 штуки).
6. Используй массив "pattern_highlights" (если есть) как список ключевых противоречий — упомяни каждый.
7. Подчеркивай важные мысли жирным, выделяй ключевые слова курсивом, делай текст легко сканируемым.
8. Для эмоционального состояния используй образные описания и списки.
9. Общая длина — до 2500 символов (чтобы точно влезло в Telegram).

ФОРМАТ ВЫВОДА:
```
🧠 <b>Ваш психологический профиль</b>

🎨 <b>Стиль общения</b>
• <b>Тон:</b> ...
• <b>Личность:</b> ...
• <b>Длина ответов:</b> ...

🧠 <b>Выявленные паттерны</b>
- <b>Название паттерна</b> (частота: X)
  <i>Короткое описание...</i>
  <b>🔀 Противоречие:</b> ...
  <b>🎭 Скрытая динамика:</b> ...
  <b>💎 Заблокированный ресурс:</b> ...
  📝 <i>Примеры из ваших слов:</i>
    • "цитата 1"
    • "цитата 2"

💡 <b>Инсайты</b>
- <b>Заголовок</b>
  <i>Ключевая мысль, почему это важно.</i>

😊 <b>Текущее состояние</b>
• <b>Настроение:</b> ...
• <b>Стресс:</b> ...
• <b>Энергия:</b> ...

🎓 <b>Что помогает</b>
- Работает: ...
- Не работает: ...

📊 <b>Статистика</b>
• Анализов: ...
• Последний анализ: ...
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

        pattern_highlights = _build_pattern_highlights(profile_data["patterns"])
        profile_data["pattern_highlights"] = pattern_highlights
        
        # ⚠️ FIX: Удаляем embeddings перед отправкой в GPT (экономим ~76KB!)
        cleaned_data = _clean_profile_for_display(profile_data)
        cleaned_data["pattern_highlights"] = pattern_highlights
        
        # Форматируем через GPT (V2 поля уже включены, дублировать не нужно)
        formatted_profile = await _format_profile_with_gpt(cleaned_data)
        
        # Удаляем "печатаю..." (с защитой от ошибки если уже удалено)
        try:
            await status_msg.delete()
        except Exception:
            pass  # Игнорируем если сообщение уже удалено
        
        # Отправляем профиль (разбиваем если слишком длинный)
        await _send_long_message(message, formatted_profile)
        
    except Exception as e:
        try:
            await status_msg.delete()
        except Exception:
            pass
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

        pattern_highlights = _build_pattern_highlights(profile_data["patterns"])
        profile_data["pattern_highlights"] = pattern_highlights
        
        # ⚠️ FIX: Удаляем embeddings перед отправкой в GPT (экономим ~76KB!)
        cleaned_data = _clean_profile_for_display(profile_data)
        cleaned_data["pattern_highlights"] = pattern_highlights
        
        # Форматируем через GPT (V2 поля уже включены, дублировать не нужно)
        formatted_profile = await _format_profile_with_gpt(cleaned_data)
        
        # Удаляем старое сообщение и отправляем профиль (с разбивкой если длинный)
        try:
            await call.message.delete()
        except Exception:
            pass
        
        await _send_long_message(call.message, formatted_profile)
        
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
    """Показать меню настроек стиля (UNIFIED V2)"""
    if not is_feature_enabled('ENABLE_STYLE_SETTINGS'):
        await call.answer("⚠️ Настройки стиля временно недоступны", show_alert=True)
        return
    
    user_id = call.from_user.id
    profile = await db_user_profile.get_or_create(user_id)
    
    # Используем новое unified меню (всё на одном экране)
    keyboard = build_style_settings_menu_v2(
        current_tone=profile.tone_style,
        current_personality=profile.personality,
        current_length=profile.message_length
    )
    
    text = (
        f'🎨 <b>Настройки стиля общения</b>\n\n'
        f'Выбери параметры ниже 👇\n'
        f'Текущие отмечены галочкой ✓\n\n'
        f'💡 <i>Изменения применяются моментально</i>'
    )
    
    try:
        await call.message.delete()
        await call.message.answer(text=text, reply_markup=keyboard)
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
        'coach': 'Строгий коуч',
        'therapist': 'Терапевт'
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


# ==========================================
# 🚀 UNIFIED STYLE HANDLER (V2)
# ==========================================

@dp.callback_query(F.data.startswith('style_'))
async def unified_style_handler(call: CallbackQuery):
    """
    Универсальный handler для нового формата style_*
    
    Формат callback_data: style_{category}_{value}
    Примеры: style_tone_friendly, style_personality_mentor, style_length_medium
    """
    parts = call.data.split('_', 2)  # style, category, value
    if len(parts) != 3:
        await call.answer("❌ Ошибка формата", show_alert=True)
        return
    
    _, category, value = parts
    user_id = call.from_user.id
    
    # Обновляем профиль в зависимости от категории
    if category == 'tone':
        await db_user_profile.update_style(user_id, tone_style=value)
        names = {
            'formal': 'Формальный 🎩',
            'friendly': 'Дружелюбный 😊',
            'sarcastic': 'Ироничный 😏',
            'motivating': 'Мотивирующий 🔥'
        }
        message = f"Тон: {names.get(value, value)}"
    
    elif category == 'personality':
        await db_user_profile.update_style(user_id, personality=value)
        names = {
            'mentor': 'Наставник 🧙',
            'friend': 'Друг 👥',
            'coach': 'Коуч 💪',
            'therapist': 'Терапевт 🧘'
        }
        message = f"Личность: {names.get(value, value)}"
    
    elif category == 'length':
        await db_user_profile.update_style(user_id, message_length=value)
        names = {
            'ultra_brief': '⚡⚡',
            'brief': '⚡',
            'medium': '📝',
            'detailed': '📚'
        }
        message = f"Длина: {names.get(value, value)}"
    
    else:
        await call.answer("❌ Неизвестная категория", show_alert=True)
        return
    
    # Обновляем меню (перерисовываем с новыми галочками)
    profile = await db_user_profile.get_or_create(user_id)
    keyboard = build_style_settings_menu_v2(
        current_tone=profile.tone_style,
        current_personality=profile.personality,
        current_length=profile.message_length
    )
    
    try:
        await call.message.edit_reply_markup(reply_markup=keyboard)
        await call.answer(f"✅ {message}", show_alert=False)
    except:
        await call.answer(f"✅ {message}", show_alert=True)


@dp.callback_query(F.data == 'noop')
async def noop_handler(call: CallbackQuery):
    """Handler для кнопок-разделителей (noop = no operation)"""
    await call.answer()


# ==========================================
# ⚡ QUICK SWITCH PRESETS
# ==========================================

@dp.callback_query(F.data == 'style_presets')
async def style_presets_callback(call: CallbackQuery):
    """Показать меню быстрых пресетов"""
    if not is_feature_enabled('ENABLE_STYLE_SETTINGS'):
        await call.answer("⚠️ Настройки стиля временно недоступны", show_alert=True)
        return
    
    from bot.keyboards.profile import build_style_presets_menu
    
    keyboard = build_style_presets_menu()
    
    text = (
        f'⚡ <b>Быстрые пресеты стиля</b>\n\n'
        f'Выбери готовую комбинацию настроек для быстрого старта!\n\n'
        f'Каждый пресет это комбинация:\n'
        f'• Тон (формальный/дружелюбный/мотивирующий)\n'
        f'• Личность (коуч/друг/терапевт/наставник)\n'
        f'• Длина ответов (кратко/средне/подробно)\n\n'
        f'💡 <i>Изменения применяются моментально</i>'
    )
    
    try:
        await call.message.delete()
        await call.message.answer(text=text, reply_markup=keyboard)
    except:
        await call.answer()


@dp.callback_query(F.data.startswith('preset_'))
async def apply_preset_callback(call: CallbackQuery):
    """Применить пресет стиля"""
    if not is_feature_enabled('ENABLE_STYLE_SETTINGS'):
        await call.answer("⚠️ Настройки стиля временно недоступны", show_alert=True)
        return
    
    from bot.keyboards.profile import STYLE_PRESETS
    
    preset_id = call.data.replace('preset_', '')
    preset = STYLE_PRESETS.get(preset_id)
    
    if not preset:
        await call.answer("❌ Пресет не найден", show_alert=True)
        return
    
    user_id = call.from_user.id
    
    # Применяем все настройки сразу
    await db_user_profile.update_style(
        user_id,
        tone_style=preset['tone'],
        personality=preset['personality'],
        message_length=preset['length']
    )
    
    await call.answer(f"✅ Применён: {preset['name']}", show_alert=False)
    
    # Показываем обновлённое меню с галочкой
    from bot.keyboards.profile import build_style_presets_menu
    keyboard = build_style_presets_menu(current_preset_id=preset_id)
    
    text = (
        f'⚡ <b>Быстрые пресеты стиля</b>\n\n'
        f'✅ <b>Применён:</b> {preset["name"]}\n'
        f'<i>{preset["description"]}</i>\n\n'
        f'Настройки:\n'
        f'• Тон: <code>{preset["tone"]}</code>\n'
        f'• Личность: <code>{preset["personality"]}</code>\n'
        f'• Длина: <code>{preset["length"]}</code>\n\n'
        f'💡 <i>Можешь выбрать другой пресет или перейти к детальным настройкам</i>'
    )
    
    try:
        await call.message.edit_text(text=text, reply_markup=keyboard)
    except:
        await call.answer()
