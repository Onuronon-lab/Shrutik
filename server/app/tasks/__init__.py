# Celery tasks package
# Import all tasks to register them with Celery

from app.tasks.audio_processing import (
    batch_process_recordings,
    calculate_consensus_for_chunks,
    cleanup_orphaned_chunks,
    process_audio_recording,
    recalculate_all_consensus,
    reprocess_failed_recordings,
)
from app.tasks.export_optimization import (
    calculate_consensus_for_chunks_export,
    check_export_alerts_task,
    cleanup_exported_chunks,
    create_export_batch_task,
)

__all__ = [
    # Audio processing tasks
    "process_audio_recording",
    "batch_process_recordings",
    "cleanup_orphaned_chunks",
    "reprocess_failed_recordings",
    "calculate_consensus_for_chunks",
    "recalculate_all_consensus",
    # Export optimization tasks
    "calculate_consensus_for_chunks_export",
    "create_export_batch_task",
    "cleanup_exported_chunks",
    "check_export_alerts_task",
]
