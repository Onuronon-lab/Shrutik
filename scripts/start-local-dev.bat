@echo off
REM Local Development Startup Script for Windows
REM This script helps you start all necessary services for local development

echo 🚀 Starting Voice Data Collection Platform - Local Development
echo ============================================================

REM Check if Redis is running
echo 📡 Checking Redis connection...
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Redis is not running. Please start Redis first:
    echo    - Download and install Redis for Windows
    echo    - Or run: redis-server
    exit /b 1
)
echo ✅ Redis is running

REM Check if PostgreSQL is running
echo 🗄️  Checking PostgreSQL connection...
pg_isready -h localhost -p 5432 >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ PostgreSQL is not running. Please start PostgreSQL first
    exit /b 1
)
echo ✅ PostgreSQL is running

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 🐍 Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment and install dependencies
echo 📦 Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM Run database migrations
echo 🔄 Running database migrations...
alembic upgrade head

REM Create uploads directory
if not exist "uploads\recordings" mkdir uploads\recordings
if not exist "uploads\chunks" mkdir uploads\chunks

echo.
echo 🎯 Starting services...
echo ======================

REM Start Celery worker
echo 🔧 Starting Celery worker...
start "Celery Worker" cmd /k "venv\Scripts\activate.bat && celery -A app.core.celery_app worker --loglevel=info --queues=default,audio_processing,consensus,batch_processing,maintenance"

REM Start Celery beat scheduler
echo ⏰ Starting Celery beat scheduler...
start "Celery Beat" cmd /k "venv\Scripts\activate.bat && celery -A app.core.celery_app beat --loglevel=info"

REM Start Flower monitoring (optional)
where flower >nul 2>&1
if %errorlevel% equ 0 (
    echo 🌸 Starting Flower monitoring on http://localhost:5555...
    start "Flower" cmd /k "venv\Scripts\activate.bat && celery -A app.core.celery_app flower --port=5555"
)

REM Wait a moment for Celery to start
timeout /t 3 /nobreak >nul

REM Start FastAPI backend
echo 🚀 Starting FastAPI backend on http://localhost:8000...
start "FastAPI Backend" cmd /k "venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo ✅ All services started successfully!
echo ==================================
echo 📊 Backend API: http://localhost:8000
echo 📊 API Docs: http://localhost:8000/docs
echo 🌸 Flower (if available): http://localhost:5555
echo.
echo 💡 To start the frontend, run in another terminal:
echo    cd frontend && npm start
echo.
echo Press any key to exit...
pause >nul