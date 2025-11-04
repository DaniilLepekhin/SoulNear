-- Migration: Cleanup unused fields
-- Date: 2025-10-31
-- Description: Remove conversation_metrics field that was declared but never used

-- Drop conversation_metrics column from user_profiles
ALTER TABLE user_profiles DROP COLUMN IF EXISTS conversation_metrics;

