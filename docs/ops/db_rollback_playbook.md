# Database Rollback Playbook

## Overview
This guide describes how to rollback database schema changes in the event of a failed deployment or critical bug caused by a migration.

## System Database (`system.db`)

The System Database is managed by **Alembic**.

### Check Current Version
```bash
uv run alembic current
```

### Rollback to Previous Version
To undo the last migration (step down 1 revision):
```bash
uv run alembic downgrade -1
```

To rollback to a specific revision (e.g., `a1b2c3d4`):
```bash
uv run alembic downgrade a1b2c3d4
```

### Emergency Restore
If Alembic fails to downgrade (e.g., data corruption):
1.  Stop the application.
2.  Restore `data/system.db` from the backup taken before deployment.
    *   *Note: Ensure backups are configured in your production environment.*

## Tenant Databases (`tenant.db`)

Tenant Databases use **Migrate-on-Connect** and do **NOT** support automatic downgrades. SQLite `ALTER TABLE` operations are often irreversible or complex to revert automatically.

### Strategy
1.  **Forward Fix**: If a migration introduces a bug, prefer pushing a **new migration** that fixes it (e.g., reverting a column change by renaming/copying).
2.  **Restore from Backup**: If data is corrupted, you must restore the specific `tenant.db` file from backup.

### Manual Rollback (Expert Only)
If you must manually revert a schema change on a specific tenant DB:
1.  Access the server.
2.  Open the DB: `sqlite3 data/organizations/{org_id}/tenant.db`
3.  Manually execute SQL to revert changes (e.g., `ALTER TABLE drop column...` - note SQLite limitations).
4.  Reset the version: `PRAGMA user_version = {previous_version};`
