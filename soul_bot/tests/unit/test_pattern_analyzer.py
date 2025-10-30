"""
🧪 Unit Tests для Pattern Analyzer

Тестируем:
1. Дедупликацию паттернов (keyword match + semantic similarity)
2. Мердж логику (occurrences growth)
3. Quick/Deep analysis flow
4. Error handling
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
import json

# Добавляем корневую директорию в path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


@pytest.fixture
def mock_openai_response():
    """Mock для OpenAI API responses"""
    def _create_response(content: str):
        mock = MagicMock()
        mock.choices = [MagicMock()]
        mock.choices[0].message = MagicMock()
        mock.choices[0].message.content = content
        mock.usage = MagicMock()
        mock.usage.total_tokens = 150
        return mock
    return _create_response


@pytest.fixture
def mock_embedding():
    """Mock для embedding generation"""
    async def _get_embedding(text: str):
        # Простой мок: одинаковые тексты → одинаковые embeddings
        # "Imposter Syndrome" → [0.1, 0.2, 0.3, ...]
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        # Генерируем 1536-dim вектор на основе хэша
        return [(hash_val % 1000) / 1000.0] * 1536
    return _get_embedding


@pytest.fixture
def sample_patterns():
    """Набор тестовых паттернов"""
    return [
        {
            'id': 'pattern-1',
            'title': 'Imposter Syndrome',
            'description': 'Feeling inadequate despite evidence of competence',
            'type': 'emotional',
            'evidence': ['I am not good enough', 'I am a fraud'],
            'occurrences': 3,
            'confidence': 0.85,
            'embedding': [0.1] * 1536
        },
        {
            'id': 'pattern-2',
            'title': 'Perfectionism',
            'description': 'Setting unrealistically high standards',
            'type': 'behavioral',
            'evidence': ['Code must be perfect', 'Rewriting 10 times'],
            'occurrences': 2,
            'confidence': 0.80,
            'embedding': [0.5] * 1536
        }
    ]


class TestPatternDeduplication:
    """Тесты дедупликации паттернов"""
    
    @pytest.mark.asyncio
    async def test_keyword_match_forces_merge(self, sample_patterns, mock_embedding):
        """Keyword match (exact title) должен форсировать мердж"""
        from bot.services import pattern_analyzer
        
        new_patterns = [{
            'title': 'Imposter Syndrome',  # Exact match!
            'description': 'Same pattern but new evidence',
            'type': 'emotional',
            'evidence': ['I will be found out', 'I do not deserve this'],
            'confidence': 0.90
        }]
        
        existing = sample_patterns.copy()
        
        with patch('bot.services.embedding_service.get_embedding', mock_embedding):
            await pattern_analyzer._add_patterns_with_dedup(
                user_id=12345,
                new_patterns=new_patterns,
                existing_patterns=existing
            )
        
        # Проверяем: должен быть 1 мердж (не добавлен новый)
        assert len(existing) == 2, "Не должно быть нового паттерна"
        
        # Occurrences увеличился
        imposter_pattern = [p for p in existing if p['title'] == 'Imposter Syndrome'][0]
        assert imposter_pattern['occurrences'] == 4, f"Expected 4, got {imposter_pattern['occurrences']}"
        
        # Evidence добавился (без дубликатов)
        assert 'I will be found out' in imposter_pattern['evidence']
        assert len(imposter_pattern['evidence']) > 2


    @pytest.mark.asyncio
    async def test_semantic_similarity_merges_similar(self, sample_patterns, mock_embedding):
        """Semantic similarity > threshold должен мерджить похожие паттерны"""
        from bot.services import pattern_analyzer
        
        # Паттерн с другим названием, но похожим смыслом
        new_patterns = [{
            'title': 'Self-Doubt at Work',  # Разное название
            'description': 'Feeling inadequate despite evidence of competence',  # Похожее описание
            'type': 'emotional',
            'evidence': ['I am not qualified'],
            'confidence': 0.85
        }]
        
        existing = sample_patterns.copy()
        
        with patch('bot.services.embedding_service.get_embedding', mock_embedding):
            # Мокаем is_duplicate для возврата high similarity
            with patch('bot.services.embedding_service.is_duplicate') as mock_is_dup:
                mock_is_dup.return_value = (True, existing[0], 0.75)  # High similarity
                
                await pattern_analyzer._add_patterns_with_dedup(
                    user_id=12345,
                    new_patterns=new_patterns,
                    existing_patterns=existing
                )
        
        # Проверяем: мердж произошёл
        assert len(existing) == 2, "Должно быть 2 паттерна (не добавился новый)"


    @pytest.mark.asyncio
    async def test_different_patterns_not_merged(self, sample_patterns, mock_embedding):
        """Разные паттерны НЕ должны мерджиться"""
        from bot.services import pattern_analyzer
        
        new_patterns = [{
            'title': 'Social Anxiety',  # Совершенно другой паттерн
            'description': 'Fear of social situations and judgment',
            'type': 'emotional',
            'evidence': ['Afraid to speak at meetings'],
            'confidence': 0.80
        }]
        
        existing = sample_patterns.copy()
        
        with patch('bot.services.embedding_service.get_embedding', mock_embedding):
            with patch('bot.services.embedding_service.is_duplicate') as mock_is_dup:
                mock_is_dup.return_value = (False, None, 0.30)  # Low similarity
                
                await pattern_analyzer._add_patterns_with_dedup(
                    user_id=12345,
                    new_patterns=new_patterns,
                    existing_patterns=existing
                )
        
        # Проверяем: добавился новый паттерн
        assert len(existing) == 3, f"Должно быть 3 паттерна, получили {len(existing)}"
        
        # Новый паттерн есть в списке
        social_anxiety = [p for p in existing if p['title'] == 'Social Anxiety']
        assert len(social_anxiety) == 1, "Social Anxiety должен быть добавлен"
        assert social_anxiety[0]['occurrences'] == 1, "Новый паттерн должен иметь occurrences=1"


class TestQuickAnalysis:
    """Тесты quick analysis"""
    
    @pytest.mark.asyncio
    async def test_quick_analysis_returns_patterns(self, mock_openai_response):
        """Quick analysis должен возвращать паттерны"""
        from bot.services import pattern_analyzer
        
        # Mock GPT response
        gpt_response = {
            "new_patterns": [
                {
                    "type": "emotional",
                    "title": "Imposter Syndrome",
                    "description": "Feeling inadequate",
                    "evidence": ["I am not good enough"],
                    "tags": ["self-doubt"],
                    "frequency": "high",
                    "confidence": 0.85
                }
            ],
            "mood": {
                "current_mood": "slightly_down",
                "stress_level": "medium",
                "energy_level": "low",
                "triggers": ["work"]
            }
        }
        
        with patch('bot.services.pattern_analyzer.client') as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_openai_response(json.dumps(gpt_response))
            )
            
            with patch('database.repository.conversation_history.get_context') as mock_get_context:
                mock_get_context.return_value = [
                    {"role": "user", "content": "I feel like a fraud"},
                    {"role": "assistant", "content": "Let's talk about that"}
                ] * 3
                
                with patch('database.repository.user_profile.get_or_create') as mock_get_profile:
                    mock_profile = MagicMock()
                    mock_profile.patterns = {'patterns': []}
                    mock_get_profile.return_value = mock_profile
                    
                    with patch('bot.services.pattern_analyzer._add_patterns_with_dedup') as mock_add:
                        mock_add.return_value = None
                        
                        # Запускаем quick analysis
                        await pattern_analyzer.quick_analysis(user_id=12345)
                        
                        # Проверяем: GPT был вызван
                        assert mock_client.chat.completions.create.called
                        
                        # Проверяем: паттерны были добавлены
                        assert mock_add.called


    @pytest.mark.asyncio
    async def test_quick_analysis_handles_errors_gracefully(self):
        """Quick analysis должен обрабатывать ошибки без падения"""
        from bot.services import pattern_analyzer
        
        with patch('bot.services.pattern_analyzer.client') as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("OpenAI API error")
            )
            
            with patch('database.repository.conversation_history.get_context') as mock_get_context:
                mock_get_context.return_value = [
                    {"role": "user", "content": "test"}
                ] * 5
                
                with patch('database.repository.user_profile.get_or_create') as mock_get_profile:
                    mock_profile = MagicMock()
                    mock_profile.patterns = {'patterns': []}
                    mock_get_profile.return_value = mock_profile
                    
                    # Должно завершиться без exception
                    try:
                        await pattern_analyzer.quick_analysis(user_id=12345)
                        success = True
                    except Exception:
                        success = False
                    
                    assert success, "Quick analysis должен обрабатывать ошибки gracefully"


class TestAnalyzeIfNeeded:
    """Тесты триггеров анализа"""
    
    @pytest.mark.asyncio
    async def test_triggers_quick_analysis_every_3_messages(self):
        """Должен запускать quick analysis каждые 3 сообщения"""
        from bot.services import pattern_analyzer
        
        with patch('database.repository.conversation_history.count_messages') as mock_count:
            with patch('bot.services.pattern_analyzer.quick_analysis') as mock_quick:
                mock_quick.return_value = None
                
                # Тест: 3 сообщения
                mock_count.return_value = 3
                await pattern_analyzer.analyze_if_needed(user_id=12345)
                assert mock_quick.called, "Quick analysis должен быть вызван на 3 сообщениях"
                
                mock_quick.reset_mock()
                
                # Тест: 6 сообщений
                mock_count.return_value = 6
                await pattern_analyzer.analyze_if_needed(user_id=12345)
                assert mock_quick.called, "Quick analysis должен быть вызван на 6 сообщениях"


    @pytest.mark.asyncio
    async def test_triggers_deep_analysis_every_20_messages(self):
        """Должен запускать deep analysis каждые 20 сообщений"""
        from bot.services import pattern_analyzer
        
        with patch('database.repository.conversation_history.count_messages') as mock_count:
            with patch('bot.services.pattern_analyzer.quick_analysis') as mock_quick:
                with patch('bot.services.pattern_analyzer.deep_analysis') as mock_deep:
                    mock_quick.return_value = None
                    mock_deep.return_value = None
                    
                    # Тест: 60 сообщений (делится и на 3, и на 20)
                    mock_count.return_value = 60
                    await pattern_analyzer.analyze_if_needed(user_id=12345)
                    
                    assert mock_quick.called, "Quick analysis также должен быть вызван (60 % 3 == 0)"
                    assert mock_deep.called, "Deep analysis должен быть вызван на 60 сообщениях (60 % 20 == 0)"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

