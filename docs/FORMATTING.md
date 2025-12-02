# Code Formatting Guide

This document explains the code formatting setup for Shrutik and how to use it.

## 🎯 Overview

Shrutik uses automated code formatters to maintain consistent code style across the entire codebase. This eliminates formatting-related merge conflicts and makes code reviews focus on logic rather than style.

## 🛠️ Tools Used

### Backend (Python)

- **Black**: Opinionated code formatter (88 character line length)
- **isort**: Import statement organizer (black-compatible profile)
- **flake8**: Style checker (non-blocking warnings)

### Frontend (TypeScript/React)

- **Prettier**: Code formatter for TS/JS/JSON/CSS
- **ESLint**: Linter with auto-fix capabilities

## 📦 Installation

### Quick Setup (Recommended)

```bash
# Install Python formatters
pip install black isort flake8

# Install frontend formatters
cd frontend
npm install --save-dev prettier
cd ..

# Set up pre-commit hooks
./scripts/setup_pre_commit.sh
```

### Manual Setup

If you prefer not to use pre-commit hooks:

```bash
# Just install the formatters
pip install black isort flake8
cd frontend && npm install --save-dev prettier && cd ..
```

## 🚀 Usage

### Automatic Formatting (Recommended)

Once you've run `./scripts/setup_pre_commit.sh`, your code will be automatically formatted every time you commit:

```bash
git add .
git commit -m "feat: add new feature"
# ✨ Code is automatically formatted before commit!
```

### Manual Formatting

Format the entire codebase before submitting a PR:

```bash
./scripts/format_code.sh
```

Format specific parts:

```bash
# Backend only
black app/ tests/ scripts/
isort app/ tests/ scripts/

# Frontend only
cd frontend
npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css}"
npm run lint:fix
```

### Pre-commit Commands

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Update hook versions
pre-commit autoupdate

# Skip hooks for one commit (not recommended)
git commit --no-verify
```

## ⚙️ Configuration Files

### `.prettierrc`

Frontend formatting rules:

- 100 character line width
- Single quotes for JS/TS
- Double quotes for JSX
- 2 space indentation
- Semicolons required
- Trailing commas (ES5)

### `pyproject.toml`

Backend formatting rules:

- 88 character line length (Black default)
- Python 3.9+ target
- Black-compatible isort profile
- Excludes: venv, migrations, build dirs

### `.pre-commit-config.yaml`

Pre-commit hook configuration:

- Black v24.10.0
- isort v5.13.2
- flake8 v7.1.1
- Prettier v4.0.0-alpha.8
- General file checks (trailing whitespace, etc.)

## 🔄 Workflow Integration

### For Contributors

1. **First time setup:**

   ```bash
   ./scripts/setup_pre_commit.sh
   ```

2. **Daily development:**

   ```bash
   # Just code and commit normally
   git add .
   git commit -m "your message"
   # Formatting happens automatically!
   ```

3. **Before creating PR:**

   ```bash
   # Optional: format everything to be sure
   ./scripts/format_code.sh

   # Review changes
   git diff

   # Commit and push
   git add .
   git commit -m "style: format code"
   git push
   ```

### For Maintainers

Run formatting on the entire codebase periodically:

```bash
./scripts/format_code.sh
git add .
git commit -m "style: format codebase"
git push
```

## 🎨 Style Guidelines

### Python

```python
# ✅ Good (Black formatted)
def calculate_total(items: list[dict], tax_rate: float = 0.1) -> float:
    """Calculate total with tax."""
    subtotal = sum(item["price"] for item in items)
    return subtotal * (1 + tax_rate)


# ❌ Bad (will be auto-fixed)
def calculate_total(items: list[dict],tax_rate: float=0.1)->float:
    subtotal=sum(item['price'] for item in items)
    return subtotal*(1+tax_rate)
```

### TypeScript/React

```typescript
// ✅ Good (Prettier formatted)
const UserCard = ({ name, email }: UserCardProps) => {
  return (
    <div className="user-card">
      <h2>{name}</h2>
      <p>{email}</p>
    </div>
  );
};

// ❌ Bad (will be auto-fixed)
const UserCard = ({name,email}:UserCardProps)=>{
  return <div className="user-card"><h2>{name}</h2><p>{email}</p></div>
}
```

## 🐛 Troubleshooting

### Pre-commit hooks not running

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Test manually
pre-commit run --all-files
```

### Formatting tools not found

```bash
# Python tools
pip install black isort flake8

# Frontend tools
cd frontend
npm install --save-dev prettier
```

### Conflicts with IDE formatting

Disable your IDE's auto-formatter or configure it to use the same settings:

- **VSCode**: Install "Black Formatter" and "Prettier" extensions
- **PyCharm**: Configure Black as external tool
- **WebStorm**: Enable Prettier integration

### Skip hooks temporarily

```bash
# Skip for one commit (use sparingly!)
git commit --no-verify -m "emergency fix"
```

## 📊 Benefits

✅ **Consistent Style**: Everyone uses the same formatting rules  
✅ **No Merge Conflicts**: Formatting differences eliminated  
✅ **Faster Reviews**: Focus on logic, not style  
✅ **Automatic**: Set it up once, forget about it  
✅ **Fast**: Only formats changed files during commits

## 🔗 Resources

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [Prettier Documentation](https://prettier.io/)
- [Pre-commit Documentation](https://pre-commit.com/)

## 💡 Tips

1. **Run formatting before creating PR** to catch everything
2. **Don't fight the formatter** - it's opinionated by design
3. **Use `--no-verify` sparingly** - only for emergencies
4. **Update hooks regularly** with `pre-commit autoupdate`
5. **Configure your IDE** to match the formatting rules

## 🆘 Need Help?

If you encounter issues with formatting:

1. Check this documentation
2. Run `./scripts/format_code.sh` manually
3. Ask in the project discussions
4. Open an issue with details
