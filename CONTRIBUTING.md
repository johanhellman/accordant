# Contributing to LLM Council

**Note**: This project is a fork of an existing project. Contribution guidelines may be limited by the original project's terms.

## Development Setup

1. Follow the setup instructions in [README.md](README.md)
2. Install development dependencies:
   ```bash
   uv sync --dev
   cd frontend && npm install
   ```

## Code Style

### Python

- Follow PEP 8 style guidelines
- Use type hints where possible
- Maximum line length: 100 characters (configured in `.editorconfig`)
- Use relative imports within the `backend/` package

### JavaScript/React

- Follow ESLint configuration in `frontend/eslint.config.js`
- Use 2-space indentation
- Use functional components with hooks

### Editor Configuration

The project includes `.editorconfig` for consistent formatting. Configure your editor to use it.

## Formatting and Linting

The project includes automated formatters and linters that are **non-blocking** (optional). They help maintain code quality but won't prevent commits.

### Python (Backend)

**Formatter & Linter**: [Ruff](https://docs.astral.sh/ruff/) (configured in `pyproject.toml`)

**Commands** (using Makefile):
```bash
make format-py          # Format Python code
make lint-py            # Check linting (no fixes)
make lint-py-fix        # Lint and auto-fix issues
make format-check-py    # Check formatting without changes
make lint-check-py      # Check linting without changes
```

**Or using uv directly**:
```bash
uv run ruff format backend/ tests/           # Format code
uv run ruff check backend/ tests/             # Check linting
uv run ruff check --fix backend/ tests/      # Auto-fix linting issues
```

### JavaScript/JSX (Frontend)

**Formatter**: [Prettier](https://prettier.io/) (configured in `frontend/.prettierrc.json`)  
**Linter**: [ESLint](https://eslint.org/) (configured in `frontend/eslint.config.js`)

**Commands** (using npm):
```bash
cd frontend
npm run format          # Format JavaScript/JSX code
npm run format:check    # Check formatting without changes
npm run lint            # Check linting (no fixes)
npm run lint:fix        # Lint and auto-fix issues
```

**Or using Makefile**:
```bash
make format-js          # Format JavaScript/JSX code
make lint-js           # Check linting (no fixes)
make lint-js-fix       # Lint and auto-fix issues
make format-check-js   # Check formatting without changes
```

### Combined Commands

**Format all code** (Python + JavaScript):
```bash
make format-all        # Format everything
make format-check-all  # Check formatting for everything
```

**Lint all code** (Python + JavaScript):
```bash
make lint-all         # Lint everything
make lint-check-all   # Check linting for everything
```

### Optional Pre-commit Hooks

Pre-commit hooks are available but **optional and non-blocking**. They will auto-format code but won't prevent commits.

**Installation** (optional):
```bash
make install-pre-commit
# OR
uv run pre-commit install
```

**Usage**:
- Hooks run automatically on `git commit`
- To skip hooks: `git commit --no-verify`
- To run manually: `make run-pre-commit`
- To skip specific hooks: `SKIP=ruff,prettier git commit`

**Note**: Pre-commit hooks are completely optional. You can always skip them with `--no-verify` if needed.

## Testing
 
Test infrastructure is set up for both backend and frontend. When contributing:
 
**Test Organization:**
- **Backend Tests**: Place all backend tests in the `tests/` directory (project root)
  - Tests should import from `backend.*` modules (e.g., `from backend.main import app`)
  - Configured in `pyproject.toml` with `testpaths = ["tests"]`
- **Frontend Tests**: Place frontend tests in `frontend/src/` (e.g., `frontend/src/api.test.js`)

**Running Tests:**
1. **Backend**: Run tests with `uv run pytest` (or `uv run pytest --cov=backend --cov-report=html` for coverage)
2. **Frontend**: Run tests with `cd frontend && npm test` (or `npm run test:coverage` for coverage)

**When Adding Tests:**
1. Add tests for new functionality in the appropriate location (`tests/` for backend, `frontend/src/` for frontend)
2. Ensure existing tests pass
3. Aim for test coverage of critical functions
4. Follow existing test patterns and naming conventions (`test_*.py` for Python, `*.test.js` for JavaScript)

## Documentation

- Update relevant documentation when adding features:
  - [README.md](README.md) for user-facing changes
  - [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for implementation notes
  - [docs/api/API_SURFACE.md](docs/api/API_SURFACE.md) for API changes
  - [docs/adr/](docs/adr/) for architectural decisions (create new ADR if needed)

## Commit Messages

Use clear, descriptive commit messages. Include:
- What changed
- Why it changed (if not obvious)
- Reference related issues or ADRs if applicable

Example:
```
feat(council): add personality mode support

Implements personality-based interactions for council members.
See ADR-005 for design rationale.

Refs: ADR-005
```

## Pull Requests

1. Create a feature branch from `main`
2. Make your changes
3. Ensure code follows style guidelines
4. Update documentation as needed
5. Submit a pull request with a clear description

## CI/CD Status

**Note**: GitHub workflows (CI/CD) are intentionally deferred per project policy. However, formatting and linting tools are now available:

- **Formatting & Linting**: Available via `make` commands or directly (see "Formatting and Linting" section above)
- **Pre-commit hooks**: Optional, non-blocking hooks available (see "Optional Pre-commit Hooks" above)
- **Manual checks**: Run `make format-check-all` and `make lint-check-all` before committing
- **Tests**: Ensure tests pass locally with `uv run pytest` and `cd frontend && npm test`

We are staying away from automated CI/CD pipelines for now, but developers are encouraged to use the available formatting and linting tools.

## Questions?

If you have questions about contributing, please open an issue or contact the repository maintainer.

