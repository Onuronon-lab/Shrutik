#!/bin/bash

# Fix Network and Restart Script
# This fixes the Docker network issue and restarts all services properly

set -e

echo "🔧 Fixing Docker network and restarting services..."

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.hub.yml" ]; then
    echo "❌ Error: docker-compose.prod.hub.yml not found. Please run this script from the project root."
    exit 1
fi

echo "📋 Current container status:"
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "🛑 Stopping all services..."
docker-compose -f docker-compose.prod.hub.yml down

echo ""
echo "🧹 Cleaning up Docker networks..."
# Remove the problematic network
docker network rm shrutik_shrutik_network 2>/dev/null || echo "Network already removed or doesn't exist"

# Clean up any orphaned networks
docker network prune -f

echo ""
echo "🔍 Checking environment variables..."
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating basic .env file..."
    cat > .env << EOF
# Basic environment variables for production
POSTGRES_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://production_user:your_secure_password_here@postgres:5432/voice_collection
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1,$(curl -s ifconfig.me)
CORS_ALLOWED_ORIGINS=http://localhost:8080,http://$(curl -s ifconfig.me):8080
DOCKER_IMAGE=ifrunruhin12/shrutik:latest
EOF
    echo "✅ Created basic .env file. Please update with your actual values."
else
    echo "✅ .env file exists"
fi

echo ""
echo "🚀 Starting all services with fresh network..."
docker-compose -f docker-compose.prod.hub.yml up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 30

echo ""
echo "📋 New container status:"
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "🧪 Testing services..."

# Test backend
echo "Testing backend health..."
if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Backend is responding"
    curl -s http://localhost:8080/health | head -c 200
    echo ""
else
    echo "❌ Backend is not responding"
fi

# Test frontend
echo "Testing frontend..."
if curl -f -s http://localhost:8080/ > /dev/null 2>&1; then
    echo "✅ Frontend is responding"
else
    echo "❌ Frontend is not responding"
fi

echo ""
echo "📋 Celery worker logs:"
docker logs --tail 10 shrutik_celery_prod 2>/dev/null || echo "Celery container not found"

echo ""
echo "📋 Celery beat logs:"
docker logs --tail 5 shrutik_celery_beat_prod 2>/dev/null || echo "Celery beat container not found"

echo ""
echo "🎉 Network fix and restart completed!"
echo ""
echo "📝 What was done:"
echo "✅ Stopped all services"
echo "✅ Removed problematic Docker network"
echo "✅ Created fresh network and containers"
echo "✅ Started all services"
echo ""
echo "🌐 Your application should be available at:"
echo "   http://$(curl -s ifconfig.me):8080"