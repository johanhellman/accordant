# ADR-005: Personality Mode for Council Members

**Status**: Accepted (Storage mechanism superseded by ADR-007)  
**Date**: 2025-11-25  
**Deciders**: Project Team

## Context

The initial implementation used a simple list of models. Users requested the ability to assign custom personalities (system prompts) to council members, allowing for character-based interactions (e.g., "The Skeptic", "The Optimist", "The Pragmatist").

## Decision

We will support two modes:

1. **Legacy Mode**: Simple list of models with basic system prompts
2. **Personality Mode**: Models with custom system prompts defined in `personalities.yaml`

Personality mode features:

- Each personality has: `id`, `name`, `model`, `personality_prompt`, optional `temperature`
- System prompt combines `BASE_SYSTEM_PROMPT` + time instruction + personality prompt
- In Stage 2, personalities exclude their own response when ranking (peer review)

## Consequences

### Positive

- **Flexibility**: Users can create custom council compositions
- **Character Consistency**: Personalities maintain their "voice" across stages
- **Backward Compatible**: Legacy mode still works for simple use cases
- **Enhanced Deliberation**: Different perspectives lead to richer discussions

### Negative

- **Code Complexity**: Dual-mode implementation increases code paths
- **Configuration Management**: Need to maintain `personalities.yaml`
- **Testing Complexity**: More scenarios to test

### Neutral

- Mode is determined by presence of `ACTIVE_PERSONALITIES` in config
- Stage 1 and Stage 2 have separate personality/legacy implementations
- See `backend/config.py` and `personalities.yaml` for configuration

## Implementation Notes

- Personalities loaded from `personalities.yaml` via `ACTIVE_PERSONALITIES` config
- Personality mode uses `_stage1_personality_mode()` and `_stage2_personality_mode()`
- Legacy mode uses `_stage1_legacy_mode()` and `_stage2_legacy_mode()`
- Personality metadata (id, name) is included in Stage 1 and Stage 2 results
- See `backend/council.py` for implementation details
