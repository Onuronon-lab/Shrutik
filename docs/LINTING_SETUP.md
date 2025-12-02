# Linting and Code Quality Setup

This guide helps you set up comprehensive linting and type checking for both Python and TypeScript in your editor (VS Code, Neovim, etc.).

## Python Linting Setup

### 1. Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

This installs:

- **black** - Code formatter
- **isort** - Import sorter
- **flake8** - Style checker
- **pylint** - Deep code analysis
- **mypy** - Static type checker

### 2. Neovim Setup (with LSP)

Add to your Neovim config (`~/.config/nvim/init.lua` or `init.vim`):

```lua
-- Python LSP with pyright
require('lspconfig').pyright.setup{
  settings = {
    python = {
      analysis = {
        typeCheckingMode = "basic",
        autoSearchPaths = true,
        useLibraryCodeForTypes = true,
        diagnosticMode = "workspace",
      }
    }
  }
}

-- Pylint integration (via null-ls or efm)
local null_ls = require("null-ls")
null_ls.setup({
  sources = {
    null_ls.builtins.diagnostics.pylint.with({
      extra_args = {"--rcfile=pylintrc"}
    }),
    null_ls.builtins.diagnostics.flake8,
    null_ls.builtins.formatting.black,
    null_ls.builtins.formatting.isort,
  },
})
```

### 3. VS Code Setup

Install extensions:

- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **Pylint** (ms-python.pylint)

Add to `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.linting.pylintArgs": ["--rcfile=pylintrc"],
  "python.analysis.typeCheckingMode": "basic",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## TypeScript/React Linting Setup

### 1. Install Frontend Dependencies

```bash
cd frontend
npm install --save-dev \
  eslint \
  @typescript-eslint/parser \
  @typescript-eslint/eslint-plugin \
  eslint-plugin-react \
  eslint-plugin-react-hooks \
  prettier \
  eslint-config-prettier
```

### 2. Neovim Setup (TypeScript LSP)

```lua
-- TypeScript LSP
require('lspconfig').tsserver.setup{
  on_attach = on_attach,
  capabilities = capabilities,
}

-- ESLint integration
null_ls.setup({
  sources = {
    null_ls.builtins.diagnostics.eslint,
    null_ls.builtins.formatting.prettier,
  },
})
```

### 3. VS Code Setup

Install extensions:

- **ESLint** (dbaeumer.vscode-eslint)
- **Prettier** (esbenp.prettier-vscode)

Frontend settings are already in `frontend/.vscode/settings.json`.

## Running Linters

### Automated (Recommended)

Run the comprehensive format script:

```bash
./scripts/format_code.sh
```

This runs:

1. Black (Python formatter)
2. isort (Import sorter)
3. flake8 (Style checker)
4. pylint (Deep analysis)
5. pyright (Type checker)
6. Prettier (TypeScript formatter)
7. ESLint (TypeScript linter)

### Manual Commands

#### Python

```bash
# Format code
black app/ tests/ scripts/
isort app/ tests/ scripts/

# Check style
flake8 app/ tests/ scripts/

# Deep analysis
pylint app/ --rcfile=pylintrc

# Type checking
pyright app/ tests/
# or
mypy app/
```

#### TypeScript

```bash
cd frontend

# Format code
npx prettier --write src/

# Lint
npx eslint src/ --ext .ts,.tsx

# Type check
npx tsc --noEmit
```

## Pre-commit Hooks

Pre-commit hooks automatically run linters before each commit.

### Setup

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

Configuration is in `.pre-commit-config.yaml`.

## Configuration Files

### Python

- **pylintrc** - Pylint configuration
- **pyrightconfig.json** - Pyright/Pylance configuration
- **.flake8** - Flake8 configuration
- **pyproject.toml** - Black and isort configuration

### TypeScript

- **frontend/tsconfig.json** - TypeScript configuration
- **frontend/.prettierrc** - Prettier configuration
- **frontend/package.json** - ESLint configuration (eslintConfig section)

## Common Issues

### "Module not found" in Neovim

Make sure your Python LSP knows about your virtual environment:

```lua
require('lspconfig').pyright.setup{
  settings = {
    python = {
      pythonPath = "./venv/bin/python"  -- or your venv path
    }
  }
}
```

### Pylint "Unable to import" errors

Pylint needs to know about your project structure:

```bash
# Add to your shell rc file
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Or run with
PYTHONPATH=. pylint app/
```

### Too many warnings

The configurations are already tuned to be reasonable. If you still get too many:

1. **Pylint**: Edit `pylintrc` and add warning codes to the `disable` list
2. **Flake8**: Edit `.flake8` and add to `extend-ignore`
3. **ESLint**: Edit `frontend/package.json` eslintConfig rules

## Ignoring Specific Lines

### Python

```python
# Disable pylint for one line
result = some_function()  # pylint: disable=some-warning

# Disable for a block
# pylint: disable=too-many-arguments
def complex_function(a, b, c, d, e, f):
    pass
# pylint: enable=too-many-arguments

# Disable flake8
import something  # noqa: F401

# Disable type checking
x = some_untyped_thing()  # type: ignore
```

### TypeScript

```typescript
// Disable ESLint for one line
const x = something(); // eslint-disable-line no-unused-vars

// Disable for next line
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const y: any = something();

// Disable type checking
// @ts-ignore
const z = untyped();
```

## CI/CD Integration

Linting runs automatically in CI/CD via pre-commit hooks. See `.github/workflows/` for configuration.

## Best Practices

1. **Run format script before committing**: `./scripts/format_code.sh`
2. **Fix errors, not just warnings**: Errors indicate real problems
3. **Don't disable too many rules**: They're there for a reason
4. **Use type hints**: They help catch bugs early
5. **Keep code clean**: Linters help maintain quality

## Getting Help

- **Pylint docs**: https://pylint.readthedocs.io/
- **Pyright docs**: https://github.com/microsoft/pyright
- **ESLint docs**: https://eslint.org/docs/
- **TypeScript docs**: https://www.typescriptlang.org/docs/

---

**Remember**: Linters are tools to help you, not to annoy you. If a rule doesn't make sense for your use case, it's okay to disable it with a comment explaining why! 🚀
