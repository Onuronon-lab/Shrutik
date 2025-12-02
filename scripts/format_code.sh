#!/bin/bash

# Code Formatting Script for Shrutik
# Run this before submitting a PR to ensure consistent code formatting

set -e

echo "🎨 Formatting Shrutik codebase..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track if any tools are missing
MISSING_TOOLS=0

# Check if we're in the project root
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Backend Python formatting
echo -e "${BLUE}🐍 Formatting Python backend...${NC}"

if command -v black &> /dev/null; then
    black app/ tests/ scripts/ --line-length 88 --target-version py39
    echo -e "${GREEN}✓ Python code formatted with black${NC}"
else
    echo -e "${YELLOW}⚠️  black not installed. Install with: pip install black${NC}"
    MISSING_TOOLS=1
fi

if command -v isort &> /dev/null; then
    isort app/ tests/ scripts/ --profile black
    echo -e "${GREEN}✓ Python imports sorted with isort${NC}"
else
    echo -e "${YELLOW}⚠️  isort not installed. Install with: pip install isort${NC}"
    MISSING_TOOLS=1
fi

# Optional: Run flake8 for style checking (non-blocking)
if command -v flake8 &> /dev/null; then
    echo -e "${BLUE}🔍 Checking code style with flake8...${NC}"
    flake8 app/ tests/ scripts/ --max-line-length=88 --extend-ignore=E203,W503 || {
        echo -e "${YELLOW}⚠️  flake8 found some style issues (not blocking)${NC}"
    }
else
    echo -e "${YELLOW}💡 Tip: Install flake8 for style checking: pip install flake8${NC}"
fi

# Optional: Run pylint for deeper analysis (non-blocking)
if command -v pylint &> /dev/null; then
    echo -e "${BLUE}🔍 Running pylint analysis...${NC}"
    pylint app/ --rcfile=pylintrc --exit-zero 2>/dev/null || {
        echo -e "${YELLOW}⚠️  pylint found some issues (not blocking)${NC}"
    }
else
    echo -e "${YELLOW}💡 Tip: Install pylint for deeper analysis: pip install pylint${NC}"
fi

# Optional: Run pyright for type checking (non-blocking)
if command -v pyright &> /dev/null; then
    echo -e "${BLUE}🔍 Running pyright type checking...${NC}"
    pyright app/ tests/ 2>/dev/null || {
        echo -e "${YELLOW}⚠️  pyright found some type issues (not blocking)${NC}"
    }
else
    echo -e "${YELLOW}💡 Tip: Install pyright for type checking: npm install -g pyright${NC}"
fi

echo ""

# Frontend TypeScript/React formatting
echo -e "${BLUE}⚛️  Formatting TypeScript/React frontend...${NC}"

if [ -d "frontend" ]; then
    cd frontend

    if [ -f "package.json" ]; then
        # Install prettier if not present
        if ! npm list prettier &> /dev/null; then
            echo -e "${BLUE}📦 Installing prettier...${NC}"
            npm install --save-dev prettier --silent
        fi

        # Format with prettier using config from root
        if command -v npx &> /dev/null; then
            npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css}" --config ../.prettierrc
            echo -e "${GREEN}✓ Frontend code formatted with prettier${NC}"
        else
            echo -e "${YELLOW}⚠️  npx not available${NC}"
            MISSING_TOOLS=1
        fi

        # Optional: Run eslint fix if available
        if npm list eslint &> /dev/null; then
            echo -e "${BLUE}🔍 Running ESLint auto-fix...${NC}"
            npx eslint --fix "src/**/*.{ts,tsx,js,jsx}" --quiet || {
                echo -e "${YELLOW}⚠️  ESLint found some issues (not blocking)${NC}"
            }
        fi
    fi

    cd ..
else
    echo -e "${YELLOW}⚠️  frontend directory not found${NC}"
fi

echo ""

# Summary
if [ $MISSING_TOOLS -eq 0 ]; then
    echo -e "${GREEN}✅ Code formatting complete!${NC}"
else
    echo -e "${YELLOW}⚠️  Some formatting tools are missing. Install them for complete formatting:${NC}"
    echo -e "${YELLOW}   pip install black isort flake8${NC}"
fi

echo ""
echo "📝 Next steps:"
echo "  1. Review the changes: git diff"
echo "  2. Stage the changes: git add ."
echo "  3. Commit: git commit -m 'style: format code'"
echo "  4. Push and create PR"
echo ""
echo "💡 Pro tip: Set up pre-commit hooks to auto-format on commit!"
echo "   See: https://pre-commit.com/"
