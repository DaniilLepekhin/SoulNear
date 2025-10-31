import os

for key, value in (
    ("BOT_TOKEN", "123456:TESTTOKEN"),
    ("OPENAI_API_KEY", "test-key"),
    ("POSTGRES_PASSWORD", "test-password"),
    ("POSTGRES_DB", "test-db"),
    ("TEST", "true"),
):
    os.environ.setdefault(key, value)

from bot.services.quiz_service.generator import _pick_branch_question


def test_pick_branch_question_detects_loneliness_pattern():
    contradictions = [
        "User claims to have many friends but feels lonely often. Surface connections only.",
    ]
    previous_answers = [
        {"question_text": "Do you have friends?", "answer_value": "Да, много"},
    ]

    branch = _pick_branch_question(contradictions, previous_answers, category="relationships", question_number=5)

    assert branch is not None
    assert branch["id"].startswith("branch_lonely")
    assert branch["type"] == "open"
    assert "одиночества" in branch["text"].lower()


def test_pick_branch_question_returns_none_before_baseline_phase():
    contradictions = ["Any contradiction"]
    branch = _pick_branch_question(contradictions, [], category="work", question_number=2)

    assert branch is None


