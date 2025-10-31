from celery import Celery
from celery.signals import task_failure, task_success, task_retry, worker_ready
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

celery_app = Celery(
    "voice_collection",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]
)

# Enhanced Celery configuration with monitoring and retry mechanisms
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task tracking and monitoring
    task_track_started=True,
    task_always_eager=False,
    
    # Task execution limits
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Result backend configuration
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
    result_compression='gzip',
    
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # 1 minute default retry delay
    task_max_retries=3,
    
    # Routing and queues
    task_routes={
        'process_audio_recording': {'queue': 'audio_processing'},
        'calculate_consensus_for_chunks': {'queue': 'consensus'},
        'batch_process_recordings': {'queue': 'batch_processing'},
        'cleanup_orphaned_chunks': {'queue': 'maintenance'},
        'reprocess_failed_recordings': {'queue': 'maintenance'},
        'recalculate_all_consensus': {'queue': 'maintenance'},
    },
    
    # Queue configuration
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'exchange_type': 'direct',
            'routing_key': 'default',
        },
        'audio_processing': {
            'exchange': 'audio_processing',
            'exchange_type': 'direct',
            'routing_key': 'audio_processing',
        },
        'consensus': {
            'exchange': 'consensus',
            'exchange_type': 'direct',
            'routing_key': 'consensus',
        },
        'batch_processing': {
            'exchange': 'batch_processing',
            'exchange_type': 'direct',
            'routing_key': 'batch_processing',
        },
        'maintenance': {
            'exchange': 'maintenance',
            'exchange_type': 'direct',
            'routing_key': 'maintenance',
        },
    },
    
    # Monitoring and events
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-orphaned-chunks': {
            'task': 'cleanup_orphaned_chunks',
            'schedule': 3600.0,  # Run every hour
        },
        'recalculate-consensus': {
            'task': 'recalculate_all_consensus',
            'schedule': 21600.0,  # Run every 6 hours
        },
        'reprocess-failed-recordings': {
            'task': 'reprocess_failed_recordings',
            'schedule': 7200.0,  # Run every 2 hours
        },
    },
)


# Signal handlers for monitoring and logging
@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """Handle task failures for monitoring and alerting."""
    logger.error(f"Task {sender.name} [{task_id}] failed: {exception}")
    logger.error(f"Traceback: {traceback}")
    
    # Here you could add alerting logic, e.g., send to monitoring system
    # or create database records for failed tasks


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Handle successful task completion."""
    logger.info(f"Task {sender.name} completed successfully")


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwargs):
    """Handle task retries."""
    logger.warning(f"Task {sender.name} [{task_id}] retrying: {reason}")


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handle worker ready event."""
    logger.info(f"Celery worker {sender.hostname} is ready")