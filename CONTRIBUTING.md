# Contributing to Shrutik

Thank you for your interest in contributing to Shrutik! This guide will help you get started.

## 🚀 Quick Start

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/Shrutik.git
cd Shrutik
```

### 2. Set Up Development Environment

**Backend:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install black isort flake8  # Formatting tools
```

**Frontend:**

```bash
cd frontend
npm install
cd ..
```

### 3. Set Up Pre-commit Hooks (Recommended)

Choose one of these options:

**Option A: Pre-commit Framework (Recommended)**

```bash
./scripts/setup_pre_commit.sh
```

**Option B: Simple Git Hook**

```bash
./scripts/install_git_hook.sh
```

This ensures your code is automatically formatted before each commit!

## 📝 Code Style

We use automated formatters to maintain consistent code style:

- **Python**: Black (88 char lines) + isort + flake8
- **TypeScript/React**: Prettier + ESLint

### Manual Formatting

Before submitting a PR, run:

```bash
./scripts/format_code.sh
```

This formats the entire codebase.

## 🔄 Development Workflow

1. **Create a branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code
   - Add tests if applicable
   - Ensure code is formatted (automatic with pre-commit hooks)

3. **Test your changes**

   ```bash
   # Backend tests
   pytest

   # Frontend tests
   cd frontend
   npm test
   ```

4. **Format code** (if not using pre-commit hooks)

   ```bash
   ./scripts/format_code.sh
   ```

5. **Commit your changes**

   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Use conventional commit messages:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting)
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance tasks

6. **Push and create PR**

   ```bash
   git push origin feature/your-feature-name
   ```

   Then create a Pull Request on GitHub.

## 🧪 Testing

### Backend Tests

```bash
pytest
pytest tests/test_specific.py  # Run specific test file
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 📋 Pull Request Guidelines

- Fill out the PR template completely
- Ensure all tests pass
- Code must be formatted (run `./scripts/format_code.sh`)
- Add tests for new features
- Update documentation if needed
- Keep PRs focused on a single feature/fix

## 🔧 Useful Commands

### Formatting

```bash
./scripts/format_code.sh              # Format entire codebase
pre-commit run --all-files            # Run all pre-commit hooks
git commit --no-verify                # Skip pre-commit hooks (not recommended)
```

### Pre-commit

```bash
pre-commit run                        # Run on staged files
pre-commit run --all-files            # Run on all files
pre-commit autoupdate                 # Update hook versions
```

### Backend

```bash
black app/ tests/                     # Format Python code
isort app/ tests/                     # Sort imports
flake8 app/ tests/                    # Check style
```

### Frontend

```bash
cd frontend
npm run format                        # Format with Prettier
npm run lint                          # Check with ESLint
npm run lint:fix                      # Fix ESLint issues
```

## 🐛 Reporting Issues

When reporting issues, please include:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, Node version)
- Screenshots if applicable

## 💡 Getting Help

- Check existing issues and PRs
- Read the documentation
- Ask questions in discussions
- Join our community channels

## 📜 Code of Conduct

Please be respectful and constructive in all interactions. We're building an inclusive community.

## 🎉 Thank You!

Your contributions make Shrutik better for everyone. We appreciate your time and effort!
