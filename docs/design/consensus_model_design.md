# Design Document: Consensus Model for LLM Council

**Status**: Draft
**Date**: 2025-12-04
**Author**: Antigravity (AI Assistant)
**Context**: Proof of Concept (Internal)

## 1. Context & Background

The current LLM Council implementation utilizes a "Ranking Model" where multiple personalities (LLMs with specific system prompts) generate responses to a user query (Stage 1), and then rank each other's responses (Stage 2) to determine a "winner." The Chairman then synthesizes a final answer based on the voting results (Stage 3).

While effective for competitive evaluation, this model encourages a "winner-takes-all" dynamic. The goal is to introduce an optional **"Consensus Model"** that shifts the focus from ranking to **synthesis**. In this mode, the Chairman will focus on the qualitative critiques and strengths identified by the personalities to forge a cohesive narrative.

## 2. Goals & Non-Goals

### Goals

* **Surface Strengths**: Leverage the existing Stage 2 evaluation to inform the final synthesis.
* **Forge Cohesion**: Empower the Chairman to create a unified narrative that is greater than the sum of its parts.
* **Configurable Mode**: Allow the system to switch between "Ranking" and "Consensus" modes per conversation or organization.
* **Unified Pipeline**: Use a single, robust evaluation step (Stage 2) that serves both modes.

### Non-Goals

* **Real-time Debate**: We are not implementing a multi-turn back-and-forth debate.
* **Complex Scoring**: We are avoiding complex numerical scoring rubrics.

## 3. High-Level Architecture

The system will retain the 3-stage pipeline. The primary architectural change is in **Stage 3**, where the input to the Chairman changes based on the mode.

* **Stage 1 (Generation)**: Identical for both modes.
* **Stage 2 (Evaluation)**: **Unified**. Personalities evaluate peers using a standard template that includes **both** structured critique (Strengths/Weaknesses) and a final ranking.
* **Stage 3 (Synthesis)**:
  * *Ranking Mode*: Chairman focuses on the **Rankings** to declare a winner.
  * *Consensus Mode*: Chairman focuses on the **Strengths & Weaknesses** to synthesize a consensus.

## 4. Detailed Design

### 4.1. Data Model Changes

No major schema changes. `Stage2Result` will continue to hold the full text response, which will now be more structured.

### 4.2. Stage 2: Unified Evaluation

We will refine the `DEFAULT_RANKING_PROMPT` to enforce a stricter response template.

**New Default Prompt Structure**:
> "Analyze the following responses. For each response, you MUST provide:
>
> 1. **Strengths**: What does this response do well?
> 2. **Weaknesses**: What is missing or incorrect?
>
> After evaluating all responses, provide a **FINAL RANKING**..."

This ensures that every Stage 2 execution produces *both* the qualitative data needed for Consensus Mode and the quantitative data needed for Ranking Mode.

### 4.3. Stage 3: Consensus Synthesis

The Chairman's role shifts based on the mode.

**Workflow**:

1. Gather Stage 1 responses.
2. Gather Stage 2 results (which now contain structured critiques).
3. **Branching Logic**:
    * If `mode == "ranking"`: Use `chairman_prompt` (Standard voting report).
    * If `mode == "consensus"`: Use `consensus_chairman_prompt`.

**Prompt Strategy (Consensus Mode)**:
The `consensus_chairman_prompt` will instruct the Chairman to:

* Ignore the rankings.
* Read the "Strengths" and "Weaknesses" sections from the peer evaluations.
* Synthesize a final answer that combines the identified strengths.

## 5. Architectural Decision Records (ADRs)

### ADR-012: Explicit Mode Switch vs. Hybrid Approach

**Decision**: We will implement a strict configuration switch (`mode="ranking"` vs `mode="consensus"`) rather than trying to do both simultaneously or inferring intent.
**Rationale**:

* **Clarity**: Keeps the pipeline predictable.
* **POC Scope**: Distinct modes allow for clearer A/B testing.

### ADR-013: Unified Evaluation Prompt

**Decision**: We will use a single, unified prompt for Stage 2 that asks for *both* structured critique and ranking, rather than swapping prompts based on mode.
**Rationale**:

* **Simplicity**: Stage 2 logic remains identical for all modes.
* **Richness**: We always capture the "why" behind the ranking, which is valuable even in Ranking Mode.
* **Flexibility**: The mode only dictates how the Chairman *consumes* this data in Stage 3.

### ADR-014: Stateless Pipeline

**Decision**: The consensus process will remain a single-pass pipeline.
**Rationale**:

* **Latency**: Multi-turn debate significantly increases response time.
* **Consistency**: Fits the existing architecture.

## 6. API & Configuration

### API Changes

* `POST /api/chat`: Accept an optional `mode` parameter.

### Configuration

* `system-prompts.yaml`:
  * `ranking_prompt`: Updated default to include structured critique instructions.
  * `consensus_chairman_prompt`: New template for Stage 3 (Consensus Mode).

## 7. Risks & Mitigation

* **Risk**: Prompt Compliance. Models might fail to follow the strict "Strengths/Weaknesses" structure.
  * *Mitigation*: Use strong system instructions and potentially few-shot examples in the prompt.
* **Risk**: Token Usage. Detailed critiques for every model might be verbose.
  * *Mitigation*: Instruct models to be concise in their critiques.

## 8. Future Considerations

* **Hybrid Mode**: Since we now have both data points, a "Hybrid" mode that reports the winner *and* the consensus synthesis is trivial to implement later.
