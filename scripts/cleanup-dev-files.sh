#!/bin/bash

# Cleanup Development Files Script
# Removes test files, development dependencies, and cache files for production deployment

set -e

echo "🧹 Starting cleanup of development files..."

# Remove Python test files and cache
echo "Removing Python test files and cache..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf .pytest_cache/
rm -rf tests/
rm -rf .coverage
rm -rf htmlcov/

# Remove test database files
echo "Removing test database files..."
find . -name "test*.db" -delete

# Remove Node.js development files
echo "Removing Node.js development files..."
rm -rf frontend/node_modules/.cache/
rm -rf frontend/.vite/
rm -rf frontend/coverage/
rm -rf frontend/dist/

# Remove development configuration files
echo "Removing development configuration files..."
rm -f .env.example
rm -f frontend/.env.example

# Remove development scripts and tools
echo "Removing development scripts..."
rm -rf frontend/scripts/
rm -f frontend/.vitecache.config.js
rm -f frontend/sourcemap.config.js
rm -f frontend/test-optimizations.js

# Remove version control files (optional - uncomment if needed)
# echo "Removing version control files..."
# rm -rf .git/
# rm -f .gitignore

# Remove documentation files (optional - uncomment if needed)
# echo "Removing documentation files..."
# rm -f README.md
# rm -f LICENSE

# Remove logs directory contents but keep the directory
echo "Cleaning logs directory..."
if [ -d "logs" ]; then
    rm -rf logs/*
fi

# Create production requirements file (already done, but ensure it exists)
if [ ! -f "requirements-prod.txt" ]; then
    echo "Creating production requirements file..."
    grep -v -E "(pytest|httpx)" requirements.txt > requirements-prod.txt
fi

echo "✅ Development files cleanup completed!"
echo ""
echo "Files removed:"
echo "  - Python cache files (__pycache__, *.pyc)"
echo "  - Test files and directories"
echo "  - Node.js cache and build artifacts"
echo "  - Development configuration files"
echo "  - Development scripts and tools"
echo ""
echo "Production deployment is now ready!"