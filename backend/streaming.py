"""Streaming orchestration for LLM Council (Async Task Based)."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from .council import (
    generate_conversation_title,
    run_council_cycle,
)
from .storage import (
    add_assistant_message,
    add_user_message,
    update_conversation_status,
    update_conversation_title,
)
from .voting_history import record_votes

logger = logging.getLogger(__name__)


def _sse_event(event_type: str, data: dict[str, Any]) -> str:
    """Helper to format data as an SSE event."""
    return f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"


class CouncilManager:
    """
    Manages async background tasks for Council consultations.
    Ensures that once started, a consultation finishes even if the client disconnects.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.active_queues = {}  # conv_id -> asyncio.Queue
        return cls._instance

    def _get_queue(self, conversation_id: str) -> asyncio.Queue:
        if conversation_id not in self.active_queues:
            self.active_queues[conversation_id] = asyncio.Queue()
        return self.active_queues[conversation_id]

    def _cleanup(self, conversation_id: str):
        if conversation_id in self.active_queues:
            del self.active_queues[conversation_id]

    async def _emit(self, conversation_id: str, event_type: str, data: dict[str, Any] = None):
        """Put an event into the queue if it exists."""
        if conversation_id in self.active_queues:
            queue = self.active_queues[conversation_id]
            await queue.put(_sse_event(event_type, data or {}))

    async def _emit_raw(self, conversation_id: str, raw_sse: str):
        if conversation_id in self.active_queues:
            await self.active_queues[conversation_id].put(raw_sse)

    async def run_task(
        self,
        conversation_id: str,
        user_query: str,
        conversation_history: dict[str, Any],
        org_id: str,
        api_key: str,
        base_url: str,
        consensus_enabled: bool = False,
    ):
        """
        The Background Worker.
        Executes the council logic via the shared generator, updates DB status, and feeds the stream queue.
        This must NEVER raise an exception out to the caller, or it crashes the Task.
        """
        try:
            logger.info(f"Starting async council task for {conversation_id}")
            update_conversation_status(conversation_id, "active", org_id)

            # Check if this is the first message
            is_first_message = len(conversation_history["messages"]) == 0

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(
                    generate_conversation_title(user_query, org_id, api_key, base_url)
                )

            # Ensure messages list includes current user query (handle stale snapshot)
            messages = conversation_history["messages"]
            if (
                not messages
                or messages[-1].get("role") != "user"
                or messages[-1].get("content") != user_query
            ):
                # Snapshot is stale or missing the new message, append it
                messages = messages + [{"role": "user", "content": user_query}]

            # Variables to hold results for final persistence
            final_stage1_results = []
            final_stage2_results = []
            final_stage3_result = {}

            # Iterate over the shared generator
            async for event in run_council_cycle(
                user_query,
                messages,
                org_id,
                api_key,
                base_url,
                consensus_enabled=consensus_enabled,
                user_id=conversation_history.get("user_id"),
            ):
                event_type = event["type"]
                data = event["data"]

                # Emit event to client
                await self._emit(conversation_id, event_type, data)

                # Handle Side Effects based on event type
                if event_type == "stage1_complete":
                    final_stage1_results = data["results"]

                elif event_type == "stage2_complete":
                    final_stage2_results = data["results"]
                    label_to_model = data["metadata"]["label_to_model"]

                    # Record Votes (DB Side Effect)
                    try:
                        turn_number = (len(messages) + 1) // 2
                        record_votes(
                            conversation_id,
                            final_stage2_results,
                            label_to_model,
                            conversation_title=conversation_history.get("title", "Unknown"),
                            turn_number=turn_number,
                            user_id=conversation_history.get("user_id"),
                            org_id=org_id,
                        )
                    except Exception as e:
                        logger.error(f"Error recording votes: {e}")

                elif event_type == "stage3_complete":
                    final_stage3_result = data["results"]

            # Wait for title generation
            if title_task:
                try:
                    title = await title_task
                    update_conversation_title(conversation_id, title, org_id)
                    await self._emit(conversation_id, "title_complete", {"title": title})
                except Exception as e:
                    logger.error(f"Title generation failed: {e}")

            # Save Result (The Critical Part)
            if final_stage1_results and final_stage3_result:
                add_assistant_message(
                    conversation_id,
                    final_stage1_results,
                    final_stage2_results,
                    final_stage3_result,
                    org_id,
                )

            # Finish
            await self._emit_raw(conversation_id, f"data: {json.dumps({'type': 'complete'})}\n\n")
            update_conversation_status(conversation_id, "idle", org_id)
            logger.info(f"Async council task finished for {conversation_id}")

        except Exception as e:
            logger.error(f"Error in async council task: {e}", exc_info=True)
            update_conversation_status(conversation_id, "error", org_id)
            await self._emit_raw(
                conversation_id, f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            )

        finally:
            # Signal end of stream logic
            # We do NOT remove the queue immediately if we want to support "late joiners"
            pass


async def run_council_generator(
    conversation_id: str,
    user_query: str,
    conversation_history: dict[str, Any],
    org_id: str,
    api_key: str,
    base_url: str,
    consensus_enabled: bool = False,
) -> AsyncGenerator[str]:
    """
    Entry point for the API.
    Spawns the background task if not running, and yields from the queue.
    """
    manager = CouncilManager()
    queue = manager._get_queue(conversation_id)

    # Add user message to DB immediately (synchronous part provided by caller usually, but we ensure here)
    # The caller (main.py) already did valid checks.

    # Add user message to DB immediately
    # This ensures it is saved before processing starts
    try:
        add_user_message(conversation_id, user_query, org_id)
    except Exception as e:
        logger.error(f"Failed to save user message: {e}")
        # We process anyway to not break the flow, or should we raise?
        # If we don't save, history will be broken. Better to log for now.
        yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to save message'})}\n\n"
        return

    # Spawn background task
    asyncio.create_task(
        manager.run_task(
            conversation_id,
            user_query,
            conversation_history,
            org_id,
            api_key,
            base_url,
            consensus_enabled=consensus_enabled,
        )
    )

    # Yield from queue
    try:
        while True:
            # Wait for next event
            # We use a timeout to prevent infinite hanging if task dies silently (though we have try/except)
            chunk = await asyncio.wait_for(queue.get(), timeout=1200.0)  # 20 min timeout
            yield chunk

            # Check for termination signals
            # This is a bit "stringy" but simple for SSE
            if '"type": "complete"' in chunk or '"type": "error"' in chunk:
                break

    except asyncio.CancelledError:
        logger.warning(
            f"Client disconnected from stream {conversation_id}. Task continues running."
        )
        # We do NOT cancel the manager task. That's the whole point!
        raise
    except Exception as e:
        logger.error(f"Error in stream generator: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': 'Stream connection error'})}\n\n"
    finally:
        # Cleanup queue listener
        manager._cleanup(conversation_id)
