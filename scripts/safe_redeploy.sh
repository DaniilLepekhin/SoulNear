#!/bin/bash
# Safe redeploy with database preservation
# Usage: 
#   ./scripts/safe_redeploy.sh           # Keep database (safe)
#   ./scripts/safe_redeploy.sh --clean   # Clean database (fresh start)

set -e

CLEAN_DB=false
BACKUP_DB=true

# Parse arguments
if [[ "$1" == "--clean" ]] || [[ "$1" == "-c" ]]; then
    CLEAN_DB=true
    echo "⚠️  WARNING: Database will be cleaned!"
    read -p "Are you sure? Type 'yes' to confirm: " -r
    if [[ ! $REPLY =~ ^yes$ ]]; then
        echo "❌ Aborted"
        exit 1
    fi
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Safe Redeploy Starting"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Backup database if it exists and we're keeping it
if [ "$CLEAN_DB" = false ] && docker ps -q -f name=soulnear_postgres > /dev/null 2>&1; then
    echo "💾 Creating database backup..."
    mkdir -p backups
    BACKUP_FILE="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
    docker exec soulnear_postgres pg_dump -U postgres soul_bot > "$BACKUP_FILE" 2>/dev/null || {
        echo "⚠️  Backup failed (database might be empty or not accessible)"
    }
    if [ -f "$BACKUP_FILE" ]; then
        echo "✅ Backup saved: $BACKUP_FILE"
    fi
fi

# Pull latest changes
echo "📥 Pulling latest code from git..."
git pull

# Stop containers gracefully
echo "🛑 Stopping containers..."
docker-compose down --timeout 30

# Remove old container metadata
echo "🧹 Cleaning old container metadata..."
docker rm -f soulnear_postgres soulnear_bot soulnear_api 2>/dev/null || true

# Clean volumes if requested
if [ "$CLEAN_DB" = true ]; then
    echo "🗑️  Removing database volume..."
    docker volume rm soulnear_postgres_data 2>/dev/null || true
    echo "✅ Database volume removed (fresh start)"
fi

# Rebuild images
echo "🔨 Building Docker images..."
docker-compose build --no-cache

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for PostgreSQL to be healthy
echo "⏳ Waiting for PostgreSQL to be ready..."
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker exec soulnear_postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    echo -n "."
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "❌ PostgreSQL did not start in time"
    docker-compose logs postgres
    exit 1
fi

# Wait a bit more for bot to initialize
echo "⏳ Waiting for bot initialization..."
sleep 5

# Check if bot started successfully
echo ""
echo "📊 Service Status:"
docker-compose ps

# Check bot logs for errors
echo ""
echo "📋 Recent Bot Logs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker-compose logs --tail=30 bot

# Check for critical errors
if docker-compose logs --tail=50 bot | grep -q "ERROR\|Traceback\|Exception"; then
    echo ""
    echo "⚠️  WARNING: Detected errors in bot logs!"
    echo "Review the logs above carefully."
else
    echo ""
    echo "✅ Bot appears to be running without errors"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Redeploy Complete!"
echo ""
echo "Useful commands:"
echo "  make logs-bot     # Watch bot logs"
echo "  make logs-db      # Watch database logs"
echo "  make ps           # Check service status"
echo "  make shell-db     # Connect to database"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

