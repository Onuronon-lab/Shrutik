# Code Formatting Section for Main README

Add this section to your main `README.md` file:

---

## 🎨 Code Formatting

Shrutik uses automated code formatters to maintain consistent code style and eliminate formatting-related merge conflicts.

### Quick Setup

```bash
# Install formatting tools
pip install black isort flake8
cd frontend && npm install && cd ..

# Set up pre-commit hooks (recommended)
./scripts/setup_pre_commit.sh
```

### Before Submitting a PR

```bash
# Format entire codebase
./scripts/format_code.sh

# Or let pre-commit hooks handle it automatically
git commit -m "your changes"  # Auto-formatted!
```

### Tools Used

- **Backend**: Black, isort, flake8
- **Frontend**: Prettier, ESLint

For detailed information, see [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/FORMATTING.md](docs/FORMATTING.md).

---

**Alternative shorter version:**

---

## 🎨 Code Formatting

We use automated formatters (Black, isort, Prettier) to maintain consistent code style.

**Setup:**

```bash
pip install black isort flake8
./scripts/setup_pre_commit.sh  # Auto-format on commit
```

**Before PR:**

```bash
./scripts/format_code.sh  # Format entire codebase
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---
