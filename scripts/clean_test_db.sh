#!/bin/bash
# 🧹 Quick wrapper for test database cleanup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Ensure ENV=test
export ENV=test

# Run cleanup script with all arguments passed through
python3 soul_bot/scripts/cleanup_test_db.py "$@"

