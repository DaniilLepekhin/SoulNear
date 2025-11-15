-- Migration: Add broadcast system fields
-- Date: 2025-11-15

-- Add broadcast system columns for general messaging
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_broadcast_message INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_broadcast_sent TIMESTAMP NULL;

-- Update existing users to have default values
UPDATE users SET last_broadcast_message = 0 WHERE last_broadcast_message IS NULL;
