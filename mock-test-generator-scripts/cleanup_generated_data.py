#!/usr/bin/env python3
"""
cleanup_generated_data.py - Clean up all generated test data

This script removes:
- Generated voice recordings (from database and filesystem)
- Generated scripts (from database)
- Audio chunks created from generated recordings (from database and filesystem)
- Transcriptions associated with generated chunks

Usage:
    DATABASE_URL=postgresql://postgres:password@postgres:5432/voice_collection \
    python cleanup_generated_data.py
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

# Check dependencies
try:
    from sqlalchemy import create_engine, text
except ImportError:
    print("ERROR: Missing sqlalchemy. Install with: pip install sqlalchemy")
    sys.exit(1)

# ----------------- CONFIG -----------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: Please set DATABASE_URL environment variable.")
    print(
        "Example: DATABASE_URL=postgresql://postgres:password@postgres:5432/voice_collection"
    )
    sys.exit(1)

# Find project root and uploads directory
script_dir = Path(__file__).parent
if script_dir.name == "mock-test-generator-scripts":
    project_root = script_dir.parent
else:
    project_root = Path.cwd()

UPLOADS_DIR = project_root / "uploads"
GENERATED_AUDIO_DIR = UPLOADS_DIR / "generated_audio"
CHUNKS_DIR = UPLOADS_DIR / "chunks"

# ----------------- DATABASE OPERATIONS -----------------

engine = create_engine(DATABASE_URL, future=True)


def get_generated_data_stats():
    """Get statistics about generated data."""
    with engine.begin() as conn:
        # Count generated scripts
        scripts_count = conn.execute(
            text(
                "SELECT COUNT(*) FROM scripts WHERE meta_data->>'generated_by' IN ('generate_test_data', 'generate_test_data_v2')"
            )
        ).scalar()

        # Count generated recordings
        recordings_count = conn.execute(
            text(
                "SELECT COUNT(*) FROM voice_recordings WHERE meta_data->>'generated_by' IN ('generate_test_data', 'generate_test_data_v2')"
            )
        ).scalar()

        # Count chunks from generated recordings
        chunks_count = conn.execute(
            text(
                """
            SELECT COUNT(ac.id)
            FROM audio_chunks ac
            JOIN voice_recordings vr ON ac.recording_id = vr.id
            WHERE vr.meta_data->>'generated_by' IN ('generate_test_data', 'generate_test_data_v2')
            """
            )
        ).scalar()

        # Count transcriptions from generated chunks
        transcriptions_count = conn.execute(
            text(
                """
            SELECT COUNT(t.id)
            FROM transcriptions t
            JOIN audio_chunks ac ON t.chunk_id = ac.id
            JOIN voice_recordings vr ON ac.recording_id = vr.id
            WHERE vr.meta_data->>'generated_by' IN ('generate_test_data', 'generate_test_data_v2')
            """
            )
        ).scalar()

        return {
            "scripts": scripts_count,
            "recordings": recordings_count,
            "chunks": chunks_count,
            "transcriptions": transcriptions_count,
        }


def get_generated_file_paths():
    """Get file paths for generated recordings and chunks."""
    with engine.begin() as conn:
        # Get recording file paths
        recording_paths = conn.execute(
            text(
                """
            SELECT id, file_path
            FROM voice_recordings
            WHERE meta_data->>'generated_by' IN ('generate_test_data', 'generate_test_data_v2')
            """
            )
        ).fetchall()

        # Get chunk file paths
        chunk_paths = conn.execute(
            text(
                """
            SELECT ac.id, ac.file_path
            FROM audio_chunks ac
            JOIN voice_recordings vr ON ac.recording_id = vr.id
            WHERE vr.meta_data->>'generated_by' IN ('generate_test_data', 'generate_test_data_v2')
            """
            )
        ).fetchall()

        return recording_paths, chunk_paths


def cleanup_database():
    """Remove generated data from database."""
    print("\n🗑️  Cleaning up database...")

    with engine.begin() as conn:
        # First, clear consensus transcript references in audio chunks to avoid foreign key constraint violations
        result = conn.execute(
            text(
                """
            UPDATE audio_chunks
            SET consensus_transcript_id = NULL
            WHERE recording_id IN (
                SELECT id FROM voice_recordings
                WHERE meta_data->>'generated_by' IN ('generate_test_data', 'generate_test_data_v2')
            )
            """
            )
        )
        consensus_refs_cleared = result.rowcount
        print(f"  ✓ Cleared {consensus_refs_cleared} consensus transcript references")

        # Delete transcriptions (now safe from foreign key constraints)
        result = conn.execute(
            text(
                """
            DELETE FROM transcriptions
            WHERE chunk_id IN (
                SELECT ac.id
                FROM audio_chunks ac
                JOIN voice_recordings vr ON ac.recording_id = vr.id
                WHERE vr.meta_data->>'generated_by' IN ('generate_test_data', 'generate_test_data_v2')
            )
            """
            )
        )
        transcriptions_deleted = result.rowcount
        print(f"  ✓ Deleted {transcriptions_deleted} transcriptions")

        # Delete audio chunks
        result = conn.execute(
            text(
                """
            DELETE FROM audio_chunks
            WHERE recording_id IN (
                SELECT id FROM voice_recordings
                WHERE meta_data->>'generated_by' IN ('generate_test_data', 'generate_test_data_v2')
            )
            """
            )
        )
        chunks_deleted = result.rowcount
        print(f"  ✓ Deleted {chunks_deleted} audio chunks")

        # Delete voice recordings
        result = conn.execute(
            text(
                """
            DELETE FROM voice_recordings
            WHERE meta_data->>'generated_by' IN ('generate_test_data', 'generate_test_data_v2')
            """
            )
        )
        recordings_deleted = result.rowcount
        print(f"  ✓ Deleted {recordings_deleted} voice recordings")

        # Delete scripts
        result = conn.execute(
            text(
                """
            DELETE FROM scripts
            WHERE meta_data->>'generated_by' IN ('generate_test_data', 'generate_test_data_v2')
            """
            )
        )
        scripts_deleted = result.rowcount
        print(f"  ✓ Deleted {scripts_deleted} scripts")

        return {
            "consensus_refs_cleared": consensus_refs_cleared,
            "transcriptions": transcriptions_deleted,
            "chunks": chunks_deleted,
            "recordings": recordings_deleted,
            "scripts": scripts_deleted,
        }


def cleanup_files(recording_paths: List[Tuple], chunk_paths: List[Tuple]):
    """Remove generated audio files from filesystem."""
    print("\n🗑️  Cleaning up files...")

    files_deleted = 0
    files_not_found = 0
    permission_errors = 0

    def try_delete_file(file_path_str):
        """Try to delete a file, handling various path formats."""
        nonlocal files_deleted, files_not_found, permission_errors

        if not file_path_str:
            return

        # Try multiple path interpretations
        possible_paths = []

        # 1. If it starts with /app/ (Docker path), convert to local path
        if file_path_str.startswith("/app/"):
            local_path = file_path_str.replace("/app/", "")
            possible_paths.append(project_root / local_path)

        # 2. If it's an absolute path, use as-is
        elif file_path_str.startswith("/"):
            possible_paths.append(Path(file_path_str))

        # 3. If it's relative, try from project root
        else:
            possible_paths.append(project_root / file_path_str)

        # 4. Also try just the filename in uploads/generated_audio
        filename = Path(file_path_str).name
        possible_paths.append(GENERATED_AUDIO_DIR / filename)

        # Try each possible path
        deleted = False
        for full_path in possible_paths:
            if full_path.exists():
                try:
                    full_path.unlink()
                    files_deleted += 1
                    deleted = True
                    break
                except PermissionError as e:
                    permission_errors += 1
                    print(f"  ⚠️  Permission denied: {full_path}")
                    print(f"      Try running with sudo or fix permissions")
                    break
                except Exception as e:
                    print(f"  ⚠️  Failed to delete {full_path}: {e}")
                    break

        if not deleted and not any(p.exists() for p in possible_paths):
            files_not_found += 1

    # Delete recording files
    for rec_id, file_path in recording_paths:
        try_delete_file(file_path)

    # Delete chunk files
    for chunk_id, file_path in chunk_paths:
        try_delete_file(file_path)

    print(f"  ✓ Deleted {files_deleted} files")
    if files_not_found > 0:
        print(f"  ℹ️  {files_not_found} files were already missing")
    if permission_errors > 0:
        print(f"  ⚠️  {permission_errors} files couldn't be deleted due to permissions")
        print(f"      Run with: sudo python {Path(__file__).name}")

    return files_deleted, files_not_found


def cleanup_empty_directories():
    """Remove empty chunk directories and generated_audio directory."""
    print("\n🗑️  Cleaning up empty directories...")

    dirs_removed = 0

    # Clean up empty chunk directories
    if CHUNKS_DIR.exists():
        for item in CHUNKS_DIR.iterdir():
            if item.is_dir():
                try:
                    # Try to remove if empty
                    item.rmdir()
                    dirs_removed += 1
                except OSError:
                    # Directory not empty, skip
                    pass

    # Remove generated_audio directory if it exists and is empty
    if GENERATED_AUDIO_DIR.exists():
        try:
            # Check if empty
            if not any(GENERATED_AUDIO_DIR.iterdir()):
                GENERATED_AUDIO_DIR.rmdir()
                dirs_removed += 1
                print(f"  ✓ Removed generated_audio directory")
            else:
                print(f"  ℹ️  generated_audio directory not empty, keeping it")
        except Exception as e:
            print(f"  ⚠️  Could not remove generated_audio directory: {e}")

    if dirs_removed > 0:
        print(f"  ✓ Removed {dirs_removed} empty directories")

    return dirs_removed


# ----------------- MAIN -----------------


def main():
    print("=" * 60)
    print("CLEANUP GENERATED TEST DATA")
    print("=" * 60)

    # Get statistics
    print("\n📊 Checking generated data...")
    stats = get_generated_data_stats()

    if all(count == 0 for count in stats.values()):
        print("\n✓ No generated data found. Nothing to clean up.")
        return

    print(f"\nFound generated data:")
    print(f"  - Scripts: {stats['scripts']}")
    print(f"  - Voice recordings: {stats['recordings']}")
    print(f"  - Audio chunks: {stats['chunks']}")
    print(f"  - Transcriptions: {stats['transcriptions']}")

    # Confirm deletion
    print("\n⚠️  WARNING: This will permanently delete all generated test data!")
    confirm = input("\nProceed with cleanup? [y/N]: ").strip().lower()

    if confirm not in ["y", "yes"]:
        print("\n❌ Cleanup cancelled.")
        return

    # Get file paths before deleting from database
    print("\n📋 Collecting file paths...")
    recording_paths, chunk_paths = get_generated_file_paths()
    print(f"  ✓ Found {len(recording_paths)} recording files")
    print(f"  ✓ Found {len(chunk_paths)} chunk files")

    # Clean up database
    db_stats = cleanup_database()

    # Clean up files
    files_deleted, files_not_found = cleanup_files(recording_paths, chunk_paths)

    # Clean up empty directories
    dirs_removed = cleanup_empty_directories()

    # Summary
    print("\n" + "=" * 60)
    print("✅ CLEANUP COMPLETE")
    print("=" * 60)
    print("\nDatabase cleanup:")
    print(f"  - Consensus references cleared: {db_stats['consensus_refs_cleared']}")
    print(f"  - Transcriptions deleted: {db_stats['transcriptions']}")
    print(f"  - Audio chunks deleted: {db_stats['chunks']}")
    print(f"  - Voice recordings deleted: {db_stats['recordings']}")
    print(f"  - Scripts deleted: {db_stats['scripts']}")
    print(f"\nFilesystem cleanup:")
    print(f"  - Files deleted: {files_deleted}")
    print(f"  - Empty directories removed: {dirs_removed}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cleanup cancelled by user.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
