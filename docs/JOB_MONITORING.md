# Job Monitoring and Background Processing

This document describes the comprehensive job monitoring and background processing system implemented for the Voice Data Collection Platform.

## Overview

The system provides:
- **Celery-based background job processing** with intelligent queuing
- **Comprehensive job monitoring** with status tracking and notifications
- **Retry mechanisms** with exponential backoff and failure handling
- **Real-time notifications** for job status updates
- **Admin dashboard** for system monitoring and management
- **Periodic maintenance tasks** for system health

## Architecture

### Components

1. **Celery Workers** - Process background tasks in dedicated queues
2. **Redis** - Message broker and result backend
3. **Celery Beat** - Scheduler for periodic tasks
4. **Flower** - Web-based monitoring tool
5. **Job Monitoring Service** - Custom monitoring and management
6. **Notification Service** - Multi-channel notification system

### Queue Structure

The system uses specialized queues for different types of tasks:

- `default` - General purpose tasks
- `audio_processing` - Audio chunking and processing tasks
- `consensus` - Transcription consensus calculation
- `batch_processing` - Batch operations
- `maintenance` - System maintenance and cleanup

## Background Tasks

### Audio Processing Tasks

#### `process_audio_recording`
- **Purpose**: Process uploaded audio recordings with intelligent chunking
- **Queue**: `audio_processing`
- **Retry**: 3 attempts with exponential backoff
- **Timeout**: 30 minutes hard limit, 25 minutes soft limit

```python
# Example usage
from app.tasks.audio_processing import process_audio_recording

# Process a recording
result = process_audio_recording.delay(recording_id=123)
```

#### `calculate_consensus_for_chunks`
- **Purpose**: Calculate consensus for multiple audio chunks
- **Queue**: `consensus`
- **Retry**: 2 attempts with exponential backoff
- **Timeout**: 30 minutes

### Batch Processing Tasks

#### `batch_process_recordings`
- **Purpose**: Process multiple recordings in batch
- **Queue**: `batch_processing`
- **Dependencies**: Calls `process_audio_recording` for each item

#### `recalculate_all_consensus`
- **Purpose**: Recalculate consensus for all eligible chunks
- **Queue**: `maintenance`
- **Schedule**: Every 6 hours

### Maintenance Tasks

#### `cleanup_orphaned_chunks`
- **Purpose**: Remove orphaned audio chunk files
- **Queue**: `maintenance`
- **Schedule**: Every hour

#### `reprocess_failed_recordings`
- **Purpose**: Retry failed recording processing
- **Queue**: `maintenance`
- **Schedule**: Every 2 hours

## Job Monitoring

### Job Status Tracking

The system tracks comprehensive job information:

```python
@dataclass
class JobInfo:
    task_id: str
    task_name: str
    status: JobStatus  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    retry_count: int
    max_retries: int
    queue: str
    priority: JobPriority
    metadata: Optional[Dict[str, Any]]
```

### API Endpoints

#### Job Information
- `GET /api/jobs/info/{task_id}` - Get detailed job information
- `GET /api/jobs/active` - List all active jobs
- `GET /api/jobs/scheduled` - List scheduled jobs
- `GET /api/jobs/statistics` - Get job execution statistics

#### Job Management (Admin Only)
- `POST /api/jobs/action/{task_id}` - Perform job actions (cancel, retry, terminate)
- `POST /api/jobs/queue/purge` - Purge queue contents
- `GET /api/jobs/workers` - Get worker status
- `GET /api/jobs/queues` - Get queue lengths

#### System Management (Admin Only)
- `POST /api/jobs/system/restart-workers` - Restart all workers
- `POST /api/jobs/system/enable-events` - Enable event monitoring
- `POST /api/jobs/system/disable-events` - Disable event monitoring

## Notification System

### Notification Channels

The system supports multiple notification channels:

- **Redis** - Real-time pub/sub notifications
- **Database** - Persistent notification storage
- **Email** - Email notifications (configurable)
- **Webhook** - HTTP webhook notifications
- **Push** - Push notifications (configurable)

### Notification Types

#### Job Notifications
Automatically sent for job status changes:

```python
# Success notification
notification_service.send_job_notification(
    job_id="task-123",
    job_name="Audio Processing",
    status="success",
    message="Successfully processed recording into 5 chunks",
    level=NotificationLevel.INFO
)

# Failure notification
notification_service.send_job_notification(
    job_id="task-123",
    job_name="Audio Processing",
    status="failed",
    message="Audio processing failed: Invalid file format",
    level=NotificationLevel.ERROR
)
```

#### System Notifications
For system-wide events and maintenance:

```python
notification_service.send_notification(
    title="System Maintenance",
    message="Scheduled maintenance completed successfully",
    level=NotificationLevel.INFO,
    channels=[NotificationChannel.REDIS, NotificationChannel.DATABASE],
    recipient_type="admin"
)
```

### Notification API Endpoints

- `GET /api/jobs/notifications` - Get user notifications
- `POST /api/jobs/notifications/{id}/read` - Mark notification as read
- `GET /api/jobs/notifications/system` - Get system notifications (admin only)

## Configuration

### Celery Configuration

Key configuration options in `app/core/celery_app.py`:

```python
celery_app.conf.update(
    # Task execution limits
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    
    # Retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Result backend
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Queue routing
    task_routes={
        'process_audio_recording': {'queue': 'audio_processing'},
        'calculate_consensus_for_chunks': {'queue': 'consensus'},
        # ... more routes
    }
)
```

### Redis Configuration

Redis is used for:
- Message brokering
- Result storage
- Job monitoring data
- Notification storage
- Real-time pub/sub

### Environment Variables

Required environment variables:

```bash
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@localhost/db
JOB_RESULT_EXPIRES=3600
JOB_MAX_RETRIES=3
JOB_RETRY_DELAY=60
```

## Docker Deployment

### Services

The system includes these Docker services:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  celery:
    build: .
    command: celery -A app.core.celery_app worker --loglevel=info --queues=default,audio_processing,consensus,batch_processing,maintenance
  
  celery-beat:
    build: .
    command: celery -A app.core.celery_app beat --loglevel=info
  
  celery-flower:
    build: .
    command: celery -A app.core.celery_app flower --port=5555
    ports:
      - "5555:5555"
```

### Starting the System

```bash
# Start all services
docker-compose up -d

# View worker logs
docker-compose logs -f celery

# View beat scheduler logs
docker-compose logs -f celery-beat

# Access Flower monitoring
open http://localhost:5555
```

## Monitoring and Maintenance

### Flower Dashboard

Access the Flower web interface at `http://localhost:5555` to monitor:
- Active tasks and workers
- Task history and statistics
- Queue lengths and throughput
- Worker resource usage

### Health Checks

The system provides health check endpoints:

```bash
# Check API health
curl http://localhost:8000/health

# Check worker status
curl http://localhost:8000/api/jobs/workers

# Check queue lengths
curl http://localhost:8000/api/jobs/queues
```

### Log Monitoring

Key log locations:
- Application logs: `docker-compose logs backend`
- Worker logs: `docker-compose logs celery`
- Beat scheduler logs: `docker-compose logs celery-beat`
- Flower logs: `docker-compose logs celery-flower`

### Performance Tuning

#### Worker Scaling

Scale workers based on load:

```bash
# Scale to 3 worker instances
docker-compose up -d --scale celery=3
```

#### Queue Optimization

Monitor queue lengths and adjust worker allocation:

```python
# Get queue statistics
queue_lengths = job_monitoring_service.get_queue_lengths()
print(f"Audio processing queue: {queue_lengths['audio_processing']} tasks")
```

#### Memory Management

Configure worker memory limits:

```python
# In celery_app.py
celery_app.conf.update(
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    worker_prefetch_multiplier=1,     # Process one task at a time
)
```

## Error Handling and Recovery

### Automatic Retry

Tasks automatically retry on failure with exponential backoff:

```python
@celery_app.task(
    autoretry_for=(AudioProcessingError,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600
)
def process_audio_recording(recording_id):
    # Task implementation
    pass
```

### Manual Recovery

Administrators can manually retry failed tasks:

```bash
# Via API
curl -X POST http://localhost:8000/api/jobs/action/task-123 \
  -H "Content-Type: application/json" \
  -d '{"action": "retry", "countdown": 60}'

# Via Flower dashboard
# Navigate to task and click "Retry"
```

### Dead Letter Queue

Failed tasks after max retries are logged for manual review:

```python
# Check failed tasks
failed_tasks = job_monitoring_service.get_failed_tasks()
for task in failed_tasks:
    print(f"Task {task.task_id} failed: {task.error}")
```

## Security Considerations

### Access Control

- Job management endpoints require admin privileges
- User notifications are isolated by user ID
- System notifications require admin access

### Data Protection

- Job results expire after 1 hour by default
- Sensitive data in job metadata is logged carefully
- Redis connections use authentication in production

### Rate Limiting

- API endpoints include rate limiting
- Worker prefetch limits prevent resource exhaustion
- Queue size monitoring prevents memory issues

## Troubleshooting

### Common Issues

#### Workers Not Processing Tasks

1. Check Redis connection:
   ```bash
   docker-compose exec redis redis-cli ping
   ```

2. Check worker status:
   ```bash
   docker-compose logs celery
   ```

3. Restart workers:
   ```bash
   docker-compose restart celery
   ```

#### High Memory Usage

1. Check worker memory limits
2. Reduce `worker_max_tasks_per_child`
3. Monitor task complexity

#### Queue Backlog

1. Scale workers: `docker-compose up -d --scale celery=N`
2. Check for stuck tasks
3. Consider task optimization

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
DEBUG=true

# Or modify celery command
celery -A app.core.celery_app worker --loglevel=debug
```

## Future Enhancements

### Planned Features

1. **Advanced Metrics** - Detailed performance analytics
2. **Auto-scaling** - Dynamic worker scaling based on load
3. **Task Prioritization** - Priority-based task scheduling
4. **Distributed Tracing** - End-to-end request tracing
5. **Alert Integration** - Integration with external alerting systems

### Integration Opportunities

1. **Prometheus/Grafana** - Advanced monitoring dashboards
2. **Sentry** - Error tracking and alerting
3. **DataDog/New Relic** - Application performance monitoring
4. **Slack/Discord** - Real-time notifications
5. **Email Services** - Automated email notifications