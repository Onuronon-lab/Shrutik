# 🚀 Quick Local Development Setup

## TL;DR - Just want to test audio uploads?

### Option 1: Simple Setup (No Celery)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup database
createdb voice_collection
alembic upgrade head

# 3. Create .env file
cp .env.development .env
# Edit .env and set: USE_CELERY=false

# 4. Start backend only
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Test audio upload
# Audio will be processed immediately (synchronously)
```

### Option 2: Full Setup (With Background Processing)
```bash
# 1-2. Same as above

# 3. Create .env file  
cp .env.development .env
# Edit .env and set: USE_CELERY=true

# 4. Start Redis
redis-server

# 5. Start all services
./scripts/start-local-dev.sh
# This starts: Backend + Celery Worker + Celery Beat + Flower

# 6. Test audio upload
# Audio will be processed in background
```

## What happens when you upload audio?

### With Celery (Background Processing)
1. **Upload** → Returns immediately with `status: "uploaded"`
2. **Background** → Celery worker processes audio into chunks
3. **Check Status** → Use `/api/recordings/{id}/progress` to monitor
4. **Complete** → Status becomes `"processed"`, chunks are available

### Without Celery (Synchronous Processing)  
1. **Upload** → Processing happens during the request
2. **Wait** → Request takes longer (processing time)
3. **Complete** → Returns with `status: "processed"`, chunks immediately available

## Quick Test

```bash
# Upload a test audio file
curl -X POST "http://localhost:8000/api/recordings/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_file=@test.wav" \
  -F "session_id=test-session" \
  -F "duration=10.5" \
  -F "audio_format=wav" \
  -F "file_size=1048576"

# Check processing status
curl "http://localhost:8000/api/recordings/1/progress"
```

## Troubleshooting

**"Redis connection failed"** → Start Redis: `redis-server`

**"Celery workers not found"** → Either:
- Start workers: `celery -A app.core.celery_app worker --loglevel=info`
- Or disable Celery: Set `USE_CELERY=false` in `.env`

**"Audio processing takes too long"** → Use Celery for background processing

**"No chunks created"** → Check logs for audio processing errors

## Need more details?
See [docs/LOCAL_DEVELOPMENT.md](docs/LOCAL_DEVELOPMENT.md) for comprehensive setup instructions.