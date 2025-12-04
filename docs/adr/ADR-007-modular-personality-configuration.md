# ADR-007: Modular Personality Configuration

**Status**: Accepted  
**Date**: 2025-11-26  
**Deciders**: Project Team  
**Supersedes**: Part of ADR-005 (Storage Mechanism)

## Context

The initial implementation of "Personality Mode" (ADR-005) stored all personality definitions in a single `personalities.yaml` file. As the number of personalities grew (e.g., 16+ distinct personas), this file became large and difficult to manage.

Challenges included:
-   **Maintainability**: Editing a single large file is error-prone.
-   **Scalability**: Adding new personalities required modifying the central file.
-   **Granularity**: Enabling/disabling specific personalities required commenting out blocks of code or complex environment variable management.
-   **System Prompts**: Global system prompts were hardcoded or mixed with personality data.

## Decision

We decided to restructure the personality configuration into a modular, directory-based system.

1.  **Directory Structure**: Create a `data/personalities/` directory to house all personality configurations.
2.  **Individual Files**: Each personality is defined in its own YAML file (e.g., `gpt_ceo.yaml`, `claude_ethicist.yaml`).
3.  **System Prompts**: Extract global system prompts (Base, Chairman, Title Generation) into a dedicated `data/personalities/system-prompts.yaml` file.
4.  **Enabled Flag**: Add an `enabled: boolean` field to personality definitions to allow easy toggling without deleting files.
5.  **Configuration Loading**: Update `backend/config.py` to scan the directory and load all valid, enabled personality files.

## Consequences

### Positive
-   **Improved Maintainability**: Personalities are isolated; errors in one file don't break others.
-   **Scalability**: Easy to add new personalities by simply dropping a new YAML file into the directory.
-   **Better UX**: Users can easily enable/disable personalities via the `enabled` flag.
-   **Separation of Concerns**: Global system prompts are separated from individual personality data.
-   **Git Friendly**: Easier to track changes to specific personalities.

### Negative
-   **File Management**: More files to manage in the file system.
-   **Loading Logic**: Slightly more complex initialization logic (directory scanning vs. single file read).

### Neutral
-   The `COUNCIL_PERSONALITIES_DIR` environment variable now points to the directory instead of a single file.
-   `COUNCIL_PERSONALITIES_ACTIVE` can still be used to filter the loaded personalities.
