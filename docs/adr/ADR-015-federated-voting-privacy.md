# ADR-015: Federated Voting Privacy & Information Firewalls

## Context
As we introduce the "Personality League Table" and "Evolution System", we need to aggregate voting data to rank AI personalities. However, `accordant` is designed as a multi-tenant system where each Organization expects data privacy.

We needed a strategy that allows:
1.  **Global Optimization**: Improving System Personalities based on their performance across all organizations.
2.  **Local Privacy**: Ensuring that Organization A's sensitive conversation data (reasoning, prompt inputs) is never visible to the Instance Admin or Organization B.

## Decision
We adopted a **Federated Aggregation** strategy with strict **Information Firewalls**.

### 1. Data Residency
*   **Voting History**: Stored locally in `data/organizations/{org_id}/voting_history.json`. This file contains **Metadata Only** (Vote counts, Rankings, Model IDs). It **does not** contain the textual reasoning or user prompts.
*   **Qualitative Feedback**: The "reasoning" text (e.g., "I voted for A because it was more concise") remains in the **Conversation Storage** (`storage.py`), which is strictly access-controlled by `org_id`.

### 2. Information Firewall
*   **Instance Admin (System Operator)**:
    *   Can see: Aggregated metrics (Total Wins, Average Rank) for System Personalities.
    *   Cannot see: User prompts, conversation content, or qualitative feedback text.
    *   Mechanism: The `calculate_instance_league_table` service aggregates counters only. It never calls `storage.get_conversation`.
*   **Organization Admin**:
    *   Can see: Full metrics for their own organization.
    *   Can see: Qualitative feedback for specific personalities, strictly from their own organization's logs.
    *   Mechanism: The `ranking_service` performs an authenticated lookup of conversation logs to generate summaries on-demand.

### 3. Federated Evolution
*   Evolution actions (Combines) are triggered by Organization Admins using their own local data and feedback.
*   The Instance Admin can eventually propagate successful System Personalities (manually) but relies on signals (Win Rate) rather than reading private user chats.

## Consequences
*   **Privacy Preserved**: No leakage of training data or sensitive business logic.
*   **Actionable Metrics**: We still get high-level signals (Win Rate) to identify best models.
*   **Complexity**: Requires dual-path logic in `ranking_service.py` (one for instance aggregation, one for local detailed view).
