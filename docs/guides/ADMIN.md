# Admin Guide

## Admin Dashboard
(Instance Admin Only)

When you log in as an Instance Admin, you are greeted by the **Admin Dashboard**. This high-level view provides a real-time pulse of the system:
*   **Total Organizations**: Number of active tenant organizations.
*   **Total Users**: Global user count across all organizations.
*   **Active Conversations**: Number of conversations active in the last 24 hours.

## Organization Management
(Instance Admin Only)

Navigate to the **Organizations** tab to manage the tenants of your Accordant instance.

*   **Create Organization**: Use the "Create" button to onboard a new tenant.
*   **Edit Organization**: Click the "Edit" icon to rename an organization or update its API configuration (Base URL).
*   **Delete Organization**: In the "Danger Zone" of an organization's details, you can permanently delete an organization and all its associated data. **This action is irreversible.**

## User Management
(Org Admin & Instance Admin)

Navigate to the **Users** tab to manage access within your organization.

*   **Role Management**: You can promote a User to an "Admin" (Organization Admin) or demote them back to a standard User.
*   **Remove User**: If a member leaves your organization, you can remove them from the list. They will no longer be able to log in to your tenant.
*   **Invitations**: Generate time-limited invite codes to onboard new team members securely.

## Managing Personalities

Accordant uses a **Structured Personality System**. This ensures that while each personality has a unique "Soul" (Identity, Tone, Reasoning), they all share a common "Body" (Structure, Metadata) to facilitate effective collaboration in the Council.

### Editing a Personality

When you edit a personality, you will see 6 specific sections:

1. **IDENTITY & ROLE**: The core persona. Who are they?
2. **INTERPRETATION OF QUESTIONS**: How do they view user queries?
3. **PROBLEM DECOMPOSITION**: How do they break down complex tasks?
4. **ANALYSIS & REASONING**: What is their logical framework?
5. **DIFFERENTIATION & BIAS**: What specific angle or bias do they represent?
6. **TONE**: What is their voice?

You do **not** need to define the output format (e.g., "Start with Analysis..."). This is handled automatically by the system.

### System Enforced Structure

In the "System Prompts" configuration, you can define:

* **Enforced Response Structure**: The headings and organization every personality must use.
* **Enforced Meta**: The metadata block (e.g., Confidence Score) that every personality must append.
* **Evolution Prompt**: The instructions used when combining personalities. You can customize how parents are merged and what traits are prioritized.

Changing these in System Prompts will instantly update *all* personalities.

## Default vs. Organization Prompts

The system uses a smart **Inheritance Model** to manage configurations:

1. **Global Defaults**: The system ships with "Default" configuration for Prompts and Personalities.
2. **Organization Overrides**: Each organization "inherits" these defaults automatically.
3. **Customization**:
    * **Prompts**: In the System Prompts editor, you can toggle "Inherit from Default" off to customize any prompt. If you customize it, your organization will no longer receive updates to that specific prompt. You can revert to default at any time.
    * **Personalities**: System Personalities (marked with a lock icon) are read-only. To edit one, click "Customize" to create a local copy (Shadowing). This copy will override the system original for your organization.

## Personality League Table

The League Table ranks personalities based on their performance in Council sessions.

* **Win Rate**: Percentage of sessions where the personality was ranked #1 by peers.
* **Average Rank**: The average position (1st, 2nd, 3rd) assigned to the personality.

### Qualitative Feedback

Expanding a row in the League Table reveals **Community Feedback**. This is a synthesized summary of what *other* personalities have said about this specific member during voting. It identifies:

* recurring Strengths
* recurring Weaknesses

## Personality Evolution

You can use the **Evolution System** to improve your council over time.

### Combining Personalities

Select 2-3 "Parent" personalities to merge into a new "Offspring".

1. Go to the **Evolution** tab.
2. Select the parents.
3. Enter a name for the new personality.
4. Click **Evolution Combine**.

The system will use an LLM to synthesize a new profile that attempts to **preserve the strengths** and **mitigate the weaknesses** of the parents, based on the qualitative feedback logs.

### Deactivating Personalities

If a personality (System or Custom) is underperforming:

1. Go to the **Profiles** tab.
2. Toggle the "Enable/Disable" switch on the card.
    * **Custom Personalities**: Are immediately disabled.
    * **System Personalities**: Are "Shadowed" first (a local copy is created) and then disabled for your organization.

## Privacy & Security

Accordant uses a **Federated Privacy Model**.

* **Organization Admins**: Have full access to your organization's conversation logs, voting history, and qualitative feedback texts.
* **Instance Admin (System Operator)**: Can see aggregated metrics (e.g., "Personality A won 50 times across all orgs") but **cannot** see the content of any conversation or the specific reasoning behind votes. Your data remains private.
