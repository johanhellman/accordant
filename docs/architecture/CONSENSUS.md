# Design Document: Consensus Model for LLM Council

**Status**: Partial Implementation / Evolving
**Date**: 2025-12-10
**Author**: Antigravity (AI Assistant)
**Context**: Proof of Concept (Internal)

## 1. Context & Background

The Accordant system utilizes a "Council" of diverse AI personalities to provide multi-faceted answers. The core mechanism involves a **3-Stage Pipeline**:

1.  **Generation**: Multiple personalities generate parallel responses.
2.  **Evaluation (Ranking)**: Personalities blindly evaluate and rank each other's responses.
3.  **Synthesis**: A Chairman model synthesizes a final answer.

Originally, the design proposed an explicit switch between "Ranking Mode" (competitive) and "Consensus Mode" (collaborative). In practice, we have adopted a **Unified Evaluation** approach where detailed qualitative data (Strengths/Weaknesses) is collected *always* during Stage 2, enabling multiple downstream applications like **Ranking**, **Feedback Summaries**, and **Personality Evolution**.

## 2. Goals & Non-Goals

### Goals

*   **Unified Evaluation**: A single, robust evaluation step that captures both quantitative rankings and qualitative critique.
*   **Data-Driven Evolution**: Use the consensus data to "evolve" new personalities that combine the strengths of top performers.
*   **Feedback Loops**: Provide personalities with summarized peer feedback to improve future performance.
*   **Consensus Synthesis**: (Future) Empower the Chairman to create a unified narrative based on qualitative strengths rather than just declaring a winner.

### Non-Goals

*   **Real-time Debate**: We are not implementing a multi-turn back-and-forth debate within a single request (latency concerns).
*   **Complex Numerical Rubrics**: Evaluations remain text-based and semantic, avoiding brittle numerical scoring.

## 3. High-Level Architecture

The system retains the 3-stage pipeline, but the data flow has expanded to support auxiliary services.

*   **Stage 1 (Generation)**: Identical. Personalities answer user queries based on their specific prompts.
*   **Stage 2 (Unified Evaluation)**: **Implemented**. Personalities evaluate peers using a strict `ranking_enforced_output_format` that demands:
    1.  **Strengths**: What does this response do well?
    2.  **Weaknesses**: What is missing or incorrect?
    3.  **Ranking**: A definitive ordered list.
*   **Stage 3 (Synthesis)**:
    *   *Current State*: Chairman synthesizes a final answer and reports the "Voting Results" (Winner).
    *   *Planned State*: Explicit "Consensus Mode" where the Chairman ignores the ranking and focuses purely on synthesizing the "Strengths".

### 3.1 Auxiliary Services (New)

The rich data from Stage 2 is now utilized by offline services:

*   **Feedback Service**: Aggregates qualitative critiques for a specific personality over time (via `generate_feedback_summary`).
*   **Evolution Service**: Uses the Feedback Service to combine two "Parent" personalities into a new "Offspring" that inherits strengths and mitigates weaknesses identified by peers (`combine_personalities`).

## 4. Current Implementation

### 4.1. Data Model
*   **`Stage2Result`**: Contains the full text evaluation and the parsed ranking.
*   **`VotingHistory`**: Logs every session, including the raw critiques. This is the dataset that powers the Evolution Service.

### 4.2. Stage 2: Unified Evaluation
The `ranking_service` and `system-prompts.yaml` enforce a standardized output format:

```yaml
ranking_enforced_output_format: |
  IMPORTANT: Your response MUST be formatted EXACTLY as follows:
  - Start with the line "{FINAL_RANKING_MARKER}"
  
  For each response being evaluated, provide a structured analysis:
  > 1. **Strengths**: What does this response do well?
  > 2. **Weaknesses**: What is missing or incorrect?
  
  End with a final ranking...
```

This ensures we *always* capture the "Why" behind the "Who".

### 4.3. Personality Evolution (Implemented)
A major innovation not in the original design is the **Evolution Service** (`backend/evolution_service.py`).

**Workflow**:
1.  **Select Parents**: System or User selects 2+ personalities.
2.  **Fetch Feedback**: System calls `generate_feedback_summary` to retrieve aggregated peer critiques (Strengths/Weaknesses) from historical Stage 2 data.
3.  **Synthesize**: The `evolution_prompt` instructs an LLM to create a new personality config:
    > "Identify complementary strengths to preserve and weaknesses to mitigate... Synthesize a new personality that inherits core values... addresses the feedback..."
4.  **Birth**: A new YAML personality file is created.

This closes the loop: **Consensus Data → Better Personalities**.

## 5. Future Work: Consensus Mode (Stage 3)

The final piece of the original design—changing how the Chairman *synthesizes* the answer in real-time—is the next logical step.

**Proposed Logic**:
*   **Input**: The same Stage 2 results we already have.
*   **Mechanism**: A switch in the Chairman's system prompt.
*   **Prompt Strategy**:
    *   *Ranking Mode (Current)*: "Report the votes. Declare a winner. Write the best answer."
    *   *Consensus Mode (Future)*: "Ignore the ranks. Read the 'Strengths' sections. Synthesize a unified answer that combines the best points from all responses."

## 6. API & Configuration

### Implemented Configuration (`data/defaults/system-prompts.yaml`)
*   `ranking_enforced_output_format`: The template for Stage 2.
*   `evolution_prompt`: The instruction for creating new personalities.
*   `feedback_synthesis_prompt`: The instruction for summarizing peer critiques.

### Planned API Changes
*   `POST /api/chat`: Add `mode="consensus"` parameter to trigger the alternative Chairman prompt.

## 7. Risks & Mitigation

*   **Risk**: Context Window Limits. Aggregating full text critiques from 5+ models for the Chairman might exceed token limits.
    *   *Mitigation*: The Chairman currently only sees the *raw text* of the answers and a *summary* of the votes. For Consensus Mode, we may need an intermediate "Summary Step" to condense the Stage 2 critiques before feeding them to the Chairman.

## 8. Conclusion
The "Consensus Model" has evolved from a simple alternative synthesis mode into a **foundational data engine** for the entire platform. By enforcing structured evaluation in Stage 2, we have enabled powerful features like Evolution and Feedback Reports, while laying the groundwork for the future Consensus Synthesis mode.
