"""
🌡️ Temperature Adapter - автоматическая адаптация стиля по эмоциональному состоянию

Зачем:
- Пользователь установил tone=sarcastic, но сейчас у него stress_level=high
- Нужно ВРЕМЕННО переключить tone на friendly + brief
- Это не меняет настройки пользователя, только текущий ответ

Логика:
- HIGH STRESS → brief + friendly (краткость + поддержка)
- LOW ENERGY → brief (не перегружаем)
- ENERGETIC → motivating + драйв
- SLIGHTLY_DOWN → friendly + empathetic

Автор: AI Agent Team
Создан: 2025-10-31
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def adapt_style_to_temperature(profile) -> dict:
    """
    Адаптировать стиль на основе эмоционального состояния
    
    Возвращает overrides которые ВРЕМЕННО переопределяют настройки пользователя
    только для текущего ответа (не сохраняются в БД).
    
    Args:
        profile: Профиль пользователя с emotional_state
        
    Returns:
        {
            'tone_override': Optional[str],  # None = не переопределяем
            'length_override': Optional[str],  # None = не переопределяем
            'intensity_modifier': float  # 0.5-1.5 (multiplier для temperature)
        }
        
    Examples:
        >>> profile.emotional_state = {'stress_level': 'high', ...}
        >>> overrides = adapt_style_to_temperature(profile)
        >>> overrides['length_override']
        'brief'  # Краткость при стрессе
        
        >>> profile.emotional_state = {'current_mood': 'energetic', ...}
        >>> overrides = adapt_style_to_temperature(profile)
        >>> overrides['tone_override']
        'motivating'  # Мотивация для энергичного состояния
    """
    # Проверяем наличие emotional_state
    emotional_state = getattr(profile, 'emotional_state', {}) or {}
    
    if not emotional_state:
        logger.debug("Temperature adapter: no emotional state, using defaults")
        return {
            'tone_override': None,
            'length_override': None,
            'intensity_modifier': 1.0
        }
    
    stress_level = emotional_state.get('stress_level', 'medium')
    current_mood = emotional_state.get('current_mood', 'neutral')
    energy_level = emotional_state.get('energy_level', 'medium')
    
    overrides = {
        'tone_override': None,
        'length_override': None,
        'intensity_modifier': 1.0
    }
    
    # ==========================================
    # PRIORITY 1: HIGH STRESS (самый важный)
    # ==========================================
    if stress_level == 'high':
        overrides['length_override'] = 'brief'  # Краткость
        overrides['tone_override'] = 'friendly'  # Убираем сарказм/формальность
        overrides['intensity_modifier'] = 0.7  # Спокойнее
        
        logger.debug(
            "Temperature adapter: HIGH STRESS detected → brief + friendly + calm (temp×0.7)"
        )
        return overrides
    
    # ==========================================
    # PRIORITY 2: LOW ENERGY
    # ==========================================
    if energy_level == 'low':
        overrides['length_override'] = 'brief'  # Не перегружаем
        overrides['intensity_modifier'] = 0.8  # Чуть спокойнее
        
        logger.debug(
            "Temperature adapter: LOW ENERGY detected → brief + calm (temp×0.8)"
        )
        return overrides
    
    # ==========================================
    # PRIORITY 3: ENERGETIC MOOD
    # ==========================================
    if current_mood == 'energetic':
        overrides['tone_override'] = 'motivating'  # Мотивация
        overrides['intensity_modifier'] = 1.3  # Больше драйва
        
        logger.debug(
            "Temperature adapter: ENERGETIC mood → motivating + drive (temp×1.3)"
        )
        return overrides
    
    # ==========================================
    # PRIORITY 4: SLIGHTLY DOWN
    # ==========================================
    if current_mood == 'slightly_down':
        overrides['tone_override'] = 'friendly'  # Эмпатия
        overrides['length_override'] = 'medium'  # Больше слов поддержки
        overrides['intensity_modifier'] = 0.9  # Чуть мягче
        
        logger.debug(
            "Temperature adapter: SLIGHTLY DOWN → friendly + medium + soft (temp×0.9)"
        )
        return overrides
    
    # ==========================================
    # DEFAULT: Нет переопределений
    # ==========================================
    logger.debug("Temperature adapter: neutral state, no overrides")
    return overrides


def apply_overrides(
    current_tone: str,
    current_personality: str,
    current_length: str,
    overrides: dict
) -> tuple[str, str, str]:
    """
    Применить overrides к текущим настройкам
    
    Args:
        current_tone: Текущий тон пользователя
        current_personality: Текущая личность
        current_length: Текущая длина
        overrides: Результат adapt_style_to_temperature()
        
    Returns:
        (effective_tone, effective_personality, effective_length)
        
    Examples:
        >>> apply_overrides('sarcastic', 'coach', 'detailed', 
        ...                 {'tone_override': 'friendly', 'length_override': 'brief'})
        ('friendly', 'coach', 'brief')
    """
    effective_tone = overrides.get('tone_override') or current_tone
    effective_personality = current_personality  # personality не переопределяем
    effective_length = overrides.get('length_override') or current_length
    
    return effective_tone, effective_personality, effective_length


__all__ = ['adapt_style_to_temperature', 'apply_overrides']

