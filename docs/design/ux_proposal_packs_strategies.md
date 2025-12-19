# UX Proposal: Council Packs & Strategy Management

## 1. Navigation Redesign
The current nesting of "Council Personalities" hides important configuration options. We propose expanding the **Council Setup** section in the **Sidebar** to make these features first-class citizens.

**Current Sidebar:**
```
Council Setup
  └─ Personalities (Contains tabs for Evolution, System Prompts, etc.)
```

**Proposed Sidebar:**
```
Council Setup
  ├─ Personalities (Manages Agents and Evolution)
  ├─ Council Packs (New: Gallery & Management)
  ├─ Strategies    (New: Consensus Strategy Configuration)
  └─ System Prompts (Moved from Personalities tab to top-level)
```
*Rationale*: This exposes "Packs" and "Strategies" immediately given their importance. "System Prompts" are also elevated to clear up the confusion about where they sit.

## 2. Page Breakdowns

### A. Council Packs (`/config/packs`)
A visual "Pack Gallery" interface.
-   **View**: Grid of cards showing System Packs and Custom Packs.
-   **Card Content**: Title, Description, "System/Custom" badge, list of included Personalities (avatars).
-   **Actions**:
    -   **"Activate"**: Sets this pack as the user's active default.
    -   **"Edit/Clone"**: Opens pack editor (for custom packs).
    -   **"View Details"**: Shows full configuration (prompts, specific strategies).

### B. Consensus Strategies (`/config/strategies`)
A CRUD interface for managing how the council reaches consensus.
-   **List View**: Table/List of available strategies (e.g., "Standard Debate", "Blind Voting", "Custom Optimistic").
-   **Editor**: Monaco Code Editor for editing the Strategy Prompt (Markdown/Jinja2).
-   **Metadata**: Name, Description, System vs Custom.

### C. Personalities Page Refinement (`/personalities`)
-   Remove "System Prompts" tab (move to top-level `System Prompts` page).
-   **Move "Voting History" and "League Table"**: These are analytics. We will group them into a single "Voting Insights" tab on this page for now, but mark them as candidates for a dedicated "Analytics" section in the future.

## 3. "New Session" Experience
Currently, "New Session" creates a conversation instantly with defaults. This prevents users from choosing a specific Pack or Strategy for *just one conversation*.

**Proposed Change:**
Clicking **"+ New Session"** opens a **Configuration Modal** (instead of instant redirect):

**New Session Modal:**
1.  **Topic/Title** (Optional)
2.  **Choose Council Pack** (Dropdown/Card Select):
    -   *Default selected*: User's Active Pack.
    -   *Options*: All available packs.
3.  **Advanced Overrides** (Collapsible):
    -   **Strategy**: Default from Pack, but can override (e.g., force "Blind Voting").
    -   **Personalities**: Default from Pack, but can add/remove specific members.
4.  **Confirm Button**: "Start Session"

*Benefit*: Use a specific "Creative Writing" pack for one task, and "Code Review" pack for another, without changing global settings.

## 4. Addressing Feedback & Questions

**Q1: Where should System Prompts sit?**
**A:** We have promoted them to a top-level item: `Council Setup > System Prompts`. This removes them from the "Personalities" page where they were hard to find.

**Q2: How to present statistics on Council Packs/Strategies?**
**A:** We should add a **Usage Insights** tab to the **Organization Dashboard** (for Instance Admins).
*   *Implementation Note*: Currently, our database tracks `strategy` in `consensus_contributions`, but does *not* explicitly link Conversations to `pack_id`. We will need a future Migration (v4) to add `pack_id` and `strategy_id` columns to the `conversations` table to enable robust "Usage by Pack" charts. For now, we can show "Active Configuration" stats (how many users have X pack active).

**Q3: How should the League Table reflect Packs/Strategies?**
**A:** The League Table is primarily about *Personality Influence*. To filter by Pack/Strategy, we would need the database changes mentioned above.
*   *Phase 1*: League Table remains global (all-time).
*   *Phase 2 (Future)*: Add dropdowns to League Table: "Filter by Pack Used" or "Filter by Strategy". This requires the schema update to track *which* pack was active during the vote.

**Q4: Documentation Updates?**
**A:** We need to update:
1.  **User Manual**: Add sections for "Managing Packs" and "Creating Custom Strategies".
2.  **Architecture**: Update `council-packs.md` to reflect the frontend structure.
3.  **Developer Guide**: Document the new `New Session` flow and how to add new System Packs via code.

## 5. Summary of Work (Frontend)
1.  **Sidebar Update**: Add routes/links for Packs, Strategies, and System Prompts.
2.  **New Pages**: Create `PacksPage.jsx`, `StrategiesPage.jsx`, `SystemPromptsPage.jsx`.
3.  **New Components**:
    -   `PackGallery`: Component for viewing/selecting packs.
    -   `StrategyManager`: Component for listing/editing strategies.
    -   `NewSessionModal`: Intercept "New Session" click.
4.  **Cleanup**: Refactor `PersonalityManager` to remove "System Prompts" and move navigation logic to Sidebar.
