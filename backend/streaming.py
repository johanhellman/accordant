"""Streaming orchestration for LLM Council."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from .council import (
    generate_conversation_title,
    stage1_collect_responses,
    stage2_collect_rankings,
    stage3_synthesize_final,
)
from .council_helpers import calculate_aggregate_rankings
from .storage import add_assistant_message, add_user_message, update_conversation_title
from .voting_history import record_votes

logger = logging.getLogger(__name__)


def _sse_event(event_type: str, data: dict[str, Any]) -> str:
    """Helper to format data as an SSE event."""
    return f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"


async def _execute_stage1_stream(
    user_query: str, messages: list[dict[str, Any]], org_id: str, api_key: str, base_url: str
) -> list[dict[str, Any]]:
    """
    Execute Stage 1 and return results.

    Args:
        user_query: The user's message
        messages: Current conversation messages
        org_id: The organization ID

    Returns:
        Stage 1 results
    """
    return await stage1_collect_responses(user_query, messages, org_id, api_key, base_url)


async def _execute_stage2_stream(
    user_query: str,
    stage1_results: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    conversation_id: str,
    conversation_history: dict[str, Any],
    org_id: str,
    api_key: str,
    base_url: str,
) -> tuple[list[dict[str, Any]], dict[str, str], list[dict[str, Any]]]:
    """
    Execute Stage 2, record votes, and return results.

    Args:
        user_query: The user's message
        stage1_results: Results from Stage 1
        messages: Current conversation messages
        conversation_id: ID of the conversation
        conversation_history: Full conversation object
        org_id: The organization ID

    Returns:
        Tuple of (stage2_results, label_to_model, aggregate_rankings)
    """
    stage2_results, label_to_model = await stage2_collect_rankings(
        user_query, stage1_results, messages, org_id, api_key, base_url
    )
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

    # Record votes
    try:
        turn_number = (len(messages) + 1) // 2
        record_votes(
            conversation_id,
            stage2_results,
            label_to_model,
            conversation_title=conversation_history.get("title", "Unknown"),
            turn_number=turn_number,
            user_id=conversation_history.get("user_id"),
            org_id=org_id,
        )
    except Exception as e:
        logger.error(f"Error recording votes: {e}")

    return stage2_results, label_to_model, aggregate_rankings


async def _execute_stage3_stream(
    user_query: str,
    stage1_results: list[dict[str, Any]],
    stage2_results: list[dict[str, Any]],
    label_to_model: dict[str, str],
    messages: list[dict[str, Any]],
    org_id: str,
    api_key: str,
    base_url: str,
) -> dict[str, Any]:
    """
    Execute Stage 3 and return final result.

    Args:
        user_query: The user's message
        stage1_results: Results from Stage 1
        stage2_results: Results from Stage 2
        label_to_model: Mapping from labels to model names
        messages: Current conversation messages
        org_id: The organization ID

    Returns:
        Stage 3 result
    """
    return await stage3_synthesize_final(
        user_query,
        stage1_results,
        stage2_results,
        label_to_model,
        messages,
        org_id,
        api_key,
        base_url,
    )


async def run_council_streaming(
    conversation_id: str,
    user_query: str,
    conversation_history: dict[str, Any],
    org_id: str,
    api_key: str,
    base_url: str,
) -> AsyncGenerator[str, None]:
    """
    Run the council process and yield SSE events.

    Args:
        conversation_id: The conversation ID
        user_query: The user's message content
        conversation_history: The full conversation object
        org_id: The organization ID

    Yields:
        SSE data strings (e.g., "data: {...}\n\n")
    """
    # Check if this is the first message
    is_first_message = len(conversation_history["messages"]) == 0

    try:
        # Add user message
        add_user_message(conversation_id, user_query, org_id)

        # FIX: Update in-memory conversation to include the new message so it's not stale
        conversation_history["messages"].append({"role": "user", "content": user_query})

        # Start title generation in parallel (don't await yet)
        title_task = None
        if is_first_message:
            title_task = asyncio.create_task(
                generate_conversation_title(user_query, org_id, api_key, base_url)
            )

        # Stage 1: Collect responses
        yield _sse_event("stage_start", {"stage": 1, "name": "Individual Responses"})
        stage1_results = await _execute_stage1_stream(
            user_query, conversation_history["messages"], org_id, api_key, base_url
        )
        yield _sse_event("stage1_complete", {"results": stage1_results})

        # Stage 2: Collect rankings
        yield _sse_event("stage_start", {"stage": 2, "name": "Peer Ranking"})
        stage2_results, label_to_model, aggregate_rankings = await _execute_stage2_stream(
            user_query,
            stage1_results,
            conversation_history["messages"],
            conversation_id,
            conversation_history,
            org_id,
            api_key,
            base_url,
        )
        yield _sse_event(
            "stage2_complete",
            {
                "results": stage2_results,
                "metadata": {
                    "label_to_model": label_to_model,
                    "aggregate_rankings": aggregate_rankings,
                },
            },
        )

        # Stage 3: Synthesize final answer
        yield _sse_event("stage_start", {"stage": 3, "name": "Final Synthesis"})
        stage3_result = await _execute_stage3_stream(
            user_query,
            stage1_results,
            stage2_results,
            label_to_model,
            conversation_history["messages"],
            org_id,
            api_key,
            base_url,
        )
        yield _sse_event("stage3_complete", {"results": stage3_result})

        # Wait for title generation if it was started
        if title_task:
            title = await title_task
            update_conversation_title(conversation_id, title, org_id)
            yield _sse_event("title_complete", {"title": title})

        # Save complete assistant message
        add_assistant_message(
            conversation_id, stage1_results, stage2_results, stage3_result, org_id
        )

        # Send completion event
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"

    except Exception as e:
        logger.error(f"Error in streaming council: {e}")
        # Send error event
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
