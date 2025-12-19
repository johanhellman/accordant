# Design Document: Council Packs

**Status**: Draft
**Date**: 2025-12-19
**Author**: Antigravity (AI Assistant)
**Context**: Feature Planning

## 1. Context & Problem Statement

Currently, users must manually configure their Council by:
1.  Enabling/Disabling individual personalities.
2.  Selecting a Consensus Strategy (if implemented in UI).
3.  Potentially modifying system prompts for specific use cases.

**Note on Consensus Strategies**: Currently, strategies are defined as System Prompts (Markdown files) in `data/defaults/consensus/*.md`. There is no UI to edit them directly.

This strictly manual process makes it difficult to switch between different "modes" of operation. For example, switching from a **"Brainstorming"** setup (Creative personalities, Novelty-seeking consensus) to a **"Risk Assessment"** setup (Skeptical personalities, Risk-Averse consensus) requires many clicks and intimate knowledge of which personalities fit which role.

## 2. Proposed Solution: Council Packs

A **Council Pack** is a predefined configuration bundle that instantly sets up the Council for a specific purpose. It follows a hybrid data pattern:

1.  **System Packs**: Default packs provided by the instance (read-only code-as-config).
2.  **Custom Packs**: User-created packs stored in the tenant database.

It encapsulates:
1.  **The Team**: A specific set of enabled personalities.
2.  **The Strategy**: A specific Consensus Strategy (e.g., `balanced`, `risk_averse`, `creative`).
3.  **The Context**: (Optional) Overrides for system prompts to set a global tone or context.

**Safe-Fail Integrity**:
*   **Updates**: Packs reference personalities by ID. Updates to the underlying personality YAML are automatically reflected.
*   **Deletes**: If a Pack references a missing personality ID (e.g., file deleted), that ID is **ignored** at runtime. The Council proceeds with the remaining valid personalities. This prevents "broken" packs from blocking the system.

### 2.1. User Stories
*   "As a user, I want to one-click switch to 'Coding Mode' so that I have the Architect, Hacker, and QA personalities enabled without manually toggling them."
*   "As a user, I want a 'Red Team' pack that enables critical personalities and sets the consensus strategy to 'Find Flaws'."
*   "As a user, I want to create my own pack based on my current configuration."

## 3. Data Model & Schema

We will introduce a new entity: `CouncilPack`.

### 3.1. Hybrid Storage Hierarchy

To align with **ADR-016 (Multi-Tenant SQLite Sharding)** and **ADR-017**:

*   **System Defaults**: `data/defaults/packs/*.yaml` (Filesystem)
    *   Immutable templates available to all organizations.
    *   Loaded into memory at startup.
*   **Organization Custom**: `tenant.db` -> `council_packs` (Database)
    *   Created by Org Admins.
    *   Stored strictly within the tenant's isolated shard.

### 3.2. Database Schema (Tenant DB)

We will introduce two new tables in `tenant.db`:

#### `council_packs`
Stores the definition of custom packs.

```sql
CREATE TABLE council_packs (
    id TEXT PRIMARY KEY,           -- UUID
    display_name TEXT NOT NULL,
    description TEXT,
    
    -- Serialized configuration
    -- Contains: { "personalities": [ids], "consensus_strategy": "strat_id", "system_prompts": {...} }
    config_json TEXT NOT NULL, 
    
    is_system BOOLEAN DEFAULT FALSE, -- Future proofing, currently FALSE for all DB rows
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `council_configuration`
Stores the **Active Runtime State** for the Council. This moves runtime toggles out of the System DB (`Organization.settings`) into the Tenant DB.

**Update (Per-User Configuration)**:
We will scope the active configuration to the `user_id`. This allows different users in the same organization to have different active packs (e.g., User A is Brainstorming, User B is Debugging).

```sql
CREATE TABLE council_configuration (
    user_id TEXT PRIMARY KEY,      -- User ID (from System DB, logical link)
    active_pack_id TEXT,           -- Reference to a pack (System or Custom)
    
    -- The actual active settings (snapshot)
    -- This allows "drift" from the pack if the user manually toggles a personality after applying
    active_personalities_json TEXT, -- List of enabled IDs
    active_strategy_id TEXT,
    active_system_prompts_json TEXT,
    
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.3. System Pack YAML Schema (Filesystem)

```yaml
id: creative_brainstorming
display_name: "Creative Brainstorming Team"
description: "A group of divergent thinkers designed to generate novel ideas."

# 1. Personalities to Enable (References IDs in data/defaults/personalities/)
personalities:
  - gpt_creative
  - claude_poet
  - gemini_futurist

# 2. Consensus Strategy
consensus_strategy: novelty_focus 

# 3. System Prompt Overrides
system_prompts:
  stage1_meta_structure: |
    IMPORTANT context: You are in a brainstorming session.
```

## 4. Backend Architecture Changes

### 4.1. New Module: `backend/packs.py`
Responsible for:
*   `PackService`:
    *   `get_all_packs(session)`: Merges System Packs (YAML) + Custom Packs (SQL).
    *   `apply_pack(session, user_id, pack_id)`: writes to `council_configuration` for that user.
    *   `create_custom_pack(session, name, config)`: writes to `council_packs`.

### 4.2. API Endpoints (`backend/org_routes.py` or new `backend/config_routes.py`)

*   `GET /api/config/packs`: List all available packs.
*   `POST /api/config/packs`: Create a Custom Pack (from current state or scratch).
*   `POST /api/config/packs/{pack_id}/apply`: Apply a pack (Updates `council_configuration` for current user).
*   `GET /api/config/active`: Get current active personalities/strategy for current user.
*   `GET /api/config/strategies`: List all available consensus strategies (dynamic from file system).

### 4.3. Impact on `council.py`
The `run_council_cycle` currently reads from `backend/config.py`.
*   **Refactor**: It must now inject a `ConfigurationService` or read from `tenant.db` using the session and `user_id`.
*   **Fallback**: If no config user exists, use a default fallback (All System Personalities Enabled).

## 5. Frontend / UX

1.  **Pack Gallery**:
    *   Cards for System Packs (Gold border) and Custom Packs.
    *   "Apply" button.
    *   "Clone" button on System Packs (creates a Custom copy).
2.  **Active State Indicator**:
    *   "Current Pack: [Name]"
    *   If user manually toggles a switch: "Current Pack: [Name] (Modified)"
3.  **Create Pack Flow**:
    *   "Save Current Setup as Pack" button.

## 6. Migration & Compatibility
*   **Migration**: New migration script for `tenant.db` to create tables.
*   **Backwards Compatibility**: Existing `Organization.settings` usage for `enabled_personalities` will be deprecated. The first time a user accesses the system, we will migrate them to a default pack if no config exists.

## 7. Implementation Steps
1.  **Documentation**: ADR-026 (Configuration Packs).
2.  **Backend**: Create `council_packs` and `council_configuration` tables (Migration).
3.  **Backend**: Implement `PackService` to read YAMLs + SQL.
4.  **Backend**: Implement "Apply" logic (writing to config table).
5.  **Refactor**: Update `council.py` to read from DB Config instead of File/Env var defaults.
6.  **Frontend**: Build Pack Gallery UI.
