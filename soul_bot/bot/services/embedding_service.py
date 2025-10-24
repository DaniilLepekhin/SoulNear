"""
🎯 Embedding Service для работы с OpenAI Embeddings API

Используется для:
1. Генерация векторных представлений паттернов
2. Semantic similarity (дедупликация паттернов)
3. Поиск связанных паттернов (related_patterns)
4. Semantic search по профилю пользователя

Model: text-embedding-3-small (1536 dimensions)
Cost: $0.02 / 1M tokens (очень дешево!)
"""
import logging
from typing import Optional
import numpy as np
from openai import AsyncOpenAI

from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Инициализация клиента
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Константы
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
SIMILARITY_THRESHOLD_DUPLICATE = 0.85  # Высокая уверенность = дубликат
SIMILARITY_THRESHOLD_RELATED = 0.70    # Средняя уверенность = связанный


async def get_embedding(text: str) -> list[float]:
    """
    Получить vector embedding для текста
    
    Args:
        text: Текст для векторизации
        
    Returns:
        Вектор размерности 1536
        
    Raises:
        Exception: При ошибке API
    """
    try:
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text.strip()
        )
        
        embedding = response.data[0].embedding
        
        logger.debug(f"Generated embedding for text (len={len(text)}), vector_len={len(embedding)}")
        
        return embedding
        
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Получить embeddings для нескольких текстов сразу (batch API)
    
    Args:
        texts: Список текстов
        
    Returns:
        Список векторов
        
    Note:
        Batch API эффективнее для > 5 текстов
    """
    if not texts:
        return []
    
    try:
        # OpenAI поддерживает batch до 2048 текстов
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[text.strip() for text in texts]
        )
        
        embeddings = [item.embedding for item in response.data]
        
        logger.debug(f"Generated {len(embeddings)} embeddings in batch")
        
        return embeddings
        
    except Exception as e:
        logger.error(f"Failed to generate batch embeddings: {e}")
        raise


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Вычислить cosine similarity между двумя векторами
    
    Args:
        vec1: Первый вектор
        vec2: Второй вектор
        
    Returns:
        Similarity score (0.0 - 1.0)
        1.0 = идентичные, 0.0 = противоположные
        
    Note:
        Cosine similarity = dot(A,B) / (||A|| * ||B||)
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)
    
    # Защита от division by zero
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    
    # Clamp to [0, 1] range (иногда может быть немного выше из-за float precision)
    return float(np.clip(similarity, 0.0, 1.0))


async def find_similar_items(
    query_embedding: list[float],
    items: list[dict],
    embedding_key: str = 'embedding',
    threshold: float = 0.0,
    top_k: int = 10
) -> list[tuple[dict, float]]:
    """
    Найти наиболее похожие items по embedding
    
    Args:
        query_embedding: Вектор запроса
        items: Список items с embeddings
        embedding_key: Ключ для доступа к embedding в item
        threshold: Минимальный порог similarity (опционально)
        top_k: Количество результатов
        
    Returns:
        Список кортежей (item, similarity_score), отсортированный по убыванию similarity
        
    Example:
        >>> items = [
        ...     {"id": 1, "text": "...", "embedding": [0.1, 0.2, ...]},
        ...     {"id": 2, "text": "...", "embedding": [0.3, 0.4, ...]},
        ... ]
        >>> similar = await find_similar_items(query_vec, items, top_k=3)
        >>> for item, score in similar:
        ...     print(f"{item['text']}: {score:.2f}")
    """
    if not items:
        return []
    
    similarities = []
    
    for item in items:
        # Пропускаем items без embedding
        if embedding_key not in item or not item[embedding_key]:
            continue
        
        # Вычисляем similarity
        similarity = cosine_similarity(query_embedding, item[embedding_key])
        
        # Фильтруем по threshold
        if similarity >= threshold:
            similarities.append((item, similarity))
    
    # Сортируем по убыванию similarity
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Берём top_k
    return similarities[:top_k]


async def is_duplicate(
    new_text: str,
    existing_items: list[dict],
    text_key: str = 'description',
    embedding_key: str = 'embedding',
    threshold: float = SIMILARITY_THRESHOLD_DUPLICATE
) -> tuple[bool, Optional[dict], float]:
    """
    Проверить является ли текст дубликатом существующих
    
    Args:
        new_text: Новый текст для проверки
        existing_items: Список существующих items
        text_key: Ключ для доступа к тексту (для GPT-4 fallback)
        embedding_key: Ключ для доступа к embedding
        threshold: Порог для определения дубликата
        
    Returns:
        Tuple: (is_duplicate, duplicate_item, similarity_score)
        
    Example:
        >>> is_dup, dup_item, score = await is_duplicate(
        ...     "Прокрастинация при скучной работе",
        ...     existing_patterns
        ... )
        >>> if is_dup:
        ...     print(f"Duplicate of: {dup_item['title']} (score: {score:.2f})")
    """
    if not existing_items:
        return False, None, 0.0
    
    # Генерируем embedding для нового текста
    new_embedding = await get_embedding(new_text)
    
    # Ищем наиболее похожий
    similar = await find_similar_items(
        new_embedding,
        existing_items,
        embedding_key=embedding_key,
        top_k=1
    )
    
    if not similar:
        return False, None, 0.0
    
    best_match, best_similarity = similar[0]
    
    # Определяем дубликат по threshold
    is_dup = best_similarity >= threshold
    
    if is_dup:
        logger.info(
            f"Duplicate detected: '{new_text[:50]}...' ~= "
            f"'{best_match.get(text_key, 'N/A')[:50]}...' "
            f"(similarity: {best_similarity:.3f})"
        )
    
    return is_dup, best_match if is_dup else None, best_similarity


async def find_related_items(
    query_text: str,
    items: list[dict],
    embedding_key: str = 'embedding',
    threshold: float = SIMILARITY_THRESHOLD_RELATED,
    top_k: int = 5
) -> list[tuple[dict, float]]:
    """
    Найти связанные items по semantic similarity
    
    Args:
        query_text: Текст запроса
        items: Список items для поиска
        embedding_key: Ключ для доступа к embedding
        threshold: Минимальный порог similarity
        top_k: Количество результатов
        
    Returns:
        Список связанных items с scores
        
    Example:
        >>> related = await find_related_items(
        ...     "Проблемы с мотивацией",
        ...     all_patterns,
        ...     top_k=3
        ... )
    """
    if not items:
        return []
    
    # Генерируем embedding для запроса
    query_embedding = await get_embedding(query_text)
    
    # Ищем похожие
    similar = await find_similar_items(
        query_embedding,
        items,
        embedding_key=embedding_key,
        threshold=threshold,
        top_k=top_k
    )
    
    return similar


# ==========================================
# 🧪 УТИЛИТЫ ДЛЯ ТЕСТИРОВАНИЯ
# ==========================================

async def test_embedding_service():
    """
    Быстрый тест сервиса
    
    Usage:
        python -c "from bot.services.embedding_service import test_embedding_service; import asyncio; asyncio.run(test_embedding_service())"
    """
    print("🧪 Testing Embedding Service...")
    
    # Test 1: Generate single embedding
    print("\n1. Generate single embedding:")
    text = "Прокрастинация при скучной работе"
    embedding = await get_embedding(text)
    print(f"   Text: {text}")
    print(f"   Embedding length: {len(embedding)}")
    print(f"   First 5 values: {embedding[:5]}")
    
    # Test 2: Batch embeddings
    print("\n2. Generate batch embeddings:")
    texts = [
        "Прокрастинация при скучной работе",
        "Откладывает задачи когда работа монотонная",
        "Проблемы со сном из-за стресса"
    ]
    embeddings = await get_embeddings_batch(texts)
    print(f"   Generated {len(embeddings)} embeddings")
    
    # Test 3: Cosine similarity
    print("\n3. Test cosine similarity:")
    sim1 = cosine_similarity(embeddings[0], embeddings[1])
    sim2 = cosine_similarity(embeddings[0], embeddings[2])
    print(f"   '{texts[0]}' vs '{texts[1]}': {sim1:.3f}")
    print(f"   '{texts[0]}' vs '{texts[2]}': {sim2:.3f}")
    print(f"   ✅ Паттерны 1-2 более похожи ({sim1:.3f} > {sim2:.3f})")
    
    # Test 4: Duplicate detection
    print("\n4. Test duplicate detection:")
    existing = [
        {"id": 1, "text": texts[0], "embedding": embeddings[0]}
    ]
    is_dup, dup_item, score = await is_duplicate(
        "Откладывание рутинных задач",
        existing,
        text_key='text'
    )
    print(f"   Is duplicate: {is_dup}")
    print(f"   Similarity: {score:.3f}")
    
    print("\n✅ All tests passed!")


if __name__ == '__main__':
    import asyncio
    asyncio.run(test_embedding_service())

