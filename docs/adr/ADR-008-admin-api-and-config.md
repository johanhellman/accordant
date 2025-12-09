# ADR-008: Admin API and Configuration Precedence

**Status**: Accepted
**Date**: 2025-11-26
**Deciders**: Project Team

## Context

Users need to manage personalities and system prompts via a UI. This requires an API to read and write these configurations. Additionally, we need to clarify how configuration changes made via the UI interact with existing environment variable configurations, especially for model selection.

## Decision

### 1. Admin API

We will expose a set of REST endpoints under `/api` to manage:

- Personalities (CRUD)
- System Prompts (Read/Update)
- Model Discovery (Read)

These endpoints will read/write directly to the YAML files in `data/personalities/`.

### 2. Configuration Precedence

To support both easy UI-based configuration and robust deployment-based configuration, we establish the following precedence rule for model selection (`CHAIRMAN_MODEL`, `TITLE_GENERATION_MODEL`):

1. **Environment Variables**: Highest priority. If `CHAIRMAN_MODEL` is set in `.env` or the process environment, it overrides everything else. This ensures production deployments can enforce specific models.
2. **File Configuration**: If no env var is set, the value from `data/personalities/system-prompts.yaml` is used. This allows the UI to control the setting in a default local environment.
3. **Hardcoded Defaults**: If neither is set, the application falls back to safe defaults defined in code.

### 3. Secrets Management

API Keys and other secrets will **NOT** be exposed or editable via the Admin API. They must remain in environment variables for security.

## Consequences

### Positive

- **Usability**: Users can manage the system via a GUI.
- **Flexibility**: Deployment overrides are still possible.
- **Security**: Secrets are not exposed.

### Negative

- **Complexity**: The configuration loading logic becomes slightly more complex to handle the precedence.
- **User Confusion**: Users might try to change a setting in the UI that is being overridden by an env var. The UI needs to communicate this state clearly.
