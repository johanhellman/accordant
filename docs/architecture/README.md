# Architecture Documentation

## Overview

Accordant implements the **LLM Council**: a 3‑stage deliberation system where multiple LLMs collaboratively answer user questions through anonymized peer review and a final synthesis step.

### Key Documents

*   **[System Overview](OVERVIEW.md)**: High‑level architecture, data flow, and key backend/frontend components.
*   **[Async Flow](ASYNC_FLOW.md)**: Detailed sequence of the 3-stage deliberation process.
*   **[Consensus Model](CONSENSUS.md)**: Design of the ranking and synthesis algorithms.
*   **[Database](DATABASE.md)**: SQLite multi-tenant storage schema.
*   **[ADRs](../adr/ADR_INDEX.md)**: Architecture Decision Records explaining the *why* behind decisions.

## Federated Privacy

Accordant uses a **Federated Aggregation** model to balance organization privacy with global system improvement.

*   **Data Residency**: All sensitive data resides within the Tenant/Organization boundary.
*   **Privacy Firewall**: The "Instance Admin" sees aggregated metrics but **not** raw conversation logs.
*   **On-Demand Retrieval**: Qualitative feedback is fetched only when requested by an authorized Organization Admin.
