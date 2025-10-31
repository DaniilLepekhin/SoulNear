"""
🧠 Pattern Analyzer Service - Автоматический анализ паттернов пользователя

Основные функции:
1. Quick Analysis (после 5 сообщений) - паттерны + mood
2. Deep Analysis (после 20 сообщений) - инсайты + recommendations
3. Дедупликация через embeddings
4. Learning loop (что работает/не работает)

Architecture: Moderate + Embeddings
"""
import logging
import uuid
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Optional
import json

from openai import AsyncOpenAI
from sqlalchemy import update

from config import OPENAI_API_KEY, is_feature_enabled
from bot.services import embedding_service
from bot.services.constants import (
    SIMILARITY_THRESHOLD_DUPLICATE,
    SIMILARITY_THRESHOLD_RELATED,
    QUICK_ANALYSIS_FREQUENCY,
    DEEP_ANALYSIS_FREQUENCY,
    QUICK_ANALYSIS_CONTEXT_SIZE,
    DEEP_ANALYSIS_CONTEXT_SIZE,
    QUICK_ANALYSIS_MIN_MESSAGES,
    DEEP_ANALYSIS_MIN_MESSAGES,
    MAX_EVIDENCE_PER_PATTERN,
    MAX_INSIGHTS,
    MAX_LEARNING_ITEMS,
    MODEL_ANALYSIS,
    TEMPERATURE_ANALYSIS
)
from bot.services.prompt.analysis_prompts import get_quick_analysis_prompt, get_deep_analysis_prompt
from database.repository import user_profile, conversation_history
from database.database import db
from database.models.user_profile import UserProfile
import database.repository.user as db_user

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# ==========================================
# 🎯 QUICK ANALYSIS (каждые 5 сообщений)
# ==========================================

async def quick_analysis(user_id: int, assistant_type: str = 'helper'):
    """
    Быстрый анализ последних 5-10 сообщений
    
    Выявляет:
    - 1-2 новых паттерна (если есть)
    - Текущее настроение (mood)
    - Уровень стресса/энергии
    
    Args:
        user_id: ID пользователя
        assistant_type: Тип ассистента
    """
    if not is_feature_enabled('ENABLE_PATTERN_ANALYSIS'):
        return
    
    try:
        logger.info(f"Quick analysis for user {user_id}")
        
        # Получаем последние сообщения (из constants)
        messages = await conversation_history.get_context(
            user_id=user_id,
            assistant_type=assistant_type,
            max_messages=QUICK_ANALYSIS_CONTEXT_SIZE
        )
        
        if len(messages) < QUICK_ANALYSIS_MIN_MESSAGES:
            logger.debug("Not enough messages for analysis")
            return
        
        # Получаем текущий профиль
        profile = await user_profile.get_or_create(user_id)
        existing_patterns = profile.patterns.get('patterns', [])
        
        # Анализируем через GPT-4
        analysis = await _analyze_conversation_quick(messages, existing_patterns)
        
        if not analysis:
            logger.warning(f"[QUICK ANALYSIS] User {user_id}: GPT returned None")
            return
        
        # LOG: Сколько паттернов вернул GPT
        new_patterns_count = len(analysis.get('new_patterns', []))
        logger.info(f"[QUICK ANALYSIS] User {user_id}: GPT returned {new_patterns_count} new patterns")
        
        # Обновляем паттерны (с дедупликацией)
        if analysis.get('new_patterns'):
            await _add_patterns_with_dedup(user_id, analysis['new_patterns'], existing_patterns)
            # LOG: Сколько паттернов после мерджа
            updated_profile = await user_profile.get_or_create(user_id)
            total_patterns = len(updated_profile.patterns.get('patterns', []))
            logger.info(f"[QUICK ANALYSIS] User {user_id}: Total patterns after merge: {total_patterns}")
        
        # Обновляем emotional state
        if analysis.get('mood'):
            await _update_emotional_state(user_id, analysis['mood'])
        
        logger.info(f"Quick analysis complete: {len(analysis.get('new_patterns', []))} patterns, mood={analysis.get('mood', {}).get('current_mood')}")
        
    except Exception as e:
        logger.error(f"Quick analysis failed: {e}")


async def _analyze_conversation_quick(
    messages: list[dict],
    existing_patterns: list[dict]
) -> Optional[dict]:
    """
    GPT-4 анализ диалога (quick version)
    """
    # Формируем контекст диалога
    conversation_text = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in messages[-10:]
    ])
    
    # Ограничиваем размер existing patterns (GPT-4 контекст)
    existing_summaries = [
        f"- {p['title']}" 
        for p in existing_patterns[:10]
    ]
    
    # Используем промпт из отдельного модуля
    prompt = get_quick_analysis_prompt(conversation_text, existing_summaries)
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Дешевле для quick analysis
            messages=[
                {"role": "system", "content": "You are an expert psychologist analyzing conversation patterns."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        logger.error(f"GPT-4 analysis failed: {e}")
        return None


# ==========================================
# 🔍 DEEP ANALYSIS (каждые 20 сообщений)
# ==========================================

async def deep_analysis(user_id: int, assistant_type: str = 'helper'):
    """
    Глубокий анализ паттернов и генерация инсайтов
    
    Выявляет:
    - Связи между паттернами
    - Долгосрочные тренды
    - Инсайты с рекомендациями
    - Обновляет learning preferences
    
    Args:
        user_id: ID пользователя
        assistant_type: Тип ассистента
    """
    if not is_feature_enabled('ENABLE_PATTERN_ANALYSIS'):
        return
    
    try:
        logger.info(f"Deep analysis for user {user_id}")
        
        # Получаем последние сообщения (из constants)
        messages = await conversation_history.get_context(
            user_id=user_id,
            assistant_type=assistant_type,
            max_messages=DEEP_ANALYSIS_CONTEXT_SIZE
        )
        
        if len(messages) < DEEP_ANALYSIS_MIN_MESSAGES:
            logger.debug("Not enough messages for deep analysis")
            return
        
        # Получаем текущий профиль
        profile = await user_profile.get_or_create(user_id)
        existing_patterns = profile.patterns.get('patterns', [])
        existing_insights = profile.insights.get('insights', [])
        
        # Анализируем через GPT-4
        analysis = await _analyze_conversation_deep(messages, existing_patterns, existing_insights)
        
        if not analysis:
            return
        
        # Генерируем инсайты
        if analysis.get('insights'):
            await _add_insights(user_id, analysis['insights'], existing_patterns)
        
        # Обновляем related patterns
        if existing_patterns:
            await _update_related_patterns(user_id, existing_patterns)
        
        # Обновляем learning preferences
        if analysis.get('learning'):
            await _update_learning_preferences(user_id, analysis['learning'])
        
        logger.info(f"Deep analysis complete: {len(analysis.get('insights', []))} insights generated")
        
    except Exception as e:
        logger.error(f"Deep analysis failed: {e}")


async def _analyze_conversation_deep(
    messages: list[dict],
    existing_patterns: list[dict],
    existing_insights: list[dict]
) -> Optional[dict]:
    """
    GPT-4 глубокий анализ (insights + recommendations)
    """
    conversation_text = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in messages[-30:]
    ])
    
    patterns_summary = "\n".join([
        f"- [{p['type']}] {p['title']}: {p['description']} (occurs: {p.get('occurrences', 1)}x)"
        for p in existing_patterns[:15]
    ])
    
    # Используем промпт из отдельного модуля
    prompt = get_deep_analysis_prompt(conversation_text, patterns_summary)
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",  # Используем полную версию для deep analysis
            messages=[
                {"role": "system", "content": "You are an expert psychologist providing deep insights."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.4
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        logger.error(f"GPT-4 deep analysis failed: {e}")
        return None


# ==========================================
# 🔄 ДЕДУПЛИКАЦИЯ И МЕРДЖ ПАТТЕРНОВ
# ==========================================

async def _add_patterns_with_dedup(
    user_id: int,
    new_patterns: list[dict],
    existing_patterns: list[dict]
):
    """
    Добавить паттерны с проверкой на дубликаты через embeddings
    
    Двухфакторный мердж:
    1. Keyword match (exact title) → форсированный мердж (100% уверенность)
    2. Semantic similarity (embedding > threshold) → обычный мердж
    """
    for new_pattern in new_patterns:
        try:
            # Генерируем текст для embedding
            pattern_text = f"{new_pattern['title']} {new_pattern['description']}"
            
            # FACTOR 1: Keyword match (exact title)
            keyword_match = None
            for existing in existing_patterns:
                if existing['title'].lower().strip() == new_pattern['title'].lower().strip():
                    keyword_match = existing
                    break
            
            # FACTOR 2: Semantic similarity
            is_dup, duplicate, similarity = await embedding_service.is_duplicate(
                pattern_text,
                existing_patterns,
                text_key='description',
                threshold=SIMILARITY_THRESHOLD_DUPLICATE
            )
            
            # Двухфакторное решение: keyword match > semantic similarity
            if keyword_match:
                # FORCED MERGE по keyword (100% уверенность)
                duplicate = keyword_match
                is_dup = True
                similarity = 1.0
                logger.info(f"🔑 KEYWORD MATCH: '{new_pattern['title']}' → forced merge")
            
            if is_dup:
                # Мерджим с существующим
                old_occurrences = duplicate.get('occurrences', 1)
                duplicate['occurrences'] = old_occurrences + 1
                
                # Добавляем новые evidence (без дубликатов, максимум 10)
                existing_evidence = set(duplicate.get('evidence', []))
                new_evidence = [e for e in new_pattern.get('evidence', []) if e not in existing_evidence]
                duplicate['evidence'].extend(new_evidence)
                duplicate['evidence'] = duplicate['evidence'][-10:]  # Limit to last 10
                
                duplicate['last_detected'] = datetime.now().isoformat()
                duplicate['confidence'] = max(duplicate['confidence'], new_pattern.get('confidence', 0.7))
                
                logger.info(f"✅ MERGED: '{new_pattern['title']}' → '{duplicate['title']}' | similarity: {similarity:.2f} | occurrences: {old_occurrences} → {duplicate['occurrences']}")
            else:
                # Добавляем новый
                new_pattern['id'] = str(uuid.uuid4())
                new_pattern['first_detected'] = datetime.now().isoformat()
                new_pattern['last_detected'] = datetime.now().isoformat()
                new_pattern['occurrences'] = 1
                new_pattern['related_patterns'] = []
                
                # Генерируем embedding
                new_pattern['embedding'] = await embedding_service.get_embedding(pattern_text)
                
                existing_patterns.append(new_pattern)
                
                logger.info(f"Added new pattern: {new_pattern['title']}")
        
        except Exception as e:
            logger.error(f"Failed to process pattern: {e}")
            continue
    
    # Limit: максимум 20 паттернов (удаляем старые с низким confidence)
    if len(existing_patterns) > 20:
        existing_patterns.sort(
            key=lambda x: (x.get('confidence', 0.5), x.get('occurrences', 1)),
            reverse=True
        )
        existing_patterns = existing_patterns[:20]
    
    # Сохраняем
    await user_profile.update_patterns(user_id, existing_patterns)


async def _update_related_patterns(user_id: int, patterns: list[dict]):
    """
    Обновить related_patterns через semantic similarity
    """
    for i, pattern in enumerate(patterns):
        if 'embedding' not in pattern or not pattern['embedding']:
            continue
        
        # Находим 3 наиболее похожих паттерна (исключая себя)
        other_patterns = [p for j, p in enumerate(patterns) if j != i]
        
        related = await embedding_service.find_similar_items(
            pattern['embedding'],
            other_patterns,
            threshold=SIMILARITY_THRESHOLD_RELATED,
            top_k=3
        )
        
        pattern['related_patterns'] = [p['id'] for p, _ in related]
    
    # Сохраняем обновлённые паттерны
    await user_profile.update_patterns(user_id, patterns)


# ==========================================
# 💡 ИНСАЙТЫ
# ==========================================

async def _add_insights(user_id: int, new_insights: list[dict], existing_patterns: list[dict]):
    """
    Добавить инсайты (с связью к паттернам)
    """
    profile = await user_profile.get_or_create(user_id)
    existing_insights = profile.insights.get('insights', [])
    
    for insight in new_insights:
        # Генерируем ID
        insight['id'] = str(uuid.uuid4())
        insight['created_at'] = datetime.now().isoformat()
        insight['last_updated'] = datetime.now().isoformat()
        
        # Связываем с паттернами (по title)
        derived_titles = insight.get('derived_from_pattern_titles', [])
        insight['derived_from'] = [
            p['id'] for p in existing_patterns
            if p['title'] in derived_titles
        ]
        
        existing_insights.append(insight)
    
    # Limit: максимум 10 инсайтов
    if len(existing_insights) > 10:
        existing_insights = existing_insights[-10:]
    
    # Сохраняем
    await user_profile.update_insights(user_id, existing_insights)


# ==========================================
# 😊 EMOTIONAL STATE
# ==========================================

async def _update_emotional_state(user_id: int, mood_data: dict):
    """
    Обновить эмоциональное состояние
    """
    profile = await user_profile.get_or_create(user_id)
    emotional_state = profile.emotional_state
    
    # Обновляем текущее состояние
    emotional_state['current_mood'] = mood_data.get('current_mood', 'neutral')
    emotional_state['stress_level'] = mood_data.get('stress_level', 'medium')
    emotional_state['energy_level'] = mood_data.get('energy_level', 'medium')
    
    # Добавляем в историю (limit: последние 30 дней)
    mood_history = emotional_state.get('mood_history', [])
    today = datetime.now().date().isoformat()
    
    # Удаляем сегодняшнюю запись если есть (будем обновлять)
    mood_history = [m for m in mood_history if m.get('date') != today]
    
    # Добавляем новую
    mood_history.append({
        'date': today,
        'mood': mood_data.get('current_mood'),
        'triggers': mood_data.get('triggers', [])
    })
    
    # Limit: последние 30 записей
    emotional_state['mood_history'] = mood_history[-30:]
    
    # Сохраняем
    async with db() as session:
        await session.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(
                emotional_state=emotional_state,
                updated_at=datetime.now()
            )
        )
        await session.commit()


# ==========================================
# 🎓 LEARNING PREFERENCES
# ==========================================

async def _update_learning_preferences(user_id: int, learning_data: dict):
    """
    Обновить learning preferences (что работает/не работает)
    
    Использует OrderedDict для сохранения порядка (новые элементы в конец).
    Это важно для UI - показываем последние предпочтения первыми.
    """
    profile = await user_profile.get_or_create(user_id)
    learning_prefs = profile.learning_preferences
    
    # Используем OrderedDict для сохранения порядка (новые в конец)
    # Ключи = items, значения = None (нужны только уникальные ключи)
    works_well = OrderedDict.fromkeys(learning_prefs.get('works_well', []))
    doesnt_work = OrderedDict.fromkeys(learning_prefs.get('doesnt_work', []))
    
    # Добавляем новые элементы (дедупликация автоматическая)
    for item in learning_data.get('works_well', []):
        works_well[item] = None
    for item in learning_data.get('doesnt_work', []):
        doesnt_work[item] = None
    
    # Limit: последние 10 (самые свежие)
    learning_prefs['works_well'] = list(works_well.keys())[-MAX_LEARNING_ITEMS:]
    learning_prefs['doesnt_work'] = list(doesnt_work.keys())[-MAX_LEARNING_ITEMS:]
    
    # Сохраняем
    async with db() as session:
        await session.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(
                learning_preferences=learning_prefs,
                updated_at=datetime.now()
            )
        )
        await session.commit()


# ==========================================
# 🎯 PUBLIC API
# ==========================================

async def analyze_if_needed(user_id: int, assistant_type: str = 'helper'):
    """
    Проверить нужен ли анализ и запустить если нужно
    
    Триггеры:
    - После 3 сообщений → quick analysis (увеличено с 5 для роста occurrences)
    - После 20 сообщений → deep analysis
    
    Args:
        user_id: ID пользователя
        assistant_type: Тип ассистента
    """
    if not is_feature_enabled('ENABLE_PATTERN_ANALYSIS'):
        return
    
    # Считаем сообщения
    message_count = await conversation_history.count_messages(user_id, assistant_type)
    
    # Quick analysis (частота из constants)
    if message_count > 0 and message_count % QUICK_ANALYSIS_FREQUENCY == 0:
        await quick_analysis(user_id, assistant_type)
    
    # Deep analysis (частота из constants)
    if message_count > 0 and message_count % DEEP_ANALYSIS_FREQUENCY == 0:
        await deep_analysis(user_id, assistant_type)

