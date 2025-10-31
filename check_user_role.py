#!/usr/bin/env python3
"""
Script to check user roles in the database.
"""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.config import settings

def check_user_role(email: str):
    """Check the role of a specific user."""
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            print(f"User found:")
            print(f"  ID: {user.id}")
            print(f"  Name: {user.name}")
            print(f"  Email: {user.email}")
            print(f"  Role: {user.role.value}")
            print(f"  Created: {user.created_at}")
            
            # Check if user has export permission
            from app.core.security import PermissionChecker
            has_export = PermissionChecker.has_permission(user.role, "export_data")
            print(f"  Has export permission: {has_export}")
            
        else:
            print(f"User with email '{email}' not found.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_user_role.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    check_user_role(email)