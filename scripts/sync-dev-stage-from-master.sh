#!/bin/bash
# Sync master to dev-stage script (sync-dev-stage-from-master.sh)
# This script syncs changes from master to dev-stage (production testing updates)
# Excludes test files, development configs, README, and unnecessary directories
# Flow: deployment-dev → master → dev-stage → deployment-prod

set -e
set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Shrutik: Sync master → dev-stage (Production Updates)    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Files and directories to exclude from sync
EXCLUDE_PATTERNS=(
    "^README\.md$"
    "^\.kiro/"
    "^\.pytest_cache/"
    "^__pycache__/"
    "test.*\.db$"
    "test.*\.db-.*$"
    "\.pyc$"
    "\.pyo$"
    "^\.flake8$"
    "^\.pre-commit-config\.yaml$"
    "^pylintrc$"
    "^pyrightconfig\.json$"
    "^frontend/.*__tests__/"
    "^frontend/.*\.test\."
    "^frontend/.*\.spec\."
    "^frontend/vitest\.config\."
    "^frontend/test-optimizations\.js$"
    "^frontend/\.vitecache\.config\.js$"
    "^frontend/sourcemap\.config\.js$"
    "^frontend/dev-performance-metrics\.json$"
    "^frontend/scripts/"
    "^frontend/src/setupTests\."
    "^frontend/src/App\.test\."
)

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

# Check if dev-stage and master branches exist
if ! git show-ref --verify --quiet refs/heads/dev-stage; then
    echo -e "${RED}Error: dev-stage branch does not exist${NC}"
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

echo -e "${BLUE}→ Switching to master...${NC}"
git checkout master

echo -e "${BLUE}→ Pulling latest master...${NC}"
git pull origin master

echo -e "${BLUE}→ Switching to dev-stage...${NC}"
git checkout dev-stage

echo -e "${BLUE}→ Pulling latest dev-stage...${NC}"
git pull origin dev-stage

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Analyzing changes between master and dev-stage${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Function to check if file should be excluded
should_exclude() {
    local file="$1"
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        if echo "$file" | grep -qE "$pattern"; then
            return 0  # Should exclude
        fi
    done
    return 1  # Should not exclude
}

# Get list of files that exist in both branches (excluding excluded patterns)
ALL_COMMON_FILES=$(comm -12 \
    <(git ls-tree -r --name-only dev-stage | sort) \
    <(git ls-tree -r --name-only master | sort))

# Filter out excluded files
COMMON_FILES=""
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    if ! should_exclude "$file"; then
        if [ -z "$COMMON_FILES" ]; then
            COMMON_FILES="$file"
        else
            COMMON_FILES="$COMMON_FILES"$'\n'"$file"
        fi
    fi
done <<< "$ALL_COMMON_FILES"

# Get list of files that only exist in master (new files, excluding excluded patterns)
ALL_NEW_FILES=$(comm -13 \
    <(git ls-tree -r --name-only dev-stage | sort) \
    <(git ls-tree -r --name-only master | sort))

# Filter out excluded files
NEW_FILES=""
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    if ! should_exclude "$file"; then
        if [ -z "$NEW_FILES" ]; then
            NEW_FILES="$file"
        else
            NEW_FILES="$NEW_FILES"$'\n'"$file"
        fi
    fi
done <<< "$ALL_NEW_FILES"

# Get list of files that were modified
MODIFIED_FILES=""
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    if ! git diff --quiet dev-stage master -- "$file" 2>/dev/null; then
        if [ -z "$MODIFIED_FILES" ]; then
            MODIFIED_FILES="$file"
        else
            MODIFIED_FILES="$MODIFIED_FILES"$'\n'"$file"
        fi
    fi
done <<< "$COMMON_FILES"

MODIFIED_COUNT=$(echo "$MODIFIED_FILES" | grep -c . || echo "0")
NEW_COUNT=$(echo "$NEW_FILES" | grep -c . || echo "0")

echo -e "${GREEN}✓ Found $MODIFIED_COUNT modified files in master (production updates)${NC}"
echo -e "${YELLOW}✓ Found $NEW_COUNT new files in master (production updates)${NC}"
echo ""

if [ "$MODIFIED_COUNT" -eq 0 ] && [ "$NEW_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ No changes to sync. dev-stage is up to date!${NC}"
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

# Handle modified files interactively
if [ "$MODIFIED_COUNT" -gt 0 ]; then
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Modified files in master (production updates)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    SYNCED_COUNT=0
    SKIPPED_COUNT=0
    
    # Temporarily disable exit on error for interactive section
    set +e
    
    # Convert to array to avoid subshell issues
    mapfile -t MODIFIED_ARRAY <<< "$MODIFIED_FILES"
    
    # Debug: show array size
    echo -e "${BLUE}Processing ${#MODIFIED_ARRAY[@]} files...${NC}"
    echo ""
    
    for file in "${MODIFIED_ARRAY[@]}"; do
        # Skip empty lines
        [[ -z "$file" ]] && continue
        
        echo -e "${YELLOW}Modified: $file${NC}"
        
        # Show diff summary
        DIFF_STATS=$(git diff --stat dev-stage master -- "$file" 2>/dev/null)
        if [ -n "$DIFF_STATS" ]; then
            echo -e "${BLUE}$DIFF_STATS${NC}"
        fi
        
        read -p "$(echo -e ${GREEN}Sync this file from master? \(y/n/d=show diff\) ${NC})" -n 1 -r </dev/tty
        echo
        
        if [[ $REPLY =~ ^[Dd]$ ]]; then
            git diff dev-stage master -- "$file" 2>/dev/null | head -50
            echo ""
            read -p "$(echo -e ${GREEN}Sync this file from master? \(y/n\) ${NC})" -n 1 -r </dev/tty
            echo
        fi
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git checkout master -- "$file" 2>/dev/null
            echo -e "${GREEN}✓ Synced from master${NC}"
            ((SYNCED_COUNT++))
        else
            echo -e "${YELLOW}⊘ Skipped${NC}"
            ((SKIPPED_COUNT++))
        fi
        echo ""
    done
    
    # Re-enable exit on error
    set -e
    
    echo -e "${GREEN}✓ Synced $SYNCED_COUNT files, skipped $SKIPPED_COUNT files${NC}"
    echo ""
fi

# Handle new files interactively (file by file)
if [ "$NEW_COUNT" -gt 0 ]; then
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  New files in master (production updates)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    ADDED_COUNT=0
    SKIPPED_COUNT=0
    
    # Temporarily disable exit on error for interactive section
    set +e
    
    # Convert to array to avoid subshell issues
    mapfile -t NEW_ARRAY <<< "$NEW_FILES"
    
    for file in "${NEW_ARRAY[@]}"; do
        # Skip empty lines
        [[ -z "$file" ]] && continue
        
        echo -e "${YELLOW}New file: $file${NC}"
        
        # Show file info
        FILE_SIZE=$(git cat-file -s master:"$file" 2>/dev/null)
        if [ -n "$FILE_SIZE" ]; then
            echo -e "${BLUE}Size: $FILE_SIZE bytes${NC}"
        fi
        
        # Show first few lines if it's a text file
        if git cat-file -p master:"$file" 2>/dev/null | head -5 | grep -q '^'; then
            echo -e "${BLUE}Preview:${NC}"
            git cat-file -p master:"$file" 2>/dev/null | head -5
        fi
        
        read -p "$(echo -e ${GREEN}Add this file from master? \(y/n/v=view full\) ${NC})" -n 1 -r </dev/tty
        echo
        
        if [[ $REPLY =~ ^[Vv]$ ]]; then
            git cat-file -p master:"$file" 2>/dev/null | less
            read -p "$(echo -e ${GREEN}Add this file from master? \(y/n\) ${NC})" -n 1 -r </dev/tty
            echo
        fi
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git checkout master -- "$file" 2>/dev/null
            echo -e "${GREEN}✓ Added from master${NC}"
            ((ADDED_COUNT++))
        else
            echo -e "${YELLOW}⊘ Skipped${NC}"
            ((SKIPPED_COUNT++))
        fi
        echo ""
    done
    
    # Re-enable exit on error
    set -e
    
    echo -e "${GREEN}✓ Added $ADDED_COUNT files, skipped $SKIPPED_COUNT files${NC}"
    echo ""
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
    COMMIT_MSG="sync: merge production updates from master to dev-stage

- Synced modified files from master
- Excluded test files, development configs, and README
- Production updates from deployment-dev → master → dev-stage
- Date: $(date +%Y-%m-%d)"
fi

# Commit changes
git add -A
git commit -m "$COMMIT_MSG"

echo ""
echo -e "${GREEN}✓ Changes committed successfully${NC}"
echo ""

# Ask about pushing
read -p "$(echo -e ${GREEN}Push to origin/dev-stage? \(y/n\) ${NC})" -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}→ Pushing to origin/dev-stage...${NC}"
    git push origin dev-stage
    echo -e "${GREEN}✓ Pushed to origin/dev-stage${NC}"
else
    echo -e "${YELLOW}⊘ Not pushed. Run 'git push origin dev-stage' when ready.${NC}"
fi

# Return to original branch
if [ "$CURRENT_BRANCH" != "dev-stage" ]; then
    echo ""
    echo -e "${BLUE}→ Returning to $CURRENT_BRANCH...${NC}"
    git checkout "$CURRENT_BRANCH"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Production sync complete!                               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
