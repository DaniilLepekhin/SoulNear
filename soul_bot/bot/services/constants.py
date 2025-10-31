"""
🎯 Константы для сервисов

Централизованное хранение thresholds, limits, expected patterns и других констант.
Вместо hardcoded значений в коде - единая точка конфигурации.
"""

# ==========================================
# 🎯 PATTERN ANALYSIS
# ==========================================

# Similarity thresholds для embeddings
SIMILARITY_THRESHOLD_DUPLICATE = 0.60  # Для мерджа паттернов (было 0.50 - слишком агрессивно)
SIMILARITY_THRESHOLD_RELATED = 0.55    # Для related_patterns

# Частота анализа
QUICK_ANALYSIS_FREQUENCY = 3   # Каждые N сообщений
DEEP_ANALYSIS_FREQUENCY = 20   # Каждые N сообщений

# Limits
MAX_PATTERNS_PER_USER = 50     # Максимум паттернов в профиле
MAX_EVIDENCE_PER_PATTERN = 10  # Максимум примеров на паттерн
MAX_INSIGHTS = 10              # Максимум инсайтов
MAX_MOOD_HISTORY_DAYS = 30     # История настроения (дней)
MAX_LEARNING_ITEMS = 10        # Works well / doesn't work (каждого)

# Context для анализа
QUICK_ANALYSIS_CONTEXT_SIZE = 15   # Сообщений для quick analysis
DEEP_ANALYSIS_CONTEXT_SIZE = 30    # Сообщений для deep analysis

# Минимальное количество сообщений для анализа
QUICK_ANALYSIS_MIN_MESSAGES = 4   # Минимум для quick analysis
DEEP_ANALYSIS_MIN_MESSAGES = 10   # Минимум для deep analysis

# ==========================================
# 🚨 SAFETY NET THRESHOLDS (Critical Patterns)
# ==========================================

# Burnout detection threshold
BURNOUT_SCORE_THRESHOLD = 6  # Force-add burnout pattern if score >= 6
# Scoring: Critical symptoms (3pts each), Major (2pts), Minor (1pt)
# Example: 15h work + memory loss = 3+3 = 6pts (threshold met)

# Depression detection threshold
DEPRESSION_SCORE_THRESHOLD = 7  # Force-add depression pattern if score >= 7
# Was 9, lowered to 7 for better detection
# Scoring: Critical (4pts each), Major (3pts), Minor (1pt)
# Example: "всё бессмысленно" + "зачем жить" = 4+4 = 8pts (threshold met)

# ==========================================
# 📊 EXPECTED PATTERNS (для промптов)
# ==========================================

EXPECTED_PATTERN_TYPES = {
    'emotional': [
        'Imposter Syndrome',
        'Social Anxiety in Professional Settings',
        'Fear of Failure',
        'Fear of Success',
        'Negative Self-Talk',
        'Catastrophic Thinking'
    ],
    'behavioral': [
        'Perfectionism',
        'Procrastination Through Over-Analysis',
        'Avoidance Behavior',
        'People Pleasing',
        'Overworking as Coping'
    ],
    'cognitive': [
        'All-or-Nothing Thinking',
        'Overgeneralization',
        'Mental Filtering',
        'Discounting the Positive'
    ]
}

# Плоский список всех ожидаемых паттернов
ALL_EXPECTED_PATTERNS = [
    pattern 
    for patterns_list in EXPECTED_PATTERN_TYPES.values() 
    for pattern in patterns_list
]

# ==========================================
# 💬 OPENAI SETTINGS
# ==========================================

# Models
MODEL_CHAT = "gpt-4o"           # Основной чат
MODEL_ANALYSIS = "gpt-4o"       # Анализ паттернов (was gpt-4o-mini, upgraded for V2 depth)
MODEL_EMBEDDING = "text-embedding-3-small"  # Embeddings (1536 dim)

# Temperature
TEMPERATURE_CHAT = 0.7          # Для обычного чата
TEMPERATURE_ANALYSIS = 0.4      # Для анализа (более детерминировано)
TEMPERATURE_QUIZ = 0.5          # Для генерации вопросов

# Token limits
MAX_TOKENS_CHAT = 4096          # Максимум токенов для ответа
MAX_TOKENS_ANALYSIS = 2048      # Для анализа
SYSTEM_PROMPT_TOKEN_LIMIT = 8000  # Лимит на system prompt

# ==========================================
# 🎯 QUIZ SETTINGS
# ==========================================

QUIZ_CATEGORIES = ['relationships', 'money', 'confidence', 'fears', 'work', 'health']
QUIZ_DEFAULT_QUESTIONS_COUNT = 10
QUIZ_MIN_QUESTIONS = 5
QUIZ_MAX_QUESTIONS = 20

# ==========================================
# 📈 CONVERSATION SETTINGS
# ==========================================

MAX_CONVERSATION_HISTORY = 50   # Максимум сообщений в истории (для контекста)
DEFAULT_CONVERSATION_CONTEXT = 10  # По умолчанию берём последние N

# ==========================================
# 🎨 STYLE SETTINGS
# ==========================================

AVAILABLE_TONES = ['friendly', 'formal', 'sarcastic', 'motivating']
AVAILABLE_PERSONALITIES = ['mentor', 'friend', 'coach', 'therapist']
AVAILABLE_LENGTHS = ['ultra_brief', 'brief', 'medium', 'detailed']

# Лимиты слов для length
MESSAGE_LENGTH_LIMITS = {
    'ultra_brief': 30,    # ~20-30 слов
    'brief': 80,          # ~50-80 слов  
    'medium': 150,        # ~100-150 слов
    'detailed': 500       # ~300-500 слов (без лимита практически)
}

# ==========================================
# 🔒 SECURITY & RATE LIMITING
# ==========================================

RATE_LIMIT_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_REQUESTS_PER_HOUR = 1000

# ==========================================
# 📊 LOGGING & MONITORING
# ==========================================

# Levels для разных операций
LOG_LEVEL_CHAT = "INFO"
LOG_LEVEL_ANALYSIS = "DEBUG"
LOG_LEVEL_ERROR = "ERROR"

# ==========================================
# 🚀 PERFORMANCE
# ==========================================

# Cache TTL (seconds)
CACHE_TTL_USER_PROFILE = 300      # 5 минут
CACHE_TTL_CONVERSATION = 60       # 1 минута
CACHE_TTL_SYSTEM_PROMPT_BASE = 3600  # 1 час (базовая часть)

# Batch sizes
BATCH_SIZE_EMBEDDINGS = 10        # Генерация embeddings батчами
BATCH_SIZE_DB_QUERIES = 50        # Batch queries


# ==========================================
# 🎓 HELPER FUNCTIONS
# ==========================================

def get_expected_patterns_by_type(pattern_type: str) -> list[str]:
    """Получить список ожидаемых паттернов по типу"""
    return EXPECTED_PATTERN_TYPES.get(pattern_type, [])


def is_valid_quiz_category(category: str) -> bool:
    """Проверить валидность категории квиза"""
    return category in QUIZ_CATEGORIES


def get_message_length_limit(length_type: str) -> int:
    """Получить лимит слов для типа длины"""
    return MESSAGE_LENGTH_LIMITS.get(length_type, MESSAGE_LENGTH_LIMITS['medium'])

