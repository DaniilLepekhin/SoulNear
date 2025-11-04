"""Utility script to ensure Level 2 system prompt stays within token limits."""
import asyncio
import sys
import types
from dataclasses import dataclass
from typing import List
from unittest.mock import AsyncMock, Mock, patch


try:  # pragma: no cover - защитный импорт
    import openai  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - окружение без openai
    class _DummyAsyncOpenAI:  # pylint: disable=too-few-public-methods
        def __init__(self, *args, **kwargs):  # noqa: D401 - лаконичный стаб
            pass

    dummy_openai = types.ModuleType("openai")
    dummy_openai.AsyncOpenAI = _DummyAsyncOpenAI

    dummy_openai_types = types.ModuleType("openai.types")
    dummy_openai_types.chat = types.ModuleType("openai.types.chat")
    dummy_openai_types.chat.ChatCompletion = object

    sys.modules["openai"] = dummy_openai
    sys.modules["openai.types"] = dummy_openai_types
    sys.modules["openai.types.chat"] = dummy_openai_types.chat


def ensure_stubbed_dependencies() -> None:
    """Создаёт заглушки для внешних модулей, которых нет в тестовом окружении."""

    if "config" not in sys.modules:
        dummy_config = types.ModuleType("config")
        dummy_config.OPENAI_API_KEY = "test-openai-key"
        dummy_config.BOT_TOKEN = "test-bot-token"
        dummy_config.POSTGRES_DB = "test-db"
        dummy_config.POSTGRES_PASSWORD = "password"
        dummy_config.ENV = "test"

        feature_flags = {
            "USE_CHAT_COMPLETION": True,
            "ENABLE_PATTERN_ANALYSIS": True,
            "ENABLE_STYLE_SETTINGS": True,
        }

        def _is_feature_enabled(name: str) -> bool:
            return feature_flags.get(name, False)

        dummy_config.is_feature_enabled = _is_feature_enabled  # type: ignore[attr-defined]
        sys.modules["config"] = dummy_config

    # Пакет database.repository и его подмодули
    if "database" not in sys.modules:
        sys.modules["database"] = types.ModuleType("database")

    if "database.repository" not in sys.modules:
        repository_module = types.ModuleType("database.repository")
        sys.modules["database.repository"] = repository_module
    else:
        repository_module = sys.modules["database.repository"]

    def _ensure_repo_module(name: str) -> types.ModuleType:
        module_name = f"database.repository.{name}"
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            module = types.ModuleType(module_name)
            sys.modules[module_name] = module
        setattr(repository_module, name, module)
        return module

    _ensure_repo_module("user_profile")
    _ensure_repo_module("conversation_history")
    _ensure_repo_module("user")
    _ensure_repo_module("statistic_day")


MAX_WORD_COUNT = 1800
MAX_CHAR_COUNT = 12000


@dataclass
class MockPattern:
    id: str
    type: str
    title: str
    description: str
    evidence: List[str]
    occurrences: int
    confidence: float
    tags: List[str]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "occurrences": self.occurrences,
            "confidence": self.confidence,
            "tags": self.tags,
            "embedding": [0.0] * 4,  # короткий заглушечный вектор
        }


def build_mock_profile() -> Mock:
    profile = Mock()
    profile.tone_style = "formal"
    profile.personality = "mentor"
    profile.message_length = "brief"

    patterns = [
        MockPattern(
            id=f"pattern-{index}",
            type=pattern_type,
            title=title,
            description=description,
            evidence=evidence,
            occurrences=occurrences,
            confidence=0.82 + index * 0.02,
            tags=tags,
        ).to_dict()
        for index, (pattern_type, title, description, evidence, occurrences, tags) in enumerate(
            [
                (
                    "emotional",
                    "Imposter Syndrome",
                    "Feels like success is undeserved even with strong evidence.",
                    [
                        "Я недостаточно хорош для этой работы",
                        "Я обманщик, скоро все поймут что я ничего не знаю",
                        "Другие разработчики намного лучше меня",
                    ],
                    7,
                    ["self-doubt", "work"],
                ),
                (
                    "behavioral",
                    "Perfectionism Freeze",
                    "Delays tasks unless the plan feels flawless, leading to missed deadlines.",
                    [
                        "Не могу начать, потому что код должен быть идеальным",
                        "Лучше не делать совсем чем сделать плохо",
                        "Переписываю один и тот же код по 10 раз",
                    ],
                    9,
                    ["perfectionism", "productivity"],
                ),
                (
                    "cognitive",
                    "Social Anxiety in Team",
                    "Avoids communication in the team due to fear of judgement.",
                    [
                        "Боюсь задавать вопросы в слаке, подумают что я тупой",
                        "На стендапе молчу, хотя есть проблемы",
                        "Избегаю видеозвонков с командой",
                    ],
                    6,
                    ["anxiety", "communication"],
                ),
                (
                    "behavioral",
                    "Productivity Doomscrolling",
                    "Escapes into phone scrolling when tasks feel overwhelming.",
                    [
                        "Сижу в телефоне вместо работы",
                        "Откладываю задачи до последнего",
                        "Проваливаюсь в соцсети вместо кода",
                    ],
                    5,
                    ["avoidance", "habits"],
                ),
                (
                    "emotional",
                    "Fear Driven Perfectionism",
                    "High fear of failure pushes constant self-criticism and stalls progress.",
                    [
                        "Я опять всё испортил",
                        "Должен был сделать лучше",
                        "Меня скоро уволят",
                    ],
                    8,
                    ["fear", "perfectionism"],
                ),
            ]
        )
    ]

    profile.patterns = {"patterns": patterns}
    profile.insights = {
        "insights": [
            {
                "id": "insight-1",
                "title": "Перфекционизм блокирует действия",
                "description": "Ожидание безупречного результата приводит к прокрастинации и избеганию задач.",
                "impact": "high",
                "recommendations": [
                    "Начинай с маленьких шагов по 10 минут",
                    "Фокусируйся на результате, а не на идеальности",
                ],
                "derived_from": ["pattern-0", "pattern-1"],
                "priority": "high",
            }
        ]
    }

    profile.emotional_state = {
        "current_mood": "anxious",
        "stress_level": "high",
        "energy_level": "low",
        "mood_history": [
            {"date": "2025-10-28", "mood": "anxious", "triggers": ["дедлайн", "сравнение"]},
            {"date": "2025-10-27", "mood": "slightly_down", "triggers": ["ошибки", "сон"]},
        ],
    }

    profile.learning_preferences = {
        "works_well": [
            "конкретные чек-листы",
            "анализ прошлых ситуаций",
            "поддерживающие формулировки",
        ],
        "doesnt_work": ["общие советы", "слишком длинные сообщения"],
    }

    profile.preferences = {
        "custom_instructions": "Всегда напоминай о прогрессе и достижениях за последнюю неделю.",
    }

    return profile


def build_mock_recent_messages() -> List[dict]:
    return [
        {"role": "assistant", "content": "Понимаю, как это выматывает."},
        {
            "role": "user",
            "content": "Сегодня снова не могу заставить себя работать. Что со мной не так?",
        },
        {"role": "assistant", "content": "Давай посмотрим, что помогало раньше."},
        {
            "role": "user",
            "content": "Боюсь задавать вопросы в слаке, подумают что я тупой.",
        },
        {
            "role": "user",
            "content": "Переписываю один и тот же код по 10 раз, он всё равно кажется мне ужасным.",
        },
        {
            "role": "user",
            "content": "Лучше не делать совсем чем сделать плохо, тогда хоть не стыдно.",
        },
    ]


async def run_check() -> int:
    ensure_stubbed_dependencies()

    from bot.services import openai_service

    mock_profile = build_mock_profile()

    with patch.object(openai_service, "user_profile") as mock_user_profile, \
        patch.object(openai_service, "db_user") as mock_db_user, \
        patch.object(openai_service, "conversation_history") as mock_conversation_history:

        mock_user_profile.get_or_create = AsyncMock(return_value=mock_profile)

        mock_user = Mock()
        mock_user.real_name = "Тестовый Пользователь"
        mock_user.age = 29
        mock_user.gender = True
        mock_db_user.get = AsyncMock(return_value=mock_user)

        mock_conversation_history.get_context = AsyncMock(return_value=build_mock_recent_messages())

        system_prompt = await openai_service.build_system_prompt(user_id=42, assistant_type="helper")

    word_count = len(system_prompt.split())
    char_count = len(system_prompt)

    if word_count <= MAX_WORD_COUNT and char_count <= MAX_CHAR_COUNT:
        print(
            f"✓ OK – system prompt length is within limits (words={word_count}, chars={char_count})"
        )
        return 0

    print(
        f"⚠️ FAIL – system prompt too large (words={word_count}, chars={char_count})"
    )
    return 1


def main() -> None:
    exit_code = asyncio.run(run_check())
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()


