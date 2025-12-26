#!/usr/bin/env python3
"""
Docker Volume Checker for Shrutik

This script checks if all necessary directories are properly mounted as volumes
in Docker to prevent data loss when containers are restarted.
"""

import os
import sys


def check_directory_exists(path: str, description: str) -> bool:
    """Check if a directory exists and create it if it doesn't."""
    if os.path.exists(path):
        print(f"✅ {description}: {path} exists")
        return True
    else:
        print(f"❌ {description}: {path} does not exist")
        try:
            os.makedirs(path, exist_ok=True)
            print(f"✅ Created directory: {path}")
            return True
        except Exception as e:
            print(f"❌ Failed to create directory {path}: {e}")
            return False


def check_docker_compose_volumes():
    """Check if docker-compose.yml has the necessary volume mappings."""
    docker_compose_path = "docker-compose.yml"

    if not os.path.exists(docker_compose_path):
        print(f"❌ {docker_compose_path} not found")
        return False

    with open(docker_compose_path, "r") as f:
        content = f.read()

    required_volumes = ["./uploads:/app/uploads", "./exports:/app/exports"]

    missing_volumes = []
    for volume in required_volumes:
        if volume not in content:
            missing_volumes.append(volume)

    if missing_volumes:
        print("❌ Missing volume mappings in docker-compose.yml:")
        for volume in missing_volumes:
            print(f"   - {volume}")
        print(
            "\nTo fix this, add the missing volume mappings to your backend, celery, and celery-beat services."
        )
        return False
    else:
        print("✅ All required volume mappings found in docker-compose.yml")
        return True


def main():
    """Main function to run all checks."""
    print("🔍 Checking Docker volume configuration for Shrutik...")
    print("=" * 60)

    all_good = True

    # Check if required directories exist
    directories = [
        ("uploads", "Upload directory"),
        ("exports", "Export directory"),
        ("logs", "Logs directory"),
    ]

    for dir_path, description in directories:
        if not check_directory_exists(dir_path, description):
            all_good = False

    print()

    # Check docker-compose.yml volume mappings
    if not check_docker_compose_volumes():
        all_good = False

    print()
    print("=" * 60)

    if all_good:
        print("🎉 All checks passed! Your Docker setup should preserve data correctly.")
        print("\n💡 Remember:")
        print("   - Export batches will persist between container restarts")
        print("   - Upload files will persist between container restarts")
        print(
            "   - Database data is stored in Docker volumes (postgres_data, redis_data)"
        )
    else:
        print(
            "⚠️  Some issues were found. Please fix them before running Docker containers."
        )
        print("\n🔧 Common fixes:")
        print("   1. Ensure all directories exist on the host system")
        print("   2. Add missing volume mappings to docker-compose.yml")
        print(
            "   3. Run 'docker compose down && docker compose up -d --build' after fixes"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
