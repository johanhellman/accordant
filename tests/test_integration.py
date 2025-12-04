"""End-to-end integration tests for the full council flow."""

import os
import tempfile
from unittest.mock import patch

import pytest

import backend.openrouter
from backend import storage
from backend.council import (
    run_full_council,
    stage1_collect_responses,
    stage2_collect_rankings,
    stage3_synthesize_final,
)


class TestFullCouncilFlow:
    """Tests for complete 3-stage council deliberation flow."""

    @pytest.fixture
    def temp_data_dir(self, monkeypatch):
        """Create a temporary data directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conversations_dir = os.path.join(tmpdir, "conversations")
            os.makedirs(conversations_dir, exist_ok=True)
            monkeypatch.setattr(storage, "ORGS_DATA_DIR", conversations_dir)
            yield conversations_dir

    @pytest.fixture
    def mock_llm_responses(self):
        """Mock LLM API responses for all stages."""
        # Stage 1 responses
        stage1_responses = {
            "model1": {"content": "Response A: Python is a programming language."},
            "model2": {"content": "Response B: Python is versatile and easy to learn."},
        }

        # Stage 2 rankings
        stage2_responses = {
            "model1": {
                "content": "Response A is more comprehensive.\n\nFINAL RANKING:\n1. Response A\n2. Response B"
            },
            "model2": {
                "content": "Response B is clearer.\n\nFINAL RANKING:\n1. Response B\n2. Response A"
            },
        }

        # Stage 3 final synthesis
        stage3_response = {
            "content": "PART 1: COUNCIL REPORT\n\nVoting Results:\n| Voter | 1st Choice | 2nd Choice |\n|-------|-------------|------------|\n| model1 | Response A | Response B |\n| model2 | Response B | Response A |\n\nPART 2: FINAL ANSWER\n\nPython is a versatile programming language that is easy to learn."
        }

        return {"stage1": stage1_responses, "stage2": stage2_responses, "stage3": stage3_response}

    @pytest.mark.asyncio
    async def test_full_council_flow_personality_mode(self, temp_data_dir, mock_llm_responses):
        """Test complete council flow in personality mode."""
        # Reset semaphore to avoid event loop issues
        backend.openrouter._SEMAPHORE = None

        # Mock personalities
        mock_personalities = [
            {
                "id": "p1",
                "name": "Personality A",
                "model": "model1",
                "personality_prompt": "You are A.",
                "temperature": 0.7,
            },
            {
                "id": "p2",
                "name": "Personality B",
                "model": "model2",
                "personality_prompt": "You are B.",
                "temperature": 0.7,
            },
        ]

        # Mock query_model for all stages (since personality mode uses query_model, not query_models_parallel)
        async def mock_query_single(model, messages, **kwargs):
            # Stage 1
            if "You are A." in str(messages) or "You are B." in str(messages):
                if "model1" in model:
                    return mock_llm_responses["stage1"]["model1"]
                elif "model2" in model:
                    return mock_llm_responses["stage1"]["model2"]

            # Stage 2
            elif "FINAL RANKING" in str(messages):  # Stage 2
                for key, value in mock_llm_responses["stage2"].items():
                    if key in model or model in key:
                        return value

            # Stage 3
            elif "Chairman" in str(messages) or "COUNCIL REPORT" in str(messages):  # Stage 3
                return mock_llm_responses["stage3"]

            return None

        # Patch get_active_personalities and load_org_system_prompts
        with (
            patch("backend.council.get_active_personalities", return_value=mock_personalities),
            patch(
                "backend.council.load_org_system_prompts",
                return_value={
                    "base_system_prompt": "",
                    "chairman_prompt": "You are the Chairman.\n{user_query}\n{stage1_text}\n{voting_details_text}",
                    "title_prompt": "",
                    "ranking_prompt": "",
                },
            ),
            patch(
                "backend.council.load_org_models_config",
                return_value={
                    "chairman_model": "model1",
                    "title_model": "model1",
                    "ranking_model": "model1",
                },
            ),
            patch("backend.council.query_model", side_effect=mock_query_single),
        ):
            user_query = "What is Python?"
            messages = []

            stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
                user_query, messages, org_id="org1", api_key="key", base_url="url"
            )

            # Verify Stage 1 results
            assert len(stage1_results) > 0
            assert all("model" in r for r in stage1_results)
            assert all("response" in r for r in stage1_results)
            assert all("personality_id" in r for r in stage1_results)

            # Verify Stage 2 results
            assert len(stage2_results) > 0
            assert all("model" in r for r in stage2_results)
            assert all("ranking" in r for r in stage2_results)
            assert all("parsed_ranking" in r for r in stage2_results)

            # Verify Stage 3 result
            assert stage3_result is not None
            assert "model" in stage3_result
            assert "response" in stage3_result
            assert "PART 1" in stage3_result["response"]
            assert "PART 2" in stage3_result["response"]

            # Verify metadata
            assert "label_to_model" in metadata
            assert "aggregate_rankings" in metadata

    @pytest.mark.asyncio
    async def test_stage1_collect_responses(self, mock_llm_responses):
        """Test Stage 1 in isolation."""
        # Reset semaphore
        backend.openrouter._SEMAPHORE = None

        mock_personalities = [
            {
                "id": "p1",
                "name": "Personality A",
                "model": "model1",
                "personality_prompt": "You are A.",
                "temperature": 0.7,
            },
            {
                "id": "p2",
                "name": "Personality B",
                "model": "model2",
                "personality_prompt": "You are B.",
                "temperature": 0.7,
            },
        ]

        async def mock_query_single(model, messages, **kwargs):
            if "model1" in model:
                return mock_llm_responses["stage1"]["model1"]
            elif "model2" in model:
                return mock_llm_responses["stage1"]["model2"]
            return None

        with (
            patch("backend.council.get_active_personalities", return_value=mock_personalities),
            patch(
                "backend.council.load_org_system_prompts", return_value={"base_system_prompt": ""}
            ),
            patch("backend.council.query_model", side_effect=mock_query_single),
        ):
            results = await stage1_collect_responses(
                "What is Python?", [], org_id="org1", api_key="key", base_url="url"
            )

            assert len(results) > 0
            assert all("model" in r for r in results)
            assert all("response" in r for r in results)
            assert all("personality_id" in r for r in results)

    @pytest.mark.asyncio
    async def test_stage2_collect_rankings(self, mock_llm_responses):
        """Test Stage 2 in isolation."""
        # Reset semaphore
        backend.openrouter._SEMAPHORE = None

        stage1_results = [
            {
                "model": "model1",
                "response": "Response A content",
                "personality_id": "p1",
                "personality_name": "Personality A",
            },
            {
                "model": "model2",
                "response": "Response B content",
                "personality_id": "p2",
                "personality_name": "Personality B",
            },
        ]

        mock_personalities = [
            {
                "id": "p1",
                "name": "Personality A",
                "model": "model1",
                "personality_prompt": "You are A.",
                "temperature": 0.7,
            },
            {
                "id": "p2",
                "name": "Personality B",
                "model": "model2",
                "personality_prompt": "You are B.",
                "temperature": 0.7,
            },
        ]

        async def mock_query_single(model, messages, **kwargs):
            for key, value in mock_llm_responses["stage2"].items():
                if key in model or model in key:
                    return value
            return None

        with (
            patch("backend.council.get_active_personalities", return_value=mock_personalities),
            patch(
                "backend.council.load_org_system_prompts", return_value={"base_system_prompt": ""}
            ),
            patch("backend.council.query_model", side_effect=mock_query_single),
        ):
            rankings, label_to_model = await stage2_collect_rankings(
                "What is Python?", stage1_results, [], org_id="org1", api_key="key", base_url="url"
            )

            assert len(rankings) > 0
            assert all("model" in r for r in rankings)
            assert all("ranking" in r for r in rankings)
            assert all("parsed_ranking" in r for r in rankings)
            assert len(label_to_model) > 0

    @pytest.mark.asyncio
    async def test_stage3_synthesize_final(self, mock_llm_responses):
        """Test Stage 3 in isolation."""
        # Reset semaphore
        backend.openrouter._SEMAPHORE = None

        stage1_results = [
            {"model": "model1", "response": "Response A"},
            {"model": "model2", "response": "Response B"},
        ]
        stage2_results = [
            {
                "model": "model1",
                "ranking": "Ranking 1",
                "parsed_ranking": ["Response A", "Response B"],
            },
            {
                "model": "model2",
                "ranking": "Ranking 2",
                "parsed_ranking": ["Response B", "Response A"],
            },
        ]
        label_to_model = {"Response A": "model1", "Response B": "model2"}

        async def mock_query_single(model, messages, **kwargs):
            return mock_llm_responses["stage3"]

        with (
            patch("backend.council.query_model", side_effect=mock_query_single),
            patch(
                "backend.council.load_org_system_prompts",
                return_value={
                    "chairman_prompt": "{user_query}\n{stage1_text}\n{voting_details_text}"
                },
            ),
            patch(
                "backend.council.load_org_models_config", return_value={"chairman_model": "model1"}
            ),
        ):
            result = await stage3_synthesize_final(
                "What is Python?",
                stage1_results,
                stage2_results,
                label_to_model,
                [],
                org_id="org1",
                api_key="key",
                base_url="url",
            )

            assert result is not None
            assert "model" in result
            assert "response" in result
            assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_full_council_with_conversation_history(self, temp_data_dir, mock_llm_responses):
        """Test council flow with conversation history."""
        # Reset semaphore
        backend.openrouter._SEMAPHORE = None

        # Create a conversation with history
        conv_id = "test-integration-history"
        storage.create_conversation(conv_id, "user1", "org1")
        storage.add_user_message(conv_id, "First question", "org1")
        storage.add_assistant_message(
            conv_id,
            [{"model": "m1", "response": "First answer"}],
            [{"model": "m1", "ranking": "First ranking"}],
            {"model": "m1", "response": "PART 2: FINAL ANSWER\n\nFirst final answer"},
            "org1",
        )

        conversation = storage.get_conversation(conv_id, "org1")

        async def mock_query_single(model, messages, **kwargs):
            # Stage 1
            if "You are A." in str(messages) or "You are B." in str(messages):
                if "model1" in model:
                    return mock_llm_responses["stage1"]["model1"]
                elif "model2" in model:
                    return mock_llm_responses["stage1"]["model2"]

            # Stage 2
            elif "FINAL RANKING" in str(messages):
                for key, value in mock_llm_responses["stage2"].items():
                    if key in model or model in key:
                        return value

            # Stage 3
            elif "Chairman" in str(messages) or "COUNCIL REPORT" in str(messages):
                return mock_llm_responses["stage3"]

            return None

        mock_personalities = [
            {
                "id": "p1",
                "name": "Personality A",
                "model": "model1",
                "personality_prompt": "You are A.",
                "temperature": 0.7,
            },
            {
                "id": "p2",
                "name": "Personality B",
                "model": "model2",
                "personality_prompt": "You are B.",
                "temperature": 0.7,
            },
        ]

        with (
            patch("backend.council.get_active_personalities", return_value=mock_personalities),
            patch(
                "backend.council.load_org_system_prompts",
                return_value={
                    "base_system_prompt": "",
                    "chairman_prompt": "You are the Chairman.\n{user_query}\n{stage1_text}\n{voting_details_text}",
                    "title_prompt": "",
                    "ranking_prompt": "",
                },
            ),
            patch(
                "backend.council.load_org_models_config",
                return_value={
                    "chairman_model": "model1",
                    "title_model": "model1",
                    "ranking_model": "model1",
                },
            ),
            patch("backend.council.query_model", side_effect=mock_query_single),
        ):
            user_query = "What is JavaScript?"
            stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
                user_query, conversation["messages"], org_id="org1", api_key="key", base_url="url"
            )

            # Verify results include context from history
            assert stage1_results is not None
            assert stage2_results is not None
            assert stage3_result is not None
