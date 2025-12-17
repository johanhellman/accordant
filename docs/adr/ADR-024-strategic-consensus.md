# ADR-024: Strategic Consensus & Attribution

- **Status**: Accepted
- **Date**: 2025-12-17
- **Context**: The original 3-Stage Deliberation (ADR-001) defined Stage 3 as a generic "Synthesis". Users now require "Strategic Synthesis" (e.g., Risk-Averse vs. Goal-Seeking) where the Chairman applies specific lenses to the Council's input. Additionally, there is a need to "Attribution" to identify which personalities contributed to the final answer.
- **Decision**: 
    1.  **Prompt-Based Strategies**: We will implement "Consensus Strategies" as simple markdown prompt templates (e.g., `risk_averse.md`) rather than complex backend logic.
    2.  **Veto Power**: All consensus prompts must include a "Unanimous Acceptability" check to ensure no valid objections from peers are ignored.
    3.  **Attribution Metadata**: The Chairman will be prompted to output a JSON metadata block listing the `contributors` and their `weight`.
    4.  **Database Storage**: We will add a `consensus_contributions` table to the Tenant Schema to track this attribution for analytics.
    5.  **Tenant Configuration**: Strategies are configured at the Tenant level (System Prompts), not User level, to ensure consistent governance.
- **Consequences**:
    - **Positive**: flexible definition of "Consensus" without code changes; rich analytics on personality influence.
    - **Negative**: "Attribution" is probabilistic (LLM-reported), not deterministic.
    - **Amends**: Refines the definition of Stage 3 in ADR-001.
