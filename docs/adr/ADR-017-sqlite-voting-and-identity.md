# ADR-017: SQLite Voting Storage & UUID Identity

## Status
Accepted

## Context
The system previously stored voting history in JSON files (`voting_history.json`) and relied on Personality Names as primary identifiers. This led to several issues:
1.  **Concurrency**: JSON file writes are not safe under high load.
2.  **Identity Ambiguity**: Multiple personalities with the same name caused "double counting" of votes and incorrect ranking aggregation.
3.  **Data Isolation**: JSON files complicate the strict physical separation pattern established in [ADR-016](ADR-016-multi-tenant-sqlite-sharding.md).

## Decision

### 1. Voting History in Tenant Database
We will move the storage of voting history from JSON files to the **Tenant SQLite Database** (`tenant.db`).
- A new `votes` table will be created.
- This ensures transactional integrity and strict per-organization isolation.

### 2. UUID-Based Identity
We will enforce the use of **UUIDs** (`id`) as the primary key for all personality logic (Voting, Ranking, Council execution).
- The `name` field will be used strictly for display and will no longer affect data aggregation.
- Uniqueness of names is *not* enforced; duplicate names are allowed but will be tracked separately via their UUIDs.

### 3. Qualitative Feedback Storage
Contrary to the initial [ADR-015](ADR-015-federated-voting-privacy.md), we *will* store the qualitative reasoning text in the `votes` table within the Tenant DB.
- **Justification**: Storing it alongside the vote simplifies the feedback synthesis loop significantly.
- **Privacy**: Since the Tenant DB is physically isolated per organization, the privacy guarantees of "Instance Admins cannot seeing private thoughts" are maintained (Instance Admins do not mount Tenant DBs).

## Consequences

### Positive
*   **Correctness**: Eliminates vote double-counting and ranking bugs caused by name collisions.
*   **Consistency**: Aligns all persistent data storage with the SQLite Multi-Tenant architecture.
*   **Performance**: SQL queries for league tables are more efficient than parsing large JSON arrays.

### Negative
*   **Breaking Change**: Existing voting history in JSON format will be **discarded**. We are not writing a migration script for the legacy data.
*   **Complexity**: SQL queries are slightly more complex to write than simple list comprehensions.

## References
*   Refines [ADR-015](ADR-015-federated-voting-privacy.md)
*   Implements [ADR-016](ADR-016-multi-tenant-sqlite-sharding.md)
