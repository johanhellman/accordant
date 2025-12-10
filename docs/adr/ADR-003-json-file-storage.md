# ADR-003: JSON-Based File Storage

**Status**: Superseded by [ADR-016](016-sqlite-migration.md)  
**Date**: 2025-11-25  
**Deciders**: Project Team

## Context

The application needs to persist conversation data. We considered several options:

- SQLite database
- PostgreSQL/MySQL
- JSON files
- NoSQL databases (MongoDB, etc.)

Given the project's scope (local web app, single-user focused) and simplicity requirements, we needed a lightweight solution.

## Decision

We will use JSON file-based storage:

- Each conversation stored as a separate JSON file in `data/conversations/`
- File naming: `{conversation_id}.json`
- Voting history stored in `data/voting_history.json`
- All storage operations are synchronous file I/O

## Consequences

### Positive

- **Simplicity**: No database setup or migrations required
- **Portability**: Easy to backup, move, or inspect data
- **Human-Readable**: JSON files can be edited/viewed directly
- **No Dependencies**: Uses only Python standard library for file operations

### Negative

- **No Concurrency**: File-based storage doesn't handle concurrent writes well
- **No Querying**: Can't efficiently query across conversations
- **Scalability Limits**: Not suitable for high-volume or multi-user scenarios
- **No Transactions**: No atomic operations or rollback capability

### Neutral

- Storage directory is gitignored (see `.gitignore`)
- Files are created on-demand when conversations are created
- See `backend/storage.py` for implementation

## Implementation Notes

- `ensure_data_dir()` creates the data directory if it doesn't exist
- Conversation structure: `{id, created_at, title, messages[]}`
- Assistant messages include `{role, stage1, stage2, stage3}` structure
- Metadata (label_to_model, aggregate_rankings) is NOT persisted, only returned via API
