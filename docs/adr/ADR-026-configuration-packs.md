# ADR-026: Configuration Packs

**Status**: Accepted
**Date**: 2025-12-19
**Context**: Feature Planning

## Context

Users currently configure the Council manually by toggling individual personalities and selecting strategies. This is tedious when switching between different operational modes (e.g., "Brainstorming" vs "Risk Assessment").

We need a way to bundle these settings into a single "Pack" that can be applied instantly.

## Decision

We will implement **Council Packs** using a **Hybrid Storage** and **Per-User Configuration** model.

### 1. Hybrid Storage for Definitions

*   **System Packs**: Defined in `data/defaults/packs/*.yaml`. These are read-only templates provided by the application.
*   **Custom Packs**: Stored in the `tenant.db` in a `council_packs` table. These are created by organization admins.

### 2. Per-User Active State

The active configuration (which pack is applied) will be stored in `tenant.db` in a `council_configuration` table, keyed by `user_id`.
*   This ensures strict data isolation (aligning with [ADR-016](ADR-016-multi-tenant-sqlite-sharding.md)).
*   This allows different users in the same organization to have different active setups simultaneously.

### 3. Cloning vs Shadowing

We explicitly reject "Shadowing" (overriding a system pack by creating a custom one with the same ID). Instead, we use a **Clone** pattern: a user copies a System Pack to create a new, distinct Custom Pack.

## Consequences

### Positive
*   **UX**: Instant switching between complex configurations.
*   **Isolation**: User runtime state is isolated in their tenant shard.
*   **Flexibility**: Users can customize their experience without affecting others in the org.

### Negative
*   **Complexity**: Backend must merge two data sources (YAML + SQL) for listing packs.
*   **Migration**: We must migrate existing "Legacy" configuration (stored in `Organization.settings`) to the new table on first access.
