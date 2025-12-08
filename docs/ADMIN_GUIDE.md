# Admin Guide

## Managing Personalities

Accordant uses a **Structured Personality System**. This ensures that while each personality has a unique "Soul" (Identity, Tone, Reasoning), they all share a common "Body" (Structure, Metadata) to facilitate effective collaboration in the Council.

### Editing a Personality
When you edit a personality, you will see 6 specific sections:
1.  **IDENTITY & ROLE**: The core persona. Who are they?
2.  **INTERPRETATION OF QUESTIONS**: How do they view user queries?
3.  **PROBLEM DECOMPOSITION**: How do they break down complex tasks?
4.  **ANALYSIS & REASONING**: What is their logical framework?
5.  **DIFFERENTIATION & BIAS**: What specific angle or bias do they represent?
6.  **TONE**: What is their voice?

You do **not** need to define the output format (e.g., "Start with Analysis..."). This is handled automatically by the system.

### System Enforced Structure
In the "System Prompts" configuration, you can define:
*   **Enforced Response Structure**: The headings and organization every personality must use.
*   **Enforced Meta**: The metadata block (e.g., Confidence Score) that every personality must append.

Changing these in System Prompts will instantly update *all* personalities.

## Default vs. Organization Prompts

The system uses a smart **Inheritance Model** to manage configurations:

1.  **Global Defaults**: The system ships with "Default" configuration for Prompts and Personalities.
2.  **Organization Overrides**: Each organization "inherits" these defaults automatically.
3.  **Customization**:
    *   **Prompts**: In the System Prompts editor, you can toggle "Inherit from Default" off to customize any prompt. If you customize it, your organization will no longer receive updates to that specific prompt. You can revert to default at any time.
    *   **Personalities**: System Personalities (marked with a lock icon) are read-only. To edit one, click "Customize" to create a local copy (Shadowing). This copy will override the system original for your organization.

## Other Configurations
...
