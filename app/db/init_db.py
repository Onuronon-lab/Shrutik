"""Database initialization utilities"""

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal, engine

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialize database with default data"""
    from app.models import Language

    try:
        db = SessionLocal()

        existing_languages = db.query(Language).first()
        if existing_languages:
            logger.info("Database already initialized")
            return

        bangla_language = Language(name="Bangla", code="bn")
        db.add(bangla_language)
        db.commit()
        db.refresh(bangla_language)

        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_admin_user(email: str, name: str, password_hash: str) -> None:
    """Create an admin user"""
    from app.models import User, UserRole

    try:
        db = SessionLocal()

        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            logger.info(f"User {email} already exists")
            return

        admin_user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            role=UserRole.ADMIN,
            meta_data={"created_by": "init_script"},
        )
        db.add(admin_user)
        db.commit()

        logger.info(f"Admin user {email} created successfully")

    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
