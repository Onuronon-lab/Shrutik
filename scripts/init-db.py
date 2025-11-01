#!/usr/bin/env python3
"""
Database initialization script for Shrutik Voice Data Collection Platform.
This script ensures all database tables are created and migrations are applied.
"""

import sys
import os
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from app.db.database import engine, SessionLocal
from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Check if database connection is working."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def check_tables_exist():
    """Check if required tables exist."""
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = [
            'users', 'languages', 'scripts', 'voice_recordings', 
            'audio_chunks', 'transcriptions', 'quality_reviews', 
            'export_audit_logs'
        ]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            logger.warning(f"⚠️  Missing tables: {missing_tables}")
            return False
        else:
            logger.info("✅ All required tables exist")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error checking tables: {e}")
        return False

def create_tables():
    """Create all database tables."""
    try:
        # Import all models to ensure they're registered
        import app.models
        from app.db.database import Base
        
        logger.info("🔄 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False

def run_alembic_migrations():
    """Run Alembic migrations."""
    try:
        import subprocess
        logger.info("🔄 Running Alembic migrations...")
        
        # Run alembic upgrade head
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        if result.returncode == 0:
            logger.info("✅ Alembic migrations completed successfully")
            return True
        else:
            logger.error(f"❌ Alembic migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error running Alembic migrations: {e}")
        return False

def create_default_language():
    """Create default Bengali language if it doesn't exist."""
    try:
        from app.models.language import Language
        
        db = SessionLocal()
        try:
            # Check if Bengali language exists
            bengali = db.query(Language).filter(Language.code == "bn").first()
            if not bengali:
                logger.info("🔄 Creating default Bengali language...")
                bengali = Language(
                    code="bn",
                    name="Bengali",
                    native_name="বাংলা",
                    is_active=True
                )
                db.add(bengali)
                db.commit()
                logger.info("✅ Default Bengali language created")
            else:
                logger.info("✅ Bengali language already exists")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error creating default language: {e}")
        return False

def main():
    """Main initialization function."""
    logger.info("🚀 Starting database initialization...")
    logger.info(f"📊 Database URL: {settings.DATABASE_URL}")
    
    # Step 1: Check database connection
    if not check_database_connection():
        logger.error("💥 Database initialization failed - no connection")
        sys.exit(1)
    
    # Step 2: Create tables if they don't exist
    if not check_tables_exist():
        logger.info("🔧 Tables missing, creating them...")
        if not create_tables():
            logger.error("💥 Database initialization failed - could not create tables")
            sys.exit(1)
    
    # Step 3: Run Alembic migrations
    if not run_alembic_migrations():
        logger.warning("⚠️  Alembic migrations failed, but continuing...")
    
    # Step 4: Create default data
    if not create_default_language():
        logger.warning("⚠️  Could not create default language, but continuing...")
    
    # Step 5: Final verification
    if check_tables_exist():
        logger.info("🎉 Database initialization completed successfully!")
        return True
    else:
        logger.error("💥 Database initialization failed - tables still missing")
        sys.exit(1)

if __name__ == "__main__":
    main()