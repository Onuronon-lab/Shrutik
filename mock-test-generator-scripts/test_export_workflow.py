#!/usr/bin/env python3
"""
test_export_workflow.py - Test the complete export batch functionality

This script tests the export batch creation and download workflow by:
1. Creating export batches from ready chunks
2. Testing batch download functionality
3. Verifying export batch contents
4. Cleaning up test data

Features:
- Creates test export batches with different parameters
- Tests local and R2 storage (if configured)
- Validates export batch contents and metadata
- Tests download limits and authentication
- Provides comprehensive workflow testing

Usage:
    DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
    python test_export_workflow.py
"""

import json
import os
import sys
from typing import Dict, List, Optional

# Check dependencies
missing_deps = []
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
except ImportError:
    missing_deps.append("sqlalchemy")

if missing_deps:
    print("ERROR: Missing required dependencies!")
    print(f"\nPlease install: pip install {' '.join(missing_deps)}")
    sys.exit(1)

# ----------------- CONFIG -----------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: Please set DATABASE_URL environment variable.")
    print(
        "Example: DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection"
    )
    sys.exit(1)

# Create database engine and session
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ExportWorkflowTester:
    """Tests the complete export batch workflow."""

    def __init__(self):
        self.db = SessionLocal()
        self.test_user_id = None
        self._setup_test_user()

    def _setup_test_user(self):
        """Create or get test user for export testing."""
        test_email = "export.tester@mock.com"

        # Check if user exists
        result = self.db.execute(
            text("SELECT id FROM users WHERE email = :email"), {"email": test_email}
        ).first()

        if result:
            self.test_user_id = result[0]
        else:
            # Create user
            result = self.db.execute(
                text(
                    """
                    INSERT INTO users (name, email, password_hash, role, meta_data)
                    VALUES (:name, :email, :pwd, :role, :meta)
                    RETURNING id
                """
                ),
                {
                    "name": "Export Tester",
                    "email": test_email,
                    "pwd": "export_tester",
                    "role": "ADMIN",  # Admin role for export access
                    "meta": json.dumps(
                        {"mock_user": True, "created_for": "export_testing"}
                    ),
                },
            )
            self.test_user_id = result.scalar_one()
            self.db.commit()

        print(f"✓ Set up test user (ID: {self.test_user_id})")

    def get_export_statistics(self) -> Dict:
        """Get current export statistics."""
        stats = {}

        # Ready chunks
        result = self.db.execute(
            text(
                """
            SELECT COUNT(*) FROM audio_chunks WHERE ready_for_export = true
        """
            )
        ).scalar()
        stats["ready_chunks"] = result

        # Existing export batches
        result = self.db.execute(
            text(
                """
            SELECT COUNT(*) FROM export_batches
        """
            )
        ).scalar()
        stats["total_batches"] = result

        # Completed export batches
        result = self.db.execute(
            text(
                """
            SELECT COUNT(*) FROM export_batches WHERE status = 'completed'
        """
            )
        ).scalar()
        stats["completed_batches"] = result

        # Chunks already exported - simplified since we don't have export batches yet
        stats["exported_chunks"] = 0

        # Available for export (ready but not exported)
        stats["available_for_export"] = stats["ready_chunks"] - stats["exported_chunks"]

        return stats

    def create_test_export_batch(
        self, max_chunks: int = 50, force_create: bool = True
    ) -> Optional[str]:
        """Create a test export batch."""
        try:
            # Import the export service
            import sys
            from pathlib import Path

            # Add app directory to path
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            sys.path.insert(0, str(project_root))

            from app.core.config import StorageConfig
            from app.models.user import UserRole
            from app.services.export_batch_service import ExportBatchService

            # Create export service
            storage_config = StorageConfig.from_env()
            export_service = ExportBatchService(self.db, storage_config)

            print(
                f"  📦 Creating export batch (max_chunks={max_chunks}, force_create={force_create})..."
            )

            # Create export batch
            batch = export_service.create_export_batch(
                max_chunks=max_chunks,
                user_id=self.test_user_id,
                user_role=UserRole.ADMIN,  # Use ADMIN role to match test user
                force_create=force_create,
            )

            print(f"  ✅ Created export batch: {batch.batch_id}")
            print(f"     - Chunks: {batch.chunk_count}")
            print(f"     - Size: {batch.file_size_bytes / (1024*1024):.2f} MB")
            print(f"     - Storage: {batch.storage_type.value}")
            print(f"     - Status: {batch.status.value}")

            return batch.batch_id

        except Exception as e:
            print(f"  ❌ Failed to create export batch: {e}")
            return None

    def test_export_batch_download(self, batch_id: str) -> bool:
        """Test downloading an export batch."""
        try:
            # Import the export service
            import sys
            from pathlib import Path

            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            sys.path.insert(0, str(project_root))

            from app.core.config import StorageConfig
            from app.models.user import UserRole
            from app.services.export_batch_service import ExportBatchService

            # Create export service
            storage_config = StorageConfig.from_env()
            export_service = ExportBatchService(self.db, storage_config)

            print(f"  📥 Testing download for batch {batch_id}...")

            # Test download
            result = export_service.download_export_batch(
                batch_id=batch_id,
                user_id=self.test_user_id,
                user_role=UserRole.ADMIN,  # Use ADMIN role to match test user
                ip_address="127.0.0.1",
                user_agent="ExportWorkflowTester/1.0",
            )

            if isinstance(result, tuple):
                # Local storage - file path and mime type
                file_path, mime_type = result
                print(f"  ✅ Local download successful:")
                print(f"     - File: {file_path}")
                print(f"     - MIME: {mime_type}")
                print(f"     - Exists: {os.path.exists(file_path)}")
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"     - Size: {file_size / (1024*1024):.2f} MB")
            else:
                # R2 storage - signed URL
                print(f"  ✅ R2 download successful:")
                print(f"     - URL: {result['download_url'][:100]}...")
                print(f"     - Expires: {result['expires_in']} seconds")

            return True

        except Exception as e:
            print(f"  ❌ Download test failed: {e}")
            return False

    def verify_export_batch_contents(self, batch_id: str) -> bool:
        """Verify the contents of an export batch."""
        try:
            # Get batch info
            result = self.db.execute(
                text("SELECT * FROM export_batches WHERE batch_id = :batch_id"),
                {"batch_id": batch_id},
            ).first()

            if not result:
                print(f"  ❌ Batch {batch_id} not found")
                return False

            print(f"  🔍 Verifying batch contents...")
            print(f"     - Batch ID: {result.batch_id}")
            print(f"     - Chunk count: {result.chunk_count}")
            print(f"     - Status: {result.status}")
            print(f"     - Storage type: {result.storage_type}")
            print(f"     - Archive path: {result.archive_path}")

            # Verify chunk IDs
            chunk_ids = result.chunk_ids
            if not chunk_ids or len(chunk_ids) == 0:
                print(f"  ❌ No chunk IDs in batch")
                return False

            print(f"     - Chunk IDs: {len(chunk_ids)} chunks")

            # Verify chunks exist and are ready for export
            placeholders = ",".join([":chunk_" + str(i) for i in range(len(chunk_ids))])
            params = {f"chunk_{i}": chunk_id for i, chunk_id in enumerate(chunk_ids)}

            chunk_check = self.db.execute(
                text(
                    f"""
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN ready_for_export THEN 1 END) as ready
                    FROM audio_chunks
                    WHERE id IN ({placeholders})
                """
                ),
                params,
            ).first()

            print(f"     - Chunks found: {chunk_check.total}/{len(chunk_ids)}")
            print(f"     - Ready for export: {chunk_check.ready}/{len(chunk_ids)}")

            if chunk_check.total != len(chunk_ids):
                print(f"  ⚠️  Some chunks not found in database")

            if chunk_check.ready != len(chunk_ids):
                print(f"  ⚠️  Some chunks not ready for export")

            # Check file existence (for local storage)
            if result.storage_type == "local" and result.archive_path:
                file_exists = os.path.exists(result.archive_path)
                print(f"     - Archive file exists: {file_exists}")

                if file_exists:
                    file_size = os.path.getsize(result.archive_path)
                    print(f"     - Archive file size: {file_size / (1024*1024):.2f} MB")

            return True

        except Exception as e:
            print(f"  ❌ Verification failed: {e}")
            return False

    def test_download_limits(self, batch_id: str) -> bool:
        """Test download rate limiting."""
        try:
            import sys
            from pathlib import Path

            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            sys.path.insert(0, str(project_root))

            from app.core.config import StorageConfig
            from app.models.user import UserRole
            from app.services.export_batch_service import ExportBatchService

            storage_config = StorageConfig.from_env()
            export_service = ExportBatchService(self.db, storage_config)

            print(f"  🚦 Testing download limits...")

            # Check current download count
            download_count = export_service.get_user_download_count_today(
                self.test_user_id
            )
            print(f"     - Current downloads today: {download_count}")

            # Check if user can download
            can_download, reset_time, downloads_today, daily_limit = (
                export_service.check_download_limit(
                    self.test_user_id,
                    UserRole.ADMIN,  # Use ADMIN role to match test user
                )
            )
            print(f"     - Can download: {can_download}")
            if reset_time:
                print(f"     - Limit resets at: {reset_time}")

            return True

        except Exception as e:
            print(f"  ❌ Download limit test failed: {e}")
            return False

    def cleanup_test_batches(self, batch_ids: List[str]):
        """Clean up test export batches."""
        if not batch_ids:
            return

        print(f"\n🧹 Cleaning up {len(batch_ids)} test batches...")

        for batch_id in batch_ids:
            try:
                # Get batch info for cleanup
                result = self.db.execute(
                    text(
                        "SELECT archive_path, storage_type FROM export_batches WHERE batch_id = :batch_id"
                    ),
                    {"batch_id": batch_id},
                ).first()

                if result:
                    # Delete local file if exists
                    if (
                        result.storage_type == "local"
                        and result.archive_path
                        and os.path.exists(result.archive_path)
                    ):
                        os.remove(result.archive_path)
                        print(f"  🗑️  Deleted archive file: {result.archive_path}")

                # Delete batch record
                self.db.execute(
                    text("DELETE FROM export_batches WHERE batch_id = :batch_id"),
                    {"batch_id": batch_id},
                )
                print(f"  🗑️  Deleted batch record: {batch_id}")

            except Exception as e:
                print(f"  ⚠️  Failed to cleanup batch {batch_id}: {e}")

        self.db.commit()

    def run_workflow_test(self):
        """Run the complete export workflow test."""
        print("=" * 60)
        print("EXPORT WORKFLOW TESTING")
        print("=" * 60)

        # Get initial statistics
        print("\n📊 Initial export statistics:")
        initial_stats = self.get_export_statistics()
        for key, value in initial_stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

        if initial_stats["available_for_export"] == 0:
            print("\n❌ No chunks available for export!")
            print("   Run prepare_export_data.py first to prepare chunks for export.")
            return

        print(
            f"\n✅ Found {initial_stats['available_for_export']} chunks available for export"
        )

        # Test different batch sizes
        test_cases = [
            {
                "max_chunks": 10,
                "force_create": True,
                "description": "Small batch (10 chunks)",
            },
            {
                "max_chunks": 25,
                "force_create": True,
                "description": "Medium batch (25 chunks)",
            },
        ]

        # Only test larger batch if we have enough chunks
        if initial_stats["available_for_export"] >= 50:
            test_cases.append(
                {
                    "max_chunks": 50,
                    "force_create": True,
                    "description": "Large batch (50 chunks)",
                }
            )

        created_batches = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'=' * 40}")
            print(f"TEST CASE {i}: {test_case['description']}")
            print(f"{'=' * 40}")

            # Create batch
            batch_id = self.create_test_export_batch(
                max_chunks=test_case["max_chunks"],
                force_create=test_case["force_create"],
            )

            if batch_id:
                created_batches.append(batch_id)

                # Verify contents
                print(f"\n🔍 Verifying batch contents...")
                self.verify_export_batch_contents(batch_id)

                # Test download
                print(f"\n📥 Testing download...")
                self.test_export_batch_download(batch_id)

                # Test download limits
                print(f"\n🚦 Testing download limits...")
                self.test_download_limits(batch_id)

            else:
                print(f"  ❌ Skipping further tests for failed batch")

            print(f"\n✅ Test case {i} completed")

        # Final statistics
        print(f"\n📊 Final export statistics:")
        final_stats = self.get_export_statistics()
        for key, value in final_stats.items():
            change = value - initial_stats[key]
            change_str = (
                f" (+{change})" if change > 0 else f" ({change})" if change < 0 else ""
            )
            print(f"  {key.replace('_', ' ').title()}: {value}{change_str}")

        # Cleanup
        cleanup = (
            input(f"\nCleanup {len(created_batches)} test batches? [Y/n]: ")
            .strip()
            .lower()
        )
        if not cleanup or cleanup in ["y", "yes"]:
            self.cleanup_test_batches(created_batches)
        else:
            print("Test batches left for manual inspection:")
            for batch_id in created_batches:
                print(f"  - {batch_id}")

        print(f"\n{'=' * 60}")
        print("EXPORT WORKFLOW TESTING COMPLETE")
        print(f"{'=' * 60}")
        print(f"Test cases run: {len(test_cases)}")
        print(f"Batches created: {len(created_batches)}")
        print(
            f"Available chunks: {initial_stats['available_for_export']} → {final_stats['available_for_export']}"
        )
        print(f"{'=' * 60}")

    def close(self):
        """Clean up database connection."""
        self.db.close()


def main():
    tester = None
    try:
        tester = ExportWorkflowTester()
        tester.run_workflow_test()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
    finally:
        if tester:
            tester.close()


if __name__ == "__main__":
    main()
