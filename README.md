# Accordant LLM Council ![Version](https://img.shields.io/badge/version-0.2.0-blue)

Instead of asking a question to a single LLM, **Accordant** lets you create a Council of multiple LLM personalities that collaborate through a structured deliberation process. Each personality provides their perspective, reviews others' work anonymously, and a Chairman synthesizes the final response.

## How It Works

Accordant uses a 3-stage deliberation process:

1. **Stage 1: First Opinions** - Your query is sent to all personalities in parallel. Each provides their individual response, which you can inspect in a tabbed view.

2. **Stage 2: Review** - Each personality reviews the others' responses (anonymized to prevent bias) and ranks them by accuracy and insight. This creates a transparent peer review process.

3. **Stage 3: Final Response** - The designated Chairman synthesizes all responses and rankings into a single, comprehensive answer.

## Key Features

- **Multi-Personality Council**: Define custom personalities with their own models, prompts, and voices
- **Anonymized Peer Review**: Stage 2 prevents models from playing favorites by anonymizing responses
- **Multi-Tenant Architecture**: Support for multiple organizations with isolated data and settings
- **Multi-User Support**: Each user has their own conversation history within their organization
- **Voting History**: Track how personalities vote and analyze consensus patterns over time
- **Fully Customizable**: Manage personalities, system prompts, and models through the UI or configuration files

## Quick Start

Get up and running in 5 minutes:

```bash
# 1. Install dependencies
uv sync
cd frontend && npm install && cd ..

# 2. Configure API key
cp .env.example .env
# Edit .env and add: OPENROUTER_API_KEY=sk-or-v1-...

# 3. Generate encryption key (for multi-tenancy)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Add the output to .env as: ENCRYPTION_KEY=...

# 4. Start the application
# Standard Mode
./start.sh

# Docker Mode (Recommended)
docker compose up -d
# App available at http://localhost:8000
# Health check: http://localhost:8000/api/health
```

Then open http://localhost:5173 in your browser.

**Prerequisites:**
- Python 3.10+ and [uv](https://docs.astral.sh/uv/)
- Node.js v18+
- OpenRouter API key ([get one here](https://openrouter.ai/))

For detailed setup instructions, see [Setup Guide](docs/SETUP.md).

## Multi-Turn Conversations

The application supports multi-turn conversations. The Council remembers the context of the discussion, allowing you to ask follow-up questions.

**Note on Context:** To save tokens, the history passed to the models includes only the **User Queries** and the **Final Answers** (Stage 3). The internal deliberations (Stage 1 individual responses and Stage 2 rankings) are stripped from the history.

## Multi-User & Admin Features

- **User Isolation**: Each user has their own private conversation history
- **Multi-Organization**: Users belong to an Organization. Data is isolated per organization
- **Admin Roles**:
  - **Instance Admin**: Manages all organizations and system-wide settings
  - **Org Admin**: Manages users, settings (API Keys), and invitations within their organization

For detailed admin documentation, see [Admin Guide](docs/ADMIN_GUIDE.md).

## Tech Stack

- **Backend:** FastAPI (Python 3.10+), async httpx, OpenRouter API
- **Frontend:** React + Vite, react-markdown for rendering
- **Storage:** JSON files in `data/conversations/` (per organization)
- **Package Management:** uv for Python, npm for JavaScript

## Documentation

### For Users
- **[Setup Guide](docs/SETUP.md)** - Complete setup and configuration instructions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Admin Guide](docs/ADMIN_GUIDE.md)** - Multi-user and admin features

### For Developers
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Implementation details, gotchas, and development notes
- **[Architecture Decision Records](docs/adr/ADR_INDEX.md)** - Key architectural decisions and rationale
- **[API Documentation](docs/api/API_SURFACE.md)** - Complete API reference
- **[System Overview](docs/design/SYSTEM_OVERVIEW.md)** - High-level architecture and component overview

### For Deployment
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment, security, and scaling

For more information, see [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## Vibe Code Alert

No line of code has been written in the traditional way. It's all been done through LLMs. Inspired by Jeff Sutherland's presentation at Crisp's [Leading Complexity](https://leadingcomplexity.com/program/) session on October 16th, 2025.

## Acknowledgements

This project was inspired by:
*   **Andrej Karpathy's [llm-council](https://github.com/karpathy/llm-council)**: The original inspiration for the multi-model council architecture.
*   **PewDiePie's [AI Council video](https://www.youtube.com/watch?v=qw4fDU18RcU)**: A conceptual exploration of the AI Council idea.
