#!/bin/bash

# Fix Export Persistence Issue
# This script fixes the common issue where export batches disappear after container restart

set -e

echo "🔧 Fixing export persistence issue..."
echo "=================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p exports
mkdir -p uploads
mkdir -p logs

echo "✅ Directories created successfully"

# Check if docker-compose.yml has the correct volume mappings
echo "🔍 Checking docker-compose.yml volume mappings..."

if grep -q "./exports:/app/exports" docker-compose.yml; then
    echo "✅ Export volume mapping found"
else
    echo "❌ Export volume mapping missing in docker-compose.yml"
    echo "   Please add './exports:/app/exports' to your backend, celery, and celery-beat services"
    exit 1
fi

if grep -q "./uploads:/app/uploads" docker-compose.yml; then
    echo "✅ Upload volume mapping found"
else
    echo "❌ Upload volume mapping missing in docker-compose.yml"
    echo "   Please add './uploads:/app/uploads' to your backend, celery, and celery-beat services"
    exit 1
fi

# Run the volume checker
echo "🔍 Running comprehensive volume check..."
python scripts/check_docker_volumes.py

echo ""
echo "🎉 Fix completed successfully!"
echo ""
echo "Next steps:"
echo "1. Stop containers: docker compose down"
echo "2. Restart containers: docker compose up -d --build"
echo "3. Your export batches should now persist between restarts"
echo ""
echo "💡 The issue was that export files were stored inside the container"
echo "   instead of being mounted as volumes. This has been fixed."
