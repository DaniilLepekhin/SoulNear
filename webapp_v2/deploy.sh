#!/bin/bash

# ==========================================
# SoulNear WebApp v2 Deployment Script
# ==========================================

echo "🚀 Starting SoulNear WebApp v2 deployment..."

# Configuration
SERVER="root@37.221.127.100"
PORT="61943"
PASSWORD="rX~\$#AJGf}fds1yh"
REMOTE_PATH="/home/soulnear_webapp_v2"

# Build project
echo "📦 Building project..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful"

# Create backup on server
echo "💾 Creating backup on server..."
sshpass -p "${PASSWORD}" ssh -p ${PORT} -o StrictHostKeyChecking=no ${SERVER} \
    "if [ -d ${REMOTE_PATH} ]; then cp -r ${REMOTE_PATH} ${REMOTE_PATH}_backup_\$(date +%Y%m%d_%H%M%S); fi"

echo "✅ Backup created"

# Upload files
echo "📤 Uploading files to server..."
sshpass -p "${PASSWORD}" scp -P ${PORT} -r -o StrictHostKeyChecking=no \
    dist/* ${SERVER}:${REMOTE_PATH}/

if [ $? -ne 0 ]; then
    echo "❌ Upload failed"
    exit 1
fi

echo "✅ Files uploaded"

# Set permissions
echo "🔐 Setting permissions..."
sshpass -p "${PASSWORD}" ssh -p ${PORT} -o StrictHostKeyChecking=no ${SERVER} \
    "chmod -R 755 ${REMOTE_PATH}"

echo "✅ Permissions set"

# Verify deployment
echo "🔍 Verifying deployment..."
FILE_COUNT=$(sshpass -p "${PASSWORD}" ssh -p ${PORT} -o StrictHostKeyChecking=no ${SERVER} \
    "ls -1 ${REMOTE_PATH} | wc -l")

if [ $FILE_COUNT -gt 0 ]; then
    echo "✅ Deployment verified: $FILE_COUNT files deployed"
else
    echo "❌ Deployment verification failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Deployment completed successfully!"
echo "=========================================="
echo ""
echo "📊 Deployment info:"
echo "  Server: ${SERVER}:${PORT}"
echo "  Path: ${REMOTE_PATH}"
echo "  Files: ${FILE_COUNT}"
echo ""
echo "🌐 WebApp URL: https://soulnear.daniillepekhin.com/webapp_2"
echo ""
echo "💡 Next steps:"
echo "  1. Test the webapp in Telegram: /webapp_2"
echo "  2. Check logs if issues occur"
echo "  3. Backup location: ${REMOTE_PATH}_backup_*"
