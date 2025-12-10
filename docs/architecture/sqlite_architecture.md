# SQLite Architecture & Audit Record

**Last Updated:** 2025-12-10
**Status:** Living Document

## 1. Architectural Decisions

### 1.1 Database Engine: SQLite
*   **Reasoning:** Chosen for simplicity, zero-configuration, and self-contained nature (single file).
*   **Trade-off:** Single-writer concurrency limit.
*   **Mitigation:** `WAL` mode (Write-Ahead Logging) should be enabled for better concurrency.
*   **Future Path:** Migration to PostgreSQL if concurrent write load exceeds ~10-20 users.

### 1.2 Multi-tenancy
*   **Strategy:** Row-level security via `org_id` column on all major tables (`users`, `conversations`).
*   **Enforcement:** Application logic (backend routes) strictly enforces strict ownership checks.
*   **Alternative Considered:** One Database per User.
    *   *Decision:* Rejected for now. While it offers perfect isolation, managing thousands of database files creates significant operational complexity (file descriptors, backups, global analytics).
    *   *Future Option:* One Database per *Organization* is a viable middle-ground for sharding if a single organization grows too large or if we need stricter physical isolation.

## 2. Data Structure & Schema Warnings

### ⚠️ Primary Keys: UUIDs
We use string UUIDs for primary keys (`id`).
*   **Impact:** Slightly slower indexing and larger storage footprint compared to integers.
*   **Decision:** Acceptable for distributed ID generation and safety. No action required.

### ⚠️ Search Capability
No Full-Text Search (FTS) is currently implemented.
*   **Impact:** Searching inside conversation history requires full table scans.
*   **Status:** Not a current requirement.
*   **TODO:** Implement SQLite FTS5 extension or external search engine (Meilisearch) when search becomes a feature requirement.

## 3. Performance & Scalability Risks

### 🛑 Single SQLite File Growth
*   **Risk:** Storing all message history in `accordant.db` will cause the file to grow rapidly.
*   **Monitoring:** Monitor the `.db` file size.
*   **Threshold:** If file size exceeds 1-2GB, backup times and "vacuum" operations may impact availability.

### 🛑 Concurrency Bottlenecks (The "Writer Lock")
*   **Risk:** SQLite allows only one writer at a time. High concurrent chat traffic may lead to `database is locked` errors.
*   **Monitoring:** Log the time taken for write operations. If `commit()` times exceed 500ms consistently, or if "database locked" exceptions occur, it is time to migrate.

## 4. Security Hardening

### 🔐 Encryption Key Persistence
*   **Scenario:** If the server starts without an `ENCRYPTION_KEY` env var, it generates a random temporary key.
*   **Risk:** In Production, if the container restarts with a new random key, it will lose access to all previously encrypted secrets (API keys), effectively corrupting the data state.
*   **Policy:** The application MUST crash (fail fast) in Production if `ENCRYPTION_KEY` is missing.

### 🔐 Bulk Deletion Safety
*   **Risk:** Administrative delete functions relying solely on `user_id`.
*   **Policy:** All delete operations must strictly include `org_id` in the `WHERE` clause as a defense-in-depth measure against ID collisions or logic bugs.
