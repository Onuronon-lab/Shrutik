# Code Formatting Quick Reference

## 🚀 Quick Commands

### Setup (One-Time)

```bash
# Install tools
pip install black isort flake8

# Install pre-commit hooks (recommended)
./scripts/setup_pre_commit.sh

# OR install simple git hook
./scripts/install_git_hook.sh
```

### Daily Use

```bash
# With pre-commit hooks: just commit!
git add .
git commit -m "your message"  # Auto-formats!

# Without hooks: format manually
./scripts/format_code.sh
git add .
git commit -m "your message"
```

### Before PR

```bash
# Format everything
./scripts/format_code.sh

# Review changes
git diff

# Commit and push
git add .
git commit -m "style: format code"
git push
```

## 📋 Command Reference

| Task                   | Command                           |
| ---------------------- | --------------------------------- |
| **Format everything**  | `./scripts/format_code.sh`        |
| **Setup pre-commit**   | `./scripts/setup_pre_commit.sh`   |
| **Format Python**      | `black app/ tests/ scripts/`      |
| **Sort imports**       | `isort app/ tests/ scripts/`      |
| **Check Python style** | `flake8 app/ tests/ scripts/`     |
| **Format frontend**    | `cd frontend && npm run format`   |
| **Fix ESLint**         | `cd frontend && npm run lint:fix` |
| **Run pre-commit**     | `pre-commit run --all-files`      |
| **Update hooks**       | `pre-commit autoupdate`           |
| **Skip hooks**         | `git commit --no-verify`          |

## 🛠️ Tools & Configs

| Tool           | Config File               | Purpose                        |
| -------------- | ------------------------- | ------------------------------ |
| **Black**      | `pyproject.toml`          | Python formatter (88 chars)    |
| **isort**      | `pyproject.toml`          | Import sorter                  |
| **flake8**     | `pyproject.toml`          | Style checker                  |
| **Prettier**   | `.prettierrc`             | Frontend formatter (100 chars) |
| **ESLint**     | `frontend/package.json`   | Linter                         |
| **Pre-commit** | `.pre-commit-config.yaml` | Hook manager                   |

## 📁 What Gets Formatted

| Files             | Tools                | Location                     |
| ----------------- | -------------------- | ---------------------------- |
| `*.py`            | Black, isort, flake8 | `app/`, `tests/`, `scripts/` |
| `*.ts`, `*.tsx`   | Prettier, ESLint     | `frontend/src/`              |
| `*.js`, `*.jsx`   | Prettier, ESLint     | `frontend/src/`              |
| `*.json`          | Prettier             | `frontend/src/`              |
| `*.css`, `*.scss` | Prettier             | `frontend/src/`              |

## 🎯 Style Rules

### Python

- **Line length:** 88 characters
- **Quotes:** Double quotes
- **Indentation:** 4 spaces
- **Import order:** stdlib → third-party → local

### TypeScript/React

- **Line length:** 100 characters
- **Quotes:** Single (JS/TS), Double (JSX)
- **Indentation:** 2 spaces
- **Semicolons:** Required
- **Trailing commas:** ES5

## 🔧 Troubleshooting

| Problem                | Solution                                         |
| ---------------------- | ------------------------------------------------ |
| **Tools not found**    | `pip install black isort flake8`                 |
| **Prettier not found** | `cd frontend && npm install --save-dev prettier` |
| **Hooks not running**  | `pre-commit install`                             |
| **CI failing**         | Run `./scripts/format_code.sh` and commit        |
| **Want to skip hooks** | `git commit --no-verify` (use sparingly!)        |

## 📚 Documentation

| Document                       | Purpose              |
| ------------------------------ | -------------------- |
| `CONTRIBUTING.md`              | How to contribute    |
| `docs/FORMATTING.md`           | Detailed guide       |
| `docs/FORMATTING_WORKFLOW.md`  | Visual workflows     |
| `docs/SETUP_SUMMARY.md`        | Quick setup          |
| `docs/FORMATTING_CHECKLIST.md` | Maintainer checklist |

## 💡 Pro Tips

1. ✅ **Set up pre-commit hooks** - saves time
2. ✅ **Run format before PR** - catch everything
3. ✅ **Don't fight the formatter** - it's opinionated
4. ✅ **Update hooks monthly** - `pre-commit autoupdate`
5. ✅ **Configure your IDE** - match the rules

## 🚦 CI/CD

**Workflow:** `.github/workflows/formatting.yml`

**Runs on:**

- Pull requests
- Pushes to main/develop/deployment-dev

**Checks:**

- ✅ Python formatting (black, isort)
- ✅ Python style (flake8)
- ✅ Frontend formatting (prettier)
- ✅ Frontend linting (ESLint)

## 🎓 Learning Resources

- [Black](https://black.readthedocs.io/) - Python formatter
- [isort](https://pycqa.github.io/isort/) - Import sorter
- [Prettier](https://prettier.io/) - Frontend formatter
- [Pre-commit](https://pre-commit.com/) - Hook framework

## 📞 Need Help?

1. Check `docs/FORMATTING.md`
2. Run `./scripts/format_code.sh`
3. Reinstall hooks: `./scripts/setup_pre_commit.sh`
4. Open an issue with error details

---

**Remember:** Consistent formatting = fewer conflicts = faster reviews = happier team! 🎉
