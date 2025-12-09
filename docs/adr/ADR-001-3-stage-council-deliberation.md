# ADR-001: 3-Stage Council Deliberation System

**Status**: Accepted  
**Date**: 2025-11-25  
**Deciders**: Project Team

## Context

The project aims to create a collaborative LLM system where multiple AI models work together to provide better answers than any single model alone. We needed a structured process that:

- Allows multiple models to provide initial responses
- Enables models to evaluate each other's work
- Synthesizes a final answer from the collective deliberation

## Decision

We will implement a 3-stage deliberation system:

1. **Stage 1: First Opinions** - All council models receive the user query and provide individual responses in parallel
2. **Stage 2: Review** - Each model evaluates and ranks the anonymized responses from other models
3. **Stage 3: Final Response** - A designated Chairman model synthesizes all responses and rankings into a final answer

## Consequences

### Positive

- **Parallel Processing**: Stage 1 queries run in parallel, minimizing latency
- **Bias Prevention**: Stage 2 anonymization prevents models from playing favorites
- **Quality Improvement**: Multiple perspectives lead to more comprehensive answers
- **Transparency**: Users can inspect all stages of deliberation

### Negative

- **Higher Token Usage**: Multiple API calls increase costs
- **Increased Latency**: Sequential stages add to total response time
- **Complexity**: More moving parts to maintain and debug

### Neutral

- The system supports both "personality mode" (custom system prompts) and "legacy mode" (simple model list)
- History context is managed separately for each stage to optimize token usage

## Implementation Notes

- Stage 1 and Stage 2 queries run in parallel within their stages
- Stage 3 must wait for Stage 2 to complete
- Failed model queries don't block the entire process (graceful degradation)
- See `backend/council.py` for implementation details
