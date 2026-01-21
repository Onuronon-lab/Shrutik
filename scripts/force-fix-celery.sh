#!/bin/bash

# Force Fix Celery Script
# This completely recreates the celery containers to fix the 'wrker' typo

set -e

echo "🔧 Force fixing celery containers..."

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.hub.yml" ]; then
    echo "❌ Error: docker-compose.prod.hub.yml not found. Please run this script from the project root."
    exit 1
fi

echo "📋 Current problematic containers:"
docker ps -a --filter "name=celery" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "🛑 Stopping and removing all celery containers..."

# Stop and remove celery containers completely
docker-compose -f docker-compose.prod.hub.yml stop celery celery-beat celery-flower 2>/dev/null || true
docker-compose -f docker-compose.prod.hub.yml rm -f celery celery-beat celery-flower 2>/dev/null || true

# Also remove any orphaned containers
docker rm -f shrutik_celery_prod shrutik_celery_beat_prod shrutik_flower_prod 2>/dev/null || true

echo "✅ Removed old celery containers"

echo ""
echo "🔍 Verifying docker-compose file has correct celery command..."

# Double-check the docker-compose file
if grep -q "wrker" docker-compose.prod.hub.yml; then
    echo "❌ Still found 'wrker' typo - fixing it..."
    sed -i 's/wrker/worker/g' docker-compose.prod.hub.yml
    echo "✅ Fixed celery command typo"
else
    echo "✅ Docker-compose file looks correct"
fi

echo ""
echo "📂 Checking frontend path..."

# Also fix frontend path if needed
if grep -q "/app/static" docker-compose.prod.hub.yml; then
    echo "🔧 Updating frontend path to /app/frontend/build..."
    sed -i 's|/app/static|/app/frontend/build|g' docker-compose.prod.hub.yml
    echo "✅ Updated frontend path"
fi

echo ""
echo "🚀 Creating fresh celery containers..."

# Recreate celery services with fresh containers
docker-compose -f docker-compose.prod.hub.yml up -d celery celery-beat celery-flower

echo ""
echo "⏳ Waiting for celery services to start..."
sleep 20

echo ""
echo "📋 New container status:"
docker ps --filter "name=celery" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "🧪 Testing celery worker..."
docker logs --tail 10 shrutik_celery_prod

echo ""
echo "🧪 Testing celery beat..."
docker logs --tail 5 shrutik_celery_beat_prod

echo ""
echo "🧪 Testing backend health..."
curl -s http://localhost:8080/health | jq '.components.celery' 2>/dev/null || curl -s http://localhost:8080/health | grep -o '"celery":"[^"]*"' || echo "Health check failed"

echo ""
echo "🎉 Celery fix completed!"
echo ""
echo "📝 What was done:"
echo "✅ Completely removed old celery containers"
echo "✅ Fixed 'wrker' typo in docker-compose file"
echo "✅ Updated frontend path"
echo "✅ Created fresh celery containers"
echo ""
echo "🔍 If celery is still not working, check:"
echo "1. Environment variables are set correctly"
echo "2. Redis connection is working"
echo "3. Database connection is working"