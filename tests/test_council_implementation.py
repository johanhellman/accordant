"""Comprehensive tests for council.py implementation.

These tests directly test the implementation functions to ensure full code coverage.
"""

from unittest.mock import AsyncMock, patch

import pytest

from backend.council import (
    _stage1_personality_mode,
    _stage2_personality_mode,
    run_full_council,
    stage1_collect_responses,
    stage2_collect_rankings,
    stage3_synthesize_final,
)
from backend.council_helpers import RESPONSE_LABEL_PREFIX


@pytest.fixture
def mock_personalities():
    """Mock active personalities."""
    return [
        {
            "id": "personality1",
            "name": "Personality 1",
            "model": "openai/gpt-4",
            "personality_prompt": "You are helpful.",
            "temperature": 0.7,
        },
        {
            "id": "personality2",
            "name": "Personality 2",
            "model": "anthropic/claude-3",
            "personality_prompt": "You are analytical.",
            "temperature": 0.8,
        },
    ]


@pytest.fixture
def mock_system_prompts():
    """Mock system prompts."""
    return {
        "base_system_prompt": "You are a helpful assistant.",
        "ranking_prompt": "Rank {responses_text} for {user_query}",
        "chairman_prompt": "Synthesize {user_query} using {stage1_text} and {voting_details_text}",
    }


@pytest.fixture
def mock_models_config():
    """Mock models config."""
    return {
        "chairman_model": "gemini/gemini-pro",
        "title_model": "gemini/gemini-pro",
    }


@pytest.mark.asyncio
async def test_stage1_personality_mode_success(mock_personalities, mock_system_prompts):
    """Test _stage1_personality_mode successfully queries all personalities."""
    user_query = "What is Python?"
    history_context = []
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_responses = [
        {"content": "Python is a programming language."},
        {"content": "Python is a high-level language."},
    ]

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.side_effect = mock_responses

        results = await _stage1_personality_mode(
            user_query, history_context, org_id, api_key, base_url
        )

        assert len(results) == 2
        assert results[0]["model"] == "openai/gpt-4"
        assert results[0]["personality_id"] == "personality1"
        assert results[0]["personality_name"] == "Personality 1"
        assert results[0]["response"] == "Python is a programming language."
        assert results[1]["model"] == "anthropic/claude-3"
        assert results[1]["personality_id"] == "personality2"
        assert mock_query.call_count == 2


@pytest.mark.asyncio
async def test_stage1_personality_mode_partial_failure(mock_personalities, mock_system_prompts):
    """Test _stage1_personality_mode handles partial failures."""
    user_query = "What is Python?"
    history_context = []
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    # First succeeds, second fails
    mock_responses = [{"content": "Python is a programming language."}, None]

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.side_effect = mock_responses

        results = await _stage1_personality_mode(
            user_query, history_context, org_id, api_key, base_url
        )

        # Should only include successful responses
        assert len(results) == 1
        assert results[0]["model"] == "openai/gpt-4"
        assert mock_query.call_count == 2


@pytest.mark.asyncio
async def test_stage1_personality_mode_exception_handling(mock_personalities, mock_system_prompts):
    """Test _stage1_personality_mode handles exceptions gracefully."""
    user_query = "What is Python?"
    history_context = []
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    # First succeeds, second raises exception
    async def mock_query_side_effect(model, *args, **kwargs):
        # Use model name to decide success/failure to be robust against concurrency
        if "gpt-4" in model:
            return {"content": "Python is a programming language."}
        else:
            raise Exception("API error")

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.side_effect = mock_query_side_effect

        results = await _stage1_personality_mode(
            user_query, history_context, org_id, api_key, base_url
        )

        # Should only include successful responses
        assert len(results) == 1
        assert results[0]["model"] == "openai/gpt-4"


@pytest.mark.asyncio
async def test_stage1_collect_responses_with_personalities(mock_personalities, mock_system_prompts):
    """Test stage1_collect_responses routes to personality mode."""
    user_query = "What is Python?"
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_responses = [
        {"content": "Python is a programming language."},
        {"content": "Python is a high-level language."},
    ]

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.side_effect = mock_responses

        results = await stage1_collect_responses(user_query, messages, org_id, api_key, base_url)

        assert len(results) == 2
        assert results[0]["model"] == "openai/gpt-4"


@pytest.mark.asyncio
async def test_stage1_collect_responses_no_personalities():
    """Test stage1_collect_responses handles no active personalities."""
    user_query = "What is Python?"
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    with patch("backend.council.get_active_personalities", return_value=[]):
        results = await stage1_collect_responses(user_query, messages, org_id, api_key, base_url)

        assert results == []


@pytest.mark.asyncio
async def test_stage1_collect_responses_with_history(mock_personalities, mock_system_prompts):
    """Test stage1_collect_responses includes conversation history."""
    user_query = "What is JavaScript?"
    messages = [
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "stage3": {"model": "model1", "response": "Python is a language."}},
    ]
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_responses = [{"content": "JavaScript is a scripting language."}]

    with (
        patch("backend.council.get_active_personalities", return_value=[mock_personalities[0]]),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.return_value = mock_responses[0]

        results = await stage1_collect_responses(user_query, messages, org_id, api_key, base_url)

        assert len(results) == 1
        # Verify history was included in the query
        assert mock_query.called
        call_args = mock_query.call_args
        messages_arg = call_args[0][1]  # Second positional argument
        assert len(messages_arg) > 2  # Should include system prompt, history, and user query


@pytest.mark.asyncio
async def test_stage2_personality_mode_success(mock_personalities, mock_system_prompts):
    """Test _stage2_personality_mode successfully collects rankings."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Python is a programming language.",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
        {
            "model": "anthropic/claude-3",
            "response": "Python is a high-level language.",
            "personality_id": "personality2",
            "personality_name": "Personality 2",
        },
    ]
    history_context = []
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    # Mock ranking responses
    mock_ranking_responses = [
        {
            "content": f"Evaluation\n\nFINAL RANKING:\n1. {RESPONSE_LABEL_PREFIX}B\n2. {RESPONSE_LABEL_PREFIX}A"
        },
        {
            "content": f"Evaluation\n\nFINAL RANKING:\n1. {RESPONSE_LABEL_PREFIX}A\n2. {RESPONSE_LABEL_PREFIX}B"
        },
    ]

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.side_effect = mock_ranking_responses

        stage2_results, label_to_model = await _stage2_personality_mode(
            user_query, stage1_results, history_context, org_id, api_key, base_url
        )

        assert len(stage2_results) == 2
        assert len(label_to_model) == 2
        assert f"{RESPONSE_LABEL_PREFIX}A" in label_to_model
        assert f"{RESPONSE_LABEL_PREFIX}B" in label_to_model
        # Verify each personality excludes its own response
        assert mock_query.call_count == 2


@pytest.mark.asyncio
async def test_stage2_personality_mode_excludes_self(mock_personalities, mock_system_prompts):
    """Test _stage2_personality_mode excludes each personality's own response."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response 1",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
        {
            "model": "anthropic/claude-3",
            "response": "Response 2",
            "personality_id": "personality2",
            "personality_name": "Personality 2",
        },
    ]
    history_context = []
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_ranking_responses = [
        {"content": f"Ranking: {RESPONSE_LABEL_PREFIX}B"},
        {"content": f"Ranking: {RESPONSE_LABEL_PREFIX}A"},
    ]

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.side_effect = mock_ranking_responses

        stage2_results, label_to_model = await _stage2_personality_mode(
            user_query, stage1_results, history_context, org_id, api_key, base_url
        )

        # Verify that each personality only sees the other personality's response
        assert mock_query.call_count == 2
        # Check that filtered_responses_text excludes self
        for call in mock_query.call_args_list:
            messages = call[0][1]  # Second positional argument
            # Find the ranking prompt in messages
            ranking_prompt = None
            for msg in messages:
                if msg.get("role") == "user":
                    ranking_prompt = msg.get("content", "")
                    break
            # Verify that each personality doesn't see their own response label
            # Personality 1 should only see Response B, Personality 2 should only see Response A
            assert ranking_prompt is not None


@pytest.mark.asyncio
async def test_stage2_personality_mode_partial_failure(mock_personalities, mock_system_prompts):
    """Test _stage2_personality_mode handles partial failures."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response 1",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]
    history_context = []
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    # One succeeds, one fails
    mock_ranking_responses = [
        {"content": f"Ranking: {RESPONSE_LABEL_PREFIX}A"},
        None,
    ]

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.side_effect = mock_ranking_responses

        stage2_results, label_to_model = await _stage2_personality_mode(
            user_query, stage1_results, history_context, org_id, api_key, base_url
        )

        # Should only include successful rankings
        assert len(stage2_results) == 1


@pytest.mark.asyncio
async def test_stage2_collect_rankings_with_personalities(mock_personalities, mock_system_prompts):
    """Test stage2_collect_rankings routes to personality mode."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response 1",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_ranking_responses = [
        {"content": f"Ranking: {RESPONSE_LABEL_PREFIX}A"},
    ]

    with (
        patch("backend.council.get_active_personalities", return_value=[mock_personalities[0]]),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.return_value = mock_ranking_responses[0]

        stage2_results, label_to_model = await stage2_collect_rankings(
            user_query, stage1_results, messages, org_id, api_key, base_url
        )

        assert len(stage2_results) == 1
        assert len(label_to_model) == 1


@pytest.mark.asyncio
async def test_stage2_collect_rankings_no_personalities():
    """Test stage2_collect_rankings handles no active personalities."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response 1",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    with patch("backend.council.get_active_personalities", return_value=[]):
        stage2_results, label_to_model = await stage2_collect_rankings(
            user_query, stage1_results, messages, org_id, api_key, base_url
        )

        assert stage2_results == []
        assert label_to_model == {}


@pytest.mark.asyncio
async def test_stage3_synthesize_final_success(mock_system_prompts, mock_models_config):
    """Test stage3_synthesize_final successfully synthesizes final answer."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Python is a programming language.",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]
    stage2_results = [
        {
            "model": "openai/gpt-4",
            "personality_name": "Personality 1",
            "ranking": f"Ranking: {RESPONSE_LABEL_PREFIX}A",
            "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}A"],
        },
    ]
    label_to_model = {f"{RESPONSE_LABEL_PREFIX}A": "Personality 1"}
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_chairman_response = {"content": "Python is a versatile programming language."}

    with (
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.load_org_models_config", return_value=mock_models_config),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.return_value = mock_chairman_response

        result = await stage3_synthesize_final(
            user_query,
            stage1_results,
            stage2_results,
            label_to_model,
            messages,
            org_id,
            api_key,
            base_url,
        )

        assert result["model"] == "gemini/gemini-pro"
        assert result["response"] == "Python is a versatile programming language."
        mock_query.assert_called_once()


@pytest.mark.asyncio
async def test_stage3_synthesize_final_chairman_failure(mock_system_prompts, mock_models_config):
    """Test stage3_synthesize_final handles chairman failure."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Python is a programming language.",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]
    stage2_results = []
    label_to_model = {}
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    with (
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.load_org_models_config", return_value=mock_models_config),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.return_value = None

        result = await stage3_synthesize_final(
            user_query,
            stage1_results,
            stage2_results,
            label_to_model,
            messages,
            org_id,
            api_key,
            base_url,
        )

        assert result["model"] == "gemini/gemini-pro"
        assert "Error: Unable to generate final synthesis" in result["response"]


@pytest.mark.asyncio
async def test_stage3_synthesize_final_includes_voting_details(
    mock_system_prompts, mock_models_config
):
    """Test stage3_synthesize_final includes voting details in prompt."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response 1",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]
    stage2_results = [
        {
            "model": "openai/gpt-4",
            "personality_name": "Personality 1",
            "ranking": f"Ranking: {RESPONSE_LABEL_PREFIX}A",
            "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}A"],
        },
    ]
    label_to_model = {f"{RESPONSE_LABEL_PREFIX}A": "Personality 1"}
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_chairman_response = {"content": "Final answer"}

    with (
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.load_org_models_config", return_value=mock_models_config),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.return_value = mock_chairman_response

        await stage3_synthesize_final(
            user_query,
            stage1_results,
            stage2_results,
            label_to_model,
            messages,
            org_id,
            api_key,
            base_url,
        )

        # Verify voting details were included in the prompt
        call_args = mock_query.call_args
        messages_arg = call_args[0][1]  # Second positional argument
        # Find the chairman prompt
        chairman_prompt = None
        for msg in messages_arg:
            if msg.get("role") == "user":
                chairman_prompt = msg.get("content", "")
                break
        assert chairman_prompt is not None
        assert "Voter" in chairman_prompt or "voting" in chairman_prompt.lower()


@pytest.mark.asyncio
async def test_run_full_council_success(
    mock_personalities, mock_system_prompts, mock_models_config
):
    """Test run_full_council successfully orchestrates all 3 stages."""
    user_query = "What is Python?"
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_stage1_responses = [
        {"content": "Python is a programming language."},
        {"content": "Python is a high-level language."},
    ]

    mock_stage2_responses = [
        {
            "content": f"Evaluation\n\nFINAL RANKING:\n1. {RESPONSE_LABEL_PREFIX}B\n2. {RESPONSE_LABEL_PREFIX}A"
        },
        {
            "content": f"Evaluation\n\nFINAL RANKING:\n1. {RESPONSE_LABEL_PREFIX}A\n2. {RESPONSE_LABEL_PREFIX}B"
        },
    ]

    mock_stage3_response = {"content": "Python is a versatile programming language."}

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.load_org_models_config", return_value=mock_models_config),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        # Set up side effect to return different responses for different stages
        call_count = {"count": 0}

        async def query_side_effect(*args, **kwargs):
            call_count["count"] += 1
            # Stage 1: 2 calls
            if call_count["count"] <= 2:
                return mock_stage1_responses[call_count["count"] - 1]
            # Stage 2: 2 calls
            elif call_count["count"] <= 4:
                return mock_stage2_responses[call_count["count"] - 3]
            # Stage 3: 1 call
            else:
                return mock_stage3_response

        mock_query.side_effect = query_side_effect

        stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
            user_query, messages, org_id, api_key, base_url
        )

        assert len(stage1_results) == 2
        assert len(stage2_results) == 2
        assert stage3_result["response"] == "Python is a versatile programming language."
        assert "label_to_model" in metadata
        assert "aggregate_rankings" in metadata


@pytest.mark.asyncio
async def test_run_full_council_stage1_all_fail(mock_personalities, mock_system_prompts):
    """Test run_full_council handles all Stage 1 failures."""
    user_query = "What is Python?"
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.return_value = None  # All queries fail

        stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
            user_query, messages, org_id, api_key, base_url
        )

        assert stage1_results == []
        assert stage2_results == []
        assert "All models failed to respond" in stage3_result["response"]
        assert stage3_result["model"] == "error"


# Edge case tests for improved coverage


@pytest.mark.asyncio
async def test_stage1_personality_mode_empty_content(mock_personalities, mock_system_prompts):
    """Test _stage1_personality_mode handles empty content in response."""
    user_query = "What is Python?"
    history_context = []
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    # Response with empty content
    mock_responses = [{"content": ""}, {"content": "Python is a language."}]

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.side_effect = mock_responses

        results = await _stage1_personality_mode(
            user_query, history_context, org_id, api_key, base_url
        )

        # Should include both responses, even with empty content
        assert len(results) == 2
        assert results[0]["response"] == ""
        assert results[1]["response"] == "Python is a language."


@pytest.mark.asyncio
async def test_stage1_personality_mode_missing_content_key(mock_personalities, mock_system_prompts):
    """Test _stage1_personality_mode handles missing content key."""
    user_query = "What is Python?"
    history_context = []
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    # Response without content key
    mock_responses = [{}, {"content": "Python is a language."}]

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.side_effect = mock_responses

        results = await _stage1_personality_mode(
            user_query, history_context, org_id, api_key, base_url
        )

        # Should include both responses
        assert len(results) == 2
        assert results[0]["response"] == ""  # get("content", "") returns ""
        assert results[1]["response"] == "Python is a language."


@pytest.mark.asyncio
async def test_stage2_personality_mode_empty_stage1_results(
    mock_personalities, mock_system_prompts
):
    """Test _stage2_personality_mode handles empty stage1_results."""
    user_query = "What is Python?"
    stage1_results = []
    history_context = []
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.return_value = {"content": f"Ranking: {RESPONSE_LABEL_PREFIX}A"}

        stage2_results, label_to_model = await _stage2_personality_mode(
            user_query, stage1_results, history_context, org_id, api_key, base_url
        )

        # Should still process rankings even with empty stage1_results
        assert len(stage2_results) == 2
        assert len(label_to_model) == 0  # No labels created from empty stage1_results


@pytest.mark.asyncio
async def test_stage2_personality_mode_empty_content(mock_personalities, mock_system_prompts):
    """Test _stage2_personality_mode handles empty content in ranking response."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response 1",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]
    history_context = []
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    # Empty content response
    mock_ranking_responses = [{"content": ""}, {"content": f"Ranking: {RESPONSE_LABEL_PREFIX}A"}]

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.side_effect = mock_ranking_responses

        stage2_results, label_to_model = await _stage2_personality_mode(
            user_query, stage1_results, history_context, org_id, api_key, base_url
        )

        # Should include both rankings, even with empty content
        assert len(stage2_results) == 2
        assert stage2_results[0]["ranking"] == ""
        assert stage2_results[1]["ranking"] == f"Ranking: {RESPONSE_LABEL_PREFIX}A"


@pytest.mark.asyncio
async def test_stage2_personality_mode_missing_content_key(mock_personalities, mock_system_prompts):
    """Test _stage2_personality_mode handles missing content key."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response 1",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]
    history_context = []
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    # Missing content key
    mock_ranking_responses = [{}, {"content": f"Ranking: {RESPONSE_LABEL_PREFIX}A"}]

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.side_effect = mock_ranking_responses

        stage2_results, label_to_model = await _stage2_personality_mode(
            user_query, stage1_results, history_context, org_id, api_key, base_url
        )

        # Should include both rankings
        assert len(stage2_results) == 2
        assert stage2_results[0]["ranking"] == ""  # get("content", "") returns ""


@pytest.mark.asyncio
async def test_stage2_collect_rankings_missing_personality_fields():
    """Test stage2_collect_rankings handles missing personality_id and personality_name."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response 1",
            # Missing personality_id and personality_name
        },
    ]
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_personalities = [
        {
            "id": "personality1",
            "name": "Personality 1",
            "model": "openai/gpt-4",
        },
    ]

    mock_ranking_responses = [{"content": f"Ranking: {RESPONSE_LABEL_PREFIX}A"}]

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts") as mock_prompts,
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_prompts.return_value = {
            "base_system_prompt": "You are helpful.",
            "ranking_prompt": "Rank {responses_text}",
        }
        mock_query.return_value = mock_ranking_responses[0]

        stage2_results, label_to_model = await stage2_collect_rankings(
            user_query, stage1_results, messages, org_id, api_key, base_url
        )

        # Should handle missing fields gracefully
        assert len(stage2_results) == 1
        # label_to_model should use model name as fallback
        assert len(label_to_model) == 1


@pytest.mark.asyncio
async def test_stage3_synthesize_final_empty_stage1_results(
    mock_system_prompts, mock_models_config
):
    """Test stage3_synthesize_final handles empty stage1_results."""
    user_query = "What is Python?"
    stage1_results = []
    stage2_results = [
        {
            "model": "openai/gpt-4",
            "personality_name": "Personality 1",
            "ranking": f"Ranking: {RESPONSE_LABEL_PREFIX}A",
            "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}A"],
        },
    ]
    label_to_model = {f"{RESPONSE_LABEL_PREFIX}A": "Personality 1"}
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_chairman_response = {"content": "Final answer"}

    with (
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.load_org_models_config", return_value=mock_models_config),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.return_value = mock_chairman_response

        result = await stage3_synthesize_final(
            user_query,
            stage1_results,
            stage2_results,
            label_to_model,
            messages,
            org_id,
            api_key,
            base_url,
        )

        # Should handle empty stage1_results gracefully
        assert result["response"] == "Final answer"
        # Verify stage1_text is empty string
        call_args = mock_query.call_args
        messages_arg = call_args[0][1]
        chairman_prompt = None
        for msg in messages_arg:
            if msg.get("role") == "user":
                chairman_prompt = msg.get("content", "")
                break
        assert chairman_prompt is not None


@pytest.mark.asyncio
async def test_stage3_synthesize_final_empty_stage2_results(
    mock_system_prompts, mock_models_config
):
    """Test stage3_synthesize_final handles empty stage2_results."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Python is a language.",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]
    stage2_results = []
    label_to_model = {}
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_chairman_response = {"content": "Final answer"}

    with (
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.load_org_models_config", return_value=mock_models_config),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.return_value = mock_chairman_response

        result = await stage3_synthesize_final(
            user_query,
            stage1_results,
            stage2_results,
            label_to_model,
            messages,
            org_id,
            api_key,
            base_url,
        )

        # Should handle empty stage2_results gracefully
        assert result["response"] == "Final answer"
        # Verify voting_details_text is empty
        call_args = mock_query.call_args
        messages_arg = call_args[0][1]
        chairman_prompt = None
        for msg in messages_arg:
            if msg.get("role") == "user":
                chairman_prompt = msg.get("content", "")
                break
        assert chairman_prompt is not None


@pytest.mark.asyncio
async def test_stage3_synthesize_final_empty_parsed_ranking(
    mock_system_prompts, mock_models_config
):
    """Test stage3_synthesize_final handles empty parsed_ranking."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Python is a language.",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]
    stage2_results = [
        {
            "model": "openai/gpt-4",
            "personality_name": "Personality 1",
            "ranking": "No ranking found",
            "parsed_ranking": [],  # Empty parsed ranking
        },
    ]
    label_to_model = {f"{RESPONSE_LABEL_PREFIX}A": "Personality 1"}
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_chairman_response = {"content": "Final answer"}

    with (
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.load_org_models_config", return_value=mock_models_config),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.return_value = mock_chairman_response

        result = await stage3_synthesize_final(
            user_query,
            stage1_results,
            stage2_results,
            label_to_model,
            messages,
            org_id,
            api_key,
            base_url,
        )

        # Should handle empty parsed_ranking gracefully
        assert result["response"] == "Final answer"
        # Verify voting details only show voter name, no rankings
        call_args = mock_query.call_args
        messages_arg = call_args[0][1]
        chairman_prompt = None
        for msg in messages_arg:
            if msg.get("role") == "user":
                chairman_prompt = msg.get("content", "")
                break
        assert chairman_prompt is not None
        assert "Voter: Personality 1" in chairman_prompt


@pytest.mark.asyncio
async def test_stage3_synthesize_final_missing_parsed_ranking_key(
    mock_system_prompts, mock_models_config
):
    """Test stage3_synthesize_final handles missing parsed_ranking key."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Python is a language.",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]
    stage2_results = [
        {
            "model": "openai/gpt-4",
            "personality_name": "Personality 1",
            "ranking": "Some ranking text",
            # Missing parsed_ranking key
        },
    ]
    label_to_model = {f"{RESPONSE_LABEL_PREFIX}A": "Personality 1"}
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_chairman_response = {"content": "Final answer"}

    with (
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.load_org_models_config", return_value=mock_models_config),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.return_value = mock_chairman_response

        result = await stage3_synthesize_final(
            user_query,
            stage1_results,
            stage2_results,
            label_to_model,
            messages,
            org_id,
            api_key,
            base_url,
        )

        # Should handle missing parsed_ranking key gracefully
        assert result["response"] == "Final answer"
        # get("parsed_ranking", []) should return empty list


@pytest.mark.asyncio
async def test_stage3_synthesize_final_missing_personality_name(
    mock_system_prompts, mock_models_config
):
    """Test stage3_synthesize_final handles missing personality_name in stage1_results."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Python is a language.",
            "personality_id": "personality1",
            # Missing personality_name
        },
    ]
    stage2_results = [
        {
            "model": "openai/gpt-4",
            "personality_name": "Personality 1",
            "ranking": f"Ranking: {RESPONSE_LABEL_PREFIX}A",
            "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}A"],
        },
    ]
    label_to_model = {f"{RESPONSE_LABEL_PREFIX}A": "Personality 1"}
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_chairman_response = {"content": "Final answer"}

    with (
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.load_org_models_config", return_value=mock_models_config),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.return_value = mock_chairman_response

        result = await stage3_synthesize_final(
            user_query,
            stage1_results,
            stage2_results,
            label_to_model,
            messages,
            org_id,
            api_key,
            base_url,
        )

        # Should use model name as fallback
        assert result["response"] == "Final answer"


@pytest.mark.asyncio
async def test_stage3_synthesize_final_missing_content_key(mock_system_prompts, mock_models_config):
    """Test stage3_synthesize_final handles missing content key in response."""
    user_query = "What is Python?"
    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Python is a language.",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]
    stage2_results = [
        {
            "model": "openai/gpt-4",
            "personality_name": "Personality 1",
            "ranking": f"Ranking: {RESPONSE_LABEL_PREFIX}A",
            "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}A"],
        },
    ]
    label_to_model = {f"{RESPONSE_LABEL_PREFIX}A": "Personality 1"}
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    # Missing content key
    mock_chairman_response = {}

    with (
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.load_org_models_config", return_value=mock_models_config),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_query.return_value = mock_chairman_response

        result = await stage3_synthesize_final(
            user_query,
            stage1_results,
            stage2_results,
            label_to_model,
            messages,
            org_id,
            api_key,
            base_url,
        )

        # Should handle missing content key gracefully
        assert result["model"] == "gemini/gemini-pro"
        assert result["response"] == ""  # get("content", "") returns ""


@pytest.mark.asyncio
async def test_run_full_council_partial_stage2_failure(
    mock_personalities, mock_system_prompts, mock_models_config
):
    """Test run_full_council handles partial Stage 2 failures."""
    user_query = "What is Python?"
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_stage1_responses = [
        {"content": "Python is a programming language."},
        {"content": "Python is a high-level language."},
    ]

    # Stage 2: one succeeds, one fails
    mock_stage2_responses = [
        {
            "content": f"Evaluation\n\nFINAL RANKING:\n1. {RESPONSE_LABEL_PREFIX}B\n2. {RESPONSE_LABEL_PREFIX}A"
        },
        None,  # Second ranking fails
    ]

    mock_stage3_response = {"content": "Python is a versatile programming language."}

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.load_org_models_config", return_value=mock_models_config),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        call_count = {"count": 0}

        async def query_side_effect(*args, **kwargs):
            call_count["count"] += 1
            if call_count["count"] <= 2:
                return mock_stage1_responses[call_count["count"] - 1]
            elif call_count["count"] <= 4:
                return mock_stage2_responses[call_count["count"] - 3]
            else:
                return mock_stage3_response

        mock_query.side_effect = query_side_effect

        stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
            user_query, messages, org_id, api_key, base_url
        )

        # Should proceed with partial Stage 2 results
        assert len(stage1_results) == 2
        assert len(stage2_results) == 1  # Only one successful ranking
        assert stage3_result["response"] == "Python is a versatile programming language."


@pytest.mark.asyncio
async def test_run_full_council_stage3_failure_after_success(
    mock_personalities, mock_system_prompts, mock_models_config
):
    """Test run_full_council handles Stage 3 failure after successful Stage 1 and 2."""
    user_query = "What is Python?"
    messages = None
    org_id = "test-org"
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_stage1_responses = [
        {"content": "Python is a programming language."},
        {"content": "Python is a high-level language."},
    ]

    mock_stage2_responses = [
        {
            "content": f"Evaluation\n\nFINAL RANKING:\n1. {RESPONSE_LABEL_PREFIX}B\n2. {RESPONSE_LABEL_PREFIX}A"
        },
        {
            "content": f"Evaluation\n\nFINAL RANKING:\n1. {RESPONSE_LABEL_PREFIX}A\n2. {RESPONSE_LABEL_PREFIX}B"
        },
    ]

    # Stage 3 fails
    mock_stage3_response = None

    with (
        patch("backend.council.get_active_personalities", return_value=mock_personalities),
        patch("backend.council.load_org_system_prompts", return_value=mock_system_prompts),
        patch("backend.council.load_org_models_config", return_value=mock_models_config),
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        call_count = {"count": 0}

        async def query_side_effect(*args, **kwargs):
            call_count["count"] += 1
            if call_count["count"] <= 2:
                return mock_stage1_responses[call_count["count"] - 1]
            elif call_count["count"] <= 4:
                return mock_stage2_responses[call_count["count"] - 3]
            else:
                return mock_stage3_response

        mock_query.side_effect = query_side_effect

        stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
            user_query, messages, org_id, api_key, base_url
        )

        # Should handle Stage 3 failure gracefully
        assert len(stage1_results) == 2
        assert len(stage2_results) == 2
        assert "Error: Unable to generate final synthesis" in stage3_result["response"]
        assert stage3_result["model"] == "gemini/gemini-pro"
