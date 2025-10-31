"""
🧪 Tests for Critical Pattern Detection (Option 2 + 4)

Tests:
- Burnout score calculation
- Depression score calculation  
- Safety net (missing critical patterns detection)
- Stress level calculation with burnout
"""
import pytest
from bot.services.pattern_analyzer import (
    _calculate_burnout_score,
    _calculate_depression_score,
    _check_critical_patterns_missing,
    _calculate_stress_level,
    _extract_burnout_evidence,
    _extract_depression_evidence
)


class TestBurnoutDetection:
    """Tests for burnout score calculation"""
    
    def test_burnout_overwork_symptom(self):
        """Should detect overwork pattern"""
        text = "я работаю по 14 часов в день уже месяц"
        score = _calculate_burnout_score(text)
        assert score >= 3  # critical symptom = 3 points
    
    def test_burnout_cognitive_dysfunction(self):
        """Should detect cognitive dysfunction (forgetting meetings)"""
        text = "забыл про важную встречу сегодня"
        score = _calculate_burnout_score(text)
        assert score >= 3
    
    def test_burnout_concentration_loss(self):
        """Should detect inability to concentrate"""
        text = "не могу сконцентрироваться вообще"
        score = _calculate_burnout_score(text)
        assert score >= 3
    
    def test_burnout_anhedonia(self):
        """Should detect anhedonia"""
        text = "не помню когда последний раз был счастлив"
        score = _calculate_burnout_score(text)
        assert score >= 3
    
    def test_burnout_multiple_symptoms(self):
        """Should accumulate score for multiple symptoms"""
        text = """
        работаю по 12 часов каждый день
        нет сил вообще
        забыл встречу
        не могу думать
        """
        score = _calculate_burnout_score(text.lower())
        assert score >= 9  # 3 critical + 2 major = 9+
    
    def test_burnout_no_symptoms(self):
        """Should return 0 if no burnout symptoms"""
        text = "все хорошо, работаю нормально, отдыхаю"
        score = _calculate_burnout_score(text)
        assert score == 0
    
    def test_extract_burnout_evidence(self):
        """Should extract relevant quotes for burnout"""
        messages = [
            {'role': 'user', 'content': 'Работаю по 14 часов в день'},
            {'role': 'assistant', 'content': 'Понимаю'},
            {'role': 'user', 'content': 'Нет сил вообще'},
            {'role': 'user', 'content': 'Забыл про встречу'},
        ]
        
        evidence = _extract_burnout_evidence(messages, max_evidence=3)
        
        assert len(evidence) == 3
        assert any('14 часов' in e for e in evidence)
        assert any('Нет сил' in e for e in evidence)
        assert any('Забыл' in e for e in evidence)


class TestDepressionDetection:
    """Tests for depression score calculation"""
    
    def test_depression_hopelessness(self):
        """Should detect hopelessness"""
        text = "нет смысла, зачем стараться"
        score = _calculate_depression_score(text)
        assert score >= 3  # major symptom = 3 points
    
    def test_depression_worthlessness(self):
        """Should detect feelings of worthlessness"""
        text = "я полный лузер, всё делаю неправильно"
        score = _calculate_depression_score(text)
        assert score >= 3
    
    def test_depression_suicidal_ideation(self):
        """Should detect suicidal ideation (critical)"""
        text = "хочу умереть, нет смысла жить"
        score = _calculate_depression_score(text)
        assert score >= 7  # 4 (suicidal) + 3 (hopelessness)
    
    def test_depression_multiple_symptoms(self):
        """Should accumulate score for multiple symptoms"""
        text = """
        нет смысла стараться
        не помню когда был счастлив
        чувствую себя лузером
        """
        score = _calculate_depression_score(text.lower())
        assert score >= 9  # 3 major symptoms = 9 points
    
    def test_depression_no_symptoms(self):
        """Should return low score if no depression symptoms"""
        text = "все нормально, немного устал"
        score = _calculate_depression_score(text)
        assert score < 3


class TestCriticalPatternsSafetyNet:
    """Tests for _check_critical_patterns_missing()"""
    
    def test_detects_missing_burnout(self):
        """Should detect burnout when GPT missed it"""
        messages = [
            {'role': 'user', 'content': 'Работаю по 14 часов в день'},
            {'role': 'user', 'content': 'Нет сил вообще'},
            {'role': 'user', 'content': 'Забыл про важную встречу'},
            {'role': 'user', 'content': 'Не могу сконцентрироваться'},
        ]
        
        existing_patterns = [
            {'title': 'Perfectionism', 'frequency': 3},
            {'title': 'Fear of Failure', 'frequency': 2}
        ]
        
        missing = _check_critical_patterns_missing(messages, existing_patterns)
        
        assert len(missing) == 1
        assert missing[0]['title'] == 'Burnout'
        assert missing[0]['confidence'] >= 0.7
        assert missing[0]['auto_detected'] is True
        assert len(missing[0]['evidence']) > 0
    
    def test_does_not_duplicate_burnout(self):
        """Should NOT add burnout if GPT already detected it"""
        messages = [
            {'role': 'user', 'content': 'Работаю по 14 часов'},
            {'role': 'user', 'content': 'Нет сил'},
        ]
        
        existing_patterns = [
            {'title': 'Burnout', 'frequency': 5},  # Already exists
        ]
        
        missing = _check_critical_patterns_missing(messages, existing_patterns)
        
        assert len(missing) == 0
    
    def test_detects_missing_depression(self):
        """Should detect acute depression when GPT missed it"""
        messages = [
            {'role': 'user', 'content': 'Нет смысла стараться'},
            {'role': 'user', 'content': 'Не помню когда был счастлив'},
            {'role': 'user', 'content': 'Чувствую себя полным лузером'},
        ]
        
        existing_patterns = []
        
        missing = _check_critical_patterns_missing(messages, existing_patterns)
        
        # Should detect depression (3 major symptoms = 9 points >= threshold)
        assert len(missing) == 1
        assert missing[0]['title'] == 'Acute Depression'
        assert 'seek-help' in missing[0]['tags']
        assert missing[0]['requires_professional_help'] is True
    
    def test_no_false_positives(self):
        """Should NOT add critical patterns if symptoms absent"""
        messages = [
            {'role': 'user', 'content': 'Немного устал сегодня'},
            {'role': 'user', 'content': 'Работаю нормально'},
        ]
        
        existing_patterns = []
        
        missing = _check_critical_patterns_missing(messages, existing_patterns)
        
        assert len(missing) == 0


class TestStressLevelCalculation:
    """Tests for updated stress level calculation"""
    
    def test_stress_level_with_burnout(self):
        """Should return 'high' or 'critical' when burnout detected"""
        patterns = []  # No patterns yet
        
        messages = [
            {'role': 'user', 'content': 'Работаю по 14 часов в день'},
            {'role': 'user', 'content': 'Нет сил'},
            {'role': 'user', 'content': 'Забыл встречу'},
            {'role': 'user', 'content': 'Не могу концентрироваться'},
        ]
        
        stress = _calculate_stress_level(patterns, messages)
        
        assert stress in ['high', 'critical']
    
    def test_stress_level_with_burnout_pattern(self):
        """Should return 'critical' when burnout pattern exists"""
        patterns = [
            {'title': 'Burnout', 'occurrences': 5}
        ]
        
        messages = [
            {'role': 'user', 'content': 'Работаю по 14 часов'},
            {'role': 'user', 'content': 'Нет сил'},
        ]
        
        stress = _calculate_stress_level(patterns, messages)
        
        # 3 (burnout pattern) * 5 (frequency) + burnout_score (6+) = 21+ → critical
        assert stress == 'critical'
    
    def test_stress_level_low_when_no_symptoms(self):
        """Should return 'low' when no stress symptoms"""
        patterns = []
        messages = [
            {'role': 'user', 'content': 'Все хорошо'},
            {'role': 'user', 'content': 'Работаю нормально'},
        ]
        
        stress = _calculate_stress_level(patterns, messages)
        
        assert stress in ['low', 'medium']
    
    def test_stress_level_thresholds(self):
        """Should use updated thresholds (critical=10, high=6)"""
        patterns = [
            {'title': 'Fear of Failure', 'occurrences': 3}  # 2*3 = 6
        ]
        messages = []
        
        stress = _calculate_stress_level(patterns, messages)
        
        # score = 6 → should be 'high' (old threshold was 8)
        assert stress == 'high'


class TestIntegration:
    """Integration tests for full flow"""
    
    def test_full_burnout_detection_flow(self):
        """
        Test full flow:
        1. User messages with burnout symptoms
        2. GPT analysis (might miss it)
        3. Safety net catches it
        4. Stress level calculated correctly
        """
        messages = [
            {'role': 'user', 'content': 'Работаю по 14 часов в день уже месяц'},
            {'role': 'assistant', 'content': 'Понимаю'},
            {'role': 'user', 'content': 'Нет сил вообще. Забыл про важную встречу'},
            {'role': 'assistant', 'content': 'Это тревожно'},
            {'role': 'user', 'content': 'Не могу сконцентрироваться'},
        ]
        
        # Simulate GPT analysis that missed burnout
        gpt_patterns = [
            {'title': 'Perfectionism', 'type': 'behavioral'}
        ]
        
        # Safety net should catch it
        missing = _check_critical_patterns_missing(messages, gpt_patterns)
        
        assert len(missing) >= 1
        assert any(p['title'] == 'Burnout' for p in missing)
        
        # Combine patterns
        all_patterns = gpt_patterns + missing
        
        # Stress should be high/critical
        stress = _calculate_stress_level(all_patterns, messages)
        assert stress in ['high', 'critical']

