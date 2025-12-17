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

## 5. Strategic Consensus Synthesis (Stage 3 Redesign)

Instead of a binary switch between "Ranking" and "Consensus", Stage 3 will support **Swappable Consensus Prompts**. The "Strategy" is not a complex code object, but simply a prompt template that dictates *how* the Chairman synthesizes the unfiltered views from the Council.

### 5.1. Philosophy
*   **Unfiltered Input**: Personalities (Stage 1) and Peer Reviews (Stage 2) remain objective, diverse, and unfiltered. They provide the raw "evidence."
*   **Directed Synthesis**: The Chairman (Stage 3) applies a specific "Lens" to this evidence to generate the final output.

### 5.2. Use Cases
*   **Balanced Consensus**: "Find the middle ground where most personalities agree." (Default)
*   **Risk-Averse**: "Prioritize safety and stability. Reject any high-risk proposals."
*   **Goal-Seeking**: "Prioritize maximum possible outcome for X, accepting higher risk."
*   **Novelty Focus**: "Ignore safe, conventional answers. Synthesize the most novel components from the proposals."

### 5.3. The Consensus Prompt Structure
To ensure reliability, all Consensus Prompts should follow a standard skeleton while allowing the "Directive" to vary.

**Skeleton Template**:
```markdown
# Role
You are the Chairman. You represent the final decision-maker.

# Input Data
You have received proposals from {count} experts and detailed peer evaluations highlighting their strengths and weaknesses.

# STRATEGIC DIRECTIVE (Variable)
[The specific goal goes here. e.g., "Your goal is to maximize efficiency..."]

# Instructions
1. Analyze the "Weaknesses" identified in the peer reviews.
2. Filter out proposals that violate the Strategic Directive.
3. Synthesize a final answer that combines the remaining valid points.

# Output Format
Provide the final answer in the requested format.
```

## 6. API & Configuration

### 6.1. Changes
*   **Flexible Prompting**: The API will use the configured strategy for the organization.
*   **Prompt Registry**: We can maintain a registry of standard generic strategies (e.g., `strategy_risk_averse.md`, `strategy_balanced.md`) in `data/prompts/consensus/`.

### 6.2. Example: Risk-Averse Strategy
> "Your goal is to parse the inputs for any risks identified by the Council. If a high-reward option has a significant weakness, it MUST be discarded. Synthesize the safest, most robust path forward."

### 6.3. Cascading Configuration

The "Strategic Directive" is managed via a strict 2-level configuration system, aligning with our Multi-Tenant architecture:

1.  **System Default** (The "Reasonable Baseline")
    *   *File*: `data/defaults/system-prompts.yaml`
    *   *Key*: `consensus_prompt`
    *   *Behavior*: By default, the system seeks a "balanced synthesis" of all views.

2.  **Organization Override** (Tenant Scoped)
    *   *File*: `data/organizations/{org_id}/config/system-prompts.yaml`
    *   *Behavior*: An organization can override the default to enforce a specific strategy (e.g., "Risk-Averse") for all their interactions. This ensures consistent governance across the tenant.

## 7. Data Model: Contribution Attribution

To support "Contribution Attribution" (tracking which personalities influenced the consensus), we extend the Tenant Database schema.

### 7.1. New Table: `consensus_contributions`
*   **`id`**: UUID (PK)
*   **`conversation_id`**: Foreign Key to Conversations.
*   **`personality_id`**: The ID of the contributing personality.
*   **`strategy`**: The consensus strategy key used (e.g., "risk_averse").
*   **`score`**: Float (0.0 - 1.0) indicating the weight of the contribution (extracted from Chairman metadata).
*   **`reasoning`**: (Optional) Text citation or reason for inclusion.

### 7.2. Attribution Logic
The Chairman's Stage 3 Prompt will now require a metadata block:
```json
{
  "contributors": [
    {"id": "compliance_bot", "weight": 0.8, "reason": "Provided critical regulatory framework"},
    {"id": "creative_bot", "weight": 0.2, "reason": "Suggested the novel UI approach"}
  ]
}
```
This metadata is parsed and stored in the `consensus_contributions` table.

## 8. UX & Analytics

### 8.1. Chat Interface
*   **Synthesis Toggle**: Users can toggle between "Voting Mode" (Winner) and "Consensus Mode" (Synthesis) if the organization allows it.
*   **Attribution Footer**: When in Consensus Mode, the unified answer displays a footer: *"Synthesized from inputs by: [Compliance Bot, Creative Bot]"*.

### 8.2. Analytics Dashboard
*   **Contribution Heatmap**: A new view showing which personalities are most influential in consensus decisions (distinct from who wins the most votes).

## 9. Validation Strategy

*   **Unit Tests**: Verify that the prompt parser correctly extracts the JSON metadata block from the Chairman's output.
*   **E2E Tests**: Verify that toggling the mode changes the displayed answer and that attribution badges appear.

## 10. Conclusion
The "Consensus Model" is a complete end-to-end feature:
1.  **Architecture**: Prompt-based strategies logic.
2.  **Data**: New tables to track contribution attribution.
3.  **UX**: Explicit user controls and transparency via attribution.
This ensures we don't just "merge text" but actually track and credit the valuable components of the Council's diverse thinking.
