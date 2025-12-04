"""Helper functions for council orchestration."""

import datetime
import re
from collections import defaultdict
from typing import Any

from .config.personalities import DEFAULT_RANKING_PROMPT
from .schema import MessageDict, Stage2Result

# Constants for magic strings
FINAL_RANKING_MARKER = "FINAL RANKING:"
RESPONSE_LABEL_PREFIX = "Response "


def get_time_instructions() -> tuple[str, str]:
    """
    Returns both time instructions as a tuple.

    Returns:
        Tuple of (system_time_instruction, user_time_instruction)
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_instruction = f"Current System Time: {now}. You are operating in the present. Use this as your temporal anchor."
    user_instruction = f"[SYSTEM NOTE: The current date and time is {now}. Answer the following query using this as the present moment.]\n\n"
    return system_instruction, user_instruction


def get_system_time_instruction() -> str:
    """Returns the time instruction for the System Prompt."""
    system_instruction, _ = get_time_instructions()
    return system_instruction


def get_user_time_instruction() -> str:
    """Returns the time instruction to prepend to the User Message."""
    _, user_instruction = get_time_instructions()
    return user_instruction


def prepare_history_context(history_context: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Prepare history context by excluding the last user message if present.

    This helper function is used to avoid duplicating the current user query
    in the message chain, since it's typically added separately with time instructions.

    Args:
        history_context: List of message dicts with 'role' and 'content' keys

    Returns:
        History context with the last user message excluded if present,
        otherwise returns the original history context unchanged.
    """
    if history_context and history_context[-1]["role"] == "user":
        return history_context[:-1]
    return history_context


def build_message_chain(
    system_prompt: str, history: list[MessageDict], user_query: str
) -> list[MessageDict]:
    """
    Build a message chain for LLM queries.

    Constructs a standardized message array with system prompt, history context,
    and user query. This helper ensures consistent message construction across
    all stages.

    Args:
        system_prompt: System prompt to include at the start
        history: List of previous messages (will be prepared with prepare_history_context)
        user_query: Current user query to append

    Returns:
        Complete message chain ready for LLM API call
    """
    messages: list[MessageDict] = [{"role": "system", "content": system_prompt}]

    if history:
        history_to_add = prepare_history_context(history)
        messages.extend(history_to_add)

    messages.append({"role": "user", "content": user_query})
    return messages


def build_ranking_prompt(
    user_query: str, responses_text: str, exclude_self: bool = False, prompt_template: str = None
) -> str:
    """
    Build the ranking prompt template for Stage 2.

    Args:
        user_query: The original user question
        responses_text: Formatted text containing all responses to evaluate
        exclude_self: If True, uses "peers" language.
        prompt_template: Optional custom prompt template. Defaults to DEFAULT_RANKING_PROMPT.

    Returns:
        Complete ranking prompt string.
    """
    peer_text = "your peers (anonymized)" if exclude_self else "different models (anonymized)"

    template = prompt_template if prompt_template else DEFAULT_RANKING_PROMPT

    if template:
        return template.format(
            user_query=user_query,
            responses_text=responses_text,
            peer_text=peer_text,
            FINAL_RANKING_MARKER=FINAL_RANKING_MARKER,
            RESPONSE_LABEL_PREFIX=RESPONSE_LABEL_PREFIX,
        )

    return "Error: Ranking prompt not configured."


def build_llm_history(messages: list[dict[str, Any]], max_turns: int = 10) -> list[MessageDict]:
    """
    Convert storage messages to LLM-friendly format with sliding window.
    Strips internal state and keeps only the Final Answer content.
    """
    llm_history = []

    # Filter for user and assistant messages
    relevant_messages = [m for m in messages if m["role"] in ("user", "assistant")]

    # Apply sliding window (keep last N turns)
    # A "turn" is a user message + assistant message pair, so 2 * max_turns
    if len(relevant_messages) > max_turns * 2:
        relevant_messages = relevant_messages[-(max_turns * 2) :]

    for msg in relevant_messages:
        if msg["role"] == "user":
            llm_history.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            # Extract Final Answer from Stage 3
            stage3_response = msg.get("stage3", {}).get("response", "")
            final_answer = stage3_response

            # Parse out "PART 2: FINAL ANSWER" if present
            if "PART 2: FINAL ANSWER" in stage3_response:
                parts = stage3_response.split("PART 2: FINAL ANSWER")
                if len(parts) > 1:
                    final_answer = parts[1].strip()
                    # Remove any leading colon or whitespace
                    if final_answer.startswith(":"):
                        final_answer = final_answer[1:].strip()

            llm_history.append({"role": "assistant", "content": final_answer})

    return llm_history


def parse_ranking_from_text(ranking_text: str) -> list[str]:
    """
    Parse the FINAL RANKING section from the model's response.

    Args:
        ranking_text: The full text response from the model

    Returns:
        List of response labels in ranked order
    """
    # Look for FINAL_RANKING_MARKER section
    if FINAL_RANKING_MARKER in ranking_text:
        # Extract everything after FINAL_RANKING_MARKER
        parts = ranking_text.split(FINAL_RANKING_MARKER)
        if len(parts) >= 2:
            ranking_section = parts[1]
            # Try to extract numbered list format (e.g., "1. Response A")
            # This pattern looks for: number, period, optional space, "Response X"
            response_pattern = rf"\d+\.\s*{re.escape(RESPONSE_LABEL_PREFIX)}[A-Z]"
            numbered_matches = re.findall(response_pattern, ranking_section)
            if numbered_matches:
                # Extract just the "Response X" part
                label_pattern = rf"{re.escape(RESPONSE_LABEL_PREFIX)}[A-Z]"
                return [re.search(label_pattern, m).group() for m in numbered_matches]

            # Fallback: Extract all "Response X" patterns in order
            label_pattern = rf"{re.escape(RESPONSE_LABEL_PREFIX)}[A-Z]"
            matches = re.findall(label_pattern, ranking_section)
            return matches

    # Fallback: try to find any "Response X" patterns in order
    label_pattern = rf"{re.escape(RESPONSE_LABEL_PREFIX)}[A-Z]"
    matches = re.findall(label_pattern, ranking_text)
    return matches


def calculate_aggregate_rankings(
    stage2_results: list[Stage2Result], label_to_model: dict[str, str]
) -> list[dict[str, Any]]:
    """
    Calculate aggregate rankings across all models.

    Args:
        stage2_results: Rankings from each model
        label_to_model: Mapping from anonymous labels to model names

    Returns:
        List of dicts with model name and average rank, sorted best to worst
    """
    # Track positions for each model
    model_positions = defaultdict(list)

    for ranking in stage2_results:
        ranking_text = ranking["ranking"]

        # Parse the ranking from the structured format
        parsed_ranking = parse_ranking_from_text(ranking_text)

        for position, label in enumerate(parsed_ranking, start=1):
            if label in label_to_model:
                model_name = label_to_model[label]
                model_positions[model_name].append(position)

    # Calculate average position for each model
    aggregate = []
    for model, positions in model_positions.items():
        if positions:
            avg_rank = sum(positions) / len(positions)
            aggregate.append(
                {
                    "model": model,
                    "average_rank": round(avg_rank, 2),
                    "rankings_count": len(positions),
                }
            )

    # Sort by average rank (lower is better)
    aggregate.sort(key=lambda x: x["average_rank"])

    return aggregate
