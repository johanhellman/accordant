# Setup Guide

Complete setup instructions for Accordant LLM Council, including configuration options and advanced settings.

## Prerequisites

- **Python 3.10+** (3.13.2 recommended)
- **Node.js v18+** (v24.10.0 recommended)
- **[uv](https://docs.astral.sh/uv/)** - Modern Python package manager
- **npm** - Node.js package manager (comes with Node.js)
- **OpenRouter API key** - [Get one here](https://openrouter.ai/)

## Quick Start

For a minimal setup, see the [Quick Start section in README.md](../README.md#quick-start).

## Detailed Setup

### 1. Install Dependencies

The project uses [uv](https://docs.astral.sh/uv/) for Python project management.

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

1. **Stop the application** to ensure no new data is written during rotation.
2. **Generate a new key**:

   ```bash
   NEW_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
   echo "New Key: $NEW_KEY"
   ```

3. **Run the rotation script**:

   ```bash
   # Usage: python -m backend.scripts.rotate_keys <OLD_KEY> <NEW_KEY>
   uv run python -m backend.scripts.rotate_keys $ENCRYPTION_KEY $NEW_KEY
   ```

4. **Update Configuration**:
   - Update your `.env` file (or deployment secrets) with `ENCRYPTION_KEY=$NEW_KEY`.
5. **Restart the application**.

### 4. Configure Chairman & Title Models (Optional)

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

### 6. Configure Performance (Optional)

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

### 7. Configure CORS (Optional)

For local development, default CORS settings allow `http://localhost:5173` and `http://localhost:3000`. To customize:

```bash
# Comma-separated list of allowed origins
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Or as JSON array
CORS_ORIGINS='["http://localhost:5173","http://localhost:3000"]'
```

**⚠️ Important:** For production deployments, see [DEPLOYMENT.md](DEPLOYMENT.md) for secure CORS configuration.

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

Then open <http://localhost:5173> in your browser.

## Environment Variables Reference

### Required Variables

- `OPENROUTER_API_KEY` - Your OpenRouter API key
- `ENCRYPTION_KEY` - Fernet encryption key for storing API credentials

### Optional Variables

#### API Configuration

- `CHAIRMAN_MODEL` - Model for synthesizing final responses (overrides UI setting)
- `TITLE_GENERATION_MODEL` - Model for generating conversation titles (overrides UI setting)

#### Personalities

- `COUNCIL_PERSONALITIES_DIR` - Directory containing personality YAML files (default: `data/personalities`)
- `COUNCIL_PERSONALITIES_ACTIVE` - JSON array or comma-separated list of active personality IDs

#### Performance

- `MAX_CONCURRENT_REQUESTS` - Maximum concurrent API requests (default: `4`)
- `LLM_REQUEST_TIMEOUT` - Timeout for API requests in seconds (default: `180.0`)
- `LLM_MAX_RETRIES` - Number of retries for failed requests (default: `3`)

#### Logging

- `LOG_LEVEL` - Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (default: `INFO`)
- `LOG_DIR` - Directory for log files (default: `logs`)
- `LOG_FILE` - Path to log file (default: `logs/llm_council.log`)

#### CORS

- `CORS_ORIGINS` - Comma-separated origins or JSON array (default: `http://localhost:5173,http://localhost:3000`)
- `CORS_METHODS` - Allowed HTTP methods (default: `*`)
- `CORS_HEADERS` - Allowed headers (default: `*`)
- `CORS_CREDENTIALS` - Allow credentials (default: `true`)

#### Server

- `PORT` - Backend server port (default: `8001`)

## Next Steps

- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if you encounter issues
- See [ADMIN_GUIDE.md](ADMIN_GUIDE.md) for multi-user and admin features
- See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for development setup
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
