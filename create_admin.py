#!/usr/bin/env python3
"""
Script to create an admin user for the Voice Data Collection Platform
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.init_db import create_admin_user
from app.core.security import get_password_hash

def main():
    email = input("Enter admin email: ")
    name = input("Enter admin name: ")
    password = input("Enter admin password: ")
    
    password_hash = get_password_hash(password)
    
    try:
        create_admin_user(email, name, password_hash)
        print(f"✅ Admin user '{email}' created successfully!")
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")

if __name__ == "__main__":
    main()