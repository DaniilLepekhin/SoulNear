-- Миграция: Добавление таблицы quiz_sessions
-- Дата: 2025-10-24
-- Stage 4: Dynamic Quiz

-- Создаём таблицу quiz_sessions
CREATE TABLE IF NOT EXISTS quiz_sessions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    
    -- Категория и статус
    category VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'in_progress',
    
    -- Данные квиза (JSONB для гибкости)
    data JSONB NOT NULL DEFAULT '{"questions": [], "answers": [], "current_question_index": 0, "total_questions": 10}'::jsonb,
    
    -- Результаты анализа
    results JSONB,
    
    -- Временные метки
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    last_activity_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Метаданные
    source VARCHAR(32) NOT NULL DEFAULT 'menu',
    duration_seconds INTEGER
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_id ON quiz_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_status ON quiz_sessions(status);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_created_at ON quiz_sessions(created_at);

-- Индекс для поиска активных сессий
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_active ON quiz_sessions(user_id, status) 
WHERE status = 'in_progress';

-- GIN индекс для JSONB полей
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_data_gin ON quiz_sessions USING gin (data);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_results_gin ON quiz_sessions USING gin (results);

-- Комментарии
COMMENT ON TABLE quiz_sessions IS 'Сессии прохождения квизов (Stage 4)';
COMMENT ON COLUMN quiz_sessions.data IS 'Вопросы и ответы квиза (JSONB для гибкости)';
COMMENT ON COLUMN quiz_sessions.results IS 'Результаты анализа (patterns, insights, recommendations)';
COMMENT ON COLUMN quiz_sessions.status IS 'Статус: in_progress, completed, abandoned, cancelled';

