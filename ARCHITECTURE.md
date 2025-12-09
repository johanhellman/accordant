## Architecture Overview

This repository implements the **LLM Council**: a 3‑stage deliberation system where multiple LLMs collaboratively answer user questions through anonymized peer review and a final synthesis step.

For full architectural details, start here:

- **System overview**: `docs/design/SYSTEM_OVERVIEW.md`  
  High‑level architecture, data flow, and key backend/frontend components.
- **Architecture Decision Records (ADRs)**: `docs/adr/ADR_INDEX.md`  
  Rationale for major design choices (3‑stage flow, anonymized peer review, storage model, admin API, UI design, etc.).
- **API surface**: `docs/api/API_SURFACE.md`  
  HTTP endpoints, request/response shapes, and integration notes.

Contributors looking for deeper implementation notes should also see `docs/DEVELOPER_GUIDE.md`.

## Federated Architecture & Privacy

Accordant uses a **Federated Aggregation** model to balance organization privacy with global system improvement.

- **Data Residency**: All sensitive data (conversations, reasoning text) resides strictly within the Tenant/Organization boundary.
- **Privacy Firewall**: The "Instance Admin" (System Operator) can see aggregated metrics (Win Rates) but **cannot** access raw conversation logs or qualitative reasoning text.
- **On-Demand Retrieval**: Qualitative feedback summaries are generated on-demand by fetching data from secure storage only when requested by an authorized Organization Admin.

For implementation details, see [ADR-015: Federated Voting Privacy](docs/adr/ADR-015-federated-voting-privacy.md).
