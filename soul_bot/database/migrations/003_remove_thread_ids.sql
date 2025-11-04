-- ==========================================
-- Migration 003: Remove Legacy Thread IDs
-- ==========================================
-- Дата: 2025-10-31
-- Цель: Удалить устаревшие колонки thread_id (legacy Assistant API)
--
-- Context:
-- - Ранее бот использовал OpenAI Assistant API (thread-based)
-- - Теперь полностью перешли на ChatCompletion API
-- - Thread IDs больше не нужны
--
-- Экономия: 3 VARCHAR(32) колонки на каждого пользователя
-- ==========================================

-- Удаляем колонки (IF EXISTS для идемпотентности)
ALTER TABLE users DROP COLUMN IF EXISTS helper_thread_id;
ALTER TABLE users DROP COLUMN IF EXISTS assistant_thread_id;
ALTER TABLE users DROP COLUMN IF EXISTS sleeper_thread_id;

-- Подтверждение
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 003 completed: thread_id columns removed';
END $$;

