# Accordant ![Version](https://img.shields.io/badge/version-0.2.0-blue)

**Accordant** is a local web application that allows you to form your own "LLM Council". Instead of relying on a single AI provider, Accordant groups multiple LLMs (e.g., OpenAI GPT-4, Google Gemini Pro, Anthropic Claude) to review, rank, and synthesize answers to your queries.

It essentially looks like a chat interface but uses OpenRouter to send your query to multiple LLMs, asks them to review and rank each other's work, and finally, a Chairman LLM produces the final response.

It is designed to be a fully customizable platform with sophisticated personality management, allowing you to fine-tune the behavior and "voice" of each council member. The system supports multi-tenant, multi-user management, ensuring data isolation and secure access for different organizations and users. Additionally, it tracks voting history and provides aggregate statistics on a personality level, giving you deep insights into how different models and personalities align or diverge over time.

In a bit more detail, here is what happens when you submit a query:

1. **Stage 1: First opinions**. The user query is given to all LLMs individually, and the responses are collected. The individual responses are shown in a "tab view", so that the user can inspect them all one by one.
2. **Stage 2: Review**. Each individual LLM is given the responses of the other LLMs. Under the hood, the LLM identities are anonymized so that the LLM can't play favorites when judging their outputs. The LLM is asked to rank them in accuracy and insight.
3. **Stage 3: Final response**. The designated Chairman of the LLM Council takes all of the model's responses and compiles them into a single final answer that is presented to the user.

## Back-and-Forth Discussion

The application supports multi-turn conversations. The Council remembers the context of the discussion, allowing you to ask follow-up questions.

**Note on Context:** To save tokens, the history passed to the models includes only the **User Queries** and the **Final Answers** (Stage 3). The internal deliberations (Stage 1 individual responses and Stage 2 rankings) are stripped from the history.

**Future Consideration:** We are considering adding the **Voting History** (Stage 2 rankings) to the context in the future to allow the Council to reflect on its own consensus levels (e.g., "Why did we disagree?"). If implemented, this will be done on a **Personality Level** to ensure character consistency.

## Multi-User Support

The application supports multiple users with isolated chat histories.
- **User Isolation**: Each user has their own private conversation history.
- **Multi-Organization**: Users belong to an Organization. Data is isolated per organization.
- **Admin Roles**:
    - **Instance Admin**: Manages all organizations and system-wide settings.
    - **Org Admin**: Manages users, settings (API Keys), and invitations within their organization.

## Admin Features

Admins have access to special API endpoints to manage the system:
- **User Management**: View all users and promote/demote admins.
- **Organization Settings**: Configure API Keys and Gateway URLs for your organization.
- **Invitations**: Generate invite codes to add users to your organization.
- **Global Voting History**: View the full history of how personalities voted across all user conversations.

**Accessing Admin Tools:**
Currently, admin features are accessible via the API documentation (Swagger UI):
1.  Go to `http://localhost:8001/docs`
2.  Authorize using your login token (click "Authorize" and enter your credentials).
3.  Use the `admin-users` and `admin` endpoints.

## Implementation Note

This project has been implemented using a combination of **AntiGravity** and **Cursor**, utilizing custom commands to enforce structure, hygiene, and best practices. It aims to demonstrate a robust and scalable approach to local AI application development.

## Acknowledgements

This project was inspired by:
*   **Andrej Karpathy's [llm-council](https://github.com/karpathy/llm-council)**: The original inspiration for the multi-model council architecture.
*   **PewDiePie's [AI Council video](https://www.youtube.com/watch?v=qw4fDU18RcU)**: A conceptual exploration of the AI Council idea.

## Setup

### 1. Install Dependencies

The project uses [uv](https://docs.astral.sh/uv/) for project management.

**Backend:**
```bash
uv sync
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

### 2. Configure API Key

Create a `.env` file in the project root. You can copy `.env.example` as a starting point:

```bash
cp .env.example .env
```

Then edit `.env` and add your OpenRouter API key:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

Get your API key at [openrouter.ai](https://openrouter.ai/). Make sure to purchase the credits you need, or sign up for automatic top up.

### 3. Configure Encryption Key (Required for Multi-Tenancy)

Generate a secure encryption key for storing API credentials:

```bash
# Generate a Fernet key (32 url-safe base64-encoded bytes)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add this key to your `.env` file:

```bash
ENCRYPTION_KEY=your-generated-key-here
```

**Important:** Keep this key safe. If lost, all stored API keys in the database will be unrecoverable.

#### Key Rotation

**Note:** Key rotation is currently a **manual process** that requires a brief maintenance window.

To rotate the encryption key (e.g., if compromised or for compliance):

1.  **Stop the application** to ensure no new data is written during rotation.
2.  **Generate a new key**:
    ```bash
    NEW_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    echo "New Key: $NEW_KEY"
    ```
3.  **Run the rotation script**:
    ```bash
    # Usage: python -m backend.scripts.rotate_keys <OLD_KEY> <NEW_KEY>
    uv run python -m backend.scripts.rotate_keys $ENCRYPTION_KEY $NEW_KEY
    ```
4.  **Update Configuration**:
    -   Update your `.env` file (or deployment secrets) with `ENCRYPTION_KEY=$NEW_KEY`.
5.  **Restart the application**.

### 3. Configure Chairman & Title Models (Optional)
 
 You can customize the special models by adding the following variables to your `.env` file:
 
 ```bash
 # Model to synthesize the final response
 # WARNING: Setting this overrides the selection made in the UI (System Prompts > Chairman Model).
 # CHAIRMAN_MODEL=gemini/gemini-2.5-pro
 
 # Model to generate conversation titles
 # WARNING: Setting this overrides the selection made in the UI (System Prompts > Title Generation Model).
 # TITLE_GENERATION_MODEL=gemini/gemini-2.5-pro
 ```
 
 If these variables are not set, the application will use the configuration managed via the UI (stored in `data/personalities/system-prompts.yaml`).

### 5. Configure Personalities (Optional)

The application supports distinct "Personalities" for the council members. These are defined in YAML files located in the `data/personalities/` directory.

You can customize the location of these files by setting:

```bash
# Directory containing personality YAML files (Default: data/personalities)
COUNCIL_PERSONALITIES_DIR=data/personalities

# List of active personality IDs to use (JSON array or comma-separated)
# WARNING: Setting this overrides the "Enabled" status set in the UI.
# If set, only these personalities will be used.
# COUNCIL_PERSONALITIES_ACTIVE='["gpt_ceo", "claude_ethicist", "gemini_data", "grok_realist"]'
```

Each personality file (e.g., `gpt_ceo.yaml`) defines the model, name, and specific system prompts for that personality. Global system prompts are defined in `data/personalities/system-prompts.yaml`.

### 4. Configure Performance (Optional)

You can tune the performance and reliability of the application:

```bash
# Maximum number of concurrent API requests (Default: 4)
# Lower this if you hit rate limits. Increase if you have high limits.
MAX_CONCURRENT_REQUESTS=4

# Timeout for each API request in seconds (Default: 180.0)
LLM_REQUEST_TIMEOUT=180.0

# Number of retries for failed requests (Default: 3)
LLM_MAX_RETRIES=3

# Logging Level (Default: INFO)
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO
```

## Running the Application

**Option 1: Use the start script**
```bash
./start.sh
```

**Option 2: Run manually**

Terminal 1 (Backend):
```bash
uv run python -m backend.main
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

Then open http://localhost:5173 in your browser.

## Troubleshooting

### Backend Issues

**API Key Not Found**
- Error: `OPENROUTER_API_KEY or LLM_API_KEY environment variable is required`
- Solution: Ensure your `.env` file exists in the project root and contains `OPENROUTER_API_KEY=sk-or-v1-...`
- Verify: Check that `.env` is in the same directory as `pyproject.toml`

**Module Not Found Errors**
- Error: `ModuleNotFoundError: No module named 'backend'`
- Solution: Run `uv sync` to install dependencies, then use `uv run python -m backend.main` to start the backend
- Alternative: Activate the virtual environment with `source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows)

**Port Already in Use**
- Error: `Address already in use` when starting backend
- Solution: Either stop the process using port 8001, or set a different port via environment variable:
  ```bash
  PORT=8002 uv run python -m backend.main
  ```

**Rate Limiting**
- Symptom: Requests fail with timeout or rate limit errors
- Solution: Reduce `MAX_CONCURRENT_REQUESTS` in `.env` (try 2 or 1), or increase `LLM_REQUEST_TIMEOUT`

### Frontend Issues

**Port Already in Use**
- Error: Vite dev server can't start because port 5173 is in use
- Solution: Vite will automatically try the next available port, or specify one:
  ```bash
  cd frontend
  npm run dev -- --port 5174
  ```

**Dependencies Not Installing**
- Error: `npm install` fails
- Solution: Ensure you have Node.js v18+ installed. Try clearing cache:
  ```bash
  cd frontend
  rm -rf node_modules package-lock.json
  npm install
  ```

**CORS Errors**
- Error: `CORS policy: No 'Access-Control-Allow-Origin' header`
- Solution: Check your `CORS_ORIGINS` environment variable in `.env`. Default is `http://localhost:5173,http://localhost:3000`
- If using a different frontend port, add it to `CORS_ORIGINS`

### General Issues

**Conversations Not Saving**
- Symptom: Conversations disappear after restart
- Solution: Check that `data/conversations/` directory exists and is writable
- Verify: Check logs for file permission errors

**Models Not Responding**
- Symptom: All models fail or timeout
- Solution: 
  1. Check your OpenRouter API key has sufficient credits
  2. Verify model names in `COUNCIL_MODELS` are correct (check [OpenRouter models](https://openrouter.ai/models))
  3. Increase `LLM_REQUEST_TIMEOUT` if models are slow
  4. Check logs for specific error messages

**Logs Location**
- Backend logs: `logs/llm_council.log` (if configured)
- Console output: Check the terminal where you started the backend/frontend

## Development Setup

### Prerequisites

- **Python 3.10+** (3.13.2 recommended)
- **Node.js v18+** (v24.10.0 recommended)
- **uv** - Modern Python package manager ([installation guide](https://docs.astral.sh/uv/))
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

### Project Structure

```
llm-council/
├── backend/           # Python FastAPI backend
│   ├── council.py    # Core 3-stage orchestration logic
│   ├── main.py       # FastAPI app and endpoints
│   ├── openrouter.py # OpenRouter API client
│   ├── storage.py    # JSON file storage
│   └── config.py     # Configuration management
├── frontend/         # React + Vite frontend
│   └── src/
│       ├── components/ # React components
│       └── api.js     # API client
├── data/             # Data storage (gitignored)
│   └── conversations/ # Conversation JSON files
├── docs/             # Documentation
│   ├── adr/          # Architecture Decision Records
│   ├── api/          # API documentation
│   └── design/       # Design documents
└── tests/            # Test files (skeleton tests exist)
```

### Running in Development Mode

**Backend:**
```bash
# Install dependencies
uv sync

# Run with auto-reload (if uvicorn supports it)
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001

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

# Optional - Development settings
LOG_LEVEL=DEBUG  # More verbose logging
MAX_CONCURRENT_REQUESTS=2  # Lower for development to avoid rate limits
LLM_REQUEST_TIMEOUT=60.0  # Shorter timeout for faster feedback
```

### Code Style

- **Python**: No formatter/linter configured (intentionally deferred per CONTRIBUTING.md)
- **JavaScript**: ESLint 9.39.1 configured in `frontend/eslint.config.js`
- **Type Hints**: Python code uses type hints where appropriate
- **Docstrings**: Functions and classes should have docstrings

### Testing

- **Current Status**: Backend tests are implemented and passing; frontend Vitest tests are configured (see `HYGIENE_REPORT.md` for coverage details).
- **Test Location**: Backend tests live in the `tests/` directory; frontend tests live under `frontend/src` (e.g., `frontend/src/api.test.js` and component tests).
- **Running Backend Tests**: `uv run pytest` (or `uv run pytest --cov=backend --cov-report=html` for coverage reports).
- **Running Frontend Tests**: `cd frontend && npm test` (or `npm run test:coverage` for coverage).

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
4. Test API directly: `curl http://localhost:8001/` should return `{"status":"ok"}`

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines, including:
- Code style preferences
- Testing approach
- CI/CD status (intentionally deferred)
- Pre-commit hooks (intentionally deferred)

## Tech Stack

- **Backend:** FastAPI (Python 3.10+), async httpx, OpenRouter API
- **Frontend:** React + Vite, react-markdown for rendering
- **Storage:** JSON files in `data/conversations/`
- **Package Management:** uv for Python, npm for JavaScript

## Documentation

For developers and contributors:

- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Implementation details, gotchas, and development notes
- **[Architecture Decision Records](docs/adr/ADR_INDEX.md)** - Key architectural decisions and rationale
- **[API Documentation](docs/api/API_SURFACE.md)** - Complete API reference
- **[System Overview](docs/design/SYSTEM_OVERVIEW.md)** - High-level architecture and component overview

For more information, see [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## Deployment

### Production Deployment Considerations

When deploying to production, ensure the following security and configuration settings are properly configured:

#### CORS Configuration

**⚠️ Important:** Default CORS settings are permissive for local development. For production, you **must** configure restrictive CORS settings.

**Environment Variables:**

```bash
# Required: Specify exact allowed origins (comma-separated or JSON array)
# Example: CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
# Or JSON: CORS_ORIGINS='["https://yourdomain.com","https://www.yourdomain.com"]'
CORS_ORIGINS=https://yourdomain.com

# Optional: Restrict HTTP methods (default: "*" allows all)
# Example: CORS_METHODS=GET,POST,OPTIONS
CORS_METHODS=GET,POST,OPTIONS

# Optional: Restrict allowed headers (default: "*" allows all)
# Example: CORS_HEADERS=Content-Type,Authorization
CORS_HEADERS=Content-Type,Authorization

# Optional: Allow credentials (default: "true")
# Set to "false" if you don't need cookies/auth headers
CORS_CREDENTIALS=true
```

**Security Best Practices:**
- **Never use `*` for `CORS_ORIGINS` in production** - Always specify exact domain(s)
- Use HTTPS in production - CORS with credentials requires HTTPS
- Restrict `CORS_METHODS` to only what your frontend needs
- Restrict `CORS_HEADERS` to only necessary headers

**Example Production `.env`:**

```bash
# API Configuration
OPENROUTER_API_KEY=sk-or-v1-...

# CORS - Production Settings
CORS_ORIGINS=https://yourdomain.com
CORS_METHODS=GET,POST,OPTIONS
CORS_HEADERS=Content-Type,Authorization
CORS_CREDENTIALS=true

# Performance Settings
MAX_CONCURRENT_REQUESTS=4
LLM_REQUEST_TIMEOUT=180.0
LLM_MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO
LOG_DIR=/var/log/llm-council
LOG_FILE=/var/log/llm-council/llm_council.log
```

#### File System Security

**Path Validation:**
- The application validates file paths to prevent directory traversal attacks
- Environment variables for file paths (`LOG_DIR`, `LOG_FILE`, `PERSONALITIES_FILE`) are validated
- All paths are resolved to absolute paths and checked against allowed directories

**File Permissions:**
- Ensure `data/conversations/` directory has proper write permissions
- Log directories should be writable by the application user
- Consider using a database for production instead of JSON files for better scalability

#### Deployment Options

**Option 1: Docker (Recommended)**
```bash
# Build and run with Docker
docker build -t llm-council .
docker run -p 8001:8001 --env-file .env llm-council
```

**Option 2: Systemd Service**
```ini
[Unit]
Description=LLM Council API
After=network.target

[Service]
Type=simple
User=llm-council
WorkingDirectory=/opt/llm-council
Environment="PATH=/opt/llm-council/.venv/bin"
ExecStart=/opt/llm-council/.venv/bin/python -m backend.main
Restart=always

[Install]
WantedBy=multi-user.target
```

**Option 3: Reverse Proxy (nginx)**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Environment Variables for Production

See the [Configuration](#4-configure-performance-optional) section for all available environment variables. Key production considerations:

- **API Keys:** Use secret management systems (AWS Secrets Manager, HashiCorp Vault, etc.)
- **CORS:** Configure restrictive settings (see above)
- **Logging:** Set appropriate log levels and retention policies
- **Performance:** Tune `MAX_CONCURRENT_REQUESTS` based on your rate limits
- **File Paths:** Use absolute paths and ensure proper permissions
