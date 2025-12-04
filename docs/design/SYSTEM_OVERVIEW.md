# LLM Council System Overview

This document provides a high-level overview of the LLM Council system architecture, data flow, and component interactions.

## System Architecture

LLM Council is a 3-stage deliberation system where multiple LLMs collaboratively answer user questions through a structured peer review process.

### High-Level Flow

```
User Query
    ↓
Stage 1: Parallel queries → [individual responses]
    ↓
Stage 2: Anonymize → Parallel ranking queries → [evaluations + parsed rankings]
    ↓
Aggregate Rankings Calculation → [sorted by avg position]
    ↓
Stage 3: Chairman synthesis with full context
    ↓
Return: {stage1, stage2, stage3, metadata}
    ↓
Frontend: Display with tabs + validation UI
```

The entire flow is async/parallel where possible to minimize latency.

### 2. Backend (FastAPI)

The backend exposes a REST API for:
- **Chat**: Handling user queries and orchestrating the 3-stage process.
- **Admin**: Managing personalities, system prompts, and configuration.
- **History**: Retrieving past conversations.

Key modules:
- `main.py`: FastAPI application entry point and route registration.
- `council.py`: Core logic for the 3-stage deliberation process.
- `admin_routes.py`: Endpoints for managing personalities and system prompts.
- `llm_service.py`: Service for discovering available models from the provider.
- `config.py`: Configuration management (Env vars, YAML files).
- `storage.py`: JSON-based persistence for conversations.

### 3. Frontend (React)

A single-page application (SPA) built with React and Vite.

Key components:
- **ChatInterface**: The main view for interacting with the council.
- **PersonalityManager**: UI for creating and managing LLM personalities.
- **SystemPromptsEditor**: UI for configuring global prompts and council roles.
- **Sidebar**: Navigation and conversation history.

## Component Architecture

### Backend Components

- **`main.py`**: FastAPI application, handles HTTP requests and streaming responses
- **`council.py`**: Core 3-stage deliberation logic
- **`openrouter.py`**: LLM API client abstraction (OpenRouter/LiteLLM)
- **`storage.py`**: JSON-based conversation persistence
- **`config.py`**: Model configuration and environment variable management
- **`voting_history.py`**: Voting history tracking and analytics
- **`logging_config.py`**: Centralized logging configuration

### Frontend Components

- **`App.jsx`**: Main application orchestration and state management
- **`ChatInterface.jsx`**: Message input and display
- **`Stage1.jsx`**: Individual model response tabs
- **`Stage2.jsx`**: Peer review rankings with de-anonymization
- **`Stage3.jsx`**: Final synthesized answer display
- **`Sidebar.jsx`**: Conversation list and navigation

## Key Design Principles

1. **Anonymized Peer Review**: Stage 2 responses are anonymized to prevent bias
2. **Graceful Degradation**: System continues with successful responses if some models fail
3. **Transparency**: All raw outputs are inspectable by users
4. **Context Efficiency**: Only user queries and final answers are included in conversation history

## Data Models

### Conversation Structure
```json
{
  "id": "uuid",
  "created_at": "ISO timestamp",
  "messages": [
    {
      "role": "user",
      "content": "..."
    },
    {
      "role": "assistant",
      "stage1": {...},
      "stage2": {...},
      "stage3": "..."
    }
  ]
}
```

### Metadata (Ephemeral, not persisted)
- `label_to_model`: Mapping from anonymous labels to model identifiers
- `aggregate_rankings`: Calculated average rankings across all peer evaluations

## Related Documentation

- [Architecture Decision Records](../adr/ADR_INDEX.md) - Detailed architectural decisions
- [API Documentation](../api/API_SURFACE.md) - Complete API reference
- [Developer Guide](../DEVELOPER_GUIDE.md) - Implementation notes and developer guide

