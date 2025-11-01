"""
🧪 Smoke Tests для Level 2 Fixes

Быстрые тесты для проверки всех реализованных фиксов.
"""
import pytest


class TestLevel2FixesSmoke:
    """Smoke tests для всех Level 2 fixes"""
    
    def test_ultra_brief_option_in_prompts(self):
        """Проверить что ultra_brief добавлен в промпты"""
        from bot.services.openai_service import _build_style_instructions
        from unittest.mock import Mock
        
        # Mock profile
        profile = Mock()
        profile.tone_style = 'sarcastic'
        profile.personality = 'mentor'
        profile.message_length = 'ultra_brief'
        
        instructions = _build_style_instructions(profile)
        
        # Проверяем что ultra_brief упоминается
        assert 'ultra_brief' in instructions.lower() or 'ультра-коротко' in instructions.lower(), \
            "ultra_brief должен быть в промпте"
        assert '2-3' in instructions, "Должно быть указано 2-3 предложения"
    
    def test_enforce_message_length_truncates_brief(self):
        """Проверить что _enforce_message_length обрезает brief ответы"""
        from bot.services.openai_service import _enforce_message_length
        
        # Генерируем длинный текст (200 слов)
        long_text = ". ".join([f"Sentence {i}" for i in range(40)])  # ~200 words
        
        truncated = _enforce_message_length(long_text, 'brief')
        word_count = len(truncated.split())
        
        assert word_count <= 150, f"Brief должен быть <=150 слов, получилось {word_count}"
    
    def test_enforce_message_length_truncates_ultra_brief(self):
        """Проверить что ultra_brief обрезается до 50 слов"""
        from bot.services.openai_service import _enforce_message_length
        
        # Генерируем длинный текст
        long_text = " ".join(["word"] * 100)  # 100 слов
        
        truncated = _enforce_message_length(long_text, 'ultra_brief')
        word_count = len(truncated.split())
        
        assert word_count <= 50, f"ultra_brief должен быть <=50 слов, получилось {word_count}"
    
    def test_enforce_message_length_preserves_short(self):
        """Проверить что короткие ответы не обрезаются"""
        from bot.services.openai_service import _enforce_message_length
        
        short_text = "This is a short response with only ten words here."
        
        result = _enforce_message_length(short_text, 'brief')
        
        assert result == short_text, "Короткий текст не должен изменяться"
    
    def test_similarity_threshold_duplicate_lowered(self):
        """Проверить что DUPLICATE threshold снижен до 0.75"""
        from bot.services.embedding_service import SIMILARITY_THRESHOLD_DUPLICATE
        
        assert SIMILARITY_THRESHOLD_DUPLICATE == 0.75, \
            f"DUPLICATE threshold должен быть 0.75, получилось {SIMILARITY_THRESHOLD_DUPLICATE}"
    
    def test_similarity_threshold_related_lowered(self):
        """Проверить что RELATED threshold снижен до 0.65"""
        from bot.services.embedding_service import SIMILARITY_THRESHOLD_RELATED
        
        assert SIMILARITY_THRESHOLD_RELATED == 0.65, \
            f"RELATED threshold должен быть 0.65, получилось {SIMILARITY_THRESHOLD_RELATED}"
    
    def test_evidence_mentioned_in_profile_formatting(self):
        """Проверить что форматирование профиля показывает evidence"""
        from bot.handlers.user.profile import _format_patterns_section
        block = _format_patterns_section([
            {
                'title': 'Тестовый паттерн',
                'description': 'Описание',
                'contradiction': 'Противоречие',
                'hidden_dynamic': 'Динамика',
                'blocked_resource': 'Ресурс',
                'evidence': ['Цитата пользователя'],
                'confidence': 0.8,
            }
        ])

        assert '📝' in block, "Форматирование должно выделять блок с примерами"
        assert 'Цитата пользователя' in block, "Пример из слов пользователя должен попадать в текст"
    
    def test_citation_requirement_in_system_prompt(self):
        """Проверить что build_system_prompt включает требование цитирования"""
        from bot.services.openai_service import build_system_prompt
        import asyncio
        
        # Mock dependencies
        from unittest.mock import AsyncMock, Mock, patch
        
        with patch('bot.services.openai_service.user_profile') as mock_user_profile:
            # Mock profile
            mock_profile = Mock()
            mock_profile.tone_style = 'sarcastic'
            mock_profile.personality = 'mentor'
            mock_profile.message_length = 'brief'
            mock_profile.patterns = {'patterns': [
                {
                    'title': 'Test Pattern',
                    'description': 'Test description',
                    'evidence': ['test quote'],
                    'occurrences': 5,
                    'confidence': 0.9,
                    'tags': ['test']
                }
            ]}
            mock_profile.insights = {'insights': []}
            mock_profile.emotional_state = {}
            mock_profile.learning_preferences = {}
            
            mock_user_profile.get_or_create = AsyncMock(return_value=mock_profile)
            
            with patch('bot.services.openai_service.db_user') as mock_db_user:
                mock_user = Mock()
                mock_user.real_name = 'Test User'
                mock_user.age = 25
                mock_db_user.get = AsyncMock(return_value=mock_user)
                
                # Run async function
                prompt = asyncio.run(build_system_prompt(
                    user_id=12345,
                    assistant_type='helper'
                ))
                
                # Проверяем что есть требование цитирования
                assert 'ОБЯЗАТЕЛЬНОЕ' in prompt or 'ОБЯЗАТЕЛЬНО' in prompt, \
                    "Должно быть обязательное требование"
                assert 'ЦИТАТУ' in prompt or 'цитату' in prompt, \
                    "Должно требовать цитаты"
    
    def test_ultra_brief_in_keyboard(self):
        """Проверить что ultra_brief кнопка есть в клавиатуре"""
        from bot.keyboards.profile import length_menu
        
        # Проверяем что есть кнопка с ultra_brief
        found_ultra_brief = False
        for row in length_menu.inline_keyboard:
            for button in row:
                if 'ultra_brief' in button.callback_data:
                    found_ultra_brief = True
                    assert '2-3' in button.text or 'Очень' in button.text, \
                        "Текст кнопки должен упоминать 2-3 предложения или 'Очень коротко'"
        
        assert found_ultra_brief, "Должна быть кнопка для ultra_brief в length_menu"
    
    def test_ultra_brief_in_length_names(self):
        """Проверить что ultra_brief есть в length_names хендлера"""
        from bot.handlers.user.profile import set_length_callback
        import inspect
        
        source = inspect.getsource(set_length_callback)
        
        assert 'ultra_brief' in source, "ultra_brief должен быть в length_names"


class TestEnforceLengthEdgeCases:
    """Тесты для edge cases в _enforce_message_length"""
    
    def test_empty_string(self):
        """Проверить обработку пустой строки"""
        from bot.services.openai_service import _enforce_message_length
        
        result = _enforce_message_length("", 'brief')
        assert result == "", "Пустая строка должна оставаться пустой"
    
    def test_single_word(self):
        """Проверить обработку одного слова"""
        from bot.services.openai_service import _enforce_message_length
        
        result = _enforce_message_length("Hello", 'brief')
        assert result == "Hello", "Одно слово не должно изменяться"
    
    def test_exactly_at_limit(self):
        """Проверить текст ровно на лимите"""
        from bot.services.openai_service import _enforce_message_length
        
        # Ровно 150 слов
        text = " ".join(["word"] * 150)
        
        result = _enforce_message_length(text, 'brief')
        assert len(result.split()) == 150, "Текст на лимите не должен обрезаться"
    
    def test_one_word_over_limit(self):
        """Проверить текст на 1 слово больше лимита"""
        from bot.services.openai_service import _enforce_message_length
        
        # 151 слово (на 1 больше brief limit)
        text = " ".join(["word"] * 151)
        
        result = _enforce_message_length(text, 'brief')
        word_count = len(result.split())
        
        assert word_count <= 150, f"Должно обрезаться до 150, получилось {word_count}"
    
    def test_preserves_sentence_boundaries(self):
        """Проверить что обрезка происходит по предложениям"""
        from bot.services.openai_service import _enforce_message_length
        
        # 3 предложения, последнее не влезет
        text = "First sentence. " + " ".join(["word"] * 80) + ". Second sentence. " + " ".join(["word"] * 80) + ". Third sentence."
        
        result = _enforce_message_length(text, 'brief')
        
        # Не должно быть обрывов предложений
        assert result.endswith('.') or result.endswith('!') or result.endswith('?'), \
            "Результат должен заканчиваться знаком препинания"
    
    def test_unknown_length_option(self):
        """Проверить обработку неизвестной опции длины"""
        from bot.services.openai_service import _enforce_message_length
        
        long_text = " ".join(["word"] * 200)
        
        result = _enforce_message_length(long_text, 'unknown_option')
        
        # Не должно обрезать для неизвестной опции
        assert result == long_text, "Неизвестная опция не должна обрезать текст"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

