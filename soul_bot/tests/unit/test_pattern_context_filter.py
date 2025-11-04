from datetime import datetime, timedelta

from bot.services.pattern_context_filter import (
    detect_topic_from_message,
    filter_patterns_by_relevance,
    get_relevant_patterns_for_chat,
    get_relevant_patterns_for_quiz,
)


def _pattern(title: str, **overrides):
    pattern = {
        "title": title,
        "description": overrides.get("description", ""),
        "occurrences": overrides.get("occurrences", 1),
        "confidence": overrides.get("confidence", 0.7),
        "evidence": overrides.get("evidence", []),
        "context_weights": overrides.get("context_weights", {}),
        "primary_context": overrides.get("primary_context"),
        "last_detected": overrides.get("last_detected"),
    }
    if "tags" in overrides:
        pattern["tags"] = overrides["tags"]
    pattern["context_snippets"] = overrides.get("context_snippets", {})
    return pattern


def test_get_relevant_patterns_for_quiz_prefers_matching_topic():
    patterns = [
        _pattern(
            "Fear of Rejection",
            occurrences=5,
            confidence=0.9,
            context_weights={"relationships": 1.0, "money": 0.2},
        ),
        _pattern(
            "Money Avoidance",
            occurrences=2,
            confidence=0.8,
            context_weights={"money": 0.9, "work": 0.5},
        ),
    ]

    result = get_relevant_patterns_for_quiz(patterns, category="money", max_patterns=2)

    assert len(result) == 1
    assert result[0]["title"] == "Money Avoidance"


def test_filter_patterns_by_relevance_respects_freshness():
    fresh = _pattern(
        "Recent Burnout",
        occurrences=3,
        context_weights={"work": 0.9},
        last_detected=datetime.utcnow().isoformat(),
    )
    stale = _pattern(
        "Old Burnout",
        occurrences=7,
        context_weights={"work": 1.0},
        last_detected=(datetime.utcnow() - timedelta(days=180)).isoformat(),
    )

    result = filter_patterns_by_relevance([fresh, stale], current_topic="work")
    assert result[0]["title"] == "Recent Burnout"


def test_detect_topic_from_message_handles_finance_variants():
    topic = detect_topic_from_message("Хочу поднять разговор о зарплатке и бюджете")
    assert topic == "money"


def test_get_relevant_patterns_for_chat_uses_message_keywords():
    patterns = [
        _pattern(
            "Work Perfectionism",
            context_weights={"work": 0.6},
            evidence=["Я снова переписываю отчёт перед начальником"],
            last_detected=datetime.utcnow().isoformat(),
            context_snippets={"work": ["Я переписываю отчёт перед руководителем."]},
        ),
        _pattern(
            "Relationship Anxiety",
            context_weights={"relationships": 0.9},
            evidence=["Боюсь признаться партнёру"],
            last_detected=datetime.utcnow().isoformat(),
            context_snippets={"relationships": ["Боюсь признаться партнёру."]},
        ),
    ]

    message = "Как перестать нервничать перед разговором о повышении с начальником?"
    result = get_relevant_patterns_for_chat(patterns, user_message=message, max_patterns=1)

    assert len(result) == 1
    assert result[0]["title"] == "Work Perfectionism"


def test_chat_skips_cross_topic_without_snippet():
    patterns = [
        _pattern(
            "Relationship Fear",
            context_weights={"relationships": 1.0, "money": 0.3},
            evidence=["Боюсь, что останусь один"],
            context_snippets={"relationships": ["Боюсь, что останусь один."]},
            last_detected=datetime.utcnow().isoformat(),
        ),
        _pattern(
            "Money Flow",
            context_weights={"money": 1.0},
            evidence=["Тревожно смотреть на баланс счёта"],
            context_snippets={"money": ["Тревожно смотреть на баланс счёта." ]},
            last_detected=datetime.utcnow().isoformat(),
        ),
    ]

    message = "Меня душит тревога из-за денег и новых платежей"
    result = get_relevant_patterns_for_chat(
        patterns,
        user_message=message,
        detected_topic="money",
        max_patterns=2,
    )

    titles = [pattern["title"] for pattern in result]
    assert "Money Flow" in titles
    assert "Relationship Fear" not in titles


def test_chat_allows_cross_topic_with_snippet():
    patterns = [
        _pattern(
            "Relationship Fear",
            context_weights={"relationships": 1.0, "money": 0.35},
            evidence=["Когда денег мало, чувствую, что останусь один"],
            context_snippets={
                "relationships": ["Боюсь остаться один"],
                "money": ["Когда денег мало, страх остаться один вспыхивает."],
            },
            last_detected=datetime.utcnow().isoformat(),
        ),
        _pattern(
            "Money Flow",
            context_weights={"money": 1.0},
            evidence=["Тревожно смотреть на баланс счёта"],
            context_snippets={"money": ["Тревожно смотреть на баланс счёта." ]},
            last_detected=datetime.utcnow().isoformat(),
        ),
    ]

    message = "Меня давит нехватка денег для аренды"
    result = get_relevant_patterns_for_chat(
        patterns,
        user_message=message,
        detected_topic="money",
        max_patterns=2,
    )

    titles = [pattern["title"] for pattern in result]
    assert titles[0] == "Money Flow"
    assert "Relationship Fear" in titles

