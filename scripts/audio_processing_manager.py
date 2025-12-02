#!/usr/bin/env python3
"""
Audio Processing Management Script

This script provides utilities for managing the audio processing system,
including testing chunking algorithms, processing recordings, and monitoring tasks.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.database import SessionLocal
from app.models.audio_chunk import AudioChunk
from app.models.voice_recording import RecordingStatus, VoiceRecording
from app.services.audio_processing_service import (
    AudioChunkingService,
    AudioProcessingError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_chunking_algorithm(
    audio_file_path: str, output_dir: Optional[str] = None
) -> None:
    """Test the chunking algorithm on a single audio file."""
    if not os.path.exists(audio_file_path):
        logger.error(f"Audio file not found: {audio_file_path}")
        return

    logger.info(f"Testing chunking algorithm on: {audio_file_path}")

    try:
        # Initialize the chunking service
        chunking_service = AudioChunkingService()

        # Load audio
        audio_data, sr = chunking_service.load_audio(audio_file_path)
        audio_duration = len(audio_data) / sr

        logger.info(f"Loaded audio: duration={audio_duration:.2f}s, sample_rate={sr}")

        # Find sentence boundaries
        boundaries = chunking_service.find_sentence_boundaries(audio_data, sr)
        logger.info(f"Found {len(boundaries)} sentence boundaries: {boundaries}")

        # Create chunks
        chunk_intervals = chunking_service.create_chunks_intelligent(
            audio_data, sr, boundaries
        )
        logger.info(f"Created {len(chunk_intervals)} chunks")

        # Display chunk information
        for i, (start, end) in enumerate(chunk_intervals):
            duration = end - start
            logger.info(
                f"Chunk {i}: {start:.2f}s - {end:.2f}s (duration: {duration:.2f}s)"
            )

        # Save chunks if output directory specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            logger.info(f"Saving chunks to: {output_path}")

            for i, (start_time, end_time) in enumerate(chunk_intervals):
                chunk_filename = f"test_chunk_{i:03d}.wav"
                chunk_path = output_path / chunk_filename

                metadata = chunking_service.save_chunk(
                    audio_data, sr, start_time, end_time, str(chunk_path)
                )

                logger.info(f"Saved {chunk_filename}: {metadata}")

        logger.info("Chunking test completed successfully")

    except AudioProcessingError as e:
        logger.error(f"Audio processing error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def process_recording_by_id(recording_id: int) -> None:
    """Process a specific recording by ID."""
    db = SessionLocal()

    try:
        # Get recording
        recording = (
            db.query(VoiceRecording).filter(VoiceRecording.id == recording_id).first()
        )
        if not recording:
            logger.error(f"Recording {recording_id} not found")
            return

        logger.info(f"Processing recording {recording_id}: {recording.file_path}")

        # Check if file exists
        if not os.path.exists(recording.file_path):
            logger.error(f"Audio file not found: {recording.file_path}")
            return

        # Process the recording
        chunking_service = AudioChunkingService()
        chunks = chunking_service.process_recording(
            recording_id, recording.file_path, db
        )

        logger.info(
            f"Successfully processed recording {recording_id} into {len(chunks)} chunks"
        )

        # Display chunk information
        for chunk in chunks:
            logger.info(
                f"Chunk {chunk.chunk_index}: {chunk.start_time:.2f}s - {chunk.end_time:.2f}s "
                f"(duration: {chunk.duration:.2f}s)"
            )

    except Exception as e:
        logger.error(f"Failed to process recording {recording_id}: {e}")
    finally:
        db.close()


def process_all_uploaded_recordings() -> None:
    """Process all recordings with UPLOADED status."""
    db = SessionLocal()

    try:
        # Find uploaded recordings
        uploaded_recordings = (
            db.query(VoiceRecording)
            .filter(VoiceRecording.status == RecordingStatus.UPLOADED)
            .all()
        )

        if not uploaded_recordings:
            logger.info("No uploaded recordings found")
            return

        logger.info(f"Found {len(uploaded_recordings)} uploaded recordings to process")

        # Process each recording
        for recording in uploaded_recordings:
            logger.info(f"Processing recording {recording.id}")
            try:
                process_recording_by_id(recording.id)
            except Exception as e:
                logger.error(f"Failed to process recording {recording.id}: {e}")

        logger.info("Batch processing completed")

    finally:
        db.close()


def show_recording_statistics() -> None:
    """Display statistics about recordings and chunks."""
    db = SessionLocal()

    try:
        # Recording statistics
        total_recordings = db.query(VoiceRecording).count()
        uploaded_count = (
            db.query(VoiceRecording)
            .filter(VoiceRecording.status == RecordingStatus.UPLOADED)
            .count()
        )
        processing_count = (
            db.query(VoiceRecording)
            .filter(VoiceRecording.status == RecordingStatus.PROCESSING)
            .count()
        )
        chunked_count = (
            db.query(VoiceRecording)
            .filter(VoiceRecording.status == RecordingStatus.CHUNKED)
            .count()
        )
        failed_count = (
            db.query(VoiceRecording)
            .filter(VoiceRecording.status == RecordingStatus.FAILED)
            .count()
        )

        # Chunk statistics
        total_chunks = db.query(AudioChunk).count()

        logger.info("=== Recording Statistics ===")
        logger.info(f"Total recordings: {total_recordings}")
        logger.info(f"  - Uploaded: {uploaded_count}")
        logger.info(f"  - Processing: {processing_count}")
        logger.info(f"  - Chunked: {chunked_count}")
        logger.info(f"  - Failed: {failed_count}")
        logger.info(f"Total chunks: {total_chunks}")

        if chunked_count > 0:
            avg_chunks = total_chunks / chunked_count
            logger.info(f"Average chunks per recording: {avg_chunks:.1f}")

    finally:
        db.close()


def cleanup_failed_recordings() -> None:
    """Reset failed recordings to uploaded status for reprocessing."""
    db = SessionLocal()

    try:
        failed_recordings = (
            db.query(VoiceRecording)
            .filter(VoiceRecording.status == RecordingStatus.FAILED)
            .all()
        )

        if not failed_recordings:
            logger.info("No failed recordings found")
            return

        logger.info(f"Found {len(failed_recordings)} failed recordings")

        for recording in failed_recordings:
            recording.status = RecordingStatus.UPLOADED
            logger.info(f"Reset recording {recording.id} to UPLOADED status")

        db.commit()
        logger.info("Failed recordings reset successfully")

    finally:
        db.close()


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Audio Processing Management Script")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Test chunking command
    test_parser = subparsers.add_parser(
        "test-chunking", help="Test chunking algorithm on an audio file"
    )
    test_parser.add_argument("audio_file", help="Path to audio file to test")
    test_parser.add_argument("--output-dir", help="Directory to save test chunks")

    # Process recording command
    process_parser = subparsers.add_parser(
        "process-recording", help="Process a specific recording by ID"
    )
    process_parser.add_argument(
        "recording_id", type=int, help="Recording ID to process"
    )

    # Process all uploaded command
    subparsers.add_parser(
        "process-all-uploaded", help="Process all recordings with UPLOADED status"
    )

    # Statistics command
    subparsers.add_parser("stats", help="Show recording and chunk statistics")

    # Cleanup command
    subparsers.add_parser(
        "cleanup-failed", help="Reset failed recordings to uploaded status"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "test-chunking":
            test_chunking_algorithm(args.audio_file, args.output_dir)
        elif args.command == "process-recording":
            process_recording_by_id(args.recording_id)
        elif args.command == "process-all-uploaded":
            process_all_uploaded_recordings()
        elif args.command == "stats":
            show_recording_statistics()
        elif args.command == "cleanup-failed":
            cleanup_failed_recordings()
        else:
            logger.error(f"Unknown command: {args.command}")
            parser.print_help()

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
