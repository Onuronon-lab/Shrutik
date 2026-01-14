# Master to Dev-Stage Sync - Excluded Files

This document lists all files and directories that are automatically excluded when syncing from `master` to `dev-stage` for production testing.

**Flow**: `deployment-dev` → `master` → `dev-stage` → `deployment-prod`

**Purpose**: Bring stable updates from master into dev-stage for production testing, without overwriting dev-stage's own test infrastructure and staging-specific files.

## Excluded Patterns

### README Files
- `README.md` - Each branch has its own README
  - master: Comprehensive documentation for developers
  - dev-stage: Staging environment description

### Kiro Specs Directory
- `.kiro/` - Spec files stay in dev-stage for development work

### Development Configuration Files
- `.flake8` - Python linting configuration
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `pylintrc` - Pylint configuration
- `pyrightconfig.json` - Pyright type checker configuration

### Test Files and Directories
- `.pytest_cache/` - Pytest cache directory
- `__pycache__/` - Python bytecode cache directories
- `test*.db` - Test database files
- `test*.db-*` - Test database journal/WAL files
- `*.pyc` - Python compiled bytecode files
- `*.pyo` - Python optimized bytecode files

### Frontend Test Files
- `frontend/**/__tests__/` - All test directories
- `frontend/**/*.test.*` - Test files (e.g., `.test.ts`, `.test.tsx`)
- `frontend/**/*.spec.*` - Spec files (e.g., `.spec.ts`, `.spec.tsx`)
- `frontend/vitest.config.*` - Vitest configuration
- `frontend/test-optimizations.js` - Test optimization scripts
- `frontend/src/setupTests.*` - Test setup files
- `frontend/src/App.test.*` - App test files

### Frontend Development Files
- `frontend/scripts/` - Development scripts directory
- `frontend/.vitecache.config.js` - Vite cache configuration
- `frontend/sourcemap.config.js` - Sourcemap configuration
- `frontend/dev-performance-metrics.json` - Development performance metrics

## Why These Files Are Excluded

### Branch Purpose Separation
- **master**: Stable code with comprehensive docs for developers
- **dev-stage**: Production testing environment with its own test infrastructure
- Syncing master → dev-stage brings stable code without removing staging-specific tools

### Testing Infrastructure
- dev-stage needs its own tests to validate production updates
- Test files in dev-stage may be different from master
- Each branch maintains its own testing strategy

### Documentation Separation
- master has comprehensive README for developers and users
- dev-stage has staging-specific README describing test environment
- Each branch serves different audiences

### Clean Workflow
- `deployment-dev`: Unstable, all PRs merge here
- `master`: Stable with docs, default branch
- `dev-stage`: Production testing with stable code from master
- `deployment-prod`: Clean production (no tests/docs)

## Usage

Run the sync script from the repository root (while on dev-stage branch):

```bash
# Make sure you're on dev-stage branch
git checkout dev-stage

# Run the sync script
./scripts/sync-dev-stage-from-master.sh
```

The script will:
1. Fetch latest changes from both branches
2. Switch to master, pull latest stable code
3. Switch to dev-stage, pull latest
4. Identify modified and new files in master (excluding patterns above)
5. Interactively prompt you to sync each file from master
6. Commit and optionally push changes to dev-stage

## Result

After syncing:
- ✅ dev-stage has latest stable code from master
- ✅ dev-stage keeps its own tests and configs
- ✅ dev-stage keeps its staging-specific README
- ✅ Ready to test in production-like environment
- ✅ Can validate before deploying to deployment-prod

## Adding New Exclusions

To exclude additional files, edit the `EXCLUDE_PATTERNS` array in `sync-dev-stage-from-master.sh`:

```bash
EXCLUDE_PATTERNS=(
    "^README\.md$"
    "^\.kiro/"
    "^your-new-pattern$"
    # ... other patterns
)
```

Patterns use grep extended regex syntax.
