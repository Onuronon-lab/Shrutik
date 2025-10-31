# Audio Processing Modes

The Voice Data Collection Platform supports two modes for audio processing to accommodate different development and deployment scenarios.

## Processing Modes

### 1. Asynchronous Processing (Celery) - Recommended for Production

**When to use:**
- Production deployments
- Development with full background processing
- When you want non-blocking audio uploads
- When processing large audio files

**How it works:**
1. User uploads audio file
2. File is saved and marked as `UPLOADED`
3. Celery task is queued for background processing
4. User gets immediate response
5. Background worker processes audio into chunks
6. Status updates to `PROCESSED` when complete
7. User can check progress via API

**Setup:**
```bash
# In .env file
USE_CELERY=true

# Start services
redis-server
celery -A app.core.celery_app worker --loglevel=info
uvicorn app.main:app --reload
```

**Benefits:**
- ✅ Non-blocking uploads
- ✅ Scalable (multiple workers)
- ✅ Retry mechanisms
- ✅ Progress tracking
- ✅ Monitoring via Flower

**Drawbacks:**
- ❌ More complex setup
- ❌ Requires Redis
- ❌ Requires Celery workers

### 2. Synchronous Processing - Simple Development

**When to use:**
- Quick local development
- Testing without Celery setup
- Simple deployments
- When immediate results are needed

**How it works:**
1. User uploads audio file
2. File is saved and marked as `PROCESSING`
3. Audio processing happens immediately in the request
4. Chunks are created during the upload request
5. Status updates to `PROCESSED` before response
6. User gets complete results immediately

**Setup:**
```bash
# In .env file
USE_CELERY=false

# Start service
uvicorn app.main:app --reload
```

**Benefits:**
- ✅ Simple setup (no Redis/Celery needed)
- ✅ Immediate results
- ✅ Easier debugging
- ✅ No additional services required

**Drawbacks:**
- ❌ Blocking uploads (slower response)
- ❌ No retry mechanisms
- ❌ Single-threaded processing
- ❌ No progress tracking

## Automatic Mode Detection

The system automatically detects which mode to use:

```python
def _is_celery_available(self) -> bool:
    # 1. Check configuration
    if not settings.USE_CELERY:
        return False
    
    # 2. Check if workers are running
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        return stats is not None and len(stats) > 0
    except:
        return False
```

**Fallback Logic:**
1. If `USE_CELERY=false` → Always use synchronous processing
2. If `USE_CELERY=true` but no workers → Fall back to synchronous processing
3. If `USE_CELERY=true` and workers available → Use Celery processing

## API Behavior Differences

### Upload Response

**Celery Mode:**
```json
{
  "id": 123,
  "status": "uploaded",
  "message": "File uploaded successfully, processing queued"
}
```

**Synchronous Mode:**
```json
{
  "id": 123,
  "status": "processed",
  "chunks_created": 5,
  "message": "File uploaded and processed successfully"
}
```

### Progress Tracking

**Celery Mode:**
```bash
# Check progress
GET /api/recordings/123/progress
{
  "status": "processing",
  "progress": 45,
  "chunks_created": 0
}

# Later...
GET /api/recordings/123/progress
{
  "status": "processed", 
  "progress": 100,
  "chunks_created": 5
}
```

**Synchronous Mode:**
```bash
# Progress is always complete
GET /api/recordings/123/progress
{
  "status": "processed",
  "progress": 100,
  "chunks_created": 5
}
```

## Configuration Options

### Environment Variables

```bash
# Enable/disable Celery
USE_CELERY=true|false

# Celery configuration (when enabled)
REDIS_URL=redis://localhost:6379/0
JOB_MAX_RETRIES=3
JOB_RETRY_DELAY=60
```

### Runtime Detection

The system logs which mode is being used:

```
# Celery mode
INFO: Queued audio processing task abc123 for recording 456

# Synchronous mode  
INFO: Celery not available, processing recording 456 synchronously...
INFO: Successfully processed recording 456 into 5 chunks
```

## Development Workflow

### For Frontend Development
Use synchronous mode for simplicity:
```bash
USE_CELERY=false
uvicorn app.main:app --reload
```

### For Full-Stack Development
Use Celery mode to test complete workflow:
```bash
USE_CELERY=true
./scripts/start-local-dev.sh
```

### For Production Testing
Always use Celery mode:
```bash
USE_CELERY=true
# + proper Redis/Celery setup
```

## Monitoring and Debugging

### Celery Mode Monitoring

```bash
# Check worker status
celery -A app.core.celery_app inspect active

# Monitor via Flower
celery -A app.core.celery_app flower --port=5555

# Check job status via API
GET /api/jobs/active
```

### Synchronous Mode Debugging

```bash
# Check logs for processing errors
tail -f logs/app.log

# Processing happens in main thread
# Errors appear immediately in response
```

## Performance Considerations

### Celery Mode
- **Throughput:** High (parallel processing)
- **Response Time:** Fast (immediate return)
- **Resource Usage:** Distributed across workers
- **Scalability:** Horizontal (add more workers)

### Synchronous Mode
- **Throughput:** Limited (sequential processing)
- **Response Time:** Slow (includes processing time)
- **Resource Usage:** Single process
- **Scalability:** Vertical only

## Error Handling

### Celery Mode
- Automatic retries with exponential backoff
- Failed tasks can be manually retried
- Detailed error tracking in job monitoring
- Notifications for failures

### Synchronous Mode
- Immediate error response
- No automatic retries
- Simpler error debugging
- Direct error messages

## Migration Between Modes

### From Synchronous to Celery
1. Set `USE_CELERY=true`
2. Start Redis and Celery workers
3. Existing processed recordings work normally
4. New uploads use background processing

### From Celery to Synchronous
1. Set `USE_CELERY=false`
2. Stop Celery workers (optional)
3. Existing queued tasks will fail
4. New uploads use synchronous processing

**Note:** In-progress Celery tasks will fail when switching to synchronous mode. Complete or cancel them first.

## Best Practices

### Development
- Use synchronous mode for quick testing
- Use Celery mode when testing full workflow
- Monitor logs for processing errors

### Production
- Always use Celery mode
- Set up proper monitoring
- Configure retry mechanisms
- Use multiple workers for scalability

### Testing
- Test both modes in CI/CD
- Verify fallback behavior
- Test error scenarios in both modes