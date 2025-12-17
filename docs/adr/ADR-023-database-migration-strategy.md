# ADR-023: Database Migration Strategy

## Status
Accepted

## Date
2025-12-17

## Context
Accordant uses a hybrid database architecture:
1.  **System Database (`system.db`)**: Stores Users and Organizations. Shared specific schema.
2.  **Tenant Databases (`org_XXX/tenant.db`)**: Stores Conversations and Messages. One independent SQLite file per tenant.

As the schema evolves, we need a reliable way to apply changes to both database types.
*   **System DB**: Can be managed like a traditional monolithic DB.
*   **Tenant DBs**: Are created dynamically and exist in large numbers. Running a centralized migration tool against thousands of SQLite files is inefficient.

## Decision
We adopted a **Hybrid Migration Strategy**:

### 1. System Database: Alembic
We use [Alembic](https://alembic.sqlalchemy.org/) for the System Database.
*   **Why**: Standard tool, supports schema versioning, specific upgrade/downgrade paths.
*   **Workflow**:
    *   Developers modify `backend.models`.
    *   Run `alembic revision --autogenerate`.
    *   Review script.
    *   Deploy: `alembic upgrade head` runs on startup or via deployment script.

### 2. Tenant Databases: Migrate-on-Connect
We use a lightweight **Migrate-on-Connect** pattern for Tenant Databases.
*   **Why**: Each tenant DB is independent. Migration should happen when the tenant is accessed, distributing the load and ensuring isolation.
*   **Mechanism**:
    *   `backend.tenant_migrations.apply_tenant_migrations(engine)` is called whenever a connection to a tenant DB is established (`get_tenant_engine`).
    *   A custom `TENANT_MIGRATIONS` list in code defines steps (SQL statements).
    *   SQLite `PRAGMA user_version` is used to track the current schema version of each file.
*   **Safety**: Steps are transactional per database.

## Consequences
### Positive
*   **Scalability**: Tenant migrations are decentralized; no central downtime.
*   **Safety**: System DB is versioned professionally with Alembic.
*   **Simplicity**: No need for a complex "tenant registry" loop to migrate all tenants at once.

### Negative
*   **Latency**: First request to a tenant after a deployment might be slightly slower due to migration (maintenance cost is low for SQLite).
*   **Complexity**: Two different ways to manage schema changes (Alembic vs Custom).

## References
*   `backend/tenant_migrations.py`
*   `alembic.ini`
