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

import logging
import re
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

_SENTENCE_BOUNDARY_REGEX = re.compile(r'(?<=[.!?])\s+(?=[A-ZА-ЯЁ])')
_MULTISPACE_REGEX = re.compile(r'[ \t]+')
_LABEL_PATTERN = re.compile(
    r'(?im)^(?P<prefix>[ \t•\-]*)\b(?P<label>'
    r'Важно|Итого|Шаг|Вопрос|Суть|Ресурс|Практика|Наблюдение|Финал|Вывод'
    r')\b\s*:(?P<rest>[^\n]*)'
)
_KEYWORD_PHRASES_MEDIUM = [
    'цикл избегания',
    'скрытый мотив',
    'точка роста',
    'блокирующая установка',
    'опорный ресурс',
    'вектор',
    'паттерн',
    'ресурс',
]
_KEYWORD_PHRASES_DETAILED = _KEYWORD_PHRASES_MEDIUM + ['повторяющаяся петля', 'динамика', 'контраст']
_LEVEL_SETTINGS = {
    'minimal': {'max_words': 45, 'max_sentences': 2},
    'medium': {'max_words': 60, 'max_sentences': 2},
    'detailed': {'max_words': 80, 'max_sentences': 3},
}
_QUESTION_FOCUS_REGEX = re.compile(
    r'\b(что именно|что именно ты|что именно вы|что именно сейчас|что именно|что|как|зачем|почему|когда|куда|где|кто|какой|какая|какое|который)\b',
    flags=re.IGNORECASE
)


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
        logger.debug(f"Formatting: ultra brief ({word_count} words), light formatting")
        return _structure_text(text, level='minimal', word_count=word_count)
    
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
    
    return _structure_text(text, level='minimal', word_count=len(text.split()))


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
    
    formatted = '\n'.join(lines)
    return _structure_text(formatted, level='medium', word_count=len(formatted.split()))


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
    return _structure_text(formatted, level='detailed', word_count=len(formatted.split()))


__all__ = ['format_bot_message']


def _structure_text(text: str, *, level: str, word_count: int | None = None) -> str:
    normalized = _normalize_text(text)
    total_words = word_count if word_count is not None else len(normalized.split())
    
    paragraphs = _split_paragraphs(normalized)
    settings = _LEVEL_SETTINGS.get(level, _LEVEL_SETTINGS['medium'])
    expanded: list[str] = []
    for block in paragraphs:
        expanded.extend(
            _split_long_paragraph(
                block,
                max_words=settings['max_words'],
                max_sentences=settings['max_sentences']
            )
        )
    
    highlighted = [_apply_paragraph_highlights(block, level=level) for block in expanded]
    
    allow_question_focus = level in ('medium', 'detailed') and total_words >= 120
    highlighted = _highlight_final_question(
        highlighted,
        enable_focus=allow_question_focus
    )
    
    return "\n\n".join(part for part in highlighted if part).strip()


def _normalize_text(text: str) -> str:
    cleaned = text.replace('\r\n', '\n').strip()
    cleaned = _MULTISPACE_REGEX.sub(' ', cleaned)
    cleaned = re.sub(r'\n[ \t]+', '\n', cleaned)
    return cleaned


def _split_paragraphs(text: str) -> list[str]:
    raw_blocks = [block.strip() for block in text.split('\n\n') if block.strip()]
    if raw_blocks:
        return raw_blocks
    return [text.strip()] if text.strip() else []


def _split_long_paragraph(
    paragraph: str,
    *,
    max_words: int,
    max_sentences: int
) -> list[str]:
    if not paragraph:
        return []
    
    if _looks_like_list(paragraph):
        return [paragraph.strip()]
    
    sentences = _split_sentences(paragraph)
    if not sentences:
        return [paragraph.strip()]
    
    buckets: list[str] = []
    buffer: list[str] = []
    word_counter = 0
    sentence_counter = 0
    
    for sentence in sentences:
        sentence_words = len(sentence.split())
        buffer.append(sentence)
        word_counter += sentence_words
        sentence_counter += 1
        
        if word_counter >= max_words or sentence_counter >= max_sentences:
            buckets.append(' '.join(buffer).strip())
            buffer = []
            word_counter = 0
            sentence_counter = 0
    
    if buffer:
        buckets.append(' '.join(buffer).strip())
    
    return buckets or [paragraph.strip()]


def _split_sentences(paragraph: str) -> list[str]:
    if not paragraph:
        return []
    sentences = _SENTENCE_BOUNDARY_REGEX.split(paragraph)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def _looks_like_list(paragraph: str) -> bool:
    lines = [line.strip() for line in paragraph.split('\n') if line.strip()]
    if not lines:
        return False
    
    bullet_lines = sum(
        1
        for line in lines
        if re.match(r'^([•\-–—]|(\d+\.))\s', line)
    )
    return bullet_lines >= max(1, len(lines) // 2)


def _apply_paragraph_highlights(paragraph: str, *, level: str) -> str:
    if not paragraph:
        return paragraph
    
    updated = _italicize_quotes(paragraph)
    
    if level in ('medium', 'detailed'):
        updated = _highlight_labels(updated)
        updated = _highlight_keywords(updated, phrases=_KEYWORD_PHRASES_MEDIUM)
    
    if level == 'detailed':
        updated = _highlight_keywords(updated, phrases=_KEYWORD_PHRASES_DETAILED)
    
    return updated


def _italicize_quotes(text: str) -> str:
    text = re.sub(
        r'(?<!<i>)«([^»]+)»(?!</i>)',
        r'<i>«\1»</i>',
        text
    )
    text = re.sub(
        r'(?<!<i>)"([^"]+)"(?!</i>)',
        r'<i>"\1"</i>',
        text
    )
    text = re.sub(
        r"(?<!<i>)'([^']+)'(?!</i>)",
        r"<i>'\1'</i>",
        text
    )
    return text


def _highlight_labels(text: str) -> str:
    def _replace(match: re.Match) -> str:
        prefix = match.group('prefix')
        label = match.group('label')
        rest = match.group('rest')
        if '<b>' in match.group(0):
            return match.group(0)
        return f"{prefix}<b>{label}:</b>{rest}"
    
    return _LABEL_PATTERN.sub(_replace, text)


def _highlight_keywords(text: str, *, phrases: Iterable[str]) -> str:
    updated = text
    for phrase in phrases:
        updated = _bold_phrase(updated, phrase)
    return updated


def _bold_phrase(text: str, phrase: str) -> str:
    if not phrase or not text:
        return text
    
    if re.search(rf'<b>[^<]*{re.escape(phrase)}[^<]*</b>', text, flags=re.IGNORECASE):
        return text
    
    return re.sub(
        rf'(?i)\b({re.escape(phrase)})\b',
        lambda match: f"<b>{match.group(1)}</b>",
        text,
        count=1
    )


def _highlight_final_question(
    paragraphs: list[str],
    *,
    enable_focus: bool
) -> list[str]:
    if not paragraphs:
        return paragraphs
    
    last = paragraphs[-1]
    sentences = _split_sentences(last)
    if not sentences:
        return paragraphs
    
    final_sentence = sentences[-1]
    if not final_sentence.endswith('?'):
        return paragraphs
    
    if not enable_focus:
        return paragraphs
    
    if '<b>' in final_sentence:
        paragraphs[-1] = ' '.join(sentences).strip()
        return paragraphs
    
    focus = _QUESTION_FOCUS_REGEX.search(final_sentence)
    if focus:
        word = focus.group(0)
        sentences[-1] = (
            final_sentence[:focus.start()]
            + f"<b>{word}</b>"
            + final_sentence[focus.end():]
        )
        paragraphs[-1] = ' '.join(sentences).strip()
        return paragraphs
    
    # Fallback: highlight last meaningful word (but not whole sentence)
    tokens = final_sentence.rstrip(' ?').split()
    if len(tokens) >= 2:
        target = tokens[-1]
        if target and '<b>' not in target:
            sentences[-1] = final_sentence.rsplit(target, 1)[0] + f"<b>{target}</b>?"
            paragraphs[-1] = ' '.join(sentences).strip()
    
    return paragraphs

