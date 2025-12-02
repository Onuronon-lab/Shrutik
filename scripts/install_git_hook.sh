#!/bin/bash

# Simple Git Hook Installer (Alternative to pre-commit framework)
# This creates a basic pre-commit hook without external dependencies

set -e

echo "🪝 Installing simple git pre-commit hook..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'HOOK_EOF'
#!/bin/bash
# Pre-commit hook for automatic code formatting
# This runs before each commit to ensure consistent code style

echo "🔧 Running pre-commit formatting..."

# Check if there are any staged files
if git diff --cached --quiet; then
    echo "ℹ️  No staged files to format"
    exit 0
fi

# Get list of staged Python files
STAGED_PYTHON_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py)$' || true)

# Get list of staged TypeScript/React files
STAGED_TS_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E 'frontend/.*\.(ts|tsx|js|jsx)$' || true)

# Format Python files if any
if [ -n "$STAGED_PYTHON_FILES" ]; then
    echo "🐍 Formatting Python files..."

    # Check if tools are installed
    if command -v black &> /dev/null && command -v isort &> /dev/null; then
        # Format the staged files
        echo "$STAGED_PYTHON_FILES" | xargs black --line-length 88 --quiet 2>/dev/null || true
        echo "$STAGED_PYTHON_FILES" | xargs isort --profile black --quiet 2>/dev/null || true

        # Re-stage the formatted files
        echo "$STAGED_PYTHON_FILES" | xargs git add
        echo "✓ Python files formatted"
    else
        echo "⚠️  black or isort not installed. Install with: pip install black isort"
    fi
fi

# Format TypeScript/React files if any
if [ -n "$STAGED_TS_FILES" ]; then
    echo "⚛️  Formatting TypeScript/React files..."

    if [ -d "frontend" ] && command -v npx &> /dev/null; then
        cd frontend

        # Check if prettier is available
        if npm list prettier &> /dev/null || [ -f "../.prettierrc" ]; then
            # Format the staged files
            echo "$STAGED_TS_FILES" | sed 's|frontend/||g' | xargs npx prettier --write --config ../.prettierrc --loglevel silent 2>/dev/null || true
            cd ..

            # Re-stage the formatted files
            echo "$STAGED_TS_FILES" | xargs git add
            echo "✓ Frontend files formatted"
        else
            cd ..
            echo "⚠️  prettier not installed. Install with: cd frontend && npm install --save-dev prettier"
        fi
    fi
fi

echo "✅ Pre-commit formatting complete!"
exit 0
HOOK_EOF

# Make the hook executable
chmod +x .git/hooks/pre-commit

echo -e "${GREEN}✅ Git pre-commit hook installed!${NC}"
echo ""
echo "📝 What happens now:"
echo "   • Every commit will automatically format staged files"
echo "   • Python files formatted with black + isort"
echo "   • TypeScript/React files formatted with prettier"
echo "   • Only staged files are formatted (fast!)"
echo ""
echo "🔧 Requirements:"
echo "   • Python: pip install black isort"
echo "   • Frontend: cd frontend && npm install --save-dev prettier"
echo ""
echo "💡 To disable for a specific commit: git commit --no-verify"
echo ""
echo "🚀 Alternative: Use pre-commit framework for more features:"
echo "   ./scripts/setup_pre_commit.sh"
