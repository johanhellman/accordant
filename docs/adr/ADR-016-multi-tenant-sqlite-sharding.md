# ADR-016: Multi-Tenant SQLite Sharding Strategy

## Status
Accepted

## Context
The application was previously architected to use a Monolithic SQLite database (ADR-010) after moving away from JSON file storage (ADR-003). While this improved transactional integrity, it introduced new risks regarding write concurrency and data isolation as the system scales. 

We identified that a single SQLite file would become a bottleneck (global write lock) and a security risk (logical isolation only). To support a robust multi-tenant system where organizations are strictly isolated, we need a physical separation of data.

## Decision
We will adopt a **Physically Sharded SQLite Architecture**.

1.  **System Database (`system.db`)**: 
    *   Stores global, low-churn data: `Users`, `Organizations`.
    *   Handlers authentication and routing.
    *   Location: `data/system.db`

2.  **Tenant Databases (`tenant.db`)**: 
    *   Stores high-volume, privatedata: `Conversations`, `Messages`.
    *   Strictly one database per Organization.
    *   Location: `data/organizations/{org_id}/tenant.db`

3.  **Message Normalization**:
    *   We will move away from storing messages as a JSON blob.
    *   Messages will be stored in a normalized `messages` table within the Tenant DB.

## Consequences

### Positive
*   **Strict Isolation**: It is physically impossible for a SQL injection or logic bug in a chat query to leak data from another organization, as the database connection is scoped to a specific file.
*   **Concurrency**: Write operations in Organization A do not block Organization B.
*   **Scalability**: Backups, restores, and deletions can be managed per-tenant.

### Negative
*   **Logical Foreign Keys**: We cannot enforce Database-level Foreign Keys between `Users` (System DB) and `Conversations` (Tenant DB). Consistency must be managed by application logic.
*   **Complexity**: The backend must manage a registry of active database engines/sessions rather than a single global `SessionLocal`.

## Implementation Details
*   **Router**: A database utility will inspect the `org_id` context and return the appropriate `Session` bound to the correct `sqlite` file.
*   **Key Management**: The Router is responsible for ensuring the tenant DB exists and schemas are applied on first access.
