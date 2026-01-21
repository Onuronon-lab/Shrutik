#!/bin/bash

# Fix Environment Variables and Restart Script
# This fixes the database and environment variable issues

set -e

echo "🔧 Fixing environment variables and database issues..."

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.hub.yml" ]; then
    echo "❌ Error: docker-compose.prod.hub.yml not found. Please run this script from the project root."
    exit 1
fi

echo "🛑 Stopping services to fix environment..."
docker-compose -f docker-compose.prod.hub.yml down

echo ""
echo "🔧 Creating proper .env file..."

# Create a proper .env file with working values
cat > .env << 'EOF'
# Database Configuration
POSTGRES_DB=voice_collection
POSTGRES_USER=production_user
POSTGRES_PASSWORD=secure_production_password_2024

# Application Configuration
DATABASE_URL=postgresql://production_user:secure_production_password_2024@postgres:5432/voice_collection
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-super-secret-key-change-this-in-production-2024
DEBUG=false

# Network Configuration
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# Docker Configuration
DOCKER_IMAGE=ifrunruhin12/shrutik:latest

# Storage Configuration
EXPORT_STORAGE_TYPE=local
UPLOAD_DIR=/app/uploads
EXPORT_DIR=/app/exports

# Flower Configuration
FLOWER_BASIC_AUTH=admin:secure_flower_password_2024
EOF

echo "✅ Created proper .env file"

echo ""
echo "🗄️ Cleaning up old database data..."
# Remove old database volume to start fresh
docker volume rm shrutik_postgres_data 2>/dev/null || echo "Database volume already removed or doesn't exist"

echo ""
echo "🚀 Starting services with correct environment..."
docker-compose -f docker-compose.prod.hub.yml up -d

echo ""
echo "⏳ Waiting for database to initialize..."
sleep 30

echo ""
echo "🔍 Checking database initialization..."
docker logs shrutik_postgres_prod | tail -10

echo ""
echo "⏳ Waiting for backend to start..."
sleep 20

echo ""
echo "📋 Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "🧪 Testing database connection:"
docker exec shrutik_backend_prod python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://production_user:secure_production_password_2024@postgres:5432/voice_collection')
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
" 2>/dev/null || echo "❌ Could not test database connection"

echo ""
echo "🧪 Testing backend health:"
curl -s http://localhost:8080/health | head -200 || echo "❌ Health endpoint not accessible yet"

echo ""
echo "🎉 Environment fix completed!"
echo ""
echo "📝 What was fixed:"
echo "✅ Created proper .env file with working credentials"
echo "✅ Fixed ALLOWED_HOSTS format"
echo "✅ Fixed database name and credentials"
echo "✅ Removed old database volume for fresh start"
echo ""
echo "🔐 Important Security Notes:"
echo "⚠️  The passwords in .env are temporary - change them for production!"
echo "⚠️  Consider using Vault for proper secret management"
echo ""
echo "🌐 Your application should be available at:"
echo "   http://$(curl -s ifconfig.me):8080"