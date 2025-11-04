#!/bin/bash
set -e

# ✅ FIX: Auto-create database if it doesn't exist
# This script runs when PostgreSQL container starts for the first time

DB_NAME="${POSTGRES_DB:-soul_bot}"
DB_USER="${POSTGRES_USER:-postgres}"

echo "🔧 Initializing database '${DB_NAME}'..."

# Create database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "${DB_USER}" --dbname "postgres" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}') THEN
            CREATE DATABASE ${DB_NAME};
            RAISE NOTICE 'Database ${DB_NAME} created';
        ELSE
            RAISE NOTICE 'Database ${DB_NAME} already exists';
        END IF;
    END
    \$\$;
EOSQL

echo "✅ Database '${DB_NAME}' is ready!"

