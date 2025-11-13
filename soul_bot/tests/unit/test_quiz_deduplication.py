"""
Тесты для дедупликации паттернов в quiz analyzer
"""
import pytest
from bot.services.quiz_service.analyzer import (
    _deduplicate_patterns,
    _pattern_signature,
    _normalize_signature_value,
)


def test_normalize_signature_value():
    """Проверка нормализации значений для сигнатуры"""
    assert _normalize_signature_value("  Тест  Строка  ") == "тест строка"
    assert _normalize_signature_value("") == ""
    assert _normalize_signature_value(None) == ""
    assert _normalize_signature_value("Много    пробелов   здесь") == "много пробелов здесь"


def test_pattern_signature():
    """Проверка генерации сигнатуры паттерна"""
    pattern1 = {
        "title": "Тревожный баланс",
        "contradiction": "Ты хочешь управлять деньгами, но боишься их тратить.",
        "hidden_dynamic": "Страх потери денег управляет твоими решениями.",
        "blocked_resource": "У тебя есть желание управлять деньгами.",
        "description": "Описание",
        "evidence": ["Цитата 1", "Цитата 2"],
    }
    
    pattern2 = {
        "title": "  ТРЕВОЖНЫЙ  БАЛАНС  ",  # Разные пробелы и регистр
        "contradiction": "Ты хочешь управлять деньгами, но боишься их тратить.",  # То же самое
        "hidden_dynamic": "Страх потери денег управляет твоими решениями.",
        "blocked_resource": "У тебя есть желание управлять деньгами.",
        "description": "Описание",
        "evidence": ["Цитата 1", "Цитата 2"],
    }
    
    sig1 = _pattern_signature(pattern1)
    sig2 = _pattern_signature(pattern2)
    
    # Сигнатуры должны совпадать (нормализация работает)
    assert sig1 == sig2


def test_pattern_signature_different_patterns():
    """Разные паттерны должны иметь разные сигнатуры (по ключевым полям)"""
    pattern1 = {
        "title": "Тревожный баланс",
        "contradiction": "Ты хочешь управлять деньгами, но боишься их тратить.",
        "hidden_dynamic": "Страх потери денег управляет твоими решениями.",
        "blocked_resource": "У тебя есть желание управлять деньгами.",
        "description": "Описание 1",
        "evidence": ["Цитата 1"],
    }
    
    pattern2 = {
        "title": "Работа без отдачи",  # Разный title
        "contradiction": "Ты работаешь много, но не видишь результатов.",  # РАЗНОЕ ключевое поле
        "hidden_dynamic": "Потребность в признании заставляет работать больше.",
        "blocked_resource": "Ты умеешь работать много, но это не приносит удовлетворения.",
        "description": "Описание 2",
        "evidence": ["Цитата 2"],
    }
    
    sig1 = _pattern_signature(pattern1)
    sig2 = _pattern_signature(pattern2)
    
    # Разные ключевые поля -> разные сигнатуры (title игнорируется)
    assert sig1 != sig2


def test_deduplicate_patterns_empty():
    """Дедупликация пустого списка"""
    assert _deduplicate_patterns([]) == []
    assert _deduplicate_patterns(None) == []


def test_deduplicate_patterns_no_duplicates():
    """Дедупликация списка без дубликатов"""
    patterns = [
        {
            "title": "Паттерн 1",
            "contradiction": "Противоречие 1",
            "hidden_dynamic": "Динамика 1",
            "blocked_resource": "Ресурс 1",
            "description": "Описание 1",
            "evidence": ["Цитата 1"],
        },
        {
            "title": "Паттерн 2",
            "contradiction": "Противоречие 2",
            "hidden_dynamic": "Динамика 2",
            "blocked_resource": "Ресурс 2",
            "description": "Описание 2",
            "evidence": ["Цитата 2"],
        },
    ]
    
    result = _deduplicate_patterns(patterns)
    assert len(result) == 2
    assert result == patterns


def test_deduplicate_patterns_with_duplicates():
    """Дедупликация списка с дубликатами (как в примере пользователя)"""
    patterns = [
        {
            "title": "Тревожный баланс",
            "contradiction": "Ты хочешь управлять деньгами, но боишься их тратить.",
            "hidden_dynamic": "Страх потери денег управляет твоими решениями, не позволяя тебе наслаждаться ими.",
            "blocked_resource": "У тебя есть желание управлять деньгами, но страх мешает. Используй его для обдуманных инвестиций.",
            "description": "Описание 1",
            "evidence": ["Ура можно расслабиться"],
        },
        {
            "title": "Работа без отдачи",
            "contradiction": "Ты работаешь много, но не видишь результатов и часто тревожишься о деньгах.",
            "hidden_dynamic": "Потребность в признании и результатах заставляет тебя работать больше, чем нужно.",
            "blocked_resource": "Ты умеешь работать много, но это не приносит удовлетворения. Перенаправь усилия на то, что дает результат.",
            "description": "Описание 2",
            "evidence": ["Насколько часто ты чувствуешь, что работаешь много, но не видишь результатов?"],
        },
        {
            "title": "Страх потратить",
            "contradiction": "Ты хочешь управлять деньгами, но боишься их тратить.",  # ДУБЛИКАТ первого паттерна
            "hidden_dynamic": "Страх потери денег управляет твоими решениями, не позволяя тебе наслаждаться ими.",  # ДУБЛИКАТ
            "blocked_resource": "У тебя есть желание управлять деньгами, но страх мешает. Используй его для обдуманных инвестиций.",  # ДУБЛИКАТ
            "description": "Описание 3",
            "evidence": ["Как часто ты откладываешь крупные покупки из-за страха потратить деньги?"],
        },
    ]
    
    result = _deduplicate_patterns(patterns)
    
    # Должно остаться 2 паттерна (первый и второй, третий - дубликат первого)
    assert len(result) == 2
    
    # Проверяем что остались правильные паттерны
    titles = [p["title"] for p in result]
    assert "Тревожный баланс" in titles or "Страх потратить" in titles  # Один из них должен быть
    assert "Работа без отдачи" in titles


def test_deduplicate_patterns_invalid_items():
    """Дедупликация с невалидными элементами"""
    patterns = [
        {"title": "Валидный паттерн", "contradiction": "Тест"},
        None,
        "не словарь",
        {"title": "Еще один валидный", "contradiction": "Тест 2"},
    ]
    
    result = _deduplicate_patterns(patterns)
    
    # Должны остаться только валидные словари
    assert len(result) == 2
    assert all(isinstance(p, dict) for p in result)

