#!/usr/bin/env python3
"""
Script to list all users in the database.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.config import settings

def list_all_users():
    """List all users in the database."""
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        # Get all users
        users = db.query(User).all()
        
        if users:
            print(f"Found {len(users)} users:")
            print("-" * 80)
            for user in users:
                print(f"ID: {user.id}")
                print(f"Name: {user.name}")
                print(f"Email: {user.email}")
                print(f"Role: {user.role.value}")
                print(f"Created: {user.created_at}")
                print("-" * 80)
        else:
            print("No users found in the database.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_all_users()