#!/bin/bash
set -e

# ✅ PostgreSQL initialization script
# This script runs ONLY when PostgreSQL container starts for the first time
# (when /var/lib/postgresql/data is empty)
# 
# NOTE: This script does NOT run on container restart with existing volume!
# Tables are created by SQLAlchemy in bot.py startup

DB_NAME="${POSTGRES_DB:-soul_bot}"
DB_USER="${POSTGRES_USER:-postgres}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 PostgreSQL First-Time Initialization"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo ""

# Create database if it doesn't exist
echo "📊 Creating database '${DB_NAME}'..."
psql -v ON_ERROR_STOP=1 --username "${DB_USER}" --dbname "postgres" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}') THEN
            CREATE DATABASE ${DB_NAME};
            RAISE NOTICE '✅ Database ${DB_NAME} created';
        ELSE
            RAISE NOTICE 'ℹ️  Database ${DB_NAME} already exists';
        END IF;
    END
    \$\$;
EOSQL

# Configure database settings for better stability
echo "⚙️  Configuring database settings..."
psql -v ON_ERROR_STOP=1 --username "${DB_USER}" --dbname "${DB_NAME}" <<-EOSQL
    -- Increase connection limits
    ALTER SYSTEM SET max_connections = 200;
    
    -- Improve connection stability
    ALTER SYSTEM SET tcp_keepalives_idle = 60;
    ALTER SYSTEM SET tcp_keepalives_interval = 10;
    ALTER SYSTEM SET tcp_keepalives_count = 6;
    
    -- Set reasonable timeouts
    ALTER SYSTEM SET statement_timeout = '30s';
    ALTER SYSTEM SET idle_in_transaction_session_timeout = '5min';
    
    -- Better logging for debugging
    ALTER SYSTEM SET log_connections = on;
    ALTER SYSTEM SET log_disconnections = on;
    ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
EOSQL

echo ""
echo "✅ Database '${DB_NAME}' initialized successfully!"
echo "ℹ️  Note: Tables will be created by the bot on startup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

