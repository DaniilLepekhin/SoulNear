#!/bin/bash
# 🧹 Quick wrapper for test database cleanup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Ensure ENV=test
export ENV=test

# Activate venv if it exists
if [ -d "soul_bot/venv" ]; then
    source soul_bot/venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run cleanup script with all arguments passed through
python soul_bot/scripts/cleanup_test_db.py "$@"

