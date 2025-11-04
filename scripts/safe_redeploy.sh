#!/bin/bash
# Safe redeploy without losing database
# Usage: ./scripts/safe_redeploy.sh

set -e

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

# Rebuild and start
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 5

# Show status
echo ""
echo "📊 Service status:"
docker-compose ps

echo ""
echo "✅ Redeploy complete! Showing bot logs..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker-compose logs -f --tail=50 bot

