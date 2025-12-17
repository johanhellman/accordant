# ADR-024: Strategic Consensus & Attribution

**Date**: 2025-12-17
**Status**: Accepted
**Context**:
The original [ADR-001](ADR-001-3-stage-council-deliberation.md) defined Stage 3 as a simple synthesis step where the Chairman merges the answer. However, the system needs to support varying governance strategies (e.g., Risk-Averse vs. Novelty-Seeking) and must accurately attribute which parts of the synthesis came from which personality.

**Decision**:
1.  **Prompt-Based Strategy**: Instead of hardcoding synthesis logic, we will use swappable **Consensus Strategies** (prompt templates).
    *   These prompts reside in `data/defaults/consensus/`.
    *   They instruct the Chairman on *how* to weigh the evidence (e.g., "Veto any high-risk proposal").
2.  **Attribution Metadata**: The Chairman will be prompted to output a JSON metadata block `{"contributors": [{"id": "...", "weight": 0.8}]}`.
3.  **Data Model**: A new `consensus_contributions` table will store this attribution data for analytics.
4.  **Veto Power**: The default "Strategic Consensus" prompts will include a "Veto Check" step to prevent risky answers from passing if flagged by any council member.

**Consequences**:
*   **Flexibility**: Organizations can switch strategies by changing a config key.
*   **Transparency**: Users will see exactly who influenced the final answer.
*   **Complexity**: The Chairman prompt becomes more complex and requires reliable JSON parsing of the metadata block.
*   **Storage**: Requires schema migration for the new table.

**Supersedes**: Amends Stage 3 of ADR-001.
