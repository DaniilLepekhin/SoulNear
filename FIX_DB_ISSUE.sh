#!/bin/bash
# Fix database creation issue by removing old volumes and recreating everything

set -e

echo "🔧 Fixing database creation issue..."
echo ""

# Stop containers
echo "1️⃣ Stopping containers..."
docker-compose down

# Remove containers (force)
echo "2️⃣ Removing old containers..."
docker rm -f soulnear_postgres soulnear_bot soulnear_api 2>/dev/null || true

# Remove ONLY postgres volume (this will trigger init-db.sh on next start)
echo "3️⃣ Removing postgres volume to trigger init script..."
docker volume rm soulnear_postgres_data 2>/dev/null || true

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Now starting services with fresh database..."
echo ""

# Start services
docker-compose up -d --build

echo ""
echo "⏳ Waiting 10 seconds for postgres to initialize..."
sleep 10

echo ""
echo "📊 Service status:"
docker-compose ps

echo ""
echo "📋 Showing bot logs:"
docker-compose logs --tail=50 bot

