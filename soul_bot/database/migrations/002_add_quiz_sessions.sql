-- Migration: Add quiz_sessions table for Stage 4 (Dynamic Quiz System)
-- Date: 2025-10-29
-- Description: Адаптивные опросники для углубленного анализа профиля пользователя

CREATE TABLE IF NOT EXISTS quiz_sessions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    assistant_type VARCHAR(64) DEFAULT 'helper',
    
    -- Quiz metadata
    category VARCHAR(64) NOT NULL,  -- 'relationships', 'money', 'confidence', 'fears'
    status VARCHAR(32) NOT NULL DEFAULT 'in_progress',  -- 'in_progress', 'completed', 'cancelled'
    
    -- Progress tracking
    current_question_index INT NOT NULL DEFAULT 0,
    total_questions INT,
    
    -- Data storage (JSONB for flexibility)
    questions JSONB NOT NULL DEFAULT '[]',  -- [{"id": 0, "text": "...", "context": "..."}]
    answers JSONB NOT NULL DEFAULT '[]',     -- [{"question_id": 0, "text": "...", "timestamp": "..."}]
    
    -- Analysis results
    patterns JSONB,  -- Patterns extracted from quiz
    insights JSONB,  -- High-level insights
    recommendations JSONB,  -- Actionable recommendations
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    -- Foreign key constraint
    CONSTRAINT fk_quiz_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_quiz_user_status ON quiz_sessions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_quiz_category ON quiz_sessions(category);
CREATE INDEX IF NOT EXISTS idx_quiz_created ON quiz_sessions(created_at DESC);

-- Comments for documentation
COMMENT ON TABLE quiz_sessions IS 'Storage for user quiz sessions (Stage 4: Dynamic Quiz System)';
COMMENT ON COLUMN quiz_sessions.category IS 'Quiz category: relationships, money, confidence, fears';
COMMENT ON COLUMN quiz_sessions.status IS 'Current status: in_progress, completed, cancelled';
COMMENT ON COLUMN quiz_sessions.questions IS 'Array of question objects (pre-generated or dynamic)';
COMMENT ON COLUMN quiz_sessions.answers IS 'Array of user answers with timestamps';
COMMENT ON COLUMN quiz_sessions.patterns IS 'Patterns extracted from quiz answers';
COMMENT ON COLUMN quiz_sessions.insights IS 'High-level insights generated from patterns';
COMMENT ON COLUMN quiz_sessions.recommendations IS 'Actionable recommendations for user';
