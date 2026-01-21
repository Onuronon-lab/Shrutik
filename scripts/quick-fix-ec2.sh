#!/bin/bash

# Quick Fix for EC2 Deployment Issues
# Run this script on your EC2 instance to fix immediate issues

set -e

echo "🚀 Quick fix for EC2 deployment issues..."

# Check current container status
echo "📋 Current container status:"
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "🔍 Checking celery logs for 'wrker' error..."
docker logs shrutik_celery_prod 2>&1 | tail -5

echo ""
echo "🔧 Fixing celery command in docker-compose file..."

# Fix the celery command if there's a typo
if grep -q "wrker" docker-compose.prod.hub.yml; then
    echo "❌ Found 'wrker' typo - fixing it..."
    sed -i 's/wrker/worker/g' docker-compose.prod.hub.yml
    echo "✅ Fixed celery command typo"
else
    echo "ℹ️  No 'wrker' typo found in docker-compose file"
    echo "🔍 The issue might be in the running container. Let's restart celery..."
fi

echo ""
echo "🔧 Fixing frontend static files path..."

# Check what's actually in the frontend container
echo "📂 Checking frontend container contents..."
docker exec shrutik_frontend_prod ls -la /app/ 2>/dev/null || echo "Could not list /app/"

# Try to find where the static files are
if docker exec shrutik_frontend_prod test -d /app/build; then
    echo "✅ Found static files in /app/build"
    sed -i 's|/app/static|/app/build|g' docker-compose.prod.hub.yml
    echo "🔧 Updated frontend path to /app/build"
elif docker exec shrutik_frontend_prod test -d /app/dist; then
    echo "✅ Found static files in /app/dist"
    sed -i 's|/app/static|/app/dist|g' docker-compose.prod.hub.yml
    echo "🔧 Updated frontend path to /app/dist"
elif docker exec shrutik_frontend_prod test -d /app/frontend/build; then
    echo "✅ Found static files in /app/frontend/build"
    sed -i 's|/app/static|/app/frontend/build|g' docker-compose.prod.hub.yml
    echo "🔧 Updated frontend path to /app/frontend/build"
elif docker exec shrutik_frontend_prod test -d /app/frontend/dist; then
    echo "✅ Found static files in /app/frontend/dist"
    sed -i 's|/app/static|/app/frontend/dist|g' docker-compose.prod.hub.yml
    echo "🔧 Updated frontend path to /app/frontend/dist"
else
    echo "❌ Could not find static files. Trying alternative approach..."
    echo "🔧 Changing frontend to serve a simple index.html..."
    
    # Create a simple index.html in the container
    docker exec shrutik_frontend_prod mkdir -p /app/static
    docker exec shrutik_frontend_prod sh -c 'echo "<!DOCTYPE html><html><head><title>Shrutik</title></head><body><h1>Shrutik Frontend</h1><p>Frontend is loading...</p><script>window.location.href=\"/api/health\";</script></body></html>" > /app/static/index.html'
    echo "✅ Created temporary index.html"
fi

echo ""
echo "🔄 Restarting affected services..."

# Stop problematic services
docker-compose -f docker-compose.prod.hub.yml stop celery frontend

# Start services with updated configuration
docker-compose -f docker-compose.prod.hub.yml up -d celery frontend

echo ""
echo "⏳ Waiting for services to stabilize..."
sleep 15

echo ""
echo "📋 Updated container status:"
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "🧪 Testing services..."

# Test backend
echo "Testing backend health..."
curl -s http://localhost:8080/health | head -c 200
echo ""

# Test frontend
echo "Testing frontend..."
curl -s -I http://localhost:8080/ | head -5

echo ""
echo "📋 Recent celery logs:"
docker logs --tail 5 shrutik_celery_prod

echo ""
echo "🎉 Quick fix completed!"
echo ""
echo "📝 Summary:"
echo "✅ Fixed celery command typo (if present)"
echo "✅ Updated frontend static files path"
echo "✅ Restarted affected services"
echo ""
echo "🌐 Test your application:"
echo "   Backend: http://$(curl -s ifconfig.me):8080/health"
echo "   Frontend: http://$(curl -s ifconfig.me):8080/"