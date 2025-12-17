from unittest.mock import AsyncMock, patch

import pytest

from backend.council import run_council_cycle


@pytest.mark.asyncio
async def test_council_cycle_standard_flow():
    """Test standard flow without consensus enabled."""

    # Mocks
    mock_stage1 = AsyncMock(return_value=[{"model": "gpt-4", "response": "Hello"}])
    mock_stage2 = AsyncMock(return_value=([{"model": "gpt-4", "ranking": "A"}], {"A": "gpt-4"}))
    mock_stage3 = AsyncMock(return_value={"model": "gpt-4", "response": "Final Answer"})

    with (
        patch("backend.council.stage1_collect_responses", side_effect=mock_stage1),
        patch("backend.council.stage2_collect_rankings", side_effect=mock_stage2),
        patch("backend.council.stage3_synthesize_final", side_effect=mock_stage3),
        patch("backend.council.calculate_aggregate_rankings", return_value={"gpt-4": 1}),
    ):
        events = []
        async for event in run_council_cycle("test query", consensus_enabled=False):
            events.append(event)

        # Verify sequence
        assert events[0]["type"] == "stage_start"
        assert events[0]["data"]["stage"] == 1

        assert events[1]["type"] == "stage1_complete"
        assert len(events[1]["data"]["results"]) == 1

        assert events[2]["type"] == "stage_start"
        assert events[2]["data"]["stage"] == 2

        assert events[3]["type"] == "stage2_complete"
        assert "metadata" in events[3]["data"]

        assert events[4]["type"] == "stage_start"
        assert events[4]["data"]["stage"] == 3

        assert events[5]["type"] == "stage3_complete"
        assert events[5]["data"]["results"]["model"] == "gpt-4"

        # Verify calls
        mock_stage3.assert_called_once()


@pytest.mark.asyncio
async def test_council_cycle_consensus_flow():
    """Test flow with consensus enabled."""

    # Mocks
    mock_stage1 = AsyncMock(return_value=[{"model": "gpt-4", "response": "Hello"}])
    mock_stage2 = AsyncMock(return_value=([{"model": "gpt-4", "ranking": "A"}], {"A": "gpt-4"}))
    # We don't expect stage3_synthesize_final to be called
    mock_stage3 = AsyncMock()

    # Mock ConsensusService
    mock_consensus = AsyncMock(return_value=("Consensus Answer", {"gpt-4": 10}))

    with (
        patch("backend.council.stage1_collect_responses", side_effect=mock_stage1),
        patch("backend.council.stage2_collect_rankings", side_effect=mock_stage2),
        patch("backend.council.stage3_synthesize_final", side_effect=mock_stage3),
        patch("backend.council.calculate_aggregate_rankings", return_value={"gpt-4": 1}),
        patch(
            "backend.consensus_service.ConsensusService.synthesize_consensus",
            side_effect=mock_consensus,
        ),
    ):
        events = []
        async for event in run_council_cycle("test query", consensus_enabled=True):
            events.append(event)

        # Verify sequence
        assert events[-1]["type"] == "stage3_complete"
        result = events[-1]["data"]["results"]

        assert result["model"] == "consensus-strategy"
        assert result["response"] == "Consensus Answer"
        assert result["consensus_contributions"] == {"gpt-4": 10}

        # Verify calls
        mock_stage3.assert_not_called()
        mock_consensus.assert_called_once()
