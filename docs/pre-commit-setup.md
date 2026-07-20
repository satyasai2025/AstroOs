# Pre-commit Hooks Setup

> Automate code quality checks before every commit.

## Overview

AstroOS uses [pre-commit](https://pre-commit.com/) to run linting, formatting,
and security checks on every `git commit`. The configuration lives in
`.pre-commit-config.yaml` at the repo root.

### What runs on every commit

| Hook | Scope | What it does |
|------|-------|--------------|
| **ruff-lint** | Python | Lints code, auto-fixes where safe |
| **ruff-format** | Python | Formats code (black-compatible) |
| **eslint** | TypeScript (apps/web) | Lints frontend code |
| **prettier** | TypeScript/CSS/JSON (apps/web) | Formats frontend code |
| **trailing-whitespace** | All | Removes trailing whitespace |
| **end-of-file-fixer** | All | Ensures files end with newline |
| **check-yaml** | YAML | Validates YAML syntax |
| **check-json** | JSON | Validates JSON syntax |
| **check-added-large-files** | All | Blocks files >500KB |
| **check-merge-conflict** | All | Blocks unresolved merge markers |
| **detect-private-key** | All | Blocks accidental private key commits |
| **bandit** | Python | Security vulnerability scan |
| **pytest-fast** | Python | Runs fast unit tests (modified files, optional) |

## Installation

### Prerequisites

- Python 3.11+
- pip
- Node.js 20+ (for ESLint/Prettier hooks)
- pnpm 9+ (frontend dependencies)

### Step 1: Install pre-commit

```bash
pip install pre-commit
```

Verify:

```bash
pre-commit --version
# Expected: pre-commit 3.x or later
```

### Step 2: Install the hooks

From the repo root:

```bash
pre-commit install
```

This adds a git hook at `.git/hooks/pre-commit` that runs the configured
checks before every commit.

### Step 3: Install frontend dependencies (if not done already)

ESLint and Prettier run through the pre-commit framework but need the
frontend's npm packages available:

```bash
pnpm install
```

### Step 4: Run against all files (optional, but recommended)

```bash
pre-commit run --all-files
```

This runs every hook against every file in the repository. It's a good
sanity check after initial setup.

## Usage

### Normal workflow

After installation, hooks run automatically on `git commit`. If a hook
fails, the commit is blocked:

```bash
git commit -m "feat: add new endpoint"

# ruff-lint................................................................Failed
# ruff-format...............................................................Failed
# - hook id: ruff-format
# - files were modified by this hook

# Fix the issues, stage changes, and try again:
git add -A
git commit -m "feat: add new endpoint"
```

Some hooks (like `ruff-format` and `prettier`) automatically fix files.
After they run, you need to re-stage the changes:

```bash
git add -A
git commit -m "feat: add new endpoint"  # second attempt usually passes
```

### Skip hooks for a single commit

Use `--no-verify` only in emergencies (broken commit, WIP):

```bash
git commit --no-verify -m "WIP: in-progress work"
```

### Run specific hooks

```bash
# Run only ruff
pre-commit run ruff-lint --all-files

# Run only on staged files
pre-commit run trailing-whitespace
```

### Update hook versions

```bash
pre-commit autoupdate
```

Review the changes to `.pre-commit-config.yaml`, then commit them.

## Configuration

### Adding a new hook

Edit `.pre-commit-config.yaml` and add a new entry under the appropriate
repo. Example adding a YAML linter:

```yaml
- repo: https://github.com/adrienverge/yamllint
  rev: v1.35.1
  hooks:
    - id: yamllint
```

### Customizing bandit

Bandit runs with `-ll` (medium+ severity). To add exclusions, edit
`pyproject.toml`:

```toml
[tool.bandit]
exclude_dirs = ["tests/", "sdks/"]
skips = ["B101", B301"]
```

## Troubleshooting

### `pre-commit: command not found`

```bash
pip install pre-commit
```

Or check that your Python Scripts directory is on PATH.

### Hook fails due to missing Node modules

```bash
# ESLint/Prettier need the frontend's dependencies:
cd apps/web && pnpm install && cd ../..
pre-commit run eslint --all-files
```

### Hook is too slow

- Use `SKIP` environment variable to skip specific hooks:
  ```bash
  SKIP=bandit,pytest-fast git commit -m "feat: quick fix"
  ```
- The `pytest-fast` hook only runs on staged files by default. To skip entirely:
  ```bash
  SKIP=pytest-fast git commit -m "feat: no test changes"
  ```

### `pre-commit install` fails

```bash
# Reinstall from scratch
pre-commit clean
pre-commit install
```

## CI Integration

The same hooks can (and should) run in CI. The `.github/workflows/ci.yml`
pipeline includes a linting step that effectively mirrors these checks.

## Reference

- [pre-commit documentation](https://pre-commit.com/)
- [ruff documentation](https://docs.astral.sh/ruff/)
- [ESLint documentation](https://eslint.org/)
- [Prettier documentation](https://prettier.io/)
- [Bandit documentation](https://bandit.readthedocs.io/)
