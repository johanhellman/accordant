# Developer Guide for LLM Council

This file contains technical implementation details, gotchas, and important notes for developers working on the LLM Council project.

> **Note**: For architectural decisions, see [Architecture Decision Records](adr/ADR_INDEX.md).  
> For API documentation, see [API Surface](api/API_SURFACE.md).  
> For system overview, see [System Overview](design/SYSTEM_OVERVIEW.md).

## Project Overview

LLM Council is a 3-stage deliberation system where multiple LLMs collaboratively answer user questions. The key innovation is anonymized peer review in Stage 2, preventing models from playing favorites.

## Development Setup

### Prerequisites

- **Python 3.10+** (3.13.2 recommended)
- **Node.js v18+** (v24.10.0 recommended)
- **[uv](https://docs.astral.sh/uv/)** - Modern Python package manager
- **npm** - Node.js package manager (comes with Node.js)

### Development Dependencies

The project currently uses minimal development tooling by design (see CONTRIBUTING.md). However, for development you may want:

**Backend:**

- **Runtime dependencies:** Installed via `uv sync` (FastAPI, httpx, pydantic, etc.)
- **Test framework:** pytest 9.0.1 (installed as dev dependency via `uv sync --dev`)
  - Run tests: `uv run pytest`
  - Run with coverage: `uv run pytest --cov=backend --cov-report=html`
- **Test utilities:** pytest-asyncio, pytest-cov, pytest-mock (included in dev dependencies)
- **Formatting/Linting:** Ruff 0.8.0+ configured (formatter + linter)
  - Format: `make format-py` or `uv run ruff format backend/ tests/`
  - Lint: `make lint-py` or `uv run ruff check backend/ tests/`
  - Auto-fix: `make lint-py-fix` or `uv run ruff check --fix backend/ tests/`

**Frontend:**

- **Runtime dependencies:** Installed via `npm install` (React, Vite, etc.)
- **Linting:** ESLint 9.39.1 configured and installed
  - Run linting: `cd frontend && npm run lint`
  - Auto-fix: `cd frontend && npm run lint:fix`
- **Formatting:** Prettier 3.4.2+ configured
  - Format: `cd frontend && npm run format`
  - Check: `cd frontend && npm run format:check`
- **Testing:** Vitest 2.1.8 configured with React Testing Library (test infrastructure ready)

**Combined Commands (via Makefile):**

- Format all: `make format-all`
- Lint all: `make lint-all`
- See all commands: `make help`

### Running in Development Mode

**Backend:**

```bash
# Install dependencies
uv sync

# Run with auto-reload (if uvicorn supports it)
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8002

# Or use the module approach
uv run python -m backend.main
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev  # Starts Vite dev server with hot reload
```

### Environment Variables for Development

Create a `.env` file in the project root:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-...
ENCRYPTION_KEY=your-generated-key-here

# Optional - Development settings
LOG_LEVEL=DEBUG  # More verbose logging
MAX_CONCURRENT_REQUESTS=2  # Lower for development to avoid rate limits
LLM_REQUEST_TIMEOUT=60.0  # Shorter timeout for faster feedback
```

### Code Style

- **Python**: Ruff configured for formatting and linting (see above)
- **JavaScript**: ESLint 9.39.1 configured in `frontend/eslint.config.js`
- **Type Hints**: Python code uses type hints where appropriate
- **Docstrings**: Functions and classes should have docstrings

### Testing

- **Current Status**: Backend tests are implemented and passing; frontend Vitest tests are configured (see `HYGIENE_REPORT.md` for coverage details).

**Test Organization:**

- **Backend Tests**: All backend tests should be located in the `tests/` directory (project root)
  - Configured in `pyproject.toml` with `testpaths = ["tests"]`
  - Tests import from `backend.*` modules (e.g., `from backend.main import app`)
  - **Note**: There are 2 legacy test files in `backend/tests/` that should be moved to `tests/` for consistency
- **Frontend Tests**: Frontend tests live under `frontend/src` (e.g., `frontend/src/api.test.js` and component tests)
  - Configured in `frontend/vite.config.js` for Vitest

**Running Tests:**

- **Backend**: `uv run pytest` (or `uv run pytest --cov=backend --cov-report=html` for coverage reports)
- **Frontend**: `cd frontend && npm test` (or `npm run test:coverage` for coverage)

**Why Tests Are in Project Root:**

- Tests are separate from source code, making it clear they're not part of the application
- Tests import from `backend.*`, making it explicit they're testing the backend package
- Aligns with pytest configuration (`testpaths = ["tests"]`)
- Follows standard Python project structure

### Debugging

**Backend Logging:**

- Logs are configured in `backend/logging_config.py`
- Default log file: `logs/llm_council.log`
- Set `LOG_LEVEL=DEBUG` in `.env` for verbose output

**Frontend Debugging:**

- Use browser DevTools (F12)
- React DevTools extension recommended
- Check Network tab for API call issues

**Common Debugging Steps:**

1. Check backend logs: `tail -f logs/llm_council.log`
2. Check browser console for frontend errors
3. Verify API key is set: `echo $OPENROUTER_API_KEY` (or check `.env`)
4. Test API directly: `curl http://localhost:8002/` should return `{"status":"ok"}`

### Project Structure

```
accordant/
├── backend/           # Python FastAPI backend
│   ├── council.py    # Core 3-stage orchestration logic
│   ├── main.py       # FastAPI app and endpoints
│   ├── openrouter.py # OpenRouter API client
│   ├── storage.py    # Database storage logic
│   └── config.py     # Configuration management
├── frontend/         # React + Vite frontend
│   └── src/
│       ├── components/ # React components
│       └── api.js     # API client
├── data/             # Data storage (gitignored)
│   ├── system.db     # Users and Organizations
│   └── organizations/ # Tenant data
│       └── {org_id}/
│           └── tenant.db # Conversations, Messages, and Votes
├── docs/             # Documentation
│   ├── adr/          # Architecture Decision Records
│   ├── api/          # API documentation
│   └── design/       # Design documents
└── tests/            # Test files (skeleton tests exist)
```

### Route Ordering in FastAPI

**Important:** FastAPI matches routes in the order they're defined. When adding routes to `main.py`, follow this order:

1. **API routes first** - All `/api/*` endpoints must be defined before catch-all routes
2. **Static file mounting** - Mount `/assets` directory for frontend assets
3. **Root route** - Define `@app.get("/")` for SPA index page
4. **Catch-all route last** - `@app.get("/{full_path:path}")` must be the very last route

**Why this matters:**

- If catch-all route is defined before API routes, it will intercept API requests and return 404
- FastAPI matches routes top-to-bottom, so more specific routes must come first
- The catch-all route is needed for SPA client-side routing, but must not interfere with API calls

**Example structure in `main.py`:**

```python
# 1. API routes (health, auth, conversations, etc.)
@app.get("/api/health")
async def health_check():
    ...

@app.get("/api/auth/me")
async def get_current_user():
    ...

# ... all other API routes ...

# 2. Static file mounting (after all API routes)
app.mount("/assets", StaticFiles(...))

# 3. Root route
@app.get("/")
async def root():
    return FileResponse("index.html")

# 4. Catch-all route (MUST BE LAST)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(404, "API endpoint not found")
    return FileResponse("index.html")
```

### Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines, including:

- Code style preferences
- Testing approach
- CI/CD status (intentionally deferred)
- Pre-commit hooks (intentionally deferred)

## Multi-Tenancy Architecture

The system uses a **Physically Sharded SQLite Architecture** (ADR-016) to ensure strict data isolation and write scalability.

- **System DB (`data/system.db`)**: 
  - Stores global data: Users, Organizations, Registration info.
  - Low write volume, mostly read-heavy.
- **Tenant DBs (`data/organizations/{org_id}/tenant.db`)**: 
  - Stores private data: Conversations, Messages, Voting History.
  - One database file per organization.
  - High write volume, better concurrency (writes to Org A don't block Org B).
- **Secrets**: API keys are encrypted at rest using Fernet (symmetric encryption).

See [ADR-016](adr/ADR-016-multi-tenant-sqlite-sharding.md) and [ADR-013](adr/013-secrets-management.md) for details.

## Implementation Details

### Backend Structure (`backend/`)

**`config.py`**

- Contains `CHAIRMAN_MODEL` (model that synthesizes final answer)
- Loads personalities from `data/personalities/` (or `COUNCIL_PERSONALITIES_DIR`)
- Loads global system prompts from `system-prompts.yaml`
- Uses environment variable `OPENROUTER_API_KEY` from `.env`
- Uses environment variable `OPENROUTER_API_KEY` from `.env`
- Backend runs on **port 8002** (NOT 8000 or 8001 - user had other apps on those ports)

**`auth.py` & `users.py`**

- **Authentication**: JWT-based auth using OAuth2PasswordBearer.
- **User Management**: `users.py` stores users in `system.db` via `SystemSessionLocal`.
- **Roles**: Supports `is_admin` flag. First registered user is auto-admin.
- **Security**: `UserResponse` model ensures password hashes are never returned in API responses.

**`admin_routes.py` & `admin_users_routes.py`**

- **Admin API**: Endpoints for managing personalities, system prompts, and users.
- **Voting History**: Admin route to fetch global voting history with user attribution.

**`openrouter.py`**

- `query_model()`: Single async model query
- `query_models_parallel()`: Parallel queries using `asyncio.gather()`
- Returns dict with 'content' and optional 'reasoning_details'
- Graceful degradation: returns None on failure, continues with successful responses

**`council.py`** - The Core Logic

- `stage1_collect_responses()`: Parallel queries to all council models
- `stage2_collect_rankings()`:
  - Anonymizes responses as "Response A, B, C, etc."
  - Creates `label_to_model` mapping for de-anonymization
  - Prompts models to evaluate and rank (with strict format requirements)
  - Returns tuple: (rankings_list, label_to_model_dict)
  - Each ranking includes both raw text and `parsed_ranking` list
- `stage3_synthesize_final()`: Chairman synthesizes from all responses + rankings
- `parse_ranking_from_text()`: Extracts "FINAL RANKING:" section, handles both numbered lists and plain format
- `calculate_aggregate_rankings()`: Computes average rank position across all peer evaluations

**`storage.py`**

- **Tenant-Aware**: Uses `get_tenant_session(org_id)` to connect to the correct `tenant.db`.
- **Normalized Schema**: Messages are stored in a dedicated `Message` table, linked to `Conversation`.
- **Performance**: Normalized storage prevents large JSON blob overhead during chat appends.

**`main.py`**

- FastAPI app with CORS enabled for localhost:5173 and localhost:3000
- Initialized `system.db` tables on startup.
- POST `/api/conversations/{id}/message` returns metadata in addition to stages
- Metadata includes: label_to_model mapping and aggregate_rankings

**`organizations.py` & `invitations.py`**

- **Organization Model**: Stored in `system.db`.
- **Invitation Model**: `{code, org_id, expires_at, is_active}`
- **Org Routes**: Public endpoints for creating orgs and joining via invite code.

### Personalities System

The system supports a modular "Personalities" architecture:

- **Directory**: `data/personalities/` contains individual YAML files for each personality.
- **Structure**: Each YAML file defines `id`, `name`, `model`, `personality_prompt`, `ui` metadata, and an `enabled` flag.
- **System Prompts**: `data/personalities/system-prompts.yaml` contains global prompts:
  - `base_system_prompt`: Shared by all personalities.
  - `chairman_prompt`: Used by the chairman in Stage 3.
  - `title_generation_prompt`: Used for generating conversation titles.
- **Loading**: `config.py` scans the directory, loads enabled personalities into `PERSONALITY_REGISTRY`, and loads system prompts.
- **Activation**: `COUNCIL_PERSONALITIES_ACTIVE` env var controls which personalities participate in the council.

**Note**: In Multi-Tenancy, personalities are loaded from `data/organizations/{org_id}/personalities/`. The global `data/personalities/` serves as a template/fallback.

### System Prompts Configuration

The system uses a hierarchical configuration for system prompts:

1. **Defaults**: `data/defaults/system-prompts.yaml` contains the baseline prompts.
2. **Overrides**: `data/organizations/{org_id}/config/system-prompts.yaml` contains organization-specific overrides.

**Prompt Assembly (Stage 2)**:
To ensure the Consensus Model works correctly, the Ranking Prompt is **assembled dynamically** from three parts:

1. **Enforced Context**: Prepend user query and peer responses (handled by backend).
2. **Instructions**: The configurable part (from YAML) where admins define *how* to evaluate.
3. **Enforced Format**: Append strict output formatting rules (handled by backend).

**Important**: When editing `ranking_prompt` in YAML or the UI, you should **ONLY** provide the evaluation instructions (e.g., "Evaluate for creativity"). Do not include placeholders like `{user_query}` or formatting rules, as these are enforced by the system.

### Frontend Structure (`frontend/src/`)

**`App.jsx`**

- Main orchestration: manages conversations list and current conversation
- Handles message sending and metadata storage
- Important: metadata is stored in the UI state for display but not persisted to backend JSON
- Important: metadata is stored in the UI state for display

**`components/ChatInterface.jsx`**

- Multiline textarea (3 rows, resizable)
- Enter to send, Shift+Enter for new line
- User messages wrapped in markdown-content class for padding

**`components/Stage1.jsx`**

- Tab view of individual model responses
- ReactMarkdown rendering with markdown-content wrapper

**`components/Stage2.jsx`**

- **Critical Feature**: Tab view showing RAW evaluation text from each model
- De-anonymization happens CLIENT-SIDE for display (models receive anonymous labels)
- Shows "Extracted Ranking" below each evaluation so users can validate parsing
- Aggregate rankings shown with average position and vote count
- Explanatory text clarifies that boldface model names are for readability only

**`components/Stage3.jsx`**

- Final synthesized answer from chairman
- Green-tinted background (#f0fff0) to highlight conclusion

**Styling (`*.css`)**

- Light mode theme (not dark mode)
- Primary color: #4a90e2 (blue)
- Global markdown styling in `index.css` with `.markdown-content` class
- 12px padding on all markdown content to prevent cluttered appearance

## Key Implementation Patterns

> **Architectural Decisions**: For detailed design decisions and rationale, see [Architecture Decision Records](adr/ADR_INDEX.md).

### Stage 2 Prompt Format

The Stage 2 prompt is very specific to ensure parseable output:

```
1. Evaluate each response individually first
2. Provide "FINAL RANKING:" header
3. Numbered list format: "1. Response C", "2. Response A", etc.
4. No additional text after ranking section
```

This strict format allows reliable parsing while still getting thoughtful evaluations. See [ADR-002](adr/ADR-002-anonymized-peer-review.md) for the design rationale.

### De-anonymization Strategy

- Models receive: "Response A", "Response B", etc.
- Backend creates mapping: `{"Response A": "openai/gpt-5.1", ...}`
- Frontend displays model names in **bold** for readability
- Users see explanation that original evaluation used anonymous labels
- This prevents bias while maintaining transparency

### Error Handling Philosophy

- Continue with successful responses if some models fail (graceful degradation)
- Never fail the entire request due to single model failure
- Log errors but don't expose to user unless all models fail

### UI/UX Transparency

- All raw outputs are inspectable via tabs
- Parsed rankings shown below raw text for validation
- Users can verify system's interpretation of model outputs
- This builds trust and allows debugging of edge cases

## Important Implementation Details

### Relative Imports

All backend modules use relative imports (e.g., `from .config import ...`) not absolute imports. This is critical for Python's module system to work correctly when running as `python -m backend.main`.

### Port Configuration

- Backend: 8002 (changed from 8000/8001 to avoid conflict)
- Frontend: 5173 (Vite default)
- Update both `backend/main.py` and `frontend/src/api.js` if changing

### Markdown Rendering

All ReactMarkdown components must be wrapped in `<div className="markdown-content">` for proper spacing. This class is defined globally in `index.css`.

### Model Configuration

Models are hardcoded in `backend/config.py`. Chairman can be same or different from council members. The current default is Gemini as chairman per user preference.

## Common Gotchas

1. **Module Import Errors**: Always run backend as `python -m backend.main` from project root, not from backend directory
2. **CORS Issues**: Frontend must match allowed origins in `main.py` CORS middleware
3. **Ranking Parse Failures**: If models don't follow format, fallback regex extracts any "Response X" patterns in order
4. **Missing Metadata**: Metadata is ephemeral (not persisted), only available in API responses

## Testing Commands

- **Backend tests**: Run `uv run pytest` from the repository root. For HTML coverage reports, use `uv run pytest --cov=backend --cov-report=html` (outputs to `htmlcov/`).
- **Frontend tests**: From `frontend/`, run `npm test` for the default Vitest run, or `npm run test:coverage` to collect coverage.
- **Frontend linting**: From `frontend/`, run `npm run lint` to execute ESLint with the configured rules.

## Future Enhancement Ideas

- Configurable council/chairman via UI instead of config file
- Streaming responses instead of batch loading
- Export conversations to markdown/PDF
- Model performance analytics over time
- Custom ranking criteria (not just accuracy/insight)
- Support for reasoning models (o1, etc.) with special handling

## Testing Notes

Use `test_openrouter.py` to verify API connectivity and test different model identifiers before adding to council. The script tests both streaming and non-streaming modes.

## Data Flow

See [System Overview](design/SYSTEM_OVERVIEW.md) for detailed data flow diagrams and component interactions.
