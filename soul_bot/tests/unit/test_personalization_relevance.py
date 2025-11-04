"""
Unit tests для context relevance check в персонализации

Тестируем _is_personalization_relevant() - функцию которая определяет
нужно ли применять персонализацию к текущему сообщению пользователя.
"""

import pytest
from bot.services.personalization.engine import _is_personalization_relevant


class TestPersonalizationRelevance:
    """Тесты для context relevance check"""
    
    # ==========================================
    # ❌ FACTUAL QUESTIONS (должны вернуть False)
    # ==========================================
    
    def test_factual_question_weather(self):
        """Фактический вопрос о погоде → персонализация не нужна"""
        message = "Какая погода сегодня?"
        pattern = {"title": "Procrastination", "tags": ["avoidance"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is False, "Factual question о погоде не должен триггерить персонализацию"
    
    def test_factual_question_time(self):
        """Фактический вопрос о времени"""
        message = "Сколько сейчас времени?"
        pattern = {"title": "Anxiety", "tags": ["stress"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is False
    
    def test_factual_question_location(self):
        """Фактический вопрос о месте"""
        message = "Где находится ближайшая аптека?"
        pattern = {"title": "Burnout", "tags": ["exhaustion"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is False
    
    def test_factual_question_definition(self):
        """Вопрос о определении термина"""
        message = "Что такое когнитивная терапия?"
        pattern = {"title": "Depression", "tags": ["sadness"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is False
    
    # ==========================================
    # ✅ FACTUAL QUESTIONS + EMOTIONS (должны вернуть True)
    # ==========================================
    
    def test_factual_question_with_emotion(self):
        """Фактический вопрос + эмоциональный контекст → персонализация нужна"""
        message = "Какая погода? Мне страшно выходить на улицу"
        pattern = {"title": "Social Anxiety", "tags": ["fear", "avoidance"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True, "Вопрос с эмоциями должен триггерить персонализацию"
    
    def test_question_with_feeling(self):
        """Вопрос с глаголом чувств"""
        message = "Почему я чувствую тревогу?"
        pattern = {"title": "Anxiety", "tags": ["worry"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True
    
    # ==========================================
    # ✅ PATTERN KEYWORDS PRESENT (должны вернуть True)
    # ==========================================
    
    def test_pattern_tag_in_message(self):
        """Тег паттерна присутствует в сообщении"""
        message = "Опять прокрастинирую, не могу начать работу"
        pattern = {"title": "Procrastination", "tags": ["procrastination", "avoidance"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True, "Наличие тега паттерна → персонализация релевантна"
    
    def test_pattern_title_in_message(self):
        """Слово из названия паттерна в сообщении"""
        message = "У меня syndrome какой-то, не могу работать"
        pattern = {"title": "Imposter Syndrome", "tags": ["self-doubt"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True, "Слово из названия паттерна → персонализация релевантна"
    
    def test_russian_pattern_tag(self):
        """Русский тег паттерна"""
        message = "Снова выгорание, сил нет"
        pattern = {"title": "Burnout", "tags": ["выгорание", "усталость"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True
    
    # ==========================================
    # ✅ EMOTIONAL CONTENT (должны вернуть True)
    # ==========================================
    
    def test_emotional_feeling_sad(self):
        """Сообщение с эмоцией грусти"""
        message = "Мне так грустно сегодня"
        pattern = {"title": "Depression", "tags": ["low mood"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True, "Эмоциональный контент → персонализация релевантна"
    
    def test_emotional_fear(self):
        """Сообщение со страхом"""
        message = "Я боюсь не справиться с проектом"
        pattern = {"title": "Performance Anxiety", "tags": ["fear"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True
    
    def test_emotional_cannot_do(self):
        """'Не могу' - эмоциональный маркер"""
        message = "Не могу заснуть уже третью ночь"
        pattern = {"title": "Insomnia", "tags": ["sleep issues"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True
    
    def test_emotional_burnout(self):
        """Маркер выгорания"""
        message = "Выгорел полностью, ничего не хочется"
        pattern = {"title": "Burnout", "tags": ["exhaustion"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True
    
    def test_emotional_stress(self):
        """Стресс-маркер"""
        message = "Столько стресса на работе, не выдержу"
        pattern = {"title": "Work Stress", "tags": ["overwhelm"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True
    
    # ==========================================
    # ❌ VERY SHORT MESSAGES (должны вернуть False)
    # ==========================================
    
    def test_very_short_message_2_words(self):
        """Очень короткое сообщение (2 слова)"""
        message = "Как дела"
        pattern = {"title": "Anxiety", "tags": ["worry"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is False, "Короткие сообщения (< 5 слов) → скорее всего не эмоциональные"
    
    def test_very_short_message_3_words(self):
        """Короткое сообщение (3 слова)"""
        message = "Всё нормально спасибо"
        pattern = {"title": "Depression", "tags": ["low mood"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is False
    
    def test_short_message_4_words(self):
        """На границе (4 слова)"""
        message = "Да всё хорошо вроде"
        pattern = {"title": "Anxiety", "tags": ["worry"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is False
    
    # ==========================================
    # ✅ MEDIUM/LONG MESSAGES (default True)
    # ==========================================
    
    def test_medium_message_default(self):
        """Средней длины сообщение без явных маркеров → default True"""
        message = "Сегодня был интересный день на работе"
        pattern = {"title": "Work Stress", "tags": ["job"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True, "Сообщения >= 5 слов без явных маркеров → default True (conservative)"
    
    def test_long_message_no_keywords(self):
        """Длинное сообщение без keywords → тоже True (conservative)"""
        message = "Ходил гулять в парк, было холодно, встретил старого друга и немного поговорили"
        pattern = {"title": "Loneliness", "tags": ["isolation"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True
    
    # ==========================================
    # 🛡️ EDGE CASES
    # ==========================================
    
    def test_empty_message(self):
        """Пустое сообщение"""
        message = ""
        pattern = {"title": "Anxiety", "tags": ["worry"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is False
    
    def test_whitespace_only_message(self):
        """Только пробелы"""
        message = "   "
        pattern = {"title": "Depression", "tags": ["sadness"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is False
    
    def test_empty_pattern(self):
        """Пустой паттерн"""
        message = "Чувствую тревогу"
        pattern = {}
        
        result = _is_personalization_relevant(message, pattern)
        
        # Должен вернуть True т.к. есть эмоциональный контент
        assert result is True
    
    def test_pattern_no_tags_no_title(self):
        """Паттерн без тегов и названия"""
        message = "Какая погода сегодня?"
        pattern = {"tags": [], "title": ""}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is False  # Factual question
    
    def test_none_pattern(self):
        """None вместо паттерна"""
        message = "Чувствую тревогу"
        pattern = None
        
        result = _is_personalization_relevant(message, pattern)
        
        # Должен вернуть True т.к. есть эмоциональный контент "Чувствую"
        # (проверка эмоций идёт ПЕРЕД проверкой паттерна)
        assert result is True
    
    # ==========================================
    # 🧪 COMPLEX CASES
    # ==========================================
    
    def test_question_but_emotional(self):
        """Вопрос, но эмоциональный контекст очевиден"""
        message = "Почему мне так тяжело каждый день?"
        pattern = {"title": "Depression", "tags": ["low mood"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True, "Вопрос с 'тяжело' → эмоциональный контент → True"
    
    def test_mixed_factual_and_pattern_keyword(self):
        """Фактический вопрос + keyword паттерна"""
        message = "Когда пройдёт этот procrastination?"
        pattern = {"title": "Procrastination", "tags": ["procrastination"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        # Должен вернуть True т.к. есть keyword паттерна
        assert result is True
    
    def test_case_insensitive_tags(self):
        """Проверка case-insensitive для тегов"""
        message = "Опять ПРОКРАСТИНАЦИЯ проклятая"
        pattern = {"title": "Procrastination", "tags": ["прокрастинация"]}
        
        result = _is_personalization_relevant(message, pattern)
        
        assert result is True
    
    def test_partial_word_match_in_title(self):
        """Частичное совпадение слова из title"""
        message = "У меня какой-то синдром самозванца наверное"
        pattern = {"title": "Imposter Syndrome", "tags": []}
        
        result = _is_personalization_relevant(message, pattern)
        
        # "syndrome" из "Imposter Syndrome" есть в сообщении
        assert result is True


# ==========================================
# 🎯 INTEGRATION-STYLE TESTS (не полная интеграция, но ближе к реальности)
# ==========================================

class TestPersonalizationRelevanceIntegration:
    """Более реалистичные сценарии"""
    
    def test_real_scenario_weather_question(self):
        """Реальный сценарий: пользователь спрашивает о погоде, есть паттерн прокрастинации"""
        message = "Какая погода сегодня?"
        pattern = {
            "title": "Procrastination",
            "type": "behavioral",
            "tags": ["avoidance", "procrastination"],
            "evidence": ["опять откладываю дела"],
            "occurrences": 5
        }
        
        result = _is_personalization_relevant(message, pattern)
        
        # НЕ должен показывать "ты откладываешь дела 5 раз" для вопроса о погоде
        assert result is False
    
    def test_real_scenario_emotional_about_pattern(self):
        """Реальный сценарий: пользователь говорит об эмоциях, связанных с паттерном"""
        message = "Опять не могу начать работу, чувствую вину"
        pattern = {
            "title": "Procrastination",
            "type": "behavioral",
            "tags": ["avoidance", "procrastination"],
            "evidence": ["откладываю всё на последний момент"],
            "occurrences": 8
        }
        
        result = _is_personalization_relevant(message, pattern)
        
        # Должен показать персонализацию (и "не могу", и tag "procrastination" косвенно)
        assert result is True
    
    def test_real_scenario_short_greeting(self):
        """Реальный сценарий: короткое приветствие"""
        message = "Привет"
        pattern = {
            "title": "Anxiety",
            "tags": ["worry", "stress"]
        }
        
        result = _is_personalization_relevant(message, pattern)
        
        # Короткое сообщение → не персонализируем
        assert result is False
    
    def test_real_scenario_long_story(self):
        """Реальный сценарий: длинный рассказ без явных keywords"""
        message = "Сегодня встретил коллегу в кафе, мы поговорили о новом проекте"
        pattern = {
            "title": "Work-Life Balance Issues",
            "tags": ["overwork", "burnout"]
        }
        
        result = _is_personalization_relevant(message, pattern)
        
        # Длинное сообщение → default True (conservative)
        assert result is True

