# Shrutik Branch Workflow

## Branch Structure

```
deployment-dev  →  master  →  dev-stage  →  deployment-prod
(unstable dev)  (stable+docs) (prod testing)  (clean production)
```

## Branch Purposes

### `deployment-dev`
- **Unstable development branch**
- Where all PRs get merged
- Active development with frequent changes
- May have breaking changes or incomplete features
- Includes tests, docs, and development tools

### `master`
- **Stable version with documentation**
- More stable than deployment-dev
- Default branch for the repository
- Contains proper README and documentation
- Anyone can understand Shrutik from this branch
- Includes tests and development tools
- Source for dev-stage testing

### `dev-stage`
- **Production testing environment**
- Tests Shrutik in production-like environment
- Gets stable updates from master
- Used to verify features before production release
- Includes tests for validation
- Keeps its own README describing staging purpose

### `deployment-prod`
- **Clean production deployment**
- Only necessary files for production
- No tests, docs, or development tools
- Optimized and minimal
- What actually runs on production servers

## Sync Workflows

### 1. deployment-dev → master (Stable Release)
**Script**: `scripts/sync-deployment-dev-to-master.sh` (your existing script)

**Purpose**: Promote stable features from development to master

**Excludes**: Nothing (syncs everything including docs and README)

**When to use**: When deployment-dev is stable and you want to update master

```bash
# Run from any branch
./scripts/sync-deployment-dev-to-master.sh
```

### 2. master → dev-stage (Production Testing)
**Script**: `scripts/sync-dev-stage-from-master.sh` (this new script)

**Purpose**: Bring stable updates from master into dev-stage for production testing

**Excludes**: 
- README.md (dev-stage keeps its own staging README)
- Test files and directories (dev-stage has its own tests)
- Development configs (dev-stage has its own)
- .kiro/ specs directory

**When to use**: After master is updated, sync to dev-stage for production testing

```bash
# Make sure you're on dev-stage branch
git checkout dev-stage

# Run the sync script
./scripts/sync-dev-stage-from-master.sh
```

### 3. dev-stage → deployment-prod (Production Deployment)
**Script**: Not yet created (would exclude tests, docs, dev tools)

**Purpose**: Deploy clean production code after testing in dev-stage

**Excludes**: 
- All test files and directories
- All documentation
- README.md
- Development configs
- .kiro/ specs
- Any non-essential files

**When to use**: After testing in dev-stage is successful

## Typical Workflow

1. **Develop features** in `deployment-dev`
   ```bash
   git checkout deployment-dev
   # Make changes, merge PRs, commit, push
   # This branch is unstable but active
   ```

2. **Stabilize in master** (deployment-dev → master)
   ```bash
   ./scripts/sync-deployment-dev-to-master.sh
   # Review and sync stable features
   # This updates master with stable code + docs
   # Master is the public face of Shrutik
   ```

3. **Test in production environment** (master → dev-stage)
   ```bash
   git checkout dev-stage
   ./scripts/sync-dev-stage-from-master.sh
   # Review and sync production updates
   # dev-stage now has latest stable code for testing
   # Test in production-like environment
   ```

4. **Verify in dev-stage**
   ```bash
   # Run tests, verify features work in production environment
   # dev-stage simulates production but has test tools
   # Catch any production-specific issues
   ```

5. **Deploy to production** (dev-stage → deployment-prod)
   ```bash
   # Sync clean code to deployment-prod (script TBD)
   # Deploy deployment-prod branch to production EC2
   # Only essential files, no tests or docs
   ```

## File Exclusions

### What gets excluded when syncing master → dev-stage?

- `README.md` - dev-stage has its own staging-specific README
- `.kiro/` - Spec files stay in dev-stage
- Test files: `test*.db`, `__tests__/`, `*.test.*`, `*.spec.*`
- Python cache: `__pycache__/`, `*.pyc`
- Dev configs: `.flake8`, `pylintrc`, `pyrightconfig.json`, etc.
- Frontend test configs: `vitest.config.*`, test scripts, etc.

### Why exclude these?

- **dev-stage** needs its own tests to validate production updates
- **master** includes docs and tests for developers
- Syncing master → dev-stage brings stable code without overwriting staging-specific files
- Each branch maintains its purpose

## Branch Comparison

| Branch | Purpose | Stability | Tests | Docs | README | Deployed |
|--------|---------|-----------|-------|------|--------|----------|
| `deployment-dev` | Active development | Unstable | ✅ | ✅ | Dev-focused | No |
| `master` | Stable + Documentation | Stable | ✅ | ✅ | Comprehensive | No |
| `dev-stage` | Production testing | Stable | ✅ | ❌ | Staging-focused | Staging server |
| `deployment-prod` | Production | Stable | ❌ | ❌ | Minimal/None | Production EC2 |

## Quick Reference

| Action | Script | Direction | Purpose | Excludes |
|--------|--------|-----------|---------|----------|
| Stable Release | `sync-deployment-dev-to-master.sh` | deployment-dev → master | Update stable branch | Nothing |
| Production Testing | `sync-dev-stage-from-master.sh` | master → dev-stage | Test in prod environment | Tests, configs, README |
| Production Deploy | TBD | dev-stage → deployment-prod | Clean production code | Tests, docs, configs |

## Notes

- **deployment-dev**: Unstable, all PRs merge here
- **master**: Stable, has docs, default branch, public-facing
- **dev-stage**: Production testing environment, validates before prod
- **deployment-prod**: Clean production code only, what runs on EC2
- All sync scripts are interactive with diff previews
- Always run from repository root
- For dev-stage sync, be on dev-stage branch first
