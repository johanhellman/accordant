# Design Document: Consensus Model for LLM Council

**Status**: Draft
**Date**: 2025-12-04
**Author**: Antigravity (AI Assistant)
**Context**: Proof of Concept (Internal)

## 1. Context & Background
The current LLM Council implementation utilizes a "Ranking Model" where multiple personalities (LLMs with specific system prompts) generate responses to a user query (Stage 1), and then rank each other's responses (Stage 2) to determine a "winner." The Chairman then synthesizes a final answer based on the voting results (Stage 3).

While effective for competitive evaluation, this model encourages a "winner-takes-all" dynamic. The goal is to introduce an optional **"Consensus Model"** that shifts the focus from ranking to **synthesis**. In this mode, personalities will critique peers to identify strengths and synergies, allowing the Chairman to forge a cohesive narrative that combines the best elements of all perspectives.

## 2. Goals & Non-Goals

### Goals
*   **Surface Strengths**: Enable personalities to explicitly identify and articulate the strong points of peer responses.
*   **Forge Cohesion**: Empower the Chairman to create a unified narrative that is greater than the sum of its parts.
*   **Configurable Mode**: Allow the system to switch between "Ranking" and "Consensus" modes per conversation or organization.
*   **Holistic Integration**: Ensure the new mode integrates seamlessly with the existing 3-stage architecture.

### Non-Goals
*   **Real-time Debate**: We are not implementing a multi-turn back-and-forth debate between personalities (yet). This remains a 3-stage pipeline.
*   **Complex Scoring**: We are avoiding complex numerical scoring rubrics for the consensus mode in favor of qualitative critique.

## 3. High-Level Architecture
The system will retain the 3-stage pipeline but introduce a branching logic in Stage 2 and Stage 3 based on the selected `mode`.

*   **Stage 1 (Generation)**: Identical for both modes. Personalities generate initial responses.
*   **Stage 2 (Evaluation)**:
    *   *Ranking Mode*: Personalities rank peers (Current).
    *   *Consensus Mode*: Personalities provide qualitative **Critiques** of peers (New).
*   **Stage 3 (Synthesis)**:
    *   *Ranking Mode*: Chairman summarizes votes and declares a winner.
    *   *Consensus Mode*: Chairman synthesizes a unified narrative from the critiques and content.

## 4. Detailed Design

### 4.1. Data Model Changes
We need to extend the schema to support the new critique data.

**`backend/schema.py`**
```python
class Stage2ConsensusResult(TypedDict):
    """Result from a consensus critique in Stage 2."""
    model: str
    personality_name: str | None
    critique: str  # The full text analysis/critique
    # Future: strengths: list[str], weaknesses: list[str]
```

### 4.2. Stage 2: Peer Critique (Consensus Mode)
Instead of a ranking prompt, we will use a **Critique Prompt**.

**Workflow**:
1.  Gather Stage 1 responses.
2.  Anonymize responses (Label A, B, C...).
3.  Send to each personality with the `critique_prompt`.

**Prompt Strategy**:
The prompt will instruct the model to:
*   Analyze each response.
*   Identify unique insights or superior explanations.
*   Point out gaps or contradictions.
*   *Crucially*: Do not rank them.

### 4.3. Stage 3: Consensus Synthesis
The Chairman's role shifts from "Returning Officer" to "Chief Editor/Synthesizer."

**Workflow**:
1.  Gather Stage 1 content.
2.  Gather Stage 2 critiques.
3.  Send to Chairman with `consensus_chairman_prompt`.

**Prompt Strategy**:
The prompt will provide:
*   The original query.
*   The full text of all responses.
*   The full text of all critiques.
*   Instruction: "Draft a single, comprehensive response that incorporates the best elements of all responses, guided by the peer critiques. Resolve contradictions by weighing the evidence presented."

## 5. Architectural Decision Records (ADRs)

### ADR-001: Explicit Mode Switch vs. Hybrid Approach
**Decision**: We will implement a strict configuration switch (`mode="ranking"` vs `mode="consensus"`) rather than trying to do both simultaneously or inferring intent.
**Rationale**:
*   **Clarity**: Keeps the pipeline predictable and easier to debug.
*   **Token Costs**: Running both ranking and critique simultaneously doubles Stage 2 costs.
*   **POC Scope**: For a proof of concept, distinct modes allow for clearer A/B testing of the output quality.

### ADR-002: Text-Based Critique vs. Structured Scoring
**Decision**: Stage 2 output will be primarily free-text critiques rather than structured JSON scores (e.g., Accuracy: 8/10).
**Rationale**:
*   **LLM Strength**: LLMs are better at qualitative nuance than consistent numerical scoring.
*   **Richness**: A text critique ("Model A explained the 'why' better, but B had better code examples") is more useful for the Chairman's synthesis than a raw score.
*   **Flexibility**: Allows personalities to highlight unexpected strengths that a fixed rubric might miss.

### ADR-003: Stateless Pipeline
**Decision**: The consensus process will remain a single-pass pipeline (Stage 1 -> 2 -> 3) rather than an iterative conversation.
**Rationale**:
*   **Latency**: Multi-turn debate significantly increases response time.
*   **Complexity**: Managing state and convergence criteria for a debate loop is complex.
*   **Consistency**: Fits the existing architecture (Request -> Response) without major refactoring.

## 6. API & Configuration

### API Changes
*   `POST /api/chat`: Accept an optional `mode` parameter in the request body.
    *   `mode`: "ranking" (default) | "consensus"

### Configuration
*   `system-prompts.yaml`: Add new keys for consensus prompts.
    *   `critique_prompt`: Template for Stage 2.
    *   `consensus_chairman_prompt`: Template for Stage 3.

## 7. Risks & Mitigation
*   **Risk**: "Mushy" Consensus. The synthesis might become a generic average of all answers, losing sharp, distinct insights.
    *   *Mitigation*: Tune the Chairman prompt to prioritize "best evidence" and "unique insights" over "middle ground."
*   **Risk**: Context Window Limits. Including full responses AND full critiques might exceed context limits for long conversations.
    *   *Mitigation*: Use models with large context windows (Gemini 1.5 Pro, Claude 3 Opus). Implement summarization if needed in future.

## 8. Future Considerations
*   **Iterative Refinement**: Allow the Chairman to ask follow-up questions to specific personalities if the consensus is unclear.
*   **Hybrid Mode**: A mode that ranks *and* critiques, useful for detailed auditing.
*   **User-Guided Consensus**: Allow the user to weigh in during the process (e.g., "Focus more on Model B's approach").
