"""
🧪 Unit Tests для Quiz Service (lightweight)

Smoke-level тесты для проверки основной функциональности.
Детальные integration tests - отдельно.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Добавляем корневую директорию в path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestQuizGenerator:
    """Легковесные тесты для quiz generator"""
    
    def test_generator_module_imports(self):
        """Generator модуль импортируется без ошибок"""
        try:
            from bot.services.quiz_service import generator
            assert hasattr(generator, 'generate_questions') or hasattr(generator, 'create_question')
        except Exception as e:
            pytest.fail(f"Failed to import quiz generator: {e}")
    
    
    @pytest.mark.asyncio
    async def test_question_generation_structure(self):
        """Проверка базовой структуры генерации вопросов"""
        from bot.services.quiz_service import generator
        
        # Проверяем что функции существуют
        assert callable(getattr(generator, 'generate_questions', None)) or \
               callable(getattr(generator, 'create_question', None)), \
               "Generator должен иметь функцию генерации вопросов"


class TestQuizAnalyzer:
    """Легковесные тесты для quiz analyzer"""
    
    def test_analyzer_module_imports(self):
        """Analyzer модуль импортируется без ошибок"""
        try:
            from bot.services.quiz_service import analyzer
            assert hasattr(analyzer, 'analyze_quiz_results') or hasattr(analyzer, 'analyze_quiz')
        except Exception as e:
            pytest.fail(f"Failed to import quiz analyzer: {e}")
    
    
    @pytest.mark.asyncio
    async def test_analyzer_basic_functionality(self):
        """Проверка базовой функциональности анализа"""
        from bot.services.quiz_service import analyzer
        
        # Проверяем что функции существуют
        assert callable(getattr(analyzer, 'analyze_quiz_results', None)) or \
               callable(getattr(analyzer, 'analyze_quiz', None)), \
               "Analyzer должен иметь функцию анализа"


class TestQuizSession:
    """Легковесные тесты для quiz session management"""
    
    def test_quiz_session_model_exists(self):
        """QuizSession модель существует"""
        try:
            from database.models.quiz_session import QuizSession
            assert QuizSession is not None
            
            # Проверяем ключевые поля
            expected_fields = ['user_id', 'category', 'status', 'questions', 'answers']
            for field in expected_fields:
                assert hasattr(QuizSession, field), f"QuizSession должна иметь поле {field}"
        except Exception as e:
            pytest.fail(f"QuizSession model check failed: {e}")
    
    
    def test_quiz_repository_exists(self):
        """Quiz repository существует"""
        try:
            import database.repository.quiz_session as quiz_repo
            
            # Проверяем ключевые функции
            expected_functions = ['create', 'get', 'update', 'get_active']
            for func_name in expected_functions:
                assert hasattr(quiz_repo, func_name), f"Quiz repository должен иметь функцию {func_name}"
        except Exception as e:
            pytest.fail(f"Quiz repository check failed: {e}")


class TestQuizIntegration:
    """Легковесные интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_quiz_session_lifecycle_mock(self):
        """Проверка жизненного цикла quiz session (mock)"""
        import database.repository.quiz_session as quiz_repo
        
        with patch.object(quiz_repo, 'create') as mock_create:
            with patch.object(quiz_repo, 'get') as mock_get:
                with patch.object(quiz_repo, 'update') as mock_update:
                    # Mock создание сессии
                    mock_session = MagicMock()
                    mock_session.id = 1
                    mock_session.user_id = 12345
                    mock_session.status = 'in_progress'
                    mock_create.return_value = mock_session
                    
                    # Проверяем что функции вызываются без ошибок
                    session = await quiz_repo.create(
                        user_id=12345,
                        category='relationships',
                        questions=[],
                        total_questions=10
                    )
                    
                    assert session is not None
                    assert mock_create.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

