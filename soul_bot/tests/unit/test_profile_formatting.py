"""Unit tests for profile formatting helpers."""

import os
from types import SimpleNamespace

for key, value in (
    ("BOT_TOKEN", "123456:TESTTOKEN"),
    ("OPENAI_API_KEY", "test-key"),
    ("POSTGRES_PASSWORD", "test-password"),
    ("POSTGRES_DB", "test-db"),
    ("TEST", "true"),
):
    os.environ.setdefault(key, value)

from bot.handlers.user.profile import (
    _format_profile_compact,
    _format_patterns_section,
    _shorten,
)


class DummyProfile:
    def __init__(self):
        self.patterns = {
            "patterns": [
                {
                    "title": "Страх уязвимости",
                    "description": "Боитесь показаться настоящим",
                    "contradiction": "Говорите, что готовы быть открытым, но избегаете откровенных разговоров",
                    "hidden_dynamic": "Страх отвержения заставляет держать дистанцию",
                    "blocked_resource": "Умение чувствовать эмоции можно направить на сближение",
                    "evidence": [
                        "Когда партнёр задаёт прямые вопросы, я меняю тему",
                    ],
                    "confidence": 0.82,
                    "occurrences": 3,
                }
            ]
        }
        self.insights = {
            "insights": [
                {
                    "title": "Опора на чужое мнение",
                    "description": "Оценка себя идёт через реакцию других",
                    "recommendations": [
                        "Каждый вечер записывайте 1-2 сильные стороны, которые никто не озвучивал",
                    ],
                }
            ]
        }
        self.emotional_state = {
            "current_mood": "neutral",
            "stress_level": "medium",
            "energy_level": "low",
        }
        self.learning_preferences = {
            "works_well": ["Короткие практики дыхания"],
            "doesnt_work": ["Долгие лекции"],
        }


def test_shorten_truncates_long_text():
    long_text = "слово " * 80
    shortened = _shorten(long_text, limit=60)
    assert len(shortened) <= 60
    assert not shortened.endswith("…")


def test_shorten_stops_on_sentence_boundary():
    text = "Первое предложение заканчивается точкой. Второе предложение тоже длинное и должно быть отброшено."
    shortened = _shorten(text, limit=70)
    assert shortened.endswith('.')
    assert 'Второе предложение' not in shortened


def test_format_patterns_section_includes_evidence_marker():
    patterns = [
        {
            "title": "Страх уязвимости",
            "description": "Боится показать настоящие чувства",
            "contradiction": "Хочет близости, но избегает разговоров",
            "hidden_dynamic": "Страх отвергнутым",
            "blocked_resource": "Умение сочувствовать",
            "evidence": ["Прячу настоящие мысли, чтобы не осуждали"],
            "confidence": 0.9,
        }
    ]

    block = _format_patterns_section(patterns)
    assert "📝" in block
    assert "«Прячу настоящие мысли" in block
    assert "\n\n  🔁" in block


def test_compact_profile_contains_main_sections():
    profile = DummyProfile()
    user = SimpleNamespace(real_name="Анна", age=29)

    text = _format_profile_compact(profile, user)

    assert "🧠 <b>Психологический профиль</b>" in text
    assert "Страх уязвимости" in text
    assert "💡 <b>Инсайты</b>" in text
    assert "😊 <b>Текущее состояние</b>" in text
    assert "\n\n🎓 <b>Что помогает</b>" in text

