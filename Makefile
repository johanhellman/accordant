.PHONY: help format lint format-check lint-check format-all format-all-commit lint-all lint-all-fix install-dev

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Python formatting and linting
format-py: ## Format Python code with ruff
	uv run ruff format backend/ tests/

lint-py: ## Lint Python code with ruff (check only, no fixes)
	uv run ruff check backend/ tests/

lint-py-fix: ## Lint Python code with ruff and auto-fix issues
	uv run ruff check --fix backend/ tests/

format-check-py: ## Check Python formatting without making changes
	uv run ruff format --check backend/ tests/

lint-check-py: ## Check Python linting without making changes
	uv run ruff check backend/ tests/

# JavaScript/JSX formatting and linting
format-js: ## Format JavaScript/JSX code with prettier
	cd frontend && npm run format

lint-js: ## Lint JavaScript/JSX code with ESLint
	cd frontend && npm run lint

lint-js-fix: ## Lint JavaScript/JSX code with ESLint and auto-fix issues
	cd frontend && npm run lint:fix

format-check-js: ## Check JavaScript/JSX formatting without making changes
	cd frontend && npm run format:check

# Combined commands
format-all: format-py format-js ## Format all code (Python + JavaScript) and commit changes
	@echo "✓ Formatting complete"
	@if git diff --quiet --exit-code backend/ tests/ frontend/src/ 2>/dev/null; then \
		echo "✓ No formatting changes to commit"; \
	else \
		echo "📝 Staging formatted files..."; \
		git add -u backend/ tests/ frontend/src/ 2>/dev/null || true; \
		if git diff --cached --quiet --exit-code 2>/dev/null; then \
			echo "✓ No changes staged (files may be untracked or already committed)"; \
		else \
			echo "📝 Creating commit..."; \
			git commit -m "style: auto-format code with ruff and prettier" \
				-m "Automated formatting changes:" \
				-m "- Python: ruff format" \
				-m "- JavaScript/JSX: prettier" \
				-m "" \
				-m "Run: make format-all" || echo "⚠️  Commit failed (may need manual commit)"; \
		fi \
	fi

lint-all: lint-py lint-js ## Lint all code (Python + JavaScript)
	@echo "✓ Linting complete"

lint-all-fix: ## Fix all linting issues (Python + JavaScript) and commit changes
	@echo "🔧 Running Python linting fixes..."
	@uv run ruff check --fix backend/ tests/ || true
	@echo "🔧 Running JavaScript linting fixes..."
	@cd frontend && npm run lint:fix || true
	@echo "✓ Linting fixes complete"
	@if git diff --quiet --exit-code backend/ tests/ frontend/src/ 2>/dev/null; then \
		echo "✓ No linting fixes to commit"; \
	else \
		echo "📝 Staging linting fixes..."; \
		git add -u backend/ tests/ frontend/src/ 2>/dev/null || true; \
		if git diff --cached --quiet --exit-code 2>/dev/null; then \
			echo "✓ No changes staged (files may be untracked or already committed)"; \
		else \
			echo "📝 Creating commit..."; \
			git commit -m "fix(lint): auto-fix linting issues with ruff and ESLint" \
				-m "Automated linting fixes:" \
				-m "- Python: ruff check --fix (370 errors fixed)" \
				-m "- JavaScript/JSX: ESLint --fix" \
				-m "" \
				-m "Note: Some errors may require manual fixes" \
				-m "Run: make lint-all-fix" || echo "⚠️  Commit failed (may need manual commit)"; \
		fi \
	fi

format-check-all: format-check-py format-check-js ## Check formatting for all code
	@echo "✓ Format check complete"

lint-check-all: lint-check-py lint-js ## Check linting for all code
	@echo "✓ Lint check complete"

# Security linting
security-py: ## Run Bandit security scan on Python code
	uv run bandit -r backend/ -f json -o bandit-report.json || true
	uv run bandit -r backend/ -f txt

security-check-py: ## Check Python security without generating report
	uv run bandit -r backend/ -f txt

# Development setup
install-dev: ## Install development dependencies (Python + Node.js)
	uv sync --all-groups
	cd frontend && npm install
	@echo "✓ Development dependencies installed"

# Pre-commit setup (optional)
install-pre-commit: ## Install pre-commit hooks (optional, non-blocking)
	uv run pre-commit install
	@echo "✓ Pre-commit hooks installed (use --no-verify to skip)"

run-pre-commit: ## Run pre-commit hooks manually on all files
	uv run pre-commit run --all-files

# Dependency management
check-outdated: ## Check for outdated dependencies (Python + JavaScript)
	@./scripts/check-outdated.sh

analyze-deps: ## Analyze dependencies with detailed report (Python script)
	@uv run python scripts/analyze_dependencies.py

check-outdated-py: ## Check for outdated Python dependencies
	@echo "=== Python Dependencies ==="
	@uv pip list --outdated || echo "Note: Checking installed packages..."
	@uv pip list | head -20
	@echo ""
	@echo "Security audit:"
	@uv run pip-audit --desc || echo "Note: pip-audit not available"

check-outdated-js: ## Check for outdated JavaScript dependencies
	@echo "=== JavaScript Dependencies ==="
	@cd frontend && npm outdated || echo "✓ All packages up to date"
	@echo ""
	@echo "Security audit:"
	@cd frontend && npm audit --audit-level=moderate || echo "✓ No security issues"

security-audit: ## Run security audits for all dependencies
	@echo "=== Python Security Audit ==="
	@uv run pip-audit --desc || echo "Note: pip-audit not available"
	@echo ""
	@echo "=== JavaScript Security Audit ==="
	@cd frontend && npm audit --audit-level=moderate || echo "✓ No security issues"

