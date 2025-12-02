# Sync deployment-dev to master Guide

This guide explains how to sync changes from `deployment-dev` to `master` for production releases.

## Quick Start

```bash
./scripts/sync-to-master.sh
```

## What It Does

The script automates the weekly sync process from `deployment-dev` (development branch) to `master` (production branch):

1. **Fetches latest changes** from both branches
2. **Analyzes differences** between deployment-dev and master
3. **Syncs modified files** automatically (with confirmation)
4. **Prompts for new files** - you choose what to add
5. **Commits and pushes** changes to master

## Features

### ✅ Automatic Sync

- Syncs all modified files that exist in both branches
- Excludes `README.md` automatically (branch-specific)
- Shows you exactly what will change

### 🎯 Interactive New Files

- Groups new files by directory
- Shows file count per directory
- Lets you preview files before adding
- You decide what goes to production

### 🛡️ Safety Checks

- Warns about uncommitted changes
- Shows diff summary before committing
- Confirms before pushing to remote
- Returns to your original branch when done

## Usage Example

```bash
$ ./scripts/sync-to-master.sh

╔════════════════════════════════════════════════════════════╗
║  Shrutik: Sync deployment-dev → master                    ║
╚════════════════════════════════════════════════════════════╝

→ Fetching latest changes...
→ Switching to deployment-dev...
→ Pulling latest deployment-dev...
→ Switching to master...
→ Pulling latest master...

═══════════════════════════════════════════════════════════
  Analyzing changes between deployment-dev and master
═══════════════════════════════════════════════════════════

✓ Found 15 modified files
✓ Found 3 new files

Modified files to sync:
app/api/admin.py
app/services/export_service.py
frontend/src/components/Dashboard.tsx
...

Sync all modified files to master? (y/n) y
→ Syncing modified files...
✓ Modified files synced

═══════════════════════════════════════════════════════════
  New files in deployment-dev
═══════════════════════════════════════════════════════════

Directory: app/api/v2/ (2 files)
app/api/v2/__init__.py
app/api/v2/endpoints.py

Add these files to master? (y/n/s=show all) y
✓ Added files from app/api/v2/

═══════════════════════════════════════════════════════════
  Review and commit
═══════════════════════════════════════════════════════════

Changes to be committed:
 app/api/admin.py                    | 45 +++++++++++++++++++++++++++++
 app/api/v2/__init__.py              | 12 ++++++++
 app/api/v2/endpoints.py             | 89 +++++++++++++++++++++++++++++++++++++++++++++++++++++
 app/services/export_service.py      | 23 +++++++-------
 frontend/src/components/Dashboard.tsx | 67 +++++++++++++++++++++++++++++++++++++++
 5 files changed, 225 insertions(+), 11 deletions(-)

Commit these changes? (y/n) y

Enter commit message (or press Enter for default):
[Using default message]

✓ Changes committed successfully

Push to origin/master? (y/n) y
→ Pushing to origin/master...
✓ Pushed to origin/master

╔════════════════════════════════════════════════════════════╗
║  ✓ Sync complete!                                          ║
╚════════════════════════════════════════════════════════════╝
```

## Workflow

### Weekly Production Release

1. **Merge all PRs to deployment-dev** throughout the week
2. **Test thoroughly** on deployment-dev
3. **Run the sync script** when ready for production:
   ```bash
   ./scripts/sync-to-master.sh
   ```
4. **Review changes** and confirm
5. **Push to master** for production deployment

### Handling New Files

When the script finds new files, you'll see:

```
Directory: docs/new-feature/ (5 files)
docs/new-feature/README.md
docs/new-feature/guide.md
docs/new-feature/api.md
... and 2 more

Add these files to master? (y/n/s=show all)
```

Options:

- **y** - Add all files from this directory
- **n** - Skip all files from this directory
- **s** - Show all files first, then decide

## Tips

### Before Running

- Ensure all PRs are merged to `deployment-dev`
- Test the deployment-dev branch thoroughly
- Check CI/CD passes on deployment-dev

### During Sync

- Review the modified files list carefully
- Be selective with new files (avoid adding experimental code)
- Use meaningful commit messages
- Always review the diff before committing

### After Sync

- Monitor production deployment
- Check that all features work as expected
- Keep deployment-dev and master in sync

## Troubleshooting

### "You have uncommitted changes"

Commit or stash your changes before running the script:

```bash
git stash
./scripts/sync-to-master.sh
git stash pop
```

### "No changes to sync"

Both branches are already in sync. Nothing to do!

### Script fails mid-way

The script is safe - it won't leave you in a broken state. If it fails:

```bash
git status  # Check current state
git reset --hard  # Reset if needed
git checkout your-branch  # Return to your branch
```

## Advanced Usage

### Dry Run (Manual)

To see what would change without actually syncing:

```bash
# See modified files
comm -12 \
  <(git ls-tree -r --name-only master | sort) \
  <(git ls-tree -r --name-only deployment-dev | sort) \
  | xargs -I {} sh -c 'git diff --quiet master deployment-dev -- {} || echo {}'

# See new files
comm -13 \
  <(git ls-tree -r --name-only master | sort) \
  <(git ls-tree -r --name-only deployment-dev | sort)
```

### Custom Excludes

Edit the script to exclude additional files:

```bash
# Line 82 - add more exclusions
COMMON_FILES=$(comm -12 \
    <(git ls-tree -r --name-only master | sort) \
    <(git ls-tree -r --name-only deployment-dev | sort) \
    | grep -v "^README.md$" \
    | grep -v "^docs/development/" \
    | grep -v "^.env.local$")
```

## Best Practices

1. **Run weekly** or before major releases
2. **Test deployment-dev first** - never sync untested code
3. **Review diffs carefully** - understand what's changing
4. **Use descriptive commit messages** - help future you
5. **Keep README.md separate** - each branch has its own
6. **Be selective with new files** - only production-ready code

## Support

If you encounter issues:

1. Check this guide first
2. Review the script output carefully
3. Check git status: `git status`
4. Ask the team in #dev-ops channel

---

**Remember**: `deployment-dev` is for development, `master` is for production. This script helps you promote stable changes safely! 🚀
