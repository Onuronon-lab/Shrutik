#!/usr/bin/env python3
"""Fix chunk file paths from absolute to relative"""

import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:password@localhost:5432/voice_collection"
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def fix_paths():
    db = SessionLocal()

    # Update paths from /app/uploads/ to uploads/
    result = db.execute(
        text(
            """
        UPDATE audio_chunks
        SET file_path = REPLACE(file_path, '/app/uploads/', 'uploads/')
        WHERE file_path LIKE '/app/uploads/%'
    """
        )
    )

    print(f"Updated {result.rowcount} chunk paths")
    db.commit()
    db.close()


if __name__ == "__main__":
    fix_paths()
