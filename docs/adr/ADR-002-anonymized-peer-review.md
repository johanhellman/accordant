# ADR-002: Anonymized Peer Review in Stage 2

**Status**: Accepted  
**Date**: 2025-11-25  
**Deciders**: Project Team

## Context

In Stage 2, models need to evaluate and rank responses from other models. If models know which response belongs to which model, they may exhibit bias (e.g., favoring models from the same provider, or models they "know" are strong).

## Decision

We will anonymize responses in Stage 2 by:

1. Labeling responses as "Response A", "Response B", "Response C", etc.
2. Creating a `label_to_model` mapping that is kept server-side
3. Only revealing model identities after rankings are collected
4. In personality mode, excluding each model's own response from their evaluation set

## Consequences

### Positive

- **Reduced Bias**: Models evaluate based on content quality, not model reputation
- **Fair Evaluation**: All models get equal treatment regardless of provider
- **Transparency**: Users can see the anonymized evaluations and the final de-anonymized results

### Negative

- **Additional Complexity**: Need to maintain label-to-model mappings
- **Parsing Requirements**: Must parse rankings from natural language responses
- **Edge Cases**: Models may not follow the ranking format exactly

### Neutral

- Frontend displays model names in bold for readability, but clearly indicates these are for display only
- The original evaluations used anonymous labels

## Implementation Notes

- Labels are generated as `chr(65 + i)` for responses (A, B, C, ...)
- Ranking prompt includes strict formatting requirements: "FINAL RANKING:" followed by numbered list
- Fallback parsing extracts any "Response X" patterns if strict format fails
- See `parse_ranking_from_text()` in `backend/council.py`
