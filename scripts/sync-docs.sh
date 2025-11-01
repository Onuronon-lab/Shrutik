#!/bin/bash

# Sync documentation files
# This script copies root-level markdown files to docs/ directory for mdBook

echo "🔄 Syncing documentation files..."

# Copy CODE_OF_CONDUCT.md to docs/
if [ -f "CODE_OF_CONDUCT.md" ]; then
    cp CODE_OF_CONDUCT.md docs/
    echo "✅ Copied CODE_OF_CONDUCT.md to docs/"
else
    echo "❌ CODE_OF_CONDUCT.md not found in root"
fi

# Copy CONTRIBUTORS.md to docs/
if [ -f "CONTRIBUTORS.md" ]; then
    cp CONTRIBUTORS.md docs/
    echo "✅ Copied CONTRIBUTORS.md to docs/"
else
    echo "❌ CONTRIBUTORS.md not found in root"
fi

# Build documentation
echo "🏗️  Building documentation..."
mdbook build

if [ $? -eq 0 ]; then
    echo "✅ Documentation built successfully!"
    echo "📖 Open book/index.html to view the documentation"
else
    echo "❌ Documentation build failed"
    exit 1
fi

echo "🎉 Documentation sync complete!"