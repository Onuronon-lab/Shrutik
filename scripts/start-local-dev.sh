#!/bin/bash

# Local Development Startup Script
# This script helps you start all necessary services for local development

set -e

echo "🚀 Starting Voice Data Collection Platform - Local Development"
echo "============================================================"

# Check if Redis is running
echo "📡 Checking Redis connection..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first:"
    echo "   - On macOS: brew services start redis"
    echo "   - On Ubuntu: sudo systemctl start redis-server"
    echo "   - Or run: redis-server"
    exit 1
fi
echo "✅ Redis is running"

# Check if PostgreSQL is running
echo "🗄️  Checking PostgreSQL connection..."
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first:"
    echo "   - On macOS: brew services start postgresql"
    echo "   - On Ubuntu: sudo systemctl start postgresql"
    exit 1
fi
echo "✅ PostgreSQL is running"

# Install Python dependencies if needed
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python -m venv venv
fi

echo "📦 Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Create uploads directory
mkdir -p uploads/recordings uploads/chunks

echo ""
echo "🎯 Starting services..."
echo "======================"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    jobs -p | xargs -r kill
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start Celery worker in background
echo "🔧 Starting Celery worker..."
celery -A app.core.celery_app worker --loglevel=info --queues=default,audio_processing,consensus,batch_processing,maintenance &
CELERY_PID=$!

# Start Celery beat scheduler in background
echo "⏰ Starting Celery beat scheduler..."
celery -A app.core.celery_app beat --loglevel=info &
BEAT_PID=$!

# Start Flower monitoring (optional)
if command -v flower &> /dev/null; then
    echo "🌸 Starting Flower monitoring on http://localhost:5555..."
    celery -A app.core.celery_app flower --port=5555 &
    FLOWER_PID=$!
fi

# Wait a moment for Celery to start
sleep 3

# Start FastAPI backend
echo "🚀 Starting FastAPI backend on http://localhost:8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo ""
echo "✅ All services started successfully!"
echo "=================================="
echo "📊 Backend API: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"
echo "🌸 Flower (if available): http://localhost:5555"
echo ""
echo "💡 To start the frontend, run in another terminal:"
echo "   cd frontend && npm start"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for all background processes
wait
