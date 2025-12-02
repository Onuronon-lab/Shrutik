#!/bin/bash

# Pre-commit Hook Setup Script
# This script sets up automatic code formatting before each commit

set -e

echo "🪝 Setting up pre-commit hooks for Shrutik..."
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

# Check if we're in the project root
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: Please run this script from the project root directory${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Installing pre-commit framework...${NC}"

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
else
    echo -e "${GREEN}✓ pre-commit already installed${NC}"
fi

echo ""
echo -e "${BLUE}🔧 Installing pre-commit hooks...${NC}"

# Install the git hook scripts
pre-commit install

echo ""
echo -e "${BLUE}📥 Installing hook dependencies (this may take a minute)...${NC}"

# Install all hook environments
pre-commit install-hooks

echo ""
echo -e "${GREEN}✅ Pre-commit hooks installed successfully!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 What happens now:"
echo "   • Every commit will automatically format your code"
echo "   • Python: black + isort + flake8"
echo "   • Frontend: prettier"
echo "   • General: trailing whitespace, file endings, etc."
echo ""
echo "🔧 Useful commands:"
echo "   • Run on all files:     pre-commit run --all-files"
echo "   • Run on staged files:  pre-commit run"
echo "   • Skip for one commit:  git commit --no-verify"
echo "   • Update hooks:         pre-commit autoupdate"
echo ""
echo "💡 Pro tip: Run 'pre-commit run --all-files' now to format existing code!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
