import os

for key, value in (
    ("BOT_TOKEN", "123456:TESTTOKEN"),
    ("OPENAI_API_KEY", "test-key"),
    ("POSTGRES_PASSWORD", "test-password"),
    ("POSTGRES_DB", "test-db"),
    ("TEST", "true"),
):
    os.environ.setdefault(key, value)

from bot.handlers.user.profile import _append_contradiction_section, _build_pattern_highlights


def test_build_pattern_highlights_filters_patterns_without_deep_fields():
    patterns = [
        {
            "title": "Imposter Syndrome",
            "contradiction": "Говорит, что все довольны, но сам уверен в провале",
            "hidden_dynamic": "Страх разоблачения",
            "blocked_resource": "Высокая самооценка, направленная против себя",
            "occurrences": 2,
        },
        {
            "title": "Neutral Pattern",
            "occurrences": 1,
        },
    ]

    highlights = _build_pattern_highlights(patterns)

    assert len(highlights) == 1
    assert highlights[0]['title'] == "Imposter Syndrome"
    assert highlights[0]['frequency'] == 2


def test_append_contradiction_section_formats_output():
    base_text = "🧠 <b>Профиль</b>"
    highlights = [
        {
            "title": "Imposter Syndrome",
            "frequency": 1,
            "contradiction": "Хвастается результатами и боится провала",
            "hidden_dynamic": "Страх разоблачения",
            "blocked_resource": "Саморефлексия",
        }
    ]

    rendered = _append_contradiction_section(base_text, highlights)

    assert "🧩 <b>Скрытые противоречия</b>" in rendered
    assert "Imposter Syndrome" in rendered
    assert "🔀" in rendered
    assert "🎭" in rendered
    assert "💎" in rendered


