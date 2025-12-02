#!/bin/bash

# Sync deployment-dev to master script
# This script syncs changes from deployment-dev to master for existing files
# and prompts for new files/folders

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Shrutik: Sync deployment-dev → master                    ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

# Check if deployment-dev and master branches exist
if ! git show-ref --verify --quiet refs/heads/deployment-dev; then
    echo -e "${RED}Error: deployment-dev branch does not exist${NC}"
    exit 1
fi

if ! git show-ref --verify --quiet refs/heads/master; then
    echo -e "${RED}Error: master branch does not exist${NC}"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}Warning: You have uncommitted changes${NC}"
    read -p "Do you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Store current branch
CURRENT_BRANCH=$(git branch --show-current)

echo -e "${BLUE}→ Fetching latest changes...${NC}"
git fetch origin

echo -e "${BLUE}→ Switching to deployment-dev...${NC}"
git checkout deployment-dev

echo -e "${BLUE}→ Pulling latest deployment-dev...${NC}"
git pull origin deployment-dev

echo -e "${BLUE}→ Switching to master...${NC}"
git checkout master

echo -e "${BLUE}→ Pulling latest master...${NC}"
git pull origin master

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Analyzing changes between deployment-dev and master${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Get list of files that exist in both branches (excluding README.md)
COMMON_FILES=$(comm -12 \
    <(git ls-tree -r --name-only master | sort) \
    <(git ls-tree -r --name-only deployment-dev | sort) \
    | grep -v "^README.md$")

# Get list of files that only exist in deployment-dev (new files)
NEW_FILES=$(comm -13 \
    <(git ls-tree -r --name-only master | sort) \
    <(git ls-tree -r --name-only deployment-dev | sort))

# Get list of files that were modified
MODIFIED_FILES=$(echo "$COMMON_FILES" | while read file; do
    if ! git diff --quiet master deployment-dev -- "$file" 2>/dev/null; then
        echo "$file"
    fi
done)

MODIFIED_COUNT=$(echo "$MODIFIED_FILES" | grep -c . || echo "0")
NEW_COUNT=$(echo "$NEW_FILES" | grep -c . || echo "0")

echo -e "${GREEN}✓ Found $MODIFIED_COUNT modified files${NC}"
echo -e "${YELLOW}✓ Found $NEW_COUNT new files${NC}"
echo ""

if [ "$MODIFIED_COUNT" -eq 0 ] && [ "$NEW_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ No changes to sync. Master is up to date!${NC}"
    git checkout "$CURRENT_BRANCH"
    exit 0
fi

# Show modified files
if [ "$MODIFIED_COUNT" -gt 0 ]; then
    echo -e "${BLUE}Modified files to sync:${NC}"
    echo "$MODIFIED_FILES" | head -20
    if [ "$MODIFIED_COUNT" -gt 20 ]; then
        echo -e "${YELLOW}... and $((MODIFIED_COUNT - 20)) more${NC}"
    fi
    echo ""
fi

# Prompt for confirmation to sync modified files
if [ "$MODIFIED_COUNT" -gt 0 ]; then
    read -p "$(echo -e ${GREEN}Sync all modified files to master? \(y/n\) ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}→ Syncing modified files...${NC}"
        echo "$MODIFIED_FILES" | while read file; do
            git checkout deployment-dev -- "$file" 2>/dev/null || true
        done
        echo -e "${GREEN}✓ Modified files synced${NC}"
    else
        echo -e "${YELLOW}⊘ Skipped modified files${NC}"
    fi
    echo ""
fi

# Handle new files interactively
if [ "$NEW_COUNT" -gt 0 ]; then
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  New files in deployment-dev${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    # Group files by directory
    declare -A DIR_FILES
    while IFS= read -r file; do
        dir=$(dirname "$file")
        if [ -z "${DIR_FILES[$dir]}" ]; then
            DIR_FILES[$dir]="$file"
        else
            DIR_FILES[$dir]="${DIR_FILES[$dir]}"$'\n'"$file"
        fi
    done <<< "$NEW_FILES"

    # Ask about each directory
    for dir in "${!DIR_FILES[@]}"; do
        files="${DIR_FILES[$dir]}"
        file_count=$(echo "$files" | wc -l)

        echo -e "${YELLOW}Directory: $dir/ ($file_count files)${NC}"
        echo "$files" | head -5
        if [ "$file_count" -gt 5 ]; then
            echo -e "${YELLOW}... and $((file_count - 5)) more${NC}"
        fi
        echo ""

        read -p "$(echo -e ${GREEN}Add these files to master? \(y/n/s=show all\) ${NC})" -n 1 -r
        echo

        if [[ $REPLY =~ ^[Ss]$ ]]; then
            echo "$files"
            echo ""
            read -p "$(echo -e ${GREEN}Add these files to master? \(y/n\) ${NC})" -n 1 -r
            echo
        fi

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "$files" | while read file; do
                git checkout deployment-dev -- "$file" 2>/dev/null || true
            done
            echo -e "${GREEN}✓ Added files from $dir/${NC}"
        else
            echo -e "${YELLOW}⊘ Skipped files from $dir/${NC}"
        fi
        echo ""
    done
fi

# Check if there are any changes staged
if git diff --cached --quiet; then
    echo -e "${YELLOW}No changes were staged. Nothing to commit.${NC}"
    git checkout "$CURRENT_BRANCH"
    exit 0
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Review and commit${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Show summary of changes
echo -e "${BLUE}Changes to be committed:${NC}"
git diff --cached --stat
echo ""

read -p "$(echo -e ${GREEN}Commit these changes? \(y/n\) ${NC})" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⊘ Aborting. Resetting changes...${NC}"
    git reset --hard
    git checkout "$CURRENT_BRANCH"
    exit 1
fi

# Get commit message
echo ""
echo -e "${BLUE}Enter commit message (or press Enter for default):${NC}"
read -r COMMIT_MSG

if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="sync: merge changes from deployment-dev to master

- Synced modified files from deployment-dev
- Updated for production release
- Date: $(date +%Y-%m-%d)"
fi

# Commit changes
git add -A
git commit -m "$COMMIT_MSG"

echo ""
echo -e "${GREEN}✓ Changes committed successfully${NC}"
echo ""

# Ask about pushing
read -p "$(echo -e ${GREEN}Push to origin/master? \(y/n\) ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}→ Pushing to origin/master...${NC}"
    git push origin master
    echo -e "${GREEN}✓ Pushed to origin/master${NC}"
else
    echo -e "${YELLOW}⊘ Not pushed. Run 'git push origin master' when ready.${NC}"
fi

# Return to original branch
if [ "$CURRENT_BRANCH" != "master" ]; then
    echo ""
    echo -e "${BLUE}→ Returning to $CURRENT_BRANCH...${NC}"
    git checkout "$CURRENT_BRANCH"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Sync complete!                                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
