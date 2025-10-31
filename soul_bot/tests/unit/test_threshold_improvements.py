"""
Unit tests для улучшений V2.1 - thresholds и regex patterns

Быстрые тесты для проверки:
- Новые thresholds (burnout: 6, depression: 7)
- Новые regex patterns для depression detection
- Константы импортируются корректно
"""
import pytest
from bot.services.constants import (
    BURNOUT_SCORE_THRESHOLD,
    DEPRESSION_SCORE_THRESHOLD,
    MODEL_ANALYSIS
)


class TestThresholdConstants:
    """Test that threshold constants are set correctly"""
    
    def test_burnout_threshold_is_6(self):
        """Burnout threshold should be 6 (2 critical symptoms)"""
        assert BURNOUT_SCORE_THRESHOLD == 6
    
    def test_depression_threshold_lowered_to_7(self):
        """Depression threshold lowered from 9 to 7 for better detection"""
        assert DEPRESSION_SCORE_THRESHOLD == 7
    
    def test_model_analysis_upgraded_to_gpt4o(self):
        """MODEL_ANALYSIS should be gpt-4o (upgraded from gpt-4o-mini)"""
        assert MODEL_ANALYSIS == "gpt-4o"


class TestImprovedDepressionDetection:
    """Test that new regex patterns work"""
    
    def test_no_way_out_pattern_detected(self):
        """New pattern 'не вижу выхода' should be detected"""
        import re
        from bot.services.pattern_analyzer import _calculate_depression_score
        
        text = "Просто устал от всего... Не вижу выхода."
        score = _calculate_depression_score(text.lower())
        
        # "не вижу выхода" = 3pts (major symptom)
        # "устал от всего" = 1pt (minor)
        # Total: 4pts
        assert score >= 3, f"Expected score >= 3 for 'не вижу выхода', got {score}"
    
    def test_combined_depression_symptoms_hit_threshold(self):
        """Multiple symptoms should trigger threshold (7pts)"""
        from bot.services.pattern_analyzer import _calculate_depression_score
        
        text = """
        Иногда думаю что всё это бессмысленно.
        Зачем жить если ничего не меняется?
        Не вижу выхода из этой ситуации.
        """
        
        score = _calculate_depression_score(text.lower())
        
        # "всё бессмысленно" = 4pts (critical: severe_hopelessness)
        # "не вижу выхода" = 3pts (major: no_way_out)
        # Total: 7pts → should hit threshold!
        assert score >= DEPRESSION_SCORE_THRESHOLD, \
            f"Expected score >= {DEPRESSION_SCORE_THRESHOLD}, got {score}"
    
    def test_safety_net_triggers_with_lower_threshold(self):
        """Safety net should trigger with new threshold (7 instead of 9)"""
        from bot.services.pattern_analyzer import _check_critical_patterns_missing
        
        messages = [
            {"role": "user", "content": "Всё бессмысленно"},
            {"role": "user", "content": "Зачем жить если ничего не меняется"},
            {"role": "user", "content": "Не вижу выхода"},
        ]
        
        existing_patterns = []
        
        missing = _check_critical_patterns_missing(messages, existing_patterns)
        
        # With threshold 7 (lowered from 9), this should trigger
        # Score: 4 (bессмысленно) + 3 (не вижу выхода) = 7pts
        assert len(missing) > 0, "Expected safety net to detect depression with threshold 7"
        assert any('depression' in p['title'].lower() for p in missing)


class TestBurnoutDetectionUnchanged:
    """Verify burnout detection still works (threshold unchanged at 6)"""
    
    def test_burnout_threshold_still_works(self):
        """Burnout should still trigger at 6pts (unchanged)"""
        from bot.services.pattern_analyzer import _check_critical_patterns_missing
        
        messages = [
            {"role": "user", "content": "Работаю по 15 часов каждый день"},
            {"role": "user", "content": "Забыл про важную встречу вчера"},
            {"role": "user", "content": "Мозг просто отключается"},
        ]
        
        existing_patterns = []
        
        missing = _check_critical_patterns_missing(messages, existing_patterns)
        
        # Score: 3 (overwork) + 3 (cognitive_dysfunction) + 3 (concentration) = 9pts
        # Threshold 6 → should trigger
        assert len(missing) > 0, "Expected safety net to detect burnout"
        assert any('burnout' in p['title'].lower() for p in missing)


# Run with: pytest soul_bot/tests/unit/test_threshold_improvements.py -v

