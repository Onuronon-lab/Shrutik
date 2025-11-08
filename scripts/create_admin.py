#!/usr/bin/env python3
"""
Script to create an admin user directly in the database.
Use this for initial setup or emergency admin creation.

Requires direct database access.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from getpass import getpass

# Add project root to Python path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from app.core.security import get_password_hash
from app.db.database import SessionLocal
from app.models.user import User, UserRole


def create_admin_user(name: str, email: str, password: str, role: UserRole = UserRole.ADMIN) -> bool:
    """Create an admin user directly in the database."""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ User with email '{email}' already exists (id={existing_user.id}, role={existing_user.role.value})")
            return False
        
        # Create the user
        password_hash = get_password_hash(password)
        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ User created successfully!")
        print(f"   ID: {user.id}")
        print(f"   Name: {user.name}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role.value}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    # Safety check: Require explicit confirmation in production
    if os.getenv("ENVIRONMENT") == "production":
        confirm = input("⚠️  WARNING: Running in PRODUCTION environment. Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return 1
    
    parser = argparse.ArgumentParser(
        description="Create an admin user for the Shrutik application.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (prompts for password)
  python scripts/create_admin.py --name "Admin User" --email admin@example.com
  
  # With password (not recommended for production)
  python scripts/create_admin.py --name "Admin" --email admin@example.com --password secret123
  
  # Create a SWORIK_DEVELOPER user
  python scripts/create_admin.py --name "Developer" --email dev@example.com --role sworik_developer
        """
    )
    
    parser.add_argument("--name", required=True, help="Full name of the user")
    parser.add_argument("--email", required=True, help="Email address (used for login)")
    parser.add_argument("--password", help="Password (if not provided, will prompt securely)")
    parser.add_argument(
        "--role",
        choices=["admin", "sworik_developer", "contributor"],
        default="admin",
        help="User role (default: admin)"
    )
    
    args = parser.parse_args()
    
    # Get password securely if not provided
    if args.password:
        password = args.password
        print("⚠️  Warning: Passing password via command line is insecure!")
    else:
        password = getpass("Enter password: ")
        password_confirm = getpass("Confirm password: ")
        
        if password != password_confirm:
            print("❌ Passwords do not match!")
            return 1
    
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long!")
        return 1
    
    # Map string role to enum
    role_map = {
        "admin": UserRole.ADMIN,
        "sworik_developer": UserRole.SWORIK_DEVELOPER,
        "contributor": UserRole.CONTRIBUTOR
    }
    role = role_map[args.role]
    
    print(f"\nCreating user:")
    print(f"  Name: {args.name}")
    print(f"  Email: {args.email}")
    print(f"  Role: {args.role}")
    print()
    
    success = create_admin_user(args.name, args.email, password, role)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
