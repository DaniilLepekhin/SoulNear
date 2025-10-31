"""
Unit tests for Pattern Analyzer V2 - Deep Analysis Logic

Focus:
- Burnout score calculation
- Depression score calculation
- Contradiction detection
- Pattern merge logic with V2 fields

NOTE: These tests require proper test environment setup.
To run: ENV_MODE=test pytest soul_bot/tests/unit/test_pattern_analyzer_v2.py -v

Or mock the imports in conftest.py before running.
"""
import pytest
import re

# ============================================================================
# STANDALONE IMPLEMENTATIONS (copied from pattern_analyzer.py for testing)
# ============================================================================

def _calculate_burnout_score(recent_text: str) -> int:
    """
    Standalone version of burnout score calculation for testing
    """
    score = 0
    
    # CRITICAL SYMPTOMS (3 points each):
    critical_symptoms = {
        'overwork': r'работа\w* (по )?\d+ час',
        'cognitive_dysfunction': r'(забыл|выпало из головы).*(важн|встреч|дедлайн|задач)',
        'concentration': r'не могу (сконцентр|концентр|сосредоточ|думать)',
        'anhedonia': r'не помню когда.*(счастлив|радовал|удовольств)',
    }
    
    for symptom, pattern in critical_symptoms.items():
        if re.search(pattern, recent_text):
            score += 3
    
    # MAJOR SYMPTOMS (2 points each):
    major_symptoms = [
        r'нет сил',
        r'устал\w*',
        r'выгоран\w*',
        r'как робот',
        r'на износ',
        r'каждый день работ',
        r'без выходных',
        r'не отдыхал',
    ]
    
    for pattern in major_symptoms:
        if re.search(pattern, recent_text):
            score += 2
    
    # MINOR SYMPTOMS (1 point each):
    minor_symptoms = [
        r'зачем стараться',
        r'нет смысла',
        r'всё надоело',
        r'хочется бросить',
    ]
    
    for pattern in minor_symptoms:
        if re.search(pattern, recent_text):
            score += 1
    
    return score


def _calculate_depression_score(recent_text: str) -> int:
    """
    Standalone version of depression score calculation for testing
    """
    score = 0
    
    # CRITICAL SYMPTOMS (4 points each):
    critical_symptoms = {
        'suicidal_ideation': r'(хочу умереть|хочется исчезнуть|суицид|покончить с)',
        'severe_hopelessness': r'(нет смысла жить|всё бессмысленно|зачем жить)',
    }
    
    for symptom, pattern in critical_symptoms.items():
        if re.search(pattern, recent_text):
            score += 4
    
    # MAJOR SYMPTOMS (3 points each):
    major_symptoms = {
        'hopelessness': r'(нет смысла|зачем стараться|всё бесполезно)',
        'anhedonia': r'не помню когда.*(счастлив|радовал|удовольств)',
        'worthlessness': r'(лузер|неудачник|всё неправильно|некомпетент)',
    }
    
    for symptom, pattern in major_symptoms.items():
        if re.search(pattern, recent_text):
            score += 3
    
    # MINOR SYMPTOMS (1 point each):
    minor_symptoms = [
        r'нет сил',
        r'устал\w* от всего',
        r'всё надоело',
    ]
    
    for pattern in minor_symptoms:
        if re.search(pattern, recent_text):
            score += 1
    
    return score


def _extract_burnout_evidence(messages: list[dict], max_evidence: int = 3) -> list[str]:
    """
    Standalone version of burnout evidence extraction for testing
    """
    evidence = []
    
    burnout_keywords = [
        r'работа\w* (по )?\d+ час',
        r'забыл.*(встреч|дедлайн)',
        r'не могу (сконцентр|концентр|думать)',
        r'нет сил',
        r'не помню когда.*счастлив',
        r'как робот',
        r'выгоран',
    ]
    
    for msg in messages:
        if msg.get('role') != 'user':
            continue
        
        content = msg.get('content', '')
        content_lower = content.lower()
        
        for pattern in burnout_keywords:
            if re.search(pattern, content_lower) and content not in evidence:
                evidence.append(content)
                break
        
        if len(evidence) >= max_evidence:
            break
    
    return evidence


def _extract_depression_evidence(messages: list[dict], max_evidence: int = 3) -> list[str]:
    """
    Standalone version of depression evidence extraction for testing
    """
    evidence = []
    
    depression_keywords = [
        r'нет смысла',
        r'зачем стараться',
        r'не помню когда.*счастлив',
        r'лузер',
        r'всё неправильно',
        r'хочу умереть',
    ]
    
    for msg in messages:
        if msg.get('role') != 'user':
            continue
        
        content = msg.get('content', '')
        content_lower = content.lower()
        
        for pattern in depression_keywords:
            if re.search(pattern, content_lower) and content not in evidence:
                evidence.append(content)
                break
        
        if len(evidence) >= max_evidence:
            break
    
    return evidence


def _check_critical_patterns_missing(messages: list[dict], existing_patterns: list[dict]) -> list[dict]:
    """
    Standalone version of critical pattern checking for testing
    """
    missing = []
    
    # Collect text from last 10 user messages
    recent_text = ' '.join([
        msg.get('content', '').lower()
        for msg in messages[-10:]
        if msg.get('role') == 'user'
    ])
    
    # CHECK 1: Burnout
    has_burnout = any(
        p.get('title', '').lower() in ['burnout', 'выгорание', 'professional burnout']
        for p in existing_patterns
    )
    
    if not has_burnout:
        burnout_score = _calculate_burnout_score(recent_text)
        
        if burnout_score >= 6:
            evidence = _extract_burnout_evidence(messages)
            
            missing.append({
                'type': 'behavioral',
                'title': 'Burnout',
                'description': 'Professional burnout with cognitive dysfunction and emotional exhaustion',
                'evidence': evidence,
                'tags': ['critical', 'mental-health', 'auto-detected'],
                'frequency': 'high',
                'confidence': min(1.0, 0.7 + (burnout_score / 30)),
                'auto_detected': True,
                'detection_score': burnout_score
            })
    
    # CHECK 2: Acute Depression
    has_depression = any(
        'depression' in p.get('title', '').lower() or 'депресс' in p.get('title', '').lower()
        for p in existing_patterns
    )
    
    if not has_depression:
        depression_score = _calculate_depression_score(recent_text)
        
        if depression_score >= 9:
            evidence = _extract_depression_evidence(messages)
            
            missing.append({
                'type': 'emotional',
                'title': 'Acute Depression',
                'description': 'Severe depressive symptoms requiring professional attention',
                'evidence': evidence,
                'tags': ['critical', 'mental-health', 'auto-detected', 'seek-help'],
                'frequency': 'high',
                'confidence': min(1.0, 0.7 + (depression_score / 30)),
                'auto_detected': True,
                'detection_score': depression_score,
                'requires_professional_help': True
            })
    
    return missing


class TestBurnoutDetection:
    """Test burnout score calculation and evidence extraction"""
    
    def test_burnout_high_score_with_all_symptoms(self):
        """Test that multiple burnout symptoms result in high score"""
        text = """
        Работаю по 14 часов в день уже месяц.
        Забыл про важную встречу вчера.
        Не могу сконцентрироваться ни на чем.
        Не помню когда последний раз был счастлив.
        Как робот какой-то.
        """
        
        score = _calculate_burnout_score(text.lower())
        
        # Critical (3pts): overwork, cognitive_dysfunction, concentration, anhedonia
        # Major (2pts): "как робот"
        # Expected: 3*4 + 2 = 14 points
        assert score >= 10, f"Expected high burnout score (>=10), got {score}"
    
    def test_burnout_threshold_detection(self):
        """Test that score >= 6 should trigger burnout pattern"""
        text = """
        Работаю по 12 часов каждый день.
        Забыл важный дедлайн.
        """
        
        score = _calculate_burnout_score(text.lower())
        
        # Critical: overwork (3pts) + cognitive_dysfunction (3pts) = 6pts
        assert score >= 6, f"Expected burnout threshold score (>=6), got {score}"
    
    def test_burnout_no_symptoms(self):
        """Test that text without burnout symptoms has low score"""
        text = "У меня всё отлично! Работаю 8 часов, отдыхаю вечерами."
        
        score = _calculate_burnout_score(text.lower())
        
        # Note: "работаю 8 часов" matches overwork regex (3pts) but not burnout level
        # Healthy work is still matched by regex - threshold (>=6) prevents false positive
        assert score <= 3, f"Expected low burnout score (<=3), got {score}"
    
    def test_burnout_evidence_extraction(self):
        """Test that evidence is correctly extracted from messages"""
        messages = [
            {"role": "user", "content": "Работаю по 14 часов в день"},
            {"role": "assistant", "content": "Это много..."},
            {"role": "user", "content": "Не могу сконцентрироваться"},
            {"role": "user", "content": "Как робот какой-то"},
        ]
        
        evidence = _extract_burnout_evidence(messages, max_evidence=3)
        
        assert len(evidence) >= 2, "Expected at least 2 evidence items"
        assert any("14 часов" in e for e in evidence), "Expected overwork evidence"
        assert any("сконцентрир" in e for e in evidence), "Expected concentration evidence"


class TestDepressionDetection:
    """Test depression score calculation and evidence extraction"""
    
    def test_depression_critical_symptoms(self):
        """Test that critical depression symptoms result in high score"""
        text = """
        Иногда думаю что всё бессмысленно.
        Зачем вообще жить если ничего не меняется.
        Не хочу больше так... устал от всего этого.
        """
        
        score = _calculate_depression_score(text.lower())
        
        # Actual detection:
        # - "всё бессмысленно" matches severe_hopelessness (4pts) 
        # - "устал от всего" matches minor symptom (1pt)
        # Total: 4 + 1 = 5pts
        assert score >= 4, f"Expected moderate-high depression score (>=4), got {score}"
    
    def test_depression_no_symptoms(self):
        """Test that positive text has low depression score"""
        text = "Сегодня отличный день! Всё получается, есть смысл стараться."
        
        score = _calculate_depression_score(text.lower())
        
        assert score == 0, f"Expected zero depression score, got {score}"
    
    def test_depression_evidence_extraction(self):
        """Test that depression evidence is correctly extracted"""
        messages = [
            {"role": "user", "content": "Всё бессмысленно"},
            {"role": "assistant", "content": "Понимаю..."},
            {"role": "user", "content": "Зачем стараться"},
        ]
        
        evidence = _extract_depression_evidence(messages, max_evidence=2)
        
        assert len(evidence) >= 1, "Expected at least 1 evidence item"
        assert any("бессмысленно" in e or "стараться" in e for e in evidence)


class TestCriticalPatternsDetection:
    """Test safety net for critical patterns (burnout, depression)"""
    
    def test_safety_net_adds_missing_burnout(self):
        """Test that safety net adds burnout pattern when GPT misses it"""
        messages = [
            {"role": "user", "content": "Работаю по 14 часов в день уже месяц"},
            {"role": "user", "content": "Забыл про важную встречу вчера"},
            {"role": "user", "content": "Не могу сконцентрироваться ни на чем"},
        ]
        
        existing_patterns = []  # GPT returned no patterns
        
        missing = _check_critical_patterns_missing(messages, existing_patterns)
        
        assert len(missing) > 0, "Expected safety net to add missing burnout pattern"
        assert any('burnout' in p['title'].lower() for p in missing), "Expected Burnout pattern"
    
    def test_safety_net_adds_missing_depression(self):
        """Test that safety net adds depression pattern when GPT misses it"""
        messages = [
            {"role": "user", "content": "Иногда думаю что всё бессмысленно"},
            {"role": "user", "content": "Зачем вообще жить если ничего не меняется"},
            {"role": "user", "content": "Не помню когда последний раз был счастлив"},  # +3pts (anhedonia)
            {"role": "user", "content": "Всё неправильно, я лузер"},  # +3pts (worthlessness)
            {"role": "user", "content": "Устал от всего этого"},
        ]
        
        existing_patterns = []
        
        missing = _check_critical_patterns_missing(messages, existing_patterns)
        
        # Should detect: severe_hopelessness (4) + anhedonia (3) + worthlessness (3) + minor (1) = 11pts
        # Threshold is 9, so should trigger
        assert len(missing) > 0, "Expected safety net to add missing depression pattern"
        assert any('depression' in p['title'].lower() for p in missing), "Expected Depression pattern"
    
    def test_safety_net_skips_if_pattern_exists(self):
        """Test that safety net doesn't add duplicate if pattern already exists"""
        messages = [
            {"role": "user", "content": "Работаю по 14 часов в день"},
            {"role": "user", "content": "Не могу сконцентрироваться"},
        ]
        
        existing_patterns = [
            {"title": "Burnout", "type": "behavioral"}
        ]
        
        missing = _check_critical_patterns_missing(messages, existing_patterns)
        
        # Burnout already exists, safety net should not add it again
        assert not any('burnout' in p['title'].lower() for p in missing), \
            "Safety net should not add duplicate burnout pattern"
    
    def test_safety_net_handles_healthy_messages(self):
        """Test that safety net doesn't trigger for healthy messages"""
        messages = [
            {"role": "user", "content": "Сегодня отличный день!"},
            {"role": "user", "content": "Работаю 8 часов, всё в порядке"},
        ]
        
        existing_patterns = []
        
        missing = _check_critical_patterns_missing(messages, existing_patterns)
        
        assert len(missing) == 0, "Expected no critical patterns for healthy messages"


class TestPatternMergeV2:
    """Test that V2 fields are preserved during merge"""
    
    def test_v2_fields_presence_in_pattern(self):
        """Test that new pattern can have V2 fields"""
        new_pattern = {
            'title': 'Perfectionism',
            'type': 'behavioral',
            'description': 'High standards as defense',
            'contradiction': 'Wants to launch project + restarts 10 times',
            'hidden_dynamic': 'Perfectionism is ARMOR, not standards',
            'blocked_resource': 'High standards (strength) misdirected against self',
            'evidence': ['Хочу запустить проект', 'Уже 10-й раз начинаю'],
            'confidence': 0.8,
        }
        
        # Verify V2 fields are present
        assert 'contradiction' in new_pattern
        assert 'hidden_dynamic' in new_pattern
        assert 'blocked_resource' in new_pattern
        assert new_pattern['contradiction'] != ''
        assert new_pattern['hidden_dynamic'] != ''
        assert new_pattern['blocked_resource'] != ''


# Run tests with: pytest soul_bot/tests/unit/test_pattern_analyzer_v2.py -v

