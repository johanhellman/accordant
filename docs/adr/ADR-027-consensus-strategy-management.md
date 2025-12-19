# ADR-027: Consensus Strategy Management

**Status**: Draft
**Date**: 2025-12-19
**Context**: Configuration Management

## Context
The system currently relies on static Markdown files (`data/defaults/consensus/*.md`) to define "Consensus Strategies". These strategies are critical prompts that guide the "Chairman" persona in synthesizing the final council response. 

As the system evolves to be multi-tenant and user-configurable (see **ADR-026 Configuration Packs**), the static nature of these files becomes a limitation:
1.  **Instance Admins** cannot update system defaults without a code deployment.
2.  **Organization Admins** cannot create custom strategies tailored to their specific domain logic.

## Decision
We will implement a **Hybrid Storage Model** for Consensus Strategies, mirroring the pattern established for Personalities and Packs.

1.  **System Strategies**:
    *   Stored as Markdown files in `data/defaults/consensus/`.
    *   Managed via GitOps (standard) OR via Instance Admin API (updates the file).
    *   Reasoning: Allows version-controlled defaults while enabling runtime updates for the instance owner.

2.  **Custom Strategies (Tenant-Scoped)**:
    *   Stored in the `tenant.db` under a new table `consensus_strategies`.
    *   Managed via Org Admin API.
    *   Reasoning: Provides data isolation and enables tenants to build proprietary logic without polluting the system defaults.

3.  **Service Name**:
    *   We will use `ConsensusStrategyService` (not `StrategyService`) to be explicit and avoid namespace collisions with future strategy types (e.g., *Evolution Strategies* or *Retrieval Strategies*).

## Consequences

### Positive
*   **Flexibility**: Admins can now iterate on the core consensus logic directly from the UI.
*   **Isolation**: Custom strategies are sandboxed to the organization.
*   **Consistency**: Follows the same "Hybrid" pattern as other config assets, reducing cognitive load for developers.

### Negative
*   **Complexity**: The system must now merge two data sources (Files + DB) to present a unified list.
*   **State Drift**: System files edited via API might drift from the git repository state if not carefully managed (Instance Admins should be aware of this).
