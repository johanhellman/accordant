# Architecture Review: Council Packs Proposal

**Date**: 2025-12-19
**Target**: `docs/architecture/council-packs.md`
**Reviewer**: Antigravity

## Executive Summary

The "Council Packs" proposal introduces a valuable meta-configuration layer that significantly improves UX by bundling Personalities, Consensus Strategies, and Prompts.

However, the proposed **File-Based Storage** for Custom Packs (`data/organizations/{org_id}/packs/*.yaml`) conflicts with the architectural direction established in **ADR-016 (Multi-Tenant SQLite Sharding)** and **ADR-017**. While it mimics the existing Personalities structure (ADR-007), continuing to add user-generated data to the filesystem re-introduces concurrency risks and violates the strict data isolation principles of the sharded database architecture.

**Key Recommendation**: Adopt a **Database-First approach** for Custom Packs and Active Configuration, placing them within the `tenant.db`.

---

## Detailed Critique

### 1. Storage & Usage of `Organization.settings` (System DB vs Tenant DB)

**The Proposal**:
> Updates `Organization.settings` [in System DB] to set `enabled` flags, `consensus_strategy`, etc.

**Critique**:
*   **Availability/Isolation Risk**: `settings` essentially becomes the "Active Runtime State" for the Council. Storing this in `system.db` (Global) creates a tight runtime dependency between Tenant operations (Chat) and the System DB.
*   **ADR-016 Alignment**: ADR-016 defines `system.db` for "global, low-churn" data (Users, Orgs). Real-time configuration toggles (which might change frequently if users swap packs often) are better suited for the **Tenant DB**.
*   **Scalability**: A single JSON blob in `Organization.settings` is difficult to query or partially update without race conditions (User A toggles a personality while User B applies a Pack).

**Recommendation**:
*   Move the **Active Configuration** (which personalities are active, current strategy) into a `configuration` table (or similar) within `tenant.db`.
*   This ensures that a Tenant's runtime state is fully encapsulated within their shard.

### 2. Custom Packs Storage (Files vs Database)

**The Proposal**:
> **Organization Custom**: `data/organizations/{org_id}/packs/*.yaml`

**Critique**:
*   **Concurrency**: Writing YAML files from the backend requires file locking to prevent corruption during concurrent edits.
*   **Inconsistency**: **ADR-017** explicitly moved Voting History *away* from JSON files to SQLite to solve these exact issues. Re-introducing file storage for Packs is a regression.
*   **Complexity**: Managing "Shadowing" (overriding system files with custom files) file-system logic is brittle compared to SQL queries (e.g., `SELECT * FROM packs WHERE org_id = ? OR is_system = 1`).

**Recommendation**:
*   Create a `council_packs` table in `tenant.db`.
*   **Schema**:
    ```sql
    CREATE TABLE council_packs (
        id TEXT PRIMARY KEY,
        display_name TEXT NOT NULL,
        description TEXT,
        is_system BOOLEAN DEFAULT FALSE, -- If we replicate system packs to DB, or just use this for 'created by system'
        config_json TEXT NOT NULL, -- The definition (personalities, strategy, prompts)
        created_at DATETIME
    );
    ```
*   *Note*: System Packs can still be defined in YAML (code-as-config) but should perhaps be "seeded" into the DB or merged in memory. For Custom Packs, DB is mandatory.

### 3. "Shadowing" Concept

**The Proposal**:
> Custom packs can "shadow" system packs if they share the same ID.

**Critique**:
*   Shadowing by ID is often confusing for users ("Why did my 'Brainstorming' pack change?").
*   It is safer to treat System Packs as immutable templates that users can **Clone** (Copy to Custom), creating a new entity with a new ID.

**Recommendation**:
*   Remove "Shadowing".
*   Implement "Clone/Fork" behavior. A user modifies a System Pack -> It becomes a new Custom Pack (e.g., "Brainstorming (Custom)").

### 4. Validation & Referential Integrity

**The Proposal**:
> Validation: Ensure packs don't reference missing personalities.

**Critique**:
*   Since Personalities remain in files (ADR-007) and Packs move to DB (per my recommendation), strict Referential Integrity (Foreign Keys) is impossible.
*   We must rely on **Application-Level Validation**.

**Recommendation**:
*   The `PackService` must validate personality IDs against the loaded registry (`get_all_personalities`) at **Write Time** (Creation) and **Read/Apply Time** (Runtime check, graceful degradation if a personality is missing).

---

## Proposed Amendments to Guidelines

### A. Extended ADR-016
Explicitly state that **all** user-generated configuration (Packs, Custom Prompts, etc.) belongs in `tenant.db`, not on the filesystem.

### B. Updated Schema for `council-packs.md`

Instead of files, propose a **Hybrid Approach**:

1.  **System Packs**: defined in `data/defaults/packs/*.yaml` (Read-only, loaded into memory at startup).
2.  **Custom Packs**: stored in `tenant.db`.
3.  **API Layer**: Merges the two lists for `GET /api/packs`.

This preserves the "Code as Config" benefit for developers (System Packs) while leveraging SQLite's safety for users (Custom Packs).

---

## Action Plan
1.  **Refine `docs/architecture/council-packs.md`** to reflect the **Tenant DB** storage strategy.
2.  **Draft ADR-026 (Configuration Packs)** formally codifying the detailed schema.
3.  **Prototype `PackService`** that abstracts the source (File vs DB) so the frontend doesn't care.
