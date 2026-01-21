#!/bin/bash

# Backend Diagnostic Script
# This identifies why the backend is unhealthy

set -e

echo "🔍 Diagnosing backend health issues..."

echo ""
echo "📋 Current container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔍 Backend container logs (last 20 lines):"
docker logs --tail 20 shrutik_backend_prod

echo ""
echo "🔍 PostgreSQL container logs (last 10 lines):"
docker logs --tail 10 shrutik_postgres_prod

echo ""
echo "🔍 Redis container logs (last 5 lines):"
docker logs --tail 5 shrutik_redis_prod

echo ""
echo "🧪 Testing database connection from backend container:"
docker exec shrutik_backend_prod python -c "
import os
import psycopg2
try:
    db_url = os.environ.get('DATABASE_URL', 'postgresql://production_user:@postgres:5432/voice_collection')
    print(f'Trying to connect to: {db_url}')
    conn = psycopg2.connect(db_url)
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
" 2>/dev/null || echo "❌ Could not test database connection"

echo ""
echo "🧪 Testing Redis connection from backend container:"
docker exec shrutik_backend_prod python -c "
import redis
try:
    r = redis.Redis(host='redis', port=6379, db=0)
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
" 2>/dev/null || echo "❌ Could not test Redis connection"

echo ""
echo "🔍 Environment variables in backend container:"
docker exec shrutik_backend_prod env | grep -E "(DATABASE_URL|REDIS_URL|SECRET_KEY|POSTGRES)" || echo "No relevant environment variables found"

echo ""
echo "🧪 Testing health endpoint directly:"
curl -v http://localhost:8080/health 2>&1 | head -20 || echo "❌ Health endpoint not accessible"

echo ""
echo "🧪 Testing backend container internal health:"
docker exec shrutik_backend_prod curl -f http://localhost:8000/health 2>/dev/null | head -200 || echo "❌ Internal health check failed"

echo ""
echo "🔍 Checking if backend process is running:"
docker exec shrutik_backend_prod ps aux | grep uvicorn || echo "❌ Uvicorn process not found"

echo ""
echo "📝 Diagnostic Summary:"
echo "1. Check the logs above for any error messages"
echo "2. Verify database and Redis connections are working"
echo "3. Ensure environment variables are properly set"
echo "4. Check if the uvicorn process is running inside the container"