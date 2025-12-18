# Design Document: Council Packs

**Status**: Draft
**Date**: 2025-12-18
**Author**: Antigravity (AI Assistant)
**Context**: Feature Planning

## 1. Context & Problem Statement

Currently, users must manually configure their Council by:
1.  Enabling/Disabling individual personalities.
2.  Selecting a Consensus Strategy (if implemented in UI).
3.  Potentially modifying system prompts for specific use cases.

This strictly manual process makes it difficult to switch between different "modes" of operation. For example, switching from a **"Brainstorming"** setup (Creative personalities, Novelty-seeking consensus) to a **"Risk Assessment"** setup (Skeptical personalities, Risk-Averse consensus) requires many clicks and intimate knowledge of which personalities fit which role.

## 2. Proposed Solution: Council Packs

A **Council Pack** is a predefined configuration bundle that instantly sets up the Council for a specific purpose. It follows the same hierarchical pattern as Personalities:

1.  **System Packs**: Default packs provided by the instance (read-only for users).
2.  **Custom Packs**: Organization-specific packs created by admins.

It encapsulates:
1.  **The Team**: A specific set of enabled personalities.
2.  **The Strategy**: A specific Consensus Strategy (e.g., `balanced`, `risk_averse`, `creative`).
3.  **The Context**: (Optional) Overrides for system prompts to set a global tone or context.

### 2.1. User Stories
*   "As a user, I want to one-click switch to 'Coding Mode' so that I have the Architect, Hacker, and QA personalities enabled without manually toggling them."
*   "As a user, I want a 'Red Team' pack that enables critical personalities and sets the consensus strategy to 'Find Flaws'."

## 3. Data Model & Schema

We will introduce a new entity: `CouncilPack`.

### 3.1. File Storage Hierarchy

Mirroring the `Personalities` architecture:

*   **System Defaults**: `data/defaults/packs/*.yaml`
    *   Available to all organizations.
    *   Immutable via API.
*   **Organization Custom**: `data/organizations/{org_id}/packs/*.yaml`
    *   Created by Org Admins.
    *   Can "shadow" a system pack if they share the same `id` (allowing overrides), or be completely new.

### 3.2. Schema Definition

```yaml
id: creative_brainstorming
name: "Creative Brainstorming Team"
description: "A group of divergent thinkers designed to generate novel ideas. Fosters creativity over safety."

# 1. Personalities to Enable
# These IDs must match the `id` field in personality YAMLs.
# All other personalities will be disabled when this pack is applied.
personalities:
  - gpt_creative
  - claude_poet
  - gemini_futurist
  - grok_contrarian

# 2. Consensus Strategy
# Maps to a filename in `data/defaults/consensus/` (without .md extension)
consensus_strategy: novelty_focus 

# 3. System Prompt Overrides (Optional)
# Allows changing the global instructions for this specific mode.
system_prompts:
  # Appended to the base prompt or fully replacing sections
  stage1_meta_structure: |
    IMPORTANT context for this session:
    You are in a brainstorming session. NO IDEA is too wild.
    Suspend judgment. Build on each other's ideas ("Yes, and...").
```

## 4. Backend Architecture Changes

### 4.1. New Configuration Module
We need a new module `backend/config/packs.py` responsible for:
*   Loading pack definitions from `data/defaults/packs/`.
*   Validating that referenced personalities and strategies exist.

### 4.2. API Endpoints
New endpoints in `backend/admin_routes.py`:

*   `GET /api/packs`: List all available packs (merging System + Custom).
    *   Response includes `source`: "system" | "custom" and `is_editable`.
*   `POST /api/packs`: Create a new Custom Pack.
*   `PUT /api/packs/{pack_id}`: Update a Custom Pack.
*   `DELETE /api/packs/{pack_id}`: Delete a Custom Pack.
*   `POST /api/packs/{pack_id}/apply`: Apply a pack to the current organization.
    *   **Side Effect**: Updates `Organization.settings` to:
        *   Set `enabled` = `True` for listed personalities.
        *   Set `enabled` = `False` for all others.
        *   Update `consensus_strategy` setting.
        *   Update `system_prompt_overrides` (new field in settings).

### 4.3. Impact on `council.py`
The `run_council_cycle` and `get_active_personalities` functions currently read directly from config. They need to be aware of the "Applied Pack" state, primarily through the `Organization.settings` which they likely already consult (or should).

*   **Prompt Loading**: `load_org_system_prompts` needs to check if a pack is active and if it has overrides.
*   **Consensus Strategy**: Needs to be plumbed from `Organization.settings` into the `ConsensusService`.

## 5. Frontend / UX

1.  **Pack Gallery**: A new tab in the "Council" or "Settings" page displaying cards for each Pack.
    *   **System Packs**: Distinct visual style (e.g., gold border).
    *   **Custom Packs**: User-created, with Edit/Delete options.
    *   "Apply Pack" button on all.
    *   "Create New Pack" button.
2.  **Active State**: When a pack is active, the UI should indicate "Current Pack: Creative Brainstorming".
3.  **Manual Override**: If a user manually toggles a personality after applying a pack, the UI should show the pack as "Modified" or "Custom".

## 6. Dependencies & Migration
*   **Consensus Mode UX**: The user noted that Consensus Modes are not currently exposed in UX. This feature (Packs) will be the primary way users interact with them initially.
*   **Default Pack**: Use the current manual configuration as a "Custom" state.
*   **Validation**: Ensure packs don't reference missing personalities (e.g. if a user deleted a custom personality that a custom pack referenced).

## 7. Gap Analysis
Based on a review of the current codebase (`backend/council.py`, `backend/consensus_service.py`) and ADRs:

1.  **Frontend Gap**:
    *   No UI exists for "Consensus Strategy" selection.
    *   No UI exists for "Pack" management.
    *   *Decision*: We will implement the Pack Gallery as the primary mechanism for both.

2.  **Backend Gap**:
    *   `Organization.settings` schema is loosely defined (JSON). We need to formalize the storage of `active_pack_id`.
    *   `consensus_service.py` exists and supports swappable prompts, but currently relies on `get_active_consensus_prompt` which defaults to a single config key `consensus_strategy`. We need to wire this to the `Organization.settings` properly.

## 8. Documentation Impact (ADRs)

*   **ADR-007 (Modular Personality Config)**:
    *   *Status*: Remains valid, but needs to be extended.
    *   *Action*: We will implicitly extend this pattern to Packs without a formal update, as the pattern is identical (System Defaults + Org Custom).
*   **ADR-024 (Strategic Consensus)**:
    *   *Status*: Accepted and Implemented.
    *   *Action*: No changes needed. The design relies heavily on this foundation.
*   **New ADR Recommendation**:
    *   We should technically draft **ADR-026: Configuration Packs** to formalize the "Meta-Configuration" layer (bundling multiple settings into a single entity).

