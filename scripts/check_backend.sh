#!/bin/bash
set -e

echo "🔍 Starting Backend Preflight Checks..."

# 1. Format Check
echo "🎨 Checking formatting (ruff)..."
uv run ruff format --check backend tests || echo "⚠️ Formatting issues found. Please run 'uv run ruff format' locally."

# 2. Lint Check
echo "🧹 Checking lint (ruff)..."
uv run ruff check backend tests || echo "⚠️ Linting issues found. Please run 'uv run ruff check --fix' locally."

# 3. Security Check
echo "🔒 Checking security (bandit)..."
uv run bandit -c pyproject.toml -r backend

# 4. Migration Check
echo "🗄️ Checking for missing migrations..."
# Update DB to head first (in CI this is critical as DB might be fresh)
uv run alembic upgrade head
# Now check if models match the head
uv run alembic check

# 5. Tests
echo "🧪 Running tests (pytest)..."
# We run pytest directly. Failures will now BLOCK the build.
# Known issues are marked as xfail in the code.
uv run python -m pytest

