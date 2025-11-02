#!/bin/bash
set -e

# ✅ FIX: Auto-create database if it doesn't exist
# This script runs when PostgreSQL container starts for the first time

echo "🔧 Checking if database '$POSTGRES_DB' exists..."

# Check if database exists
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    SELECT 'CREATE DATABASE $POSTGRES_DB'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$POSTGRES_DB')\gexec
EOSQL

echo "✅ Database '$POSTGRES_DB' is ready!"

