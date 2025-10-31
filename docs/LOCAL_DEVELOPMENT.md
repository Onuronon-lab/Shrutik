# Local Development Setup

This guide explains how to set up the Voice Data Collection Platform for local development, with and without Docker.

## Prerequisites

### Required Software

1. **Python 3.9+**
2. **Node.js 16+** and npm
3. **PostgreSQL 13+**
4. **Redis 6+**

### Optional (for full background processing)
5. **Celery** (installed via pip)

## Quick Start Options

### Option 1: Full Setup with Background Processing (Recommended)

This setup includes Celery workers for background audio processing.

#### 1. Install Dependencies

**On macOS:**
```bash
# Install PostgreSQL and Redis
brew install postgresql redis

# Start services
brew services start postgresql
brew services start redis
```

**On Ubuntu:**
```bash
# Install PostgreSQL and Redis
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server

# Start services
sudo systemctl start postgresql
sudo systemctl start redis-server
```

**On Windows:**
- Download and install PostgreSQL from https://www.postgresql.org/download/windows/
- Download and install Redis from https://github.com/microsoftarchive/redis/releases

#### 2. Setup Database

```bash
# Create database
createdb voice_collection

# Or using psql
psql -U postgres
CREATE DATABASE voice_collection;
\q
```

#### 3. Setup Python Environment

```bash
# Clone repository
git clone <repository-url>
cd voice-data-collection

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
# Copy development environment file
cp .env.development .env

# Edit .env file with your database credentials if needed
```

#### 5. Run Database Migrations

```bash
alembic upgrade head
```

#### 6. Start All Services

**On macOS/Linux:**
```bash
./scripts/start-local-dev.sh
```

**On Windows:**
```bash
scripts\start-local-dev.bat
```

**Or manually start each service:**

```bash
# Terminal 1: Start Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# Terminal 2: Start Celery Beat (for periodic tasks)
celery -A app.core.celery_app beat --loglevel=info

# Terminal 3: Start Flower (optional monitoring)
celery -A app.core.celery_app flower --port=5555

# Terminal 4: Start FastAPI Backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 5: Start Frontend
cd frontend
npm install
npm start
```

#### 7. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Flower Monitoring:** http://localhost:5555

### Option 2: Simplified Setup (No Background Processing)

If you don't want to set up Celery workers, you can run with synchronous processing.

#### 1-5. Follow steps 1-5 from Option 1

#### 6. Configure Synchronous Processing

Edit your `.env` file:
```bash
USE_CELERY=false
```

#### 7. Start Services

```bash
# Start FastAPI Backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, start Frontend
cd frontend
npm install
npm start
```

**Note:** With this setup, audio processing will happen synchronously when you upload recordings, which may cause longer response times but doesn't require Celery workers.

## Development Workflow

### Audio Processing Behavior

#### With Celery (USE_CELERY=true)
1. Upload audio file → Returns immediately
2. Audio processing happens in background
3. Check processing status via API or notifications
4. Chunks appear when processing completes

#### Without Celery (USE_CELERY=false)
1. Upload audio file → Processing happens immediately
2. Response includes processing results
3. Chunks are available immediately after upload

### API Testing

Use the interactive API documentation at http://localhost:8000/docs to test endpoints.

### Database Management

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Monitoring and Debugging

#### With Celery
- **Flower Dashboard:** http://localhost:5555
- **Job Status API:** `GET /api/jobs/active`
- **Worker Status:** `GET /api/jobs/workers`

#### Logs
```bash
# Backend logs
tail -f logs/app.log

# Celery worker logs
celery -A app.core.celery_app worker --loglevel=debug

# Database queries (if DEBUG=true)
# Check console output
```

## Common Issues and Solutions

### Issue: "Redis connection failed"

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# If not running, start it
# macOS: brew services start redis
# Ubuntu: sudo systemctl start redis-server
# Windows: Start Redis service
```

### Issue: "PostgreSQL connection failed"

**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Check database exists
psql -U postgres -l | grep voice_collection

# Create database if missing
createdb voice_collection
```

### Issue: "Celery workers not processing tasks"

**Solutions:**
1. Check if workers are running:
   ```bash
   celery -A app.core.celery_app inspect active
   ```

2. Check Redis connection:
   ```bash
   redis-cli ping
   ```

3. Restart workers:
   ```bash
   # Kill existing workers
   pkill -f celery
   
   # Start new worker
   celery -A app.core.celery_app worker --loglevel=info
   ```

4. Or switch to synchronous processing:
   ```bash
   # In .env file
   USE_CELERY=false
   ```

### Issue: "Audio processing fails"

**Check:**
1. File permissions on uploads directory
2. Audio file format is supported
3. Sufficient disk space
4. Python audio libraries installed correctly

**Debug:**
```bash
# Test audio processing manually
python -c "
import librosa
y, sr = librosa.load('path/to/audio/file.wav')
print(f'Duration: {librosa.get_duration(y=y, sr=sr)} seconds')
"
```

### Issue: "Frontend can't connect to backend"

**Solutions:**
1. Check CORS settings in `.env`:
   ```bash
   ALLOWED_HOSTS=["http://localhost:3000", "http://localhost:8000"]
   ```

2. Verify backend is running on correct port:
   ```bash
   curl http://localhost:8000/health
   ```

3. Check frontend API URL configuration

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:password@localhost:5432/voice_collection` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `SECRET_KEY` | `your-secret-key-change-in-production` | JWT secret key |
| `DEBUG` | `false` | Enable debug mode |
| `USE_CELERY` | `true` | Enable/disable Celery background processing |
| `UPLOAD_DIR` | `uploads` | Directory for uploaded files |
| `MAX_FILE_SIZE` | `104857600` | Maximum file size in bytes (100MB) |
| `ALLOWED_HOSTS` | `["http://localhost:3000"]` | CORS allowed origins |

## Development Tips

### 1. Hot Reloading

Both backend and frontend support hot reloading:
- **Backend:** Use `--reload` flag with uvicorn
- **Frontend:** npm start enables hot reloading by default

### 2. Database Seeding

Create test data for development:
```bash
python scripts/seed_database.py
```

### 3. Testing

```bash
# Run backend tests
pytest

# Run frontend tests
cd frontend
npm test
```

### 4. Code Quality

```bash
# Format Python code
black app/
isort app/

# Lint Python code
flake8 app/

# Format frontend code
cd frontend
npm run format
npm run lint
```

### 5. Performance Monitoring

With Celery enabled, monitor performance:
- Task execution times in Flower
- Queue lengths via API
- Worker resource usage

## Production Considerations

When moving to production:

1. **Enable Celery:** Set `USE_CELERY=true`
2. **Use proper Redis/PostgreSQL instances**
3. **Configure proper secret keys**
4. **Set up proper logging**
5. **Configure reverse proxy (nginx)**
6. **Set up SSL certificates**
7. **Configure monitoring and alerting**

## Getting Help

1. **Check logs** for error messages
2. **Use API documentation** at http://localhost:8000/docs
3. **Monitor Celery** via Flower dashboard
4. **Check database** for data consistency
5. **Review configuration** in `.env` file

For more detailed information, see:
- [Job Monitoring Documentation](JOB_MONITORING.md)
- [API Documentation](http://localhost:8000/docs)
- [Frontend README](../frontend/README.md)