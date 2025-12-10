# ADR 016: Migration to SQLite

## Status
Accepted (Supersedes [ADR-003](ADR-003-json-file-storage.md))

## Context
The application initially used JSON files for data persistence (ADR-003) to keep the architecture simple and lightweight. However, as the application evolved into a public-facing multi-user service, critical limitations emerged:
1.  **Lack of ACID Transactions**: Complex operations like "register user and create organization" could fail halfway, leaving the system in an inconsistent "split-brain" state (orphaned users).
2.  **Concurrency Issues**: Simultaneous writes resulted in race conditions and data loss.
3.  **Data Integrity**: No enforcement of foreign key constraints (e.g., users existing without organizations).

## Decision
We will migrate the persistence layer from JSON files to **SQLite**.

### Key Changes
1.  **Database**: Use `accordant.db` (SQLite) instead of `data/*.json`.
2.  **ORM**: Use **SQLAlchemy** for data modeling and interactions.
3.  **Schema**:
    *   `users` table
    *   `organizations` table
    *   `conversations` table
4.  **Atomics**: All state-changing operations (especially registration) must be wrapped in transactions.
5.  **Legacy Data**: Existing JSON data will be purged (Clean Slate) as part of this transition, as authorized for this test phase.

## Consequences

### Positive
*   **Data Integrity**: ACID transactions prevent partial failure states.
*   **Concurrency**: SQLite handles concurrent readers/writers significantly better than raw file I/O.
*   **Reliability**: Foreign key constraints enforce valid relationships between Users and Orgs.
*   **Simplicity**: Retains the "single file" deployment benefit of SQLite (no separate DB server required).

### Negative
*   **Introspectability**: Data is no longer directly readable/editable as plain text files (requires SQLite client).
