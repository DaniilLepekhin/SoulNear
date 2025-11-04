"""
Quiz Service (Stage 4 - Modular Architecture)

Сервис для работы с динамическими квизами

Модули:
- generator: Генерация вопросов (MVP → V2 → V3)
- analyzer: Анализ результатов (переиспользует pattern_analyzer)
"""
from . import generator
from . import analyzer

__all__ = ['generator', 'analyzer']

