#!/usr/bin/env python3
"""
Simple database initialization script - fallback for when Alembic fails.
This script just ensures tables exist and creates basic data.
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def simple_init():
    """Simple database initialization without Alembic."""
    print("🚀 Starting simple database initialization...")

    try:
        # Import all models first
        from app.db.database import Base, SessionLocal, engine
        from app.models.language import Language

        print("✅ Models imported successfully")

        # Create all tables
        print("🔄 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created")

        # Create default language
        print("🔄 Creating default Bengali language...")
        db = SessionLocal()
        try:
            # Check if Bengali language exists
            bengali = db.query(Language).filter(Language.code == "bn").first()
            if not bengali:
                bengali = Language(code="bn", name="Bengali")
                db.add(bengali)
                db.commit()
                print("✅ Default Bengali language created")
            else:
                print("✅ Bengali language already exists")
        finally:
            db.close()

        print("🎉 Simple database initialization completed!")
        return True

    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = simple_init()
    sys.exit(0 if success else 1)
