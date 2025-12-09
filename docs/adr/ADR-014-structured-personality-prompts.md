# ADR 014: Structured Personality Prompts

## Status

Accepted

## Context

The original personality system (ADR-005, ADR-007) treated the `personality_prompt` as a single monolithic string string. This approach had several limitations:

1. **Inconsistent Structure:** It was difficult to ensure all personalities followed a consistent framework (e.g., separating "Identity" from "Analysis").
2. **Hard to Enforce Global Standards:** Updating the output format or meta-requirements for *all* personalities required manually editing every single file.
3. **UI Complexity:** A single large text area was daunting for users and didn't guide them towards best practices.
4. **Unused Metadata:** Fields like `avatar`, `color`, `group`, and `tags` were present in the schema but largely unused or redundant, adding noise to the UI.

## Decision

We have decided to move to a **Structured Personality Architecture**.

### 1. Separation of Concerns

The personality prompt is now divided into two distinct categories:

* **The "Soul" (Editable):** Unique characteristics of the specific persona.
    1. **IDENTITY & ROLE:** Who they are.
    2. **INTERPRETATION OF QUESTIONS:** How they interpret queries.
    3. **PROBLEM DECOMPOSITION:** How they break down problems.
    4. **ANALYSIS & REASONING:** Their core reasoning style.
    5. **DIFFERENTIATION & BIAS:** What makes them unique/biased.
    6. **TONE:** Their voice.

* **The "Body" (Enforced):** Global constraints and output formats enforced by the system.
    1. **RESPONSE STRUCTURE:** Mandated headings and sections.
    2. **META:** Mandated metadata blocks (e.g., Confidence Score).

### 2. Schema Changes

* `personality_prompt` in `Personality` model now accepts a `dict[str, str]` corresponding to the 6 editable sections.
* **Storage Keys**: The keys in the dictionary are stored in `snake_case` (e.g., `identity_and_role`), while the system automatically maps them to display headers (e.g., "**IDENTITY & ROLE**") when constructing the prompt.
* `SystemPromptsConfig` now includes `stage1_response_structure` and `stage1_meta_structure`.
* Unused UI fields (`tags`, `group`, `color`, `avatar`) are deprecated in the UI but preserved in the schema for backward compatibility if needed, though they are no longer exposed in the editor.

### 3. Runtime Composition

At runtime (specifically in `Stage 1`), the system dynamically assembles the full system prompt:
`Base System Prompt` + `Time Instructions` + `[Formatted Editable Sections]` + `[Enforced Sections]`

### 4. Migration

Existing string-based prompts are strictly migrated. If a prompt is a string, it is moved entirely into the "IDENTITY & ROLE" section. Users can then manually refactor if desired.

## Consequences

* **Improved Consistency:** All personalities now adhere to global output standards automatically.
* **Easier Management:** Admins can tweak the global output format in one place (`System Prompts`).
* **Better UX:** The new editor provides clear guidance on how to define a personality.
* **Breaking Change:** Direct API consumers expecting a string for `personality_prompt` will receive a dictionary. The frontend has been updated to handle this.
