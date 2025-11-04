import pytest

from bot.services.quiz_service.analyzer import format_results_for_telegram


@pytest.mark.asyncio
async def test_format_results_for_telegram_structure():
    result_text = await format_results_for_telegram(
        {
            "category": "relationships",
            "new_patterns": [
                {
                    "title": "Страх уязвимости",
                    "confidence": 0.82,
                    "contradiction": "Говоришь, что хочешь быть честным, но при серьёзных разговорах делаешь шаг назад и меняешь тему, чтобы не показаться слабым.",
                    "hidden_dynamic": "Избегаешь открываться, потому что боишься, что близость приведёт к отказу.",
                    "blocked_resource": "Умение чувствовать тонкие сигналы может помочь строить доверие, если направить его наружу, а не внутрь.",
                    "evidence": [
                        "Стоит мне поделиться чем-то личным, как хочется сменить тему.",
                    ],
                }
            ],
            "recommendations": [
                "На этой неделе выбери один разговор, где скажешь честно, что чувствуешь, не обесценивая себя.",
                "Заметь момент, когда хочешь спрятаться, и назови вслух, что страшно именно потерять контакт.",
            ],
        },
        user_id=42,
    )

    assert "🤍 Я собрал краткий разбор" in result_text
    assert "🧩 <b>1. Страх уязвимости" in result_text
    assert "\n\n🔁" in result_text
    assert "<b>Шаг 1.</b>" in result_text
    assert "🤍 Выбери один шаг" in result_text
    assert "..." not in result_text


@pytest.mark.asyncio
async def test_format_results_for_telegram_limited_length():
    long_sentence = "Это предложение без точки" + " очень" * 100
    text = await format_results_for_telegram(
        {
            "category": "money",
            "new_patterns": [
                {
                    "title": "Контроль над финансовым хаосом",
                    "confidence": 0.9,
                    "contradiction": long_sentence,
                    "hidden_dynamic": long_sentence,
                    "blocked_resource": long_sentence,
                    "evidence": [long_sentence],
                }
            ],
            "recommendations": [long_sentence],
        },
        user_id=99,
    )

    # Проверяем, что финальный текст укладывается в лимиты и не обрывает слова странными символами
    for segment in text.split("\n\n"):
        if segment.strip():
            assert len(segment) <= 600  # заметно короче лимита Telegram
            assert not segment.endswith("…")

