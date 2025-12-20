#!/usr/bin/env python3
"""Debug enum issue"""

import os
import sys
from pathlib import Path

# Add app directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.export_batch import ExportBatch, ExportBatchStatus

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:password@localhost:5432/voice_collection"
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def test_enum():
    db = SessionLocal()

    print("Testing ExportBatchStatus enum...")
    print(f"COMPLETED value: {ExportBatchStatus.COMPLETED}")
    print(f"COMPLETED value type: {type(ExportBatchStatus.COMPLETED)}")
    print(f"COMPLETED string value: '{ExportBatchStatus.COMPLETED.value}'")

    # Test query
    try:
        print("\nTesting query with enum...")
        result = (
            db.query(ExportBatch.chunk_ids)
            .filter(ExportBatch.status == ExportBatchStatus.COMPLETED)
            .all()
        )
        print(f"Query successful, found {len(result)} batches")
    except Exception as e:
        print(f"Query failed: {e}")

    # Test with string value
    try:
        print("\nTesting query with string value...")
        result = (
            db.query(ExportBatch.chunk_ids)
            .filter(ExportBatch.status == "completed")
            .all()
        )
        print(f"String query successful, found {len(result)} batches")
    except Exception as e:
        print(f"String query failed: {e}")

    db.close()


if __name__ == "__main__":
    test_enum()
