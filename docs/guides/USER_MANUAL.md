# Accordant User Manual

## Introduction
Accordant is an orchestration platform that leverages a "Council" of AI personalities to provide comprehensive, high-quality answers. Instead of relying on a single AI model, Accordant consults multiple specialized personalities, peer-reviews their outputs, and synthesizes a final best-in-class response.

## 1. The Chat Interface
The core of Accordant is the Chat Interface, where you interact with the AI Council.

### 1.1 The 3-Stage Process
Every query goes through a rigorous 3-stage process:

1.  **Stage 1: Initial Consultation**
    *   Your query is sent to multiple active AI Personalities simultaneously.
    *   Each personality generates an independent response based on its specific expertise (e.g., "The Skeptic", "The Visionary").
    *   **Goal**: Gather diverse perspectives.

2.  **Stage 2: Peer Review & Ranking**
    *   The personalities review each other's responses blindly.
    *   They rank the responses based on accuracy, completeness, and adherence to instructions.
    *   **Goal**: Filter out hallucinations and identify the strongest elements.

3.  **Stage 3: Chairman Synthesis**
    *   The "Chairman" AI analyzes all responses and the peer review data.
    *   It synthesizes a final, authoritative answer that combines the best insights from the council.
    *   **Goal**: Deliver a single, high-quality answer.

## 2. Managing Personalities
(Admin Only) The Personality Manager allows you to configure the council members.

### 2.1 Viewing Personalities
*   Navigate to the **Personalities** tab.
*   You will see a list of System Defaults (provided by Accordant) and Custom Personalities (created by your organization).

### 2.2 Creating a Personality
1.  Click **"Add Personality"**.
2.  **Name**: Give it a descriptive name.
3.  **Model**: Select the underlying LLM (e.g., GPT-4, Gemini).
4.  **Instructions**: Define its behavior.
    *   *System Prompt*: The core instruction.
    *   *Ranking Instruction*: How it should evaluate others.
    *   *Identity*: Its tone and style.

### 2.3 Evolution (Combining Personalities)
You can breed new personalities by combining existing ones!
1.  Go to the **Evolution Panel** (often within Personality Manager).
2.  Select 2-3 "Parent" personalities.
3.  Click **"Combine"**.
4.  The system will generate a new "Offspring" personality that attempts to merge the strengths of its parents.

## 3. League Table & Voting
The League Table tracks the performance of your AI council.

*   **Win Rate**: The percentage of time a personality's response was ranked highly by peers.
*   **Average Rank**: Its average position in peer reviews (Lower is better).
*   **Sessions**: Number of conversations it has participated in.
*   **Community Feedback**: Qualitative summary of what users liked/disliked about this personality's outputs.

## 4. Organization Management
(Instance Admin Only)
*   **Invitations**: Generate invite codes for new users to join your organization.
*   **Settings**: Configure API keys (OpenRouter) and base URLs.

## 5. User Settings
Every user has access to their personal settings page to manage their profile and security.

*   **Profile**: Update your display name.
*   **Change Password**: Securely update your login password.
*   **Export Data**: Request a download of your personal conversation history in JSON format.
*   **Delete Account**: Permanently delete your personal account and data from the system. **Warning: This cannot be undone.**
