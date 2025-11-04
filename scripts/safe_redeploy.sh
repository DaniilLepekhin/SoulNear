#!/bin/bash
# Safe redeploy without losing database
# Usage: 
#   ./scripts/safe_redeploy.sh           # Keep database
#   ./scripts/safe_redeploy.sh --clean   # Clean database (fresh start)

set -e

CLEAN_DB=false

# Parse arguments
if [[ "$1" == "--clean" ]] || [[ "$1" == "-c" ]]; then
    CLEAN_DB=true
    echo "⚠️  WARNING: Database will be cleaned!"
fi

echo "🔄 Safe redeploy starting..."

# Pull latest changes
echo "📥 Pulling from git..."
git pull

# Stop and remove containers (but keep volumes!)
echo "🛑 Stopping containers..."
docker-compose down

# Remove old container images metadata to avoid 'ContainerConfig' errors
echo "🧹 Cleaning old container metadata..."
docker rm -f soulnear_postgres soulnear_bot soulnear_api 2>/dev/null || true

# Clean volumes if requested
if [ "$CLEAN_DB" = true ]; then
    echo "🗑️  Removing database volume (fresh DB)..."
    docker volume rm soulnear_postgres_data 2>/dev/null || true
fi

# Rebuild and start
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Show status
echo ""
echo "📊 Service status:"
docker-compose ps

echo ""
echo "✅ Redeploy complete! Showing bot logs..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker-compose logs -f --tail=50 bot

