"""
📝 Adaptive Formatting - адаптивное форматирование ответов бота

Зачем:
- Короткие ответы (< 50 слов) не нужно форматировать - plain text
- Средние (50-100) - минимально (выделяем action verbs)
- Длинные (100-300) - структура (заголовки, списки)
- Очень длинные (300+) - полное форматирование (секции, highlights)

Логика:
- Ultra brief: NO formatting (plain text)
- Brief: minimal (bold action verbs)
- Medium: structured (headers, lists)
- Detailed: full formatting (sections, emojis, quotes)

Учитываем learning_preferences: если пользователь не любит bold/списки → не используем

Автор: AI Agent Team
Создан: 2025-10-31
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def format_bot_message(
    text: str,
    message_length_preference: str,
    learning_preferences: Optional[dict] = None,
    assistant_type: Optional[str] = None
) -> str:
    """
    Адаптивное форматирование ответа бота в зависимости от длины и предпочтений
    
    Args:
        text: Исходный текст от GPT
        message_length_preference: ultra_brief|brief|medium|detailed
        learning_preferences: Что работает/не работает для пользователя
        
    Returns:
        Отформатированный текст (HTML для Telegram)
        
    Examples:
        >>> format_bot_message("Попробуй сделать это.", "ultra_brief", None)
        "Попробуй сделать это."  # No formatting
        
        >>> format_bot_message("Начни с малого. Попробуй выделить 5 минут.", "brief", None)
        "<b>Начни</b> с малого. <b>Попробуй</b> выделить 5 минут."  # Bold verbs
    """
    if not text or not text.strip():
        return text
    
    word_count = len(text.split())
    
    # Для основного чата Soul Near сохраняем свободную форму (без автосписков)
    if assistant_type == 'helper':
        logger.debug("Formatting skipped for helper assistant to preserve free-form tone")
        return text
    
    # Проверяем learning preferences
    if learning_preferences:
        doesnt_work = learning_preferences.get('doesnt_work', [])
        
        # Если пользователь не любит форматирование → возвращаем как есть
        formatting_dislikes = ['списки', 'bold', 'жирный текст', 'formatting', 'emojis']
        if any(dislike.lower() in ' '.join(doesnt_work).lower() for dislike in formatting_dislikes):
            logger.debug("Formatting skipped: user doesn't like formatting")
            return text
    
    # ==========================================
    # ULTRA BRIEF (< 50 words): NO FORMATTING
    # ==========================================
    if word_count < 50:
        logger.debug(f"Formatting: ultra brief ({word_count} words), no formatting")
        return text
    
    # ==========================================
    # BRIEF (50-100 words): MINIMAL FORMATTING
    # ==========================================
    elif word_count < 100:
        logger.debug(f"Formatting: brief ({word_count} words), minimal formatting")
        return _apply_minimal_formatting(text)
    
    # ==========================================
    # MEDIUM (100-300 words): STRUCTURED
    # ==========================================
    elif word_count < 300:
        logger.debug(f"Formatting: medium ({word_count} words), structured formatting")
        return _apply_medium_formatting(text)
    
    # ==========================================
    # DETAILED (300+ words): FULL FORMATTING
    # ==========================================
    else:
        logger.debug(f"Formatting: detailed ({word_count} words), full formatting")
        return _apply_detailed_formatting(text)


def _apply_minimal_formatting(text: str) -> str:
    """
    Brief: выделяем только action verbs (призывы к действию)
    
    Examples:
        "Начни с малого" → "<b>Начни</b> с малого"
        "Попробуй выделить 5 минут" → "<b>Попробуй</b> выделить 5 минут"
    """
    # Список action verbs (призывы к действию)
    action_verbs = [
        'начни', 'сделай', 'попробуй', 'выдели', 'запиши',
        'подумай', 'прочитай', 'напиши', 'спроси', 'обрати',
        'позвони', 'сходи', 'поговори', 'реши', 'выбери',
        'отдохни', 'остановись', 'подожди', 'послушай', 'посмотри'
    ]
    
    # Выделяем только в начале предложения или после переноса
    for verb in action_verbs:
        # Case-insensitive замена
        text = re.sub(
            rf'(^|\n)({verb})\b',
            r'\1<b>\2</b>',
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )
    
    return text


def _apply_medium_formatting(text: str) -> str:
    """
    Medium: структура + списки + выделение ключевых фраз
    """
    lines = text.split('\n')
    result = []
    
    # 1. Конвертируем numbered lists в bullet points
    for line in lines:
        stripped = line.strip()
        
        # Numbered list (1. 2. 3.)
        if re.match(r'^\d+\.\s', stripped):
            line = '  • ' + re.sub(r'^\d+\.\s', '', stripped)
        
        # Dash list (-)
        elif stripped.startswith('- '):
            line = '  • ' + stripped[2:]
        
        result.append(line)
    
    # 2. Выделяем ключевые фразы
    formatted = '\n'.join(result)
    
    # "Важно:", "Совет:", "Рекомендация:" и т.д.
    key_phrases = ['важно', 'совет', 'рекомендация', 'помни', 'обрати внимание', 'заметь']
    for phrase in key_phrases:
        formatted = re.sub(
            rf'\b({phrase})\b:',
            r'<b>\1</b>:',
            formatted,
            flags=re.IGNORECASE
        )
    
    # 3. Выделяем имя пользователя в начале (если есть)
    lines = formatted.split('\n')
    if lines and ',' in lines[0]:
        parts = lines[0].split(',', 1)
        # Если первое слово короткое (имя) → выделяем
        if len(parts[0].split()) == 1 and len(parts[0]) < 15:
            lines[0] = f"<b>{parts[0]}</b>,{parts[1]}"
    
    return '\n'.join(lines)


def _apply_detailed_formatting(text: str) -> str:
    """
    Detailed: секции + полная структура + emojis + цитаты
    """
    # 1. Detect sections by keywords
    sections = {
        'паттерн': '🧠',
        'инсайт': '💡',
        'рекомендац': '📌',
        'примеры': '📝',
        'шаги': '🔢',
        'итого': '✅',
        'важно': '⚠️',
        'помни': '🎯',
        'твой': '💬',
        'анализ': '🔍'
    }
    
    formatted = text
    
    # Добавляем emojis к секциям
    for keyword, emoji in sections.items():
        # Находим строки начинающиеся с keyword (case-insensitive)
        formatted = re.sub(
            rf'^({keyword}.*?):\s*',
            rf'<b>{emoji} \1:</b>\n',
            formatted,
            flags=re.IGNORECASE | re.MULTILINE
        )
    
    # 2. Конвертируем списки
    lines = formatted.split('\n')
    result = []
    
    for line in lines:
        stripped = line.strip()
        
        # Numbered list → bullet
        if re.match(r'^\d+\.\s', stripped):
            line = '  • ' + re.sub(r'^\d+\.\s', '', stripped)
        
        # Dash list → bullet
        elif stripped.startswith('- '):
            line = '  • ' + stripped[2:]
        
        result.append(line)
    
    # 3. Выделяем цитаты (italic)
    formatted = '\n'.join(result)
    
    # "Ты говорил: 'цитата'" → italic для цитаты
    formatted = re.sub(
        r"'([^']+)'",
        r"<i>'\1'</i>",
        formatted
    )
    formatted = re.sub(
        r'"([^"]+)"',
        r'<i>"\1"</i>',
        formatted
    )
    
    # 4. Выделяем ключевые слова
    key_words = ['ОБЯЗАТЕЛЬНО', 'ВАЖНО', 'КРИТИЧНО', 'СРОЧНО']
    for word in key_words:
        formatted = re.sub(
            rf'\b({word})\b',
            r'<b>\1</b>',
            formatted,
            flags=re.IGNORECASE
        )
    
    return formatted


__all__ = ['format_bot_message']

