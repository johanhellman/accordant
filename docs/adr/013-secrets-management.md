# ADR 013: Secrets Management

## Status

Accepted

## Context

With the move to multi-tenancy, each organization must configure its own LLM API keys and Gateway URLs. Storing these sensitive credentials in plain text in the file system (JSON files) poses a security risk.

## Decision

We decided to use symmetric encryption for storing sensitive configuration values at rest.

1. **Encryption Algorithm**: Fernet (symmetric encryption) from the `cryptography` library.
2. **Key Management**: The master encryption key is provided via the `ENCRYPTION_KEY` environment variable. This key must be kept secret and secure.
3. **Storage**: API keys are encrypted before being written to `data/organizations.json` (in the `api_config` field).
4. **Runtime**: Keys are decrypted only in memory when needed to make an LLM API call.
5. **API Exposure**: The Admin API never returns the full API key. It returns a masked version (e.g., `********`) to indicate a key is set.

## Consequences

### Positive

- **Security**: Sensitive keys are not readable if the storage file is compromised (without the master key).
- **Compliance**: Meets basic security best practices for credential storage.

### Negative

- **Dependency**: Adds a dependency on `cryptography`.
- **Key Management**: Losing the `ENCRYPTION_KEY` renders all stored API keys unrecoverable (requiring re-entry).
