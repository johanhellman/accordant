"""3-stage LLM Council orchestration."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Any

from .config.packs import PackService
from .config.personalities import (
    format_personality_prompt,
    get_all_personalities,
    load_org_models_config,
    load_org_system_prompts,
)

# Re-export for backward compatibility
from .council_helpers import (
    RESPONSE_LABEL_PREFIX,
    build_llm_history,
    build_message_chain,
    build_ranking_prompt,
    calculate_aggregate_rankings,
    get_time_instructions,
    parse_ranking_from_text,
)
from .database import get_tenant_session
from .openrouter import query_model
from .schema import MessageDict, Stage1Result, Stage2Result, Stage3Result

logger = logging.getLogger(__name__)


async def _stage1_personality_mode(
    user_query: str,
    history_context: list[MessageDict],
    org_id: str,
    api_key: str,
    base_url: str,
    active_personalities: list[dict[str, Any]],
    prompts: dict[str, str],
) -> list[Stage1Result]:
    """
    Stage 1 implementation for personality mode.

    Queries each active personality with their custom system prompts.

    Args:
        user_query: The user's question
        history_context: Prepared history context (from build_llm_history)
        active_personalities: Resolved list of active personality objects
        prompts: Resolved system prompts (merged defaults + pack overrides)

    Returns:
        List of Stage 1 results with personality metadata
    """
    base_system_prompt = prompts["base_system_prompt"]

    active_names = [p["name"] for p in active_personalities]
    logger.info(f"Active Personalities ({len(active_names)}): {', '.join(active_names)}")

    # Prepare tasks for each personality
    tasks = []
    for p in active_personalities:
        # Construct system prompt
        system_time_instruction, user_time_instruction = get_time_instructions()
        system_prompt = (
            base_system_prompt
            + "\n\n"
            + system_time_instruction
            + "\n\n"
            + format_personality_prompt(p, prompts, include_enforced=True)
        )

        # Prepend time instruction to user query
        modified_user_query = user_time_instruction + "\n\n" + user_query

        # Build message chain
        current_messages = build_message_chain(system_prompt, history_context, modified_user_query)

        tasks.append({"personality": p, "messages": current_messages})

    # Execute queries in parallel
    async def query_personality(task):
        p = task["personality"]
        logger.debug(f"Querying personality: {p['name']} (Model: {p['model']})")
        try:
            response = await query_model(
                p["model"],
                task["messages"],
                api_key=api_key,
                base_url=base_url,
                temperature=p.get("temperature"),
            )
            if response:
                logger.debug(f"Personality {p['name']} responded successfully")
            else:
                logger.warning(f"Personality {p['name']} failed to respond (None)")
            return p, response
        except Exception as e:
            logger.error(f"Error querying personality {p['name']}: {e}")
            return p, None

    results = await asyncio.gather(*[query_personality(t) for t in tasks])

    stage1_results: list[Stage1Result] = []
    for p, response in results:
        if response is not None:
            stage1_results.append(
                {
                    "model": p["model"],
                    "response": response.get("content", ""),
                    "personality_id": p["id"],
                    "personality_name": p["name"],
                }
            )
    return stage1_results


async def stage1_collect_responses(
    user_query: str,
    messages: list[dict[str, Any]] | None = None,
    org_id: str = None,
    api_key: str = None,
    base_url: str = None,
    user_id: str = None,
) -> list[Stage1Result]:
    """
    Stage 1: Collect individual responses from all council models.

    Args:
        user_query: The user's question
        messages: Full conversation history (optional)

    Returns:
        List of Stage1Result dicts with 'model', 'response', 'personality_name', 'personality_id' keys
    """
    logger.info("Starting Stage 1: Collecting responses from council members")

    # Resolve Context (Config)
    session = get_tenant_session(org_id)
    try:
        config = PackService.get_active_configuration(session, user_id or "anonymous", org_id)
    finally:
        session.close()

    # Resolve Personalities
    all_personas = get_all_personalities(org_id)
    active_ids = set(config["personalities"])
    active_personalities = [p for p in all_personas if p["id"] in active_ids]

    # Resolve Prompts
    base_prompts = load_org_system_prompts(org_id)
    # Merge overrides (pack prompts overwrite base prompts)
    prompts = {**base_prompts, **config["system_prompts"]}

    # Build history context
    history_context = build_llm_history(messages) if messages else []

    # Route to appropriate implementation
    if active_personalities:
        stage1_results = await _stage1_personality_mode(
            user_query, history_context, org_id, api_key, base_url, active_personalities, prompts
        )
    else:
        logger.warning("No active personalities found for Stage 1.")
        stage1_results = []

    logger.info(f"Stage 1 complete: Collected {len(stage1_results)} responses")
    return stage1_results


async def _stage2_personality_mode(
    user_query: str,
    stage1_results: list[Stage1Result],
    history_context: list[MessageDict],
    org_id: str,
    api_key: str,
    base_url: str,
    active_personalities: list[dict[str, Any]],
    prompts: dict[str, str],
) -> tuple[list[Stage2Result], dict[str, Any]]:
    """
    Stage 2 implementation for personality mode.

    Each personality ranks the anonymized responses of other personalities,
    excluding their own response.

    Args:
        user_query: The original user query
        stage1_results: Results from Stage 1
        history_context: Prepared history context

    Returns:
        Tuple of (rankings list, label_to_model mapping)
    """
    base_system_prompt = prompts["base_system_prompt"]

    logger.info(f"Stage 2: {len(active_personalities)} personalities participating in ranking")

    # Create anonymized labels
    labels = [chr(65 + i) for i in range(len(stage1_results))]  # A, B, C, ...

    # Create mapping from label to model/identity info
    # We now store a dict instead of a simple string name to track ID and Name
    label_to_model = {
        f"{RESPONSE_LABEL_PREFIX}{label}": {
            "name": result.get("personality_name", result["model"]),
            "id": result.get("personality_id"),
            "model": result["model"],
        }
        for label, result in zip(labels, stage1_results, strict=True)
    }

    # Prepare tasks for each personality
    tasks = []
    for p in active_personalities:
        # Filter responses to exclude the current personality's own response
        filtered_responses_text = "\n\n".join(
            [
                f"{RESPONSE_LABEL_PREFIX}{label}:\n{result['response']}"
                for label, result in zip(labels, stage1_results, strict=True)
                if result["personality_id"] != p["id"]
            ]
        )

        # Construct ranking prompt
        specific_ranking_prompt = build_ranking_prompt(
            user_query,
            filtered_responses_text,
            exclude_self=True,
            prompt_template=prompts.get("ranking_prompt"),
            enforced_context=prompts.get("ranking_enforced_context", ""),
            enforced_format=prompts.get("ranking_enforced_format", ""),
        )

        # Construct system prompt
        system_time_instruction, user_time_instruction = get_time_instructions()
        # Construct system prompt
        system_time_instruction, user_time_instruction = get_time_instructions()
        system_prompt = (
            base_system_prompt
            + "\n\n"
            + system_time_instruction
            + "\n\n"
            + format_personality_prompt(p, prompts, include_enforced=False)
        )

        # Prepend time instruction
        modified_ranking_prompt = user_time_instruction + "\n\n" + specific_ranking_prompt

        # Build message chain
        current_messages = build_message_chain(
            system_prompt, history_context, modified_ranking_prompt
        )

        tasks.append({"personality": p, "messages": current_messages})

    # Execute queries in parallel
    async def query_personality_ranking(task):
        p = task["personality"]
        response = await query_model(
            p["model"],
            task["messages"],
            api_key=api_key,
            base_url=base_url,
            temperature=p.get("temperature"),
        )
        return p, response

    results = await asyncio.gather(*[query_personality_ranking(t) for t in tasks])

    stage2_results: list[Stage2Result] = []
    for p, response in results:
        if response is not None:
            full_text = response.get("content", "")
            parsed = parse_ranking_from_text(full_text)
            stage2_results.append(
                {
                    "model": p["model"],
                    "personality_name": p["name"],
                    "personality_id": p.get("id"),
                    "ranking": full_text,
                    "parsed_ranking": parsed,
                }
            )

    return stage2_results, label_to_model


async def stage2_collect_rankings(
    user_query: str,
    stage1_results: list[Stage1Result],
    messages: list[dict[str, Any]] | None = None,
    org_id: str = None,
    api_key: str = None,
    base_url: str = None,
    user_id: str = None,
) -> tuple[list[Stage2Result], dict[str, Any]]:
    """
    Stage 2: Each model ranks the anonymized responses.

    Args:
        user_query: The original user query
        stage1_results: Results from Stage 1
        messages: Full conversation history (optional)

    Returns:
        Tuple of (rankings list, label_to_model mapping)
    """
    logger.info("Starting Stage 2: Collecting rankings from council members")

    # Resolve Context (Config) - Should be cached ideally but for now re-fetch is safer for statelessness
    session = get_tenant_session(org_id)
    try:
        config = PackService.get_active_configuration(session, user_id or "anonymous", org_id)
    finally:
        session.close()

    # Resolve Personalities
    all_personas = get_all_personalities(org_id)
    active_ids = set(config["personalities"])
    active_personalities = [p for p in all_personas if p["id"] in active_ids]

    # Resolve Prompts
    base_prompts = load_org_system_prompts(org_id)
    prompts = {**base_prompts, **config["system_prompts"]}

    # Build history context
    history_context = build_llm_history(messages) if messages else []

    # Convert stage1_results to Stage1Result type for type safety
    typed_stage1_results: list[Stage1Result] = [
        {
            "model": r["model"],
            "response": r["response"],
            "personality_id": r.get("personality_id"),
            "personality_name": r.get("personality_name"),
        }
        for r in stage1_results
    ]

    # Route to appropriate implementation
    if active_personalities:
        stage2_results, label_to_model = await _stage2_personality_mode(
            user_query,
            typed_stage1_results,
            history_context,
            org_id,
            api_key,
            base_url,
            active_personalities,
            prompts,
        )
    else:
        logger.warning("No active personalities found for Stage 2.")
        stage2_results, label_to_model = [], {}

    logger.info(f"Stage 2 complete: Received {len(stage2_results)} rankings")
    return stage2_results, label_to_model


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: list[Stage1Result],
    stage2_results: list[Stage2Result],
    label_to_model: dict[str, dict[str, Any]],  # Updated to be dict of dicts
    messages: list[dict[str, Any]] | None = None,
    org_id: str = None,
    api_key: str = None,
    base_url: str = None,
    user_id: str = None,
) -> Stage3Result:
    """
    Stage 3: Chairman synthesizes final response.

    Args:
        user_query: The original user query
        stage1_results: Individual model responses from Stage 1
        stage2_results: Rankings from Stage 2
        messages: Full conversation history (optional)

    Returns:
        Dict with 'model' and 'response' keys
    """
    logger.info("Starting Stage 3: Synthesizing final response")

    # Resolve Prompts
    # We don't necessarily need personalities here, but we do need prompts
    session = get_tenant_session(org_id)
    try:
        config = PackService.get_active_configuration(session, user_id or "anonymous", org_id)
    finally:
        session.close()

    base_prompts = load_org_system_prompts(org_id)
    prompts = {**base_prompts, **config["system_prompts"]}

    # Build history context
    history_context = build_llm_history(messages) if messages else []
    # Build comprehensive context for chairman
    stage1_text = "\n\n".join(
        [
            f"Model: {result.get('personality_name', result['model'])}\nResponse: {result['response']}"
            for result in stage1_results
        ]
    )

    # Construct detailed voting history for the prompt
    voting_details = []
    for res in stage2_results:
        voter_name = res.get("personality_name", res.get("model", "Unknown Model"))
        # We intentionally do NOT include the model name here to prevent bias
        voter_display = f"{voter_name}"
        rankings = res.get("parsed_ranking", [])

        vote_line = f"Voter: {voter_display}\n"
        for i, label in enumerate(rankings, 1):
            # Resolve label to personality name if available
            target_info_obj = label_to_model.get(label, {})
            target_name = (
                target_info_obj.get("name", "Unknown")
                if isinstance(target_info_obj, dict)
                else target_info_obj
            )

            vote_line += f"   {i}. {target_name} ({label})\n"
        voting_details.append(vote_line)

    voting_details_text = "\n".join(voting_details)

    chairman_prompt_template = prompts["chairman_prompt"]
    models_config = load_org_models_config(org_id)
    chairman_model = models_config["chairman_model"]

    chairman_prompt = chairman_prompt_template.format(
        user_query=user_query, stage1_text=stage1_text, voting_details_text=voting_details_text
    )

    system_time_instruction, user_time_instruction = get_time_instructions()
    modified_chairman_prompt = user_time_instruction + "\n\n" + chairman_prompt

    # Build message chain using helper
    current_messages = build_message_chain(
        system_time_instruction, history_context, modified_chairman_prompt
    )

    # Query the chairman model
    response = await query_model(
        chairman_model, current_messages, api_key=api_key, base_url=base_url
    )
    logger.info("Stage 3 complete: Final response synthesized")
    if response is None:
        # Fallback if chairman fails
        return {"model": chairman_model, "response": "Error: Unable to generate final synthesis."}

    return {"model": chairman_model, "response": response.get("content", "")}


async def generate_conversation_title(
    user_query: str, org_id: str, api_key: str, base_url: str
) -> str:
    """
    Generate a short title for a conversation based on the first user message.

    Args:
        user_query: The first user message

    """
    prompts = load_org_system_prompts(org_id)
    title_prompt = prompts["title_prompt"].format(user_query=user_query)

    models_config = load_org_models_config(org_id)
    title_model = models_config["title_model"]

    messages = [{"role": "user", "content": title_prompt}]

    # Use configured title generation model
    response = await query_model(
        title_model, messages, api_key=api_key, base_url=base_url, timeout=30.0
    )

    if response is None:
        # Fallback to a generic title
        return "New Conversation"

    today = "today"  # Placeholder or use context if available but unused here.
    content = response.get("content")
    title = "New Conversation" if content is None else content.strip()

    del today  # Explicitly mark as not unused for linter or jusy ignore
    # Actually just removing the assignment is better if not used
    # But user code comment suggests keeping reference.
    # Let's prefix with _
    _today = "today"

    content = response.get("content")
    title = "New Conversation" if content is None else content.strip()

    # Clean up the title - remove quotes, limit length
    title = title.strip("\"'").strip()

    # If title is empty after cleaning, use fallback
    if not title:
        return "New Conversation"

    # Truncate if too long
    if len(title) > 50:
        title = title[:47] + "..."

    return title


async def run_council_cycle(
    user_query: str,
    messages: list[dict[str, Any]] | None = None,
    org_id: str = None,
    api_key: str = None,
    base_url: str = None,
    consensus_enabled: bool = False,
    user_id: str = None,
) -> AsyncGenerator[dict[str, Any]]:
    """
    Execute the council logic sequence and yield events for each stage.
    This generator encapsulates the core business logic, preventing logic drift.

    Yields:
        Dicts with "type" and "data" keys.
        Types: "stage_start", "stage1_complete", "stage2_complete", "stage3_complete"
    """
    # --- Stage 1 ---
    yield {"type": "stage_start", "data": {"stage": 1, "name": "Individual Responses"}}

    stage1_results = await stage1_collect_responses(
        user_query, messages, org_id, api_key, base_url, user_id=user_id
    )

    # Check termination if Stage 1 failed completely (logic from run_full_council)
    if not stage1_results:
        # We define a special error/empty event or just finish?
        # Standard flow expects stage1_complete.
        yield {"type": "stage1_complete", "data": {"results": []}}
        return

    yield {"type": "stage1_complete", "data": {"results": stage1_results}}

    # --- Stage 2 ---
    yield {"type": "stage_start", "data": {"stage": 2, "name": "Peer Ranking"}}

    stage2_results, label_to_model = await stage2_collect_rankings(
        user_query, stage1_results, messages, org_id, api_key, base_url, user_id=user_id
    )

    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

    yield {
        "type": "stage2_complete",
        "data": {
            "results": stage2_results,
            "metadata": {
                "label_to_model": label_to_model,
                "aggregate_rankings": aggregate_rankings,
            },
        },
    }

    # --- Stage 3 ---
    yield {
        "type": "stage_start",
        "data": {"stage": 3, "name": "Final Synthesis"},
    }  # Stage 3: Synthesize final answer
    if consensus_enabled:
        from backend.consensus_service import ConsensusService

        # Use Strategic Consensus
        logger.info("Executing Strategic Consensus Mode (Shared Generator)")
        response_text, attribution = await ConsensusService.synthesize_consensus(
            stage1_results, stage2_results, org_id, api_key, base_url
        )

        stage3_result = {
            "model": "consensus-strategy",
            "response": response_text,
            "consensus_contributions": attribution,
        }
    else:
        stage3_result = await stage3_synthesize_final(
            user_query,
            stage1_results,
            stage2_results,
            label_to_model,
            messages,
            org_id,
            api_key,
            base_url,
            user_id=user_id,
        )

    yield {"type": "stage3_complete", "data": {"results": stage3_result}}


async def run_full_council(
    user_query: str,
    messages: list[dict[str, Any]] | None = None,
    org_id: str = None,
    api_key: str = None,
    base_url: str = None,
    consensus_enabled: bool = False,
    user_id: str = None,
) -> tuple[list[Stage1Result], list[Stage2Result], Stage3Result, dict[str, Any]]:
    """
    Run the complete 3-stage council process (Batch/Sync wrapper).

    Args:
        user_query: The user's question
        messages: Full conversation history (optional)

    Returns:
        Tuple of (stage1_results, stage2_results, stage3_result, metadata)
    """
    logger.info(f"Starting full council session for query: {user_query[:50]}...")

    # Initialize accumulation variables
    stage1_results = []
    stage2_results = []
    stage3_result = {}
    metadata = {}

    async for event in run_council_cycle(
        user_query, messages, org_id, api_key, base_url, consensus_enabled, user_id
    ):
        event_type = event["type"]
        data = event["data"]

        if event_type == "stage1_complete":
            stage1_results = data["results"]
            # Early exit check if no results
            if not stage1_results:
                return (
                    [],
                    [],
                    {
                        "model": "error",
                        "response": "All models failed to respond. Please try again.",
                    },
                    {},
                )

        elif event_type == "stage2_complete":
            stage2_results = data["results"]
            metadata = data["metadata"]

        elif event_type == "stage3_complete":
            stage3_result = data["results"]

    logger.info("Full council session complete")
    return stage1_results, stage2_results, stage3_result, metadata
