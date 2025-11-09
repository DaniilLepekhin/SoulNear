from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

profile_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧠 Мой психологический профиль', callback_data='view_psychological_profile')],
    [InlineKeyboardButton(text='🛠 Изменить информацию', callback_data='update_user_info')],
    [InlineKeyboardButton(text='⚡ Быстрые пресеты стиля', callback_data='style_presets')],
    [InlineKeyboardButton(text='🎨 Настройки стиля (детально)', callback_data='style_settings')],
    [InlineKeyboardButton(text='💳 Подписка', callback_data='premium')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]
])

gender_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='👩 Женский', callback_data='gender 0')],
    [InlineKeyboardButton(text='🧔‍♂️ Мужской', callback_data='gender 1')],
    [InlineKeyboardButton(text='😶 Не важно', callback_data='gender none')],
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
    [InlineKeyboardButton(text='🧘 Терапевт', callback_data='personality_therapist')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='style_settings')]
])

# Меню выбора длины ответов
length_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⚡⚡ Очень коротко (2-3 предложения)', callback_data='length_ultra_brief')],
    [InlineKeyboardButton(text='⚡ Кратко (1-2 абзаца)', callback_data='length_brief')],
    [InlineKeyboardButton(text='📝 Средне (3-4 абзаца)', callback_data='length_medium')],
    [InlineKeyboardButton(text='📚 Подробно (5-7 абзацев)', callback_data='length_detailed')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='style_settings')]
])


# ==========================================
# 🚀 UNIFIED STYLE MENU V2 (все в одном экране)
# ==========================================

def build_style_settings_menu_v2(current_tone: str, current_personality: str, current_length: str):
    """
    Улучшенное меню настроек - ВСЁ в одном экране
    
    Формат callback_data: style_{category}_{value}
    Например: style_tone_friendly, style_personality_mentor
    
    Преимущества:
    - 1 клик вместо 5 для изменения настройки
    - Видны текущие значения (галочки ✓)
    - Не нужно переходить между экранами
    """
    # Тон (inline, в одну строку)
    tone_buttons = [
        InlineKeyboardButton(
            text=f"{'✓ ' if current_tone == 'formal' else ''}🎩",
            callback_data='style_tone_formal'
        ),
        InlineKeyboardButton(
            text=f"{'✓ ' if current_tone == 'friendly' else ''}😊",
            callback_data='style_tone_friendly'
        ),
        InlineKeyboardButton(
            text=f"{'✓ ' if current_tone == 'sarcastic' else ''}😏",
            callback_data='style_tone_sarcastic'
        ),
        InlineKeyboardButton(
            text=f"{'✓ ' if current_tone == 'motivating' else ''}🔥",
            callback_data='style_tone_motivating'
        ),
    ]
    
    # Личность (2 в ряд)
    personality_row1 = [
        InlineKeyboardButton(
            text=f"{'✓ ' if current_personality == 'mentor' else ''}🧙 Наставник",
            callback_data='style_personality_mentor'
        ),
        InlineKeyboardButton(
            text=f"{'✓ ' if current_personality == 'friend' else ''}👥 Друг",
            callback_data='style_personality_friend'
        ),
    ]
    personality_row2 = [
        InlineKeyboardButton(
            text=f"{'✓ ' if current_personality == 'coach' else ''}💪 Коуч",
            callback_data='style_personality_coach'
        ),
        InlineKeyboardButton(
            text=f"{'✓ ' if current_personality == 'therapist' else ''}🧘 Терапевт",
            callback_data='style_personality_therapist'
        ),
    ]
    
    # Длина (2 в ряд)
    length_row1 = [
        InlineKeyboardButton(
            text=f"{'✓ ' if current_length == 'ultra_brief' else ''}⚡⚡",
            callback_data='style_length_ultra_brief'
        ),
        InlineKeyboardButton(
            text=f"{'✓ ' if current_length == 'brief' else ''}⚡",
            callback_data='style_length_brief'
        ),
    ]
    length_row2 = [
        InlineKeyboardButton(
            text=f"{'✓ ' if current_length == 'medium' else ''}📝",
            callback_data='style_length_medium'
        ),
        InlineKeyboardButton(
            text=f"{'✓ ' if current_length == 'detailed' else ''}📚",
            callback_data='style_length_detailed'
        ),
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='━━━ ТОН ━━━', callback_data='noop')],
        tone_buttons,
        [InlineKeyboardButton(text='━━ ЛИЧНОСТЬ ━━', callback_data='noop')],
        personality_row1,
        personality_row2,
        [InlineKeyboardButton(text='━━━ ДЛИНА ━━━', callback_data='noop')],
        length_row1,
        length_row2,
        [InlineKeyboardButton(text='↩️ Назад к профилю', callback_data='profile')]
    ])


# ==========================================
# ⚡ QUICK SWITCH PRESETS (быстрые комбо-настройки)
# ==========================================

STYLE_PRESETS = {
    'coach_brief': {
        'name': '💪 Коуч (кратко)',
        'description': 'Мотивация и действия, без лишних слов',
        'tone': 'motivating',
        'personality': 'coach',
        'length': 'brief'
    },
    'friend_detailed': {
        'name': '👥 Друг (подробно)',
        'description': 'Поддержка и эмпатия, развёрнутые ответы',
        'tone': 'friendly',
        'personality': 'friend',
        'length': 'detailed'
    },
    'therapist_medium': {
        'name': '🧘 Терапевт (средне)',
        'description': 'Деликатно и безоценочно, фокус на чувствах',
        'tone': 'friendly',  # терапевт должен быть дружелюбным, не формальным
        'personality': 'therapist',
        'length': 'medium'
    },
    'mentor_balanced': {
        'name': '🧙 Мудрец (сбалансировано)',
        'description': 'Мудрость и опыт, золотая середина',
        'tone': 'friendly',
        'personality': 'mentor',
        'length': 'medium'
    },
    'quick_support': {
        'name': '⚡ Быстрая поддержка',
        'description': 'Краткая эмпатия и совет',
        'tone': 'friendly',
        'personality': 'friend',
        'length': 'ultra_brief'
    },
    'formal_coach': {
        'name': '🎩 Деловой коуч',
        'description': 'Профессионально и по делу',
        'tone': 'formal',
        'personality': 'coach',
        'length': 'medium'
    }
}


def build_style_presets_menu(current_preset_id: str = None):
    """
    Меню быстрых пресетов стиля
    
    Args:
        current_preset_id: ID текущего пресета (если применён)
        
    Returns:
        Клавиатура с пресетами
    """
    buttons = []
    
    for preset_id, preset in STYLE_PRESETS.items():
        # Добавляем галочку если это текущий пресет
        text = preset['name']
        if current_preset_id == preset_id:
            text = f"✓ {text}"
        
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f'preset_{preset_id}'
            )
        ])
    
    # Кнопки навигации
    buttons.append([
        InlineKeyboardButton(text='⚙️ Детальные настройки', callback_data='style_settings')
    ])
    buttons.append([
        InlineKeyboardButton(text='↩️ Назад к профилю', callback_data='profile')
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
