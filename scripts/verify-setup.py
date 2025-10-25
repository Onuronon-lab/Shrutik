#!/usr/bin/env python3
"""
Verification script to check if the project setup is correct
"""

import sys
import os
import importlib.util

def check_file_exists(filepath):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✓ {filepath} exists")
        return True
    else:
        print(f"✗ {filepath} missing")
        return False

def check_directory_exists(dirpath):
    """Check if a directory exists"""
    if os.path.isdir(dirpath):
        print(f"✓ {dirpath}/ exists")
        return True
    else:
        print(f"✗ {dirpath}/ missing")
        return False

def check_python_import(module_name):
    """Check if a Python module can be imported"""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            print(f"✓ {module_name} can be imported")
            return True
        else:
            print(f"✗ {module_name} cannot be imported")
            return False
    except ImportError:
        print(f"✗ {module_name} import error")
        return False

def main():
    print("Voice Data Collection Platform - Setup Verification")
    print("=" * 50)
    
    all_good = True
    
    # Check core files
    core_files = [
        "app/main.py",
        "app/core/config.py",
        "app/core/celery_app.py",
        "app/db/database.py",
        "requirements.txt",
        "docker-compose.yml",
        "Dockerfile",
        "alembic.ini",
        ".env.example"
    ]
    
    print("\nChecking core files:")
    for file in core_files:
        if not check_file_exists(file):
            all_good = False
    
    # Check directories
    directories = [
        "app/api",
        "app/models",
        "app/schemas",
        "app/services",
        "app/tasks",
        "app/utils",
        "alembic",
        "scripts",
        "tests",
        "uploads"
    ]
    
    print("\nChecking directories:")
    for directory in directories:
        if not check_directory_exists(directory):
            all_good = False
    
    # Check if we can import the main app (requires dependencies)
    print("\nChecking Python imports:")
    try:
        from app.main import app
        print("✓ FastAPI app can be imported")
    except ImportError as e:
        print(f"✗ FastAPI app import failed: {e}")
        print("  Note: This is expected if dependencies are not installed")
        print("  Run: pip install -r requirements.txt")
    
    print("\n" + "=" * 50)
    if all_good:
        print("✓ Project structure setup is complete!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start services: docker-compose up -d postgres redis")
        print("3. Run migrations: alembic upgrade head")
        print("4. Start app: uvicorn app.main:app --reload")
    else:
        print("✗ Some issues found in project setup")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())