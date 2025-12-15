"""Tests for streaming orchestration functions."""

import json
import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from backend.streaming import run_council_generator


class TestStreaming:
    """Tests for streaming orchestration functions."""

    @pytest.fixture
    def temp_data_dir(self, monkeypatch):
        """Create a temporary data directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orgs_dir = os.path.join(tmpdir, "organizations")
            users_file = os.path.join(tmpdir, "users.json")
            os.makedirs(orgs_dir, exist_ok=True)
            monkeypatch.setattr("backend.organizations.ORGS_DATA_DIR", orgs_dir)
            monkeypatch.setattr("backend.users.USERS_FILE", users_file)
            yield tmpdir

    @pytest.mark.asyncio
    async def test_run_council_generator_first_message(self, temp_data_dir):
        """Test run_council_generator for first message generates title and all stages."""
        # Create conversation
        conv_id = "test-conv-1"
        org_id = "test-org"
        conversation = {
            "id": conv_id,
            "user_id": "user1",
            "org_id": org_id,
            "title": "New Conversation",
            "messages": [],
        }

        # Mock all stage functions
        with (
            patch(
                "backend.streaming.stage1_collect_responses", new_callable=AsyncMock
            ) as mock_stage1,
            patch(
                "backend.streaming.stage2_collect_rankings", new_callable=AsyncMock
            ) as mock_stage2,
            patch(
                "backend.streaming.stage3_synthesize_final", new_callable=AsyncMock
            ) as mock_stage3,
            patch(
                "backend.streaming.generate_conversation_title", new_callable=AsyncMock
            ) as mock_title,
            patch("backend.streaming.calculate_aggregate_rankings") as mock_calc_rankings,
            patch("backend.streaming.record_votes"),
            patch("backend.streaming.add_user_message") as mock_add_user,
            patch("backend.streaming.add_assistant_message") as mock_add_assistant,
            patch("backend.streaming.update_conversation_title") as mock_update_title,
        ):
            mock_stage1.return_value = [
                {
                    "model": "m1",
                    "response": "Response 1",
                    "personality_id": "p1",
                    "personality_name": "Personality 1",
                }
            ]
            mock_stage2.return_value = (
                [
                    {
                        "model": "m1",
                        "personality_name": "Personality 1",
                        "ranking": "Ranking",
                        "parsed_ranking": ["Response A"],
                    }
                ],
                {"Response A": "Personality 1"},
            )
            mock_stage3.return_value = {"model": "chairman", "response": "Final answer"}
            mock_title.return_value = "Generated Title"
            mock_calc_rankings.return_value = []

            # Collect events
            events = []
            async for event in run_council_generator(
                conv_id, "What is Python?", conversation, org_id, "test-key", "https://test.url"
            ):
                events.append(event)

            # Verify events
            event_types = []
            for event in events:
                if event.startswith("data: "):
                    data = json.loads(event[6:])  # Remove "data: " prefix
                    event_types.append(data.get("type"))

            assert "stage_start" in event_types
            assert "stage1_complete" in event_types
            assert "stage2_complete" in event_types
            assert "stage3_complete" in event_types
            assert "title_complete" in event_types
            assert "complete" in event_types

            # Verify functions were called
            mock_stage1.assert_called_once()
            mock_stage2.assert_called_once()
            mock_stage3.assert_called_once()
            mock_title.assert_called_once()
            mock_add_user.assert_called_once()
            mock_add_assistant.assert_called_once()
            mock_update_title.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_council_generator_subsequent_message(self, temp_data_dir):
        """Test run_council_generator for subsequent message does not generate title."""
        # Create conversation with existing messages
        conv_id = "test-conv-2"
        org_id = "test-org"
        conversation = {
            "id": conv_id,
            "user_id": "user1",
            "org_id": org_id,
            "title": "Existing Conversation",
            "messages": [
                {"role": "user", "content": "First question"},
                {"role": "assistant", "stage3": {"response": "First answer"}},
            ],
        }

        # Mock all stage functions
        with (
            patch(
                "backend.streaming.stage1_collect_responses", new_callable=AsyncMock
            ) as mock_stage1,
            patch(
                "backend.streaming.stage2_collect_rankings", new_callable=AsyncMock
            ) as mock_stage2,
            patch(
                "backend.streaming.stage3_synthesize_final", new_callable=AsyncMock
            ) as mock_stage3,
            patch(
                "backend.streaming.generate_conversation_title", new_callable=AsyncMock
            ) as mock_title,
            patch("backend.streaming.calculate_aggregate_rankings") as mock_calc_rankings,
            patch("backend.streaming.record_votes"),
            patch("backend.streaming.add_user_message"),
            patch("backend.streaming.add_assistant_message"),
            patch("backend.streaming.update_conversation_title") as mock_update_title,
        ):
            mock_stage1.return_value = [
                {
                    "model": "m1",
                    "response": "Response",
                    "personality_id": "p1",
                    "personality_name": "P1",
                }
            ]
            mock_stage2.return_value = ([], {})
            mock_stage3.return_value = {"model": "chairman", "response": "Final"}
            mock_calc_rankings.return_value = []

            # Collect events
            events = []
            async for event in run_council_generator(
                conv_id, "Follow-up question", conversation, org_id, "test-key", "https://test.url"
            ):
                events.append(event)

            # Verify title generation was not called
            mock_title.assert_not_called()
            mock_update_title.assert_not_called()

            # Verify other functions were called
            mock_stage1.assert_called_once()
            mock_stage2.assert_called_once()
            mock_stage3.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_council_generator_error_handling(self, temp_data_dir):
        """Test run_council_generator handles errors gracefully and sends error event."""
        conv_id = "test-conv-3"
        org_id = "test-org"
        conversation = {
            "id": conv_id,
            "user_id": "user1",
            "org_id": org_id,
            "title": "Test Conversation",
            "messages": [],
        }

        # Mock add_user_message to succeed, but stage1 to raise exception
        with (
            patch("backend.streaming.add_user_message"),
            patch(
                "backend.streaming.stage1_collect_responses", new_callable=AsyncMock
            ) as mock_stage1,
        ):
            mock_stage1.side_effect = Exception("Test error")

            # Collect events
            events = []
            async for event in run_council_generator(
                conv_id, "What is Python?", conversation, org_id, "test-key", "https://test.url"
            ):
                events.append(event)

            # Verify error event was sent
            assert len(events) > 0
            error_event = None
            for event in events:
                if event.startswith("data: "):
                    data = json.loads(event[6:])
                    if data.get("type") == "error":
                        error_event = data
                        break

            assert error_event is not None
            assert "Test error" in error_event.get("message", "")

    @pytest.mark.asyncio
    async def test_run_council_generator_stage1_empty_results(self, temp_data_dir):
        """Test run_council_generator handles empty stage1 results."""
        conv_id = "test-conv-4"
        org_id = "test-org"
        conversation = {
            "id": conv_id,
            "user_id": "user1",
            "org_id": org_id,
            "title": "Test Conversation",
            "messages": [],
        }

        with (
            patch(
                "backend.streaming.stage1_collect_responses", new_callable=AsyncMock
            ) as mock_stage1,
            patch(
                "backend.streaming.stage2_collect_rankings", new_callable=AsyncMock
            ) as mock_stage2,
            patch(
                "backend.streaming.stage3_synthesize_final", new_callable=AsyncMock
            ) as mock_stage3,
            patch(
                "backend.streaming.generate_conversation_title", new_callable=AsyncMock
            ) as mock_title,
            patch("backend.streaming.calculate_aggregate_rankings") as mock_calc_rankings,
            patch("backend.streaming.add_user_message"),
            patch("backend.streaming.add_assistant_message"),
        ):
            mock_stage1.return_value = []  # Empty results
            mock_stage2.return_value = ([], {})
            mock_stage3.return_value = {"model": "error", "response": "All models failed"}
            mock_calc_rankings.return_value = []
            mock_title.return_value = "Title"

            # Collect events
            events = []
            async for event in run_council_generator(
                conv_id, "What is Python?", conversation, org_id, "test-key", "https://test.url"
            ):
                events.append(event)

            # Should still complete
            assert len(events) > 0
            mock_stage1.assert_called_once()
            # Stage2 should still be called even with empty stage1
            mock_stage2.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_council_generator_records_votes(self, temp_data_dir):
        """Test run_council_generator records voting history."""
        conv_id = "test-conv-5"
        org_id = "test-org"
        conversation = {
            "id": conv_id,
            "user_id": "user1",
            "org_id": org_id,
            "title": "Test Title",
            "messages": [],
        }

        with (
            patch(
                "backend.streaming.stage1_collect_responses", new_callable=AsyncMock
            ) as mock_stage1,
            patch(
                "backend.streaming.stage2_collect_rankings", new_callable=AsyncMock
            ) as mock_stage2,
            patch(
                "backend.streaming.stage3_synthesize_final", new_callable=AsyncMock
            ) as mock_stage3,
            patch(
                "backend.streaming.generate_conversation_title", new_callable=AsyncMock
            ) as mock_title,
            patch("backend.streaming.calculate_aggregate_rankings") as mock_calc_rankings,
            patch("backend.streaming.record_votes") as mock_record_votes,
            patch("backend.streaming.add_user_message"),
            patch("backend.streaming.add_assistant_message"),
        ):
            mock_stage1.return_value = [
                {
                    "model": "m1",
                    "response": "Response",
                    "personality_id": "p1",
                    "personality_name": "P1",
                }
            ]
            mock_stage2.return_value = (
                [
                    {
                        "model": "m1",
                        "personality_name": "P1",
                        "ranking": "Rank",
                        "parsed_ranking": ["A"],
                    }
                ],
                {"A": "P1"},
            )
            mock_stage3.return_value = {"model": "chairman", "response": "Final"}
            mock_calc_rankings.return_value = []
            mock_title.return_value = "Generated Title"

            # Collect events
            events = []
            async for event in run_council_generator(
                conv_id, "What is Python?", conversation, org_id, "test-key", "https://test.url"
            ):
                events.append(event)

            # Verify votes were recorded
            mock_record_votes.assert_called_once()
            call_args = mock_record_votes.call_args
            # record_votes(conversation_id, stage2_results, label_to_model, conversation_title=..., turn_number=..., user_id=..., org_id=...)
            assert call_args[0][0] == conv_id  # conversation_id
            # conversation_title is passed as keyword arg: conversation_title=conversation_history.get("title", "Unknown")
            assert (
                call_args[1]["conversation_title"] == "Test Title"
            )  # conversation_title (as keyword arg)
