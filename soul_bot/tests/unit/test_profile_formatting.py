"""Unit tests for profile formatting helpers."""

import os

for key, value in (
    ("BOT_TOKEN", "123456:TESTTOKEN"),
    ("OPENAI_API_KEY", "test-key"),
    ("POSTGRES_PASSWORD", "test-password"),
    ("POSTGRES_DB", "test-db"),
    ("TEST", "true"),
):
    os.environ.setdefault(key, value)

from bot.handlers.user.profile import _clean_profile_for_display


def test_clean_profile_preserves_v2_fields():
    pattern = {
        "type": "behavioral",
        "title": "Imposter Syndrome",
        "description": "Страх разоблачения несмотря на успехи",
        "contradiction": "Говорит, что коллеги ценят, но внутри ждёт провала",
        "hidden_dynamic": "Сомнения защищают от риска разочаровать себя",
        "blocked_resource": "Способность к саморефлексии можно направить в поддержку",
        "evidence": [
            "Запустил фичу, но думаю, что это случайность",
            "Меня скоро разоблачат",
            "Запустил фичу, но думаю, что это случайность",  # дубликат
        ],
        "tags": ["critical", "auto", "pattern", "extra"],
        "confidence": 0.85,
        "occurrences": 3,
        "first_detected": "2025-10-30T10:00:00",
        "last_detected": "2025-10-31T19:00:00",
        "auto_detected": False,
        "detection_score": 12,
    }

    profile_data = {
        "patterns": [pattern],
        "insights": [],
    }

    cleaned = _clean_profile_for_display(profile_data)

    assert "patterns" in cleaned
    assert len(cleaned["patterns"]) == 1
    cleaned_pattern = cleaned["patterns"][0]

    # V2 поля должны сохраниться
    assert cleaned_pattern["contradiction"] == pattern["contradiction"]
    assert cleaned_pattern["hidden_dynamic"] == pattern["hidden_dynamic"]
    assert cleaned_pattern["blocked_resource"] == pattern["blocked_resource"]

    # Evidence сокращается до двух уникальных цитат
    assert cleaned_pattern["evidence"] == pattern["evidence"][:2]

    # Теги ограничиваются тремя значениями
    assert cleaned_pattern["tags"] == ["critical", "auto", "pattern"]

    # Дополнительные технические поля остаются
    assert cleaned_pattern["detection_score"] == pattern["detection_score"]
    assert cleaned_pattern["auto_detected"] is False

