#!/usr/bin/env python3
"""
Admin User Creation Script

This script creates an admin user for the Shrutik application.
It can be run interactively or with command line arguments.
"""

import sys
import getpass
import argparse
from app.db.init_db import create_admin_user
from app.core.security import get_password_hash
from app.core.config import settings


def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> bool:
    """Basic password validation"""
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long")
        return False
    
    if not any(c.isupper() for c in password):
        print("❌ Password must contain at least one uppercase letter")
        return False
    
    if not any(c.islower() for c in password):
        print("❌ Password must contain at least one lowercase letter")
        return False
    
    if not any(c.isdigit() for c in password):
        print("❌ Password must contain at least one digit")
        return False
    
    return True


def get_user_input():
    """Get user input interactively"""
    print("🔧 Shrutik Admin User Creation")
    print("=" * 40)
    
    # Get name
    while True:
        name = input("👤 Enter admin name: ").strip()
        if name:
            break
        print("❌ Name cannot be empty")
    
    # Get email
    while True:
        email = input("📧 Enter admin email: ").strip().lower()
        if validate_email(email):
            break
        print("❌ Please enter a valid email address")
    
    # Get password
    while True:
        password = getpass.getpass("🔒 Enter admin password: ")
        if validate_password(password):
            break
        print("Please try again with a stronger password")
    
    # Confirm password
    while True:
        confirm_password = getpass.getpass("🔒 Confirm admin password: ")
        if password == confirm_password:
            break
        print("❌ Passwords do not match")
    
    return name, email, password


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Create admin user for Shrutik")
    parser.add_argument("--name", help="Admin name")
    parser.add_argument("--email", help="Admin email")
    parser.add_argument("--password", help="Admin password")
    parser.add_argument("--non-interactive", action="store_true", 
                       help="Run in non-interactive mode (requires all arguments)")
    
    args = parser.parse_args()
    
    try:
        if args.non_interactive:
            if not all([args.name, args.email, args.password]):
                print("❌ Non-interactive mode requires --name, --email, and --password")
                sys.exit(1)
            
            name, email, password = args.name, args.email, args.password
            
            if not validate_email(email):
                print("❌ Invalid email address")
                sys.exit(1)
            
            if not validate_password(password):
                print("❌ Password does not meet requirements")
                sys.exit(1)
        else:
            name, email, password = get_user_input()
        
        # Hash the password
        password_hash = get_password_hash(password)
        
        # Create the admin user
        print("\n🔄 Creating admin user...")
        create_admin_user(email, name, password_hash)
        
        print("✅ Admin user created successfully!")
        print(f"📧 Email: {email}")
        print(f"👤 Name: {name}")
        print(f"🔑 Role: Admin")
        print("\n🚀 You can now log in to the admin dashboard!")
        
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()