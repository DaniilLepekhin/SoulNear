from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

profile_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🛠 Изменить информацию', callback_data='update_user_info')],
    [InlineKeyboardButton(text='🎨 Настройки стиля', callback_data='style_settings')],
    [InlineKeyboardButton(text='💳 Подписка', callback_data='premium')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]
])

gender_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='👩 Женский', callback_data='gender 0')],
    [InlineKeyboardButton(text='🧔‍♂️ Мужской', callback_data='gender 1')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]
])

# ==========================================
# 🎨 МЕНЮ НАСТРОЕК СТИЛЯ (Stage 2)
# ==========================================

style_settings_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🎭 Изменить тон', callback_data='change_tone')],
    [InlineKeyboardButton(text='👤 Изменить личность', callback_data='change_personality')],
    [InlineKeyboardButton(text='📏 Изменить длину ответов', callback_data='change_length')],
    [InlineKeyboardButton(text='↩️ Назад к профилю', callback_data='profile')]
])

# Меню выбора тона
tone_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🎩 Формальный', callback_data='tone_formal')],
    [InlineKeyboardButton(text='😊 Дружелюбный', callback_data='tone_friendly')],
    [InlineKeyboardButton(text='😏 Ироничный', callback_data='tone_sarcastic')],
    [InlineKeyboardButton(text='🔥 Мотивирующий', callback_data='tone_motivating')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='style_settings')]
])

# Меню выбора личности
personality_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧙‍♂️ Мудрый наставник', callback_data='personality_mentor')],
    [InlineKeyboardButton(text='👥 Поддерживающий друг', callback_data='personality_friend')],
    [InlineKeyboardButton(text='💪 Строгий коуч', callback_data='personality_coach')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='style_settings')]
])

# Меню выбора длины ответов
length_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⚡ Кратко', callback_data='length_brief')],
    [InlineKeyboardButton(text='📝 Средне', callback_data='length_medium')],
    [InlineKeyboardButton(text='📚 Подробно', callback_data='length_detailed')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='style_settings')]
])
