"""
Тесты для типов вопросов квиза

Проверяем:
1. Генерация разных типов вопросов (text, scale, multiple_choice)
2. Validation logic (mixing enforcement)
3. Normalization logic
"""
import pytest
from unittest.mock import AsyncMock, patch
from soul_bot.bot.services.quiz_service import generator


class TestQuestionTypeValidation:
    """Тесты валидации типов вопросов"""

    @pytest.mark.asyncio
    async def test_validate_forces_type_change_on_3_text_in_row(self):
        """Если последние 2 вопроса = text, должен force другой тип"""
        question = {"type": "text", "text": "Test question", "category": "relationships"}
        previous_answers = [
            {"question_type": "text", "answer_value": "Answer 1"},
            {"question_type": "text", "answer_value": "Answer 2"},
        ]

        regenerated = {
            "id": "mock",
            "text": "Насколько верно утверждение?",
            "type": "scale",
            "options": ["⭕ Никогда", "🟡 Редко", "🟠 Иногда", "🔴 Часто", "🔥 Постоянно"],
            "category": "relationships",
        }

        with patch.object(
            generator,
            "_regenerate_question_with_type",
            new=AsyncMock(return_value=regenerated),
        ) as mock_regen:
            result = await generator._validate_and_fix_question_type(
                question,
                previous_answers,
                category="relationships",
            )

        mock_regen.assert_called_once()
        assert result['type'] == 'scale', "Should force scale when 3 text in a row"
        assert result['options'][0].startswith('⭕'), "Scale options should include emoji"

    @pytest.mark.asyncio
    async def test_validate_allows_text_when_recent_not_all_text(self):
        """Если последние вопросы не все text, text разрешён"""
        question = {"type": "text", "text": "Test question"}
        previous_answers = [
            {"question_type": "scale", "answer_value": "Иногда"},
            {"question_type": "text", "answer_value": "Answer"},
        ]

        with patch.object(
            generator,
            "_regenerate_question_with_type",
            new=AsyncMock(),
        ) as mock_regen:
            result = await generator._validate_and_fix_question_type(
                question,
                previous_answers,
                category="relationships",
            )

        mock_regen.assert_not_called()
        assert result['type'] == 'text', "Should allow text when not 3 in a row"

    @pytest.mark.asyncio
    async def test_validate_skips_when_few_answers(self):
        """Не валидируем если ответов мало (< 2)"""
        question = {"type": "text", "text": "Test question"}
        previous_answers = [
            {"question_type": "text", "answer_value": "Answer 1"}
        ]

        with patch.object(
            generator,
            "_regenerate_question_with_type",
            new=AsyncMock(),
        ) as mock_regen:
            result = await generator._validate_and_fix_question_type(
                question,
                previous_answers,
                category="relationships",
            )

        mock_regen.assert_not_called()
        assert result['type'] == 'text', "Should skip validation when < 2 answers"

    def test_is_open_question_detector(self):
        """Детектор открытых вопросов должен распознавать follow-up формат"""

        assert generator._is_open_question(
            "Если бы ты узнал, что спокойствие — способ избегания, как бы это изменило твои решения?"
        ), "Should detect follow-up open question"

        assert not generator._is_open_question(
            "Как часто ты чувствуешь усталость?"
        ), "Scale-like question should not be considered open"


class TestQuestionNormalization:
    """Тесты нормализации вопросов"""
    
    def test_normalize_converts_open_to_text(self):
        """Тип 'open' должен конвертироваться в 'text'"""
        # Arrange
        questions = [
            {"id": "q1", "text": "Question", "type": "open"}
        ]
        
        # Act
        result = generator._normalize_question_list(questions, "relationships")
        
        # Assert
        assert result[0]['type'] == 'text', "Should convert 'open' to 'text'"
    
    def test_normalize_converts_choice_to_multiple_choice(self):
        """Тип 'choice' должен конвертироваться в 'multiple_choice'"""
        # Arrange
        questions = [
            {"id": "q1", "text": "Question", "type": "choice"}
        ]
        
        # Act
        result = generator._normalize_question_list(questions, "relationships")
        
        # Assert
        assert result[0]['type'] == 'multiple_choice', "Should convert 'choice' to 'multiple_choice'"
    
    def test_normalize_adds_default_scale_options(self):
        """Для type='scale' без options должны добавиться default"""
        # Arrange
        questions = [
            {"id": "q1", "text": "How often?", "type": "scale"}
        ]
        
        # Act
        result = generator._normalize_question_list(questions, "relationships")
        
        # Assert
        assert result[0]['type'] == 'scale'
        assert 'options' in result[0]
        assert len(result[0]['options']) == 5, "Scale should have 5 options"
        first_option = result[0]['options'][0]
        last_option = result[0]['options'][-1]
        assert first_option.startswith('⭕'), "First scale option should start with emoji"
        assert 'Никогда' in first_option
        assert last_option.startswith('🔥'), "Last scale option should start with emoji"
        assert 'Постоянно' in last_option
    
    def test_normalize_adds_default_multiple_choice_options(self):
        """Для type='multiple_choice' без options должны добавиться default"""
        # Arrange
        questions = [
            {"id": "q1", "text": "Choose one", "type": "multiple_choice"}
        ]
        
        # Act
        result = generator._normalize_question_list(questions, "relationships")
        
        # Assert
        assert result[0]['type'] == 'multiple_choice'
        assert 'options' in result[0]
        assert len(result[0]['options']) >= 3, "Multiple choice should have at least 3 options"
    
    def test_normalize_preserves_existing_options(self):
        """Если options уже есть, не перезаписываем"""
        # Arrange
        custom_options = ["Да", "Нет", "Может быть"]
        questions = [
            {"id": "q1", "text": "Question", "type": "multiple_choice", "options": custom_options}
        ]
        
        # Act
        result = generator._normalize_question_list(questions, "relationships")
        
        # Assert
        assert result[0]['options'] == custom_options, "Should preserve existing options"


class TestQuestionGeneration:
    """Интеграционные тесты генерации вопросов"""
    
    def test_seed_questions_have_mixed_types(self):
        """Seed questions должны содержать разные типы"""
        # Check each category
        for category, questions in generator.SEED_QUESTIONS.items():
            types = [q['type'] for q in questions]
            
            # Должен быть хотя бы 1 не-text вопрос
            non_text_count = len([t for t in types if t != 'text'])
            assert non_text_count >= 1, \
                f"Category '{category}' should have at least 1 non-text seed question"
    
    def test_seed_questions_have_scenario_questions(self):
        """Seed questions должны содержать сценарные вопросы"""
        for category, questions in generator.SEED_QUESTIONS.items():
            # Ищем вопросы с id содержащим 'scenario'
            scenario_questions = [q for q in questions if 'scenario' in q.get('id', '')]
            
            assert len(scenario_questions) >= 1, \
                f"Category '{category}' should have at least 1 scenario question"
            
            # Сценарные вопросы должны быть multiple_choice
            for q in scenario_questions:
                assert q['type'] == 'multiple_choice', \
                    "Scenario questions should be multiple_choice type"
                assert 'options' in q, "Scenario questions should have options"
                assert len(q['options']) >= 3, "Scenario questions should have 3+ options"


class TestContradictionDetection:
    """Тесты детектирования противоречий"""
    
    @pytest.mark.asyncio
    async def test_gpt_contradiction_detection_returns_list(self):
        """GPT contradiction detection должен возвращать список"""
        # Arrange
        answers = [
            {"question_text": "Do you have many friends?", "answer_value": "Yes, many"},
            {"question_text": "How often do you feel lonely?", "answer_value": "Very often"}
        ]
        
        # Mock GPT response
        mock_response = AsyncMock()
        mock_response.choices = [
            AsyncMock(message=AsyncMock(content='{"contradictions": [{"summary": "Test contradiction", "evidence": [], "insight": "Test"}]}'))
        ]
        
        with patch.object(generator.client.chat.completions, 'create', return_value=mock_response):
            # Act
            result = await generator._detect_contradictions_via_gpt(answers, "relationships")
        
        # Assert
        assert isinstance(result, list), "Should return list"
        assert len(result) > 0, "Should find contradictions"
    
    @pytest.mark.asyncio
    async def test_gpt_contradiction_fallback_on_error(self):
        """При ошибке GPT должен fallback на keyword-based"""
        # Arrange
        answers = [
            {"question_text": "Do you have many friends?", "answer_value": "Yes, many"},
            {"question_text": "How often do you feel lonely?", "answer_value": "Very often"}
        ]
        
        # Mock GPT to raise error
        with patch.object(generator.client.chat.completions, 'create', side_effect=Exception("API error")):
            # Act
            result = await generator._detect_contradictions_via_gpt(answers, "relationships")
        
        # Assert
        assert isinstance(result, list), "Should return list even on error"
        # Fallback должен найти obvious contradiction (many friends + lonely)
        assert len(result) >= 1, "Fallback should find at least 1 contradiction"


class TestFormatting:
    """Тесты форматирования вопросов"""
    
    def test_format_question_text_type(self):
        """Форматирование text вопроса"""
        # Arrange
        question = {
            "type": "text",
            "text": "Расскажите о себе",
            "category": "relationships"
        }
        
        # Act
        result = generator.format_question_for_telegram(question, 1, 10)
        
        # Assert
        assert "✍️" in result, "Should have text emoji"
        assert "Напиши что думаешь" in result or "Напишите" in result, "Should have text instruction"
        assert "🎙️" in result, "Should mention voice option"
    
    def test_format_question_scale_type(self):
        """Форматирование scale вопроса"""
        # Arrange
        question = {
            "type": "scale",
            "text": "Как часто?",
            "category": "money",
            "options": ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"]
        }
        
        # Act
        result = generator.format_question_for_telegram(question, 5, 10)
        
        # Assert
        assert "📊" in result, "Should have scale emoji"
        assert "шкале" in result.lower(), "Should mention scale"
        assert "Никогда" in result and "Постоянно" in result, "Should show scale preview"
    
    def test_format_question_multiple_choice_type(self):
        """Форматирование multiple_choice вопроса"""
        # Arrange
        question = {
            "type": "multiple_choice",
            "text": "Что выберешь?",
            "category": "purpose",
            "options": ["Вариант 1", "Вариант 2", "Вариант 3"]
        }
        
        # Act
        result = generator.format_question_for_telegram(question, 3, 10)
        
        # Assert
        assert "☑️" in result, "Should have checkbox emoji"
        assert "вариант" in result.lower(), "Should mention choice"
    
    def test_format_question_hides_counter_in_middle(self):
        """Счётчик скрыт в середине квиза (Q3-Q7)"""
        # Arrange
        question = {
            "type": "text",
            "text": "Middle question",
            "category": "relationships"
        }
        
        # Act
        result_middle = generator.format_question_for_telegram(question, 5, 10)
        result_start = generator.format_question_for_telegram(question, 1, 10)
        result_end = generator.format_question_for_telegram(question, 9, 10)
        
        # Assert
        assert "Вопрос 5" not in result_middle, "Should hide counter in middle"
        assert "Вопрос 1" in result_start, "Should show counter at start"
        assert "Вопрос 9" in result_end, "Should show counter at end"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

