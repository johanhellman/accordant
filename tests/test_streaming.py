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
            os.path.join(tmpdir, "users.json")
            os.makedirs(orgs_dir, exist_ok=True)
            monkeypatch.setattr("backend.organizations.ORGS_DATA_DIR", orgs_dir)
            yield tmpdir

    @pytest.mark.asyncio
    async def test_run_council_generator_first_message(self, temp_data_dir):
        """Test run_council_generator for first message generates title and all stages."""
        conv_id = "test-conv-1"
        org_id = "test-org"
        conversation = {
            "id": conv_id,
            "user_id": "user1",
            "org_id": org_id,
            "title": "New Conversation",
            "messages": [],
        }

        mock_events = [
            {"type": "stage_start", "data": {"stage": 1}},
            {"type": "stage1_complete", "data": {"results": [{"response": "R1"}]}},
            {"type": "stage_start", "data": {"stage": 2}},
            {
                "type": "stage2_complete",
                "data": {"results": [], "metadata": {"label_to_model": {}}},
            },
            {"type": "stage_start", "data": {"stage": 3}},
            {"type": "stage3_complete", "data": {"results": {"response": "Final"}}},
        ]

        async def mock_cycle_gen(*args, **kwargs):
            for event in mock_events:
                yield event

        with (
            patch("backend.streaming.run_council_cycle", side_effect=mock_cycle_gen) as mock_cycle,
            patch(
                "backend.streaming.generate_conversation_title", new_callable=AsyncMock
            ) as mock_title,
            patch("backend.streaming.record_votes"),
            patch("backend.streaming.add_user_message"),
            patch("backend.streaming.add_assistant_message") as mock_add_assistant,
            patch("backend.streaming.update_conversation_title") as mock_update_title,
        ):
            mock_title.return_value = "Generated Title"

            events = []
            async for event in run_council_generator(
                conv_id, "What is Python?", conversation, org_id, "test-key", "https://test.url"
            ):
                events.append(event)

            event_types = [json.loads(e[6:])["type"] for e in events if e.startswith("data: ")]

            assert "stage_start" in event_types
            assert "stage1_complete" in event_types
            assert "stage2_complete" in event_types
            assert "stage3_complete" in event_types
            assert "title_complete" in event_types
            assert "complete" in event_types

            mock_cycle.assert_called_once()
            mock_title.assert_called_once()
            mock_add_assistant.assert_called_once()
            mock_update_title.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_council_generator_subsequent_message(self, temp_data_dir):
        """Test run_council_generator for subsequent message does not generate title."""
        conv_id = "test-conv-2"
        org_id = "test-org"
        conversation = {
            "id": conv_id,
            "user_id": "user1",
            "org_id": org_id,
            "title": "Existing Conversation",
            "messages": [{"role": "user", "content": "First question"}],
        }

        async def mock_cycle_gen(*args, **kwargs):
            yield {"type": "stage1_complete", "data": {"results": []}}
            yield {"type": "stage3_complete", "data": {"results": {"response": "Final"}}}

        with (
            patch("backend.streaming.run_council_cycle", side_effect=mock_cycle_gen),
            patch(
                "backend.streaming.generate_conversation_title", new_callable=AsyncMock
            ) as mock_title,
            patch("backend.streaming.add_user_message"),
            patch("backend.streaming.add_assistant_message"),
            patch("backend.streaming.update_conversation_title") as mock_update_title,
        ):
            events = []
            async for event in run_council_generator(
                conv_id, "Follow-up", conversation, org_id, "test-key", "https://test.url"
            ):
                events.append(event)

            mock_title.assert_not_called()
            mock_update_title.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_council_generator_error_handling(self, temp_data_dir):
        """Test run_council_generator handles errors gracefully."""
        conv_id = "test-conv-3"
        org_id = "test-org"
        conversation = {"id": conv_id, "org_id": org_id, "messages": []}

        async def mock_cycle_gen(*args, **kwargs):
            raise Exception("Test error")
            yield {}  # unreachable

        with (
            patch("backend.streaming.run_council_cycle", side_effect=mock_cycle_gen),
            patch("backend.streaming.add_user_message"),
        ):
            events = []
            async for event in run_council_generator(
                conv_id, "What is Python?", conversation, org_id, "test-key", "https://test.url"
            ):
                events.append(event)

            error_event = next((json.loads(e[6:]) for e in events if "error" in e), None)
            assert error_event is not None
            assert "Test error" in error_event["message"]
