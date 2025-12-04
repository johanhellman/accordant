# ADR-006: Context Sliding Window for History

**Status**: Accepted  
**Date**: 2025-11-25  
**Deciders**: Project Team

## Context

LLM context windows are limited and expensive. Long conversations can exceed token limits or become prohibitively expensive. We need a strategy for managing conversation history that:
- Preserves recent context for coherent multi-turn conversations
- Limits token usage
- Maintains conversation flow

## Decision

We will implement a sliding window approach:
- Only include the last N turns (default: 10 turns) in the history
- A "turn" is a user message + assistant message pair
- History includes only user queries and final answers (Stage 3), not internal deliberations
- History is prepared via `build_llm_history()` which filters and limits messages

## Consequences

### Positive
- **Token Efficiency**: Limits context size, reducing costs
- **Recent Context**: Maintains coherence for recent conversation
- **Simplified History**: Only essential messages (user queries + final answers) included
- **Configurable**: `max_turns` parameter allows adjustment

### Negative
- **Context Loss**: Older conversation context is discarded
- **No Long-Term Memory**: Can't reference very old parts of conversation
- **Potential Confusion**: Models may lose track of earlier topics

### Neutral
- Internal deliberations (Stage 1, Stage 2) are excluded from history to save tokens
- Future consideration: May add voting history to context on personality level
- See `build_llm_history()` in `backend/council.py`

## Implementation Notes

- Default `max_turns=10` means last 20 messages (10 user + 10 assistant)
- History extraction filters for `role in ('user', 'assistant')`
- Assistant messages extract only Stage 3 final answer (parsing "PART 2: FINAL ANSWER" if present)
- Sliding window applied before message filtering
- See `build_llm_history()` in `backend/council.py` for implementation

