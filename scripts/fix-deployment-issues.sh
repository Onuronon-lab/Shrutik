#!/bin/bash

# Fix Deployment Issues Script
# This script fixes the celery typo and frontend static files issues

set -e

echo "🔧 Fixing deployment issues..."

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.hub.yml" ]; then
    echo "❌ Error: docker-compose.prod.hub.yml not found. Please run this script from the project root."
    exit 1
fi

# Backup the original file
cp docker-compose.prod.hub.yml docker-compose.prod.hub.yml.backup
echo "📋 Created backup: docker-compose.prod.hub.yml.backup"

echo "📋 Current container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔍 Checking for celery typo in docker-compose file..."

# Check if there's a typo in the celery command
if grep -q "wrker" docker-compose.prod.hub.yml; then
    echo "❌ Found 'wrker' typo in docker-compose.prod.hub.yml"
    echo "🔧 Fixing celery command typo..."
    sed -i 's/wrker/worker/g' docker-compose.prod.hub.yml
    echo "✅ Fixed celery command typo"
else
    echo "✅ No 'wrker' typo found in docker-compose.prod.hub.yml"
fi

echo ""
echo "🔍 Checking frontend static files issue..."

# Check if frontend container exists and inspect it
if docker ps -a --format "{{.Names}}" | grep -q "shrutik_frontend_prod"; then
    echo "📂 Checking if /app/static directory exists in frontend container..."
    
    # Check if /app/static exists in the container
    if docker exec shrutik_frontend_prod ls -la /app/static 2>/dev/null; then
        echo "✅ /app/static directory exists"
        echo "📁 Contents of /app/static:"
        docker exec shrutik_frontend_prod ls -la /app/static
    else
        echo "❌ /app/static directory not found"
        echo "🔍 Checking alternative locations..."
        
        # Check for common frontend build locations
        echo "Checking /app/dist:"
        docker exec shrutik_frontend_prod ls -la /app/dist 2>/dev/null || echo "  /app/dist not found"
        
        echo "Checking /app/build:"
        docker exec shrutik_frontend_prod ls -la /app/build 2>/dev/null || echo "  /app/build not found"
        
        echo "Checking /app/frontend/dist:"
        docker exec shrutik_frontend_prod ls -la /app/frontend/dist 2>/dev/null || echo "  /app/frontend/dist not found"
        
        echo "Checking root /app directory:"
        docker exec shrutik_frontend_prod ls -la /app/
        
        echo ""
        echo "🔧 Updating frontend service to use correct static files location..."
        
        # We need to update the docker-compose to use the correct path
        # First, let's find where the static files actually are
        STATIC_PATH=""
        if docker exec shrutik_frontend_prod test -d /app/dist; then
            STATIC_PATH="/app/dist"
        elif docker exec shrutik_frontend_prod test -d /app/build; then
            STATIC_PATH="/app/build"
        elif docker exec shrutik_frontend_prod test -d /app/frontend/dist; then
            STATIC_PATH="/app/frontend/dist"
        fi
        
        if [ -n "$STATIC_PATH" ]; then
            echo "✅ Found static files at: $STATIC_PATH"
            echo "🔧 Updating docker-compose to use $STATIC_PATH"
            sed -i "s|/app/static|$STATIC_PATH|g" docker-compose.prod.hub.yml
        else
            echo "❌ Could not find static files. The Docker image might not include built frontend files."
            echo "💡 Consider using nginx to serve static files directly or rebuild the Docker image with frontend files."
        fi
    fi
else
    echo "❌ Frontend container not found"
fi

echo ""
echo "🔄 Restarting affected services..."

# Stop and restart the problematic services
echo "Stopping celery and frontend services..."
docker-compose -f docker-compose.prod.hub.yml stop celery frontend

echo "Starting services with updated configuration..."
docker-compose -f docker-compose.prod.hub.yml up -d celery frontend

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "📋 Updated container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🧪 Testing services..."

# Test backend health
echo "Testing backend health endpoint..."
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed"
fi

# Test frontend
echo "Testing frontend..."
if curl -f http://localhost:8080/ > /dev/null 2>&1; then
    echo "✅ Frontend is responding"
else
    echo "❌ Frontend is not responding"
fi

# Check celery logs
echo ""
echo "📋 Recent celery logs:"
docker logs --tail 10 shrutik_celery_prod

echo ""
echo "🎉 Deployment fix script completed!"
echo ""
echo "📝 Next steps:"
echo "1. Check the container status above"
echo "2. Test your application at http://your-ec2-ip:8080"
echo "3. If frontend still has issues, you may need to rebuild the Docker image with proper static files"