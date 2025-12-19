# Design Document: Consensus Strategy Management

**Status**: Draft
**Date**: 2025-12-19
**Context**: Feature Planning
**Related**: ADR-026 (Configuration Packs)

## 1. Problem Statement
Currently, **Consensus Strategies** (the "Chief of Staff" prompts that drive Stage 3 synthesis) are hardcoded as static Markdown files in `data/defaults/consensus/`. 

*   **Instance Admins** have no UI to modify the system defaults without redeploying/committing code.
*   **Organization Admins** cannot create custom strategies (e.g., "Legal Review", "Creative Writing") specific to their tenant.

## 2. Proposed Solution
We will adopt the same **Hybrid Storage Pattern** used for Council Packs and Personalities.

### 2.1. Storage Hierarchy

1.  **System Strategies (Global)**
    *   **Source**: `data/defaults/consensus/*.md`
    *   **Access**: Read-only for Tenants. Read/Write for Instance Admins (via API).
    *   **Management**: GitOps (File edits) OR Instance Admin API.

2.  **Custom Strategies (Tenant-Scoped)**
    *   **Source**: `tenant.db` -> `consensus_strategies` table.
    *   **Access**: Read/Write for Org Admins.
    *   **Isolation**: Strictly scoped to the tenant database.

## 3. Data Model

### 3.1. Database Schema (`tenant.db`)
New table `consensus_strategies`:

```sql
CREATE TABLE consensus_strategies (
    id TEXT PRIMARY KEY,          -- UUID or Slug (must be unique vs system ones)
    display_name TEXT NOT NULL,
    description TEXT,
    prompt_content TEXT NOT NULL, -- The actual instructional prompt
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2. API Resource Model
Unified object returned to frontend:

```json
{
  "id": "risk_averse",
  "display_name": "Risk Averse",
  "description": "Focuses on potential downsides...",
  "prompt_content": "...",
  "source": "system",  // or "custom"
  "is_editable": false // true if source=custom OR user=instance_admin
}
```

## 4. Architecture Changes

### 4.1. New Service: `ConsensusStrategyService`
Will replace the simple `backend/config/prompts.py` functions.

*   `get_all_strategies(session, org_id)`: Merges default files + DB rows.
*   `get_strategy(session, id)`: Resolves content from DB -> Files.
*   `create_custom_strategy(...)`: Writes to DB.
*   `update_strategy(...)`: Updates DB (if custom) or File (if System + Instance Admin).

### 4.2. API Endpoints (`/api/config/strategies`)

*   `GET /`: List all (Meta only) - *Update existing endpoint*
*   `POST /`: Create Custom Strategy (Org Admin)
*   `GET /{id}`: Get full details + content
*   `PUT /{id}`: Update content (RBAC protected)
*   `DELETE /{id}`: Delete (Custom only)

## 5. Implementation Plan

### Phase 1: Backend
1.  **Migration**: Add `consensus_strategies` to `tenant.db`.
2.  **Service**: Implement `StrategyService`.
3.  **API**: Expand `config_routes.py` to support CRUD.
4.  **Refactor**: Update `council.py` / `ConsensusService` to use `StrategyService` for prompt resolution.

### Phase 2: Frontend
1.  **Admin Nav**: Add "Consensus Strategies" under the "Configuration" group (alongside "Personalities").
    *   *Rationale*: Keep configuration assets grouped together.
2.  **Settings Page**: Add "Strategies" tab to Admin Dashboard.
3.  **Editor**: Simple Markdown editor for prompts.
4.  **Selector**: Update Pack Creator to show descriptions of strategies.
