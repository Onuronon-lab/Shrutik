#!/usr/bin/env python3
"""
trigger_audio_processing.py - Manually trigger Celery audio processing tasks

This script queues Celery tasks to process uploaded voice recordings that haven't been chunked yet.
Useful when Celery workers aren't running automatically or you want to manually trigger processing.

Usage:
    DATABASE_URL=postgresql://postgres:password@postgres:5432/voice_collection \
    python trigger_audio_processing.py
"""

import os
import sys
import time
from typing import List

# Check dependencies
missing_deps = []
try:
    from sqlalchemy import create_engine, text
except ImportError:
    missing_deps.append("sqlalchemy")

try:
    from celery import Celery
except ImportError:
    missing_deps.append("celery")


if missing_deps:
    print("ERROR: Missing required dependencies!")
    print(f"\nPlease install: pip install {' '.join(missing_deps)}")
    sys.exit(1)

# ----------------- CONFIG -----------------
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

if not DATABASE_URL:
    print("ERROR: Please set DATABASE_URL environment variable.")
    print(
        "Example: DATABASE_URL=postgresql://postgres:password@postgres:5432/voice_collection"
    )
    sys.exit(1)

# ----------------- CELERY SETUP -----------------

# Create Celery app (mimics your app's celery config)
celery_app = Celery("voice_collection", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# ----------------- DATABASE OPERATIONS -----------------

engine = create_engine(DATABASE_URL, future=True)


def check_celery_workers():
    """Check if Celery workers are available."""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        if stats is None or len(stats) == 0:
            return False, "No Celery workers found"

        worker_count = len(stats)
        return True, f"Found {worker_count} active worker(s)"
    except Exception as e:
        return False, f"Error checking workers: {e}"


def check_redis_connection():
    """Check if Redis is accessible."""
    try:
        import redis as redis_lib

        r = redis_lib.from_url(REDIS_URL)
        r.ping()
        return True, "Redis connection OK"
    except Exception as e:
        return False, f"Redis connection failed: {e}"


def get_unprocessed_recordings(filter_generated: bool = False):
    """Get recordings that need processing (status = UPLOADED)."""
    with engine.begin() as conn:
        if filter_generated:
            # Only get generated test data
            query = text(
                """
                SELECT id, file_path, created_at
                FROM voice_recordings
                WHERE status = 'UPLOADED'
                AND meta_data->>'generated_by' IN ('generate_test_data', 'generate_test_data_v2')
                ORDER BY created_at ASC
                """
            )
        else:
            # Get all unprocessed recordings
            query = text(
                """
                SELECT id, file_path, created_at
                FROM voice_recordings
                WHERE status = 'UPLOADED'
                ORDER BY created_at ASC
                """
            )

        results = conn.execute(query).fetchall()
        return [{"id": r[0], "file_path": r[1], "created_at": r[2]} for r in results]


def get_processing_stats():
    """Get statistics about recording processing status."""
    with engine.begin() as conn:
        stats = {}

        # Count by status
        for status in ["UPLOADED", "PROCESSING", "CHUNKED", "FAILED"]:
            count = conn.execute(
                text(f"SELECT COUNT(*) FROM voice_recordings WHERE status = '{status}'")
            ).scalar()
            stats[status] = count

        # Count generated vs non-generated
        generated_count = conn.execute(
            text(
                """
            SELECT COUNT(*) FROM voice_recordings
            WHERE meta_data->>'generated_by' IN ('generate_test_data', 'generate_test_data_v2')
            """
            )
        ).scalar()
        stats["generated"] = generated_count
        stats["non_generated"] = (
            stats["UPLOADED"]
            + stats["PROCESSING"]
            + stats["CHUNKED"]
            + stats["FAILED"]
            - generated_count
        )

        return stats


def trigger_processing_tasks(recording_ids: List[int], batch_size: int = 10):
    """Queue Celery tasks for processing recordings."""
    print(f"\n🚀 Queuing {len(recording_ids)} recordings for processing...")

    queued = []
    failed = []

    for i, recording_id in enumerate(recording_ids, 1):
        try:
            # Queue the task (using the task name from your app)
            result = celery_app.send_task(
                "process_audio_recording", args=[recording_id], queue="audio_processing"
            )

            queued.append({"recording_id": recording_id, "task_id": result.id})

            print(
                f"  ✓ [{i}/{len(recording_ids)}] Queued recording {recording_id} (task: {result.id})"
            )

            # Small delay between batches to avoid overwhelming the queue
            if i % batch_size == 0:
                time.sleep(0.5)

        except Exception as e:
            failed.append({"recording_id": recording_id, "error": str(e)})
            print(
                f"  ✗ [{i}/{len(recording_ids)}] Failed to queue recording {recording_id}: {e}"
            )

    return queued, failed


# ----------------- MAIN -----------------


def main():
    print("=" * 60)
    print("TRIGGER AUDIO PROCESSING")
    print("=" * 60)

    # Check Redis connection
    print("\n🔍 Checking connections...")
    redis_ok, redis_msg = check_redis_connection()
    print(f"  Redis: {redis_msg}")

    if not redis_ok:
        print("\n❌ Cannot proceed without Redis connection.")
        print("   Make sure Redis is running and REDIS_URL is correct.")
        sys.exit(1)

    # Check Celery workers
    workers_ok, workers_msg = check_celery_workers()
    print(f"  Celery: {workers_msg}")

    if not workers_ok:
        print("\n⚠️  WARNING: No Celery workers detected!")
        print(
            "   Tasks will be queued but won't be processed until workers are started."
        )
        confirm = input("\n   Continue anyway? [y/N]: ").strip().lower()
        if confirm not in ["y", "yes"]:
            print("\n❌ Cancelled.")
            return

    # Get processing statistics
    print("\n📊 Current processing status:")
    stats = get_processing_stats()
    print(f"  - UPLOADED (pending): {stats['UPLOADED']}")
    print(f"  - PROCESSING: {stats['PROCESSING']}")
    print(f"  - CHUNKED (complete): {stats['CHUNKED']}")
    print(f"  - FAILED: {stats['FAILED']}")
    print(f"\n  - Generated test data: {stats['generated']}")
    print(f"  - Other recordings: {stats['non_generated']}")

    if stats["UPLOADED"] == 0:
        print("\n✓ No recordings need processing. All done!")
        return

    # Ask what to process
    print("\n📋 What would you like to process?")
    print("  1. All unprocessed recordings")
    print("  2. Only generated test data")
    print("  3. Cancel")

    choice = input("\nChoice [1-3]: ").strip()

    if choice == "3":
        print("\n❌ Cancelled.")
        return

    filter_generated = choice == "2"

    # Get unprocessed recordings
    print("\n🔍 Finding unprocessed recordings...")
    recordings = get_unprocessed_recordings(filter_generated)

    if not recordings:
        print("\n✓ No recordings found matching your criteria.")
        return

    print(f"\nFound {len(recordings)} recording(s) to process:")

    # Show first few recordings
    preview_count = min(5, len(recordings))
    for i, rec in enumerate(recordings[:preview_count], 1):
        print(f"  {i}. Recording ID {rec['id']} - {rec['file_path']}")

    if len(recordings) > preview_count:
        print(f"  ... and {len(recordings) - preview_count} more")

    # Confirm
    confirm = (
        input(f"\nQueue {len(recordings)} recording(s) for processing? [Y/n]: ")
        .strip()
        .lower()
    )
    if confirm and confirm not in ["y", "yes"]:
        print("\n❌ Cancelled.")
        return

    # Trigger processing
    recording_ids = [rec["id"] for rec in recordings]
    queued, failed = trigger_processing_tasks(recording_ids)

    # Summary
    print("\n" + "=" * 60)
    print("✅ PROCESSING TRIGGERED")
    print("=" * 60)
    print(f"\nSuccessfully queued: {len(queued)}")
    print(f"Failed to queue: {len(failed)}")

    if failed:
        print("\n⚠️  Failed recordings:")
        for item in failed[:10]:  # Show first 10 failures
            print(f"  - Recording {item['recording_id']}: {item['error']}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")

    if queued:
        print("\n💡 Tips:")
        print("  - Monitor progress in Flower: http://localhost:5555")
        print("  - Check Celery logs: docker-compose logs celery -f")
        print("  - View task status in your application")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
