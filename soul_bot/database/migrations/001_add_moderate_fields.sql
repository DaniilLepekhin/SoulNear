-- Миграция: Добавление новых полей для Moderate структуры
-- Дата: 2025-10-24
-- Stage 3: Auto-updating Profile

-- Добавляем новые JSONB поля для emotional_state, conversation_metrics, learning_preferences
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS emotional_state JSONB DEFAULT '{
  "current_mood": "neutral",
  "mood_history": [],
  "stress_level": "medium",
  "energy_level": "medium"
}'::jsonb;

ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS conversation_metrics JSONB DEFAULT '{
  "total_messages": 0,
  "avg_session_length": 0,
  "most_discussed_topics": [],
  "question_types": {}
}'::jsonb;

ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS learning_preferences JSONB DEFAULT '{
  "works_well": [],
  "doesnt_work": []
}'::jsonb;

-- Обновляем существующие пустые patterns/insights на новый формат
UPDATE user_profiles 
SET patterns = '{"patterns": []}'::jsonb 
WHERE patterns IS NULL OR patterns = '{}'::jsonb;

UPDATE user_profiles 
SET insights = '{"insights": []}'::jsonb 
WHERE insights IS NULL OR insights = '{}'::jsonb;

-- Добавляем индексы для JSONB полей (для быстрого поиска)
CREATE INDEX IF NOT EXISTS idx_user_profiles_patterns_gin ON user_profiles USING gin (patterns);
CREATE INDEX IF NOT EXISTS idx_user_profiles_insights_gin ON user_profiles USING gin (insights);
CREATE INDEX IF NOT EXISTS idx_user_profiles_emotional_state_gin ON user_profiles USING gin (emotional_state);

-- Комментарии для документации
COMMENT ON COLUMN user_profiles.emotional_state IS 'Текущее эмоциональное состояние и история (Moderate структура)';
COMMENT ON COLUMN user_profiles.conversation_metrics IS 'Метрики и статистика коммуникации';
COMMENT ON COLUMN user_profiles.learning_preferences IS 'Что работает/не работает для пользователя (learning loop)';

