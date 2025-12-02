#!/usr/bin/env python3
"""
Backfill script for transcript_count field in audio_chunks table.

This script counts existing transcriptions for each chunk and updates
the transcript_count field. It processes chunks in batches to avoid
memory issues with large datasets.

Usage:
    python scripts/backfill_transcript_count.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


def backfill_transcript_count(db: Session) -> None:
    """
    Backfill transcript_count for all audio chunks.

    Processes chunks in batches of 1000 to avoid memory issues.
    """
    logger.info("Starting transcript_count backfill...")

    try:
        # Get total count of chunks
        result = db.execute(text("SELECT COUNT(*) FROM audio_chunks"))
        total_chunks = result.scalar()
        logger.info(f"Total chunks to process: {total_chunks}")

        if total_chunks == 0:
            logger.info("No chunks found. Nothing to backfill.")
            return

        # Process in batches
        processed = 0
        updated = 0

        while processed < total_chunks:
            # Update transcript_count using a subquery
            # This is more efficient than fetching and updating individually
            query = text(
                """
                UPDATE audio_chunks
                SET transcript_count = (
                    SELECT COUNT(*)
                    FROM transcriptions
                    WHERE transcriptions.chunk_id = audio_chunks.id
                )
                WHERE audio_chunks.id IN (
                    SELECT id
                    FROM audio_chunks
                    ORDER BY id
                    LIMIT :batch_size
                    OFFSET :offset
                )
            """
            )

            result = db.execute(query, {"batch_size": BATCH_SIZE, "offset": processed})

            batch_updated = result.rowcount
            updated += batch_updated
            processed += BATCH_SIZE

            # Commit after each batch
            db.commit()

            logger.info(
                f"Progress: {min(processed, total_chunks)}/{total_chunks} chunks processed "
                f"({updated} updated)"
            )

        logger.info(f"Backfill completed successfully! Total chunks updated: {updated}")

        # Log some statistics
        result = db.execute(
            text(
                """
            SELECT
                COUNT(*) as total_chunks,
                SUM(transcript_count) as total_transcriptions,
                AVG(transcript_count) as avg_transcriptions_per_chunk,
                MAX(transcript_count) as max_transcriptions
            FROM audio_chunks
        """
            )
        )

        stats = result.fetchone()
        logger.info("Statistics after backfill:")
        logger.info(f"  Total chunks: {stats[0]}")
        logger.info(f"  Total transcriptions: {stats[1]}")
        logger.info(f"  Average transcriptions per chunk: {stats[2]:.2f}")
        logger.info(f"  Max transcriptions for a single chunk: {stats[3]}")

    except Exception as e:
        logger.error(f"Error during backfill: {e}")
        db.rollback()
        raise


def main():
    """Main entry point for the backfill script."""
    logger.info("=" * 60)
    logger.info("Audio Chunks Transcript Count Backfill Script")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        backfill_transcript_count(db)
    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        sys.exit(1)
    finally:
        db.close()

    logger.info("=" * 60)
    logger.info("Backfill script completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
