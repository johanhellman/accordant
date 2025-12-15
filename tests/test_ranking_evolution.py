import uuid
from unittest.mock import AsyncMock, patch

import pytest

from backend.models import Vote
from backend.ranking_service import calculate_league_table, generate_feedback_summary
from backend.voting_history import record_votes


@pytest.fixture
def mock_active_personalities():
    return [
        {"id": "p1", "name": "WinnerBot", "enabled": True},
        {"id": "p2", "name": "LoserBot", "enabled": True},
    ]


def test_league_table_calculation(tenant_db_session, mock_active_personalities):
    org_id = "test-org-league"

    with patch(
        "backend.ranking_service.get_active_personalities", return_value=mock_active_personalities
    ):
        # 1. Record some votes using the actual service which writes to DB
        # Session 1: WinnerBot #1, LoserBot #2
        votes_1 = [
            {
                "model": "judge",
                "ranking": "A is better",
                "parsed_ranking": ["Response A", "Response B"],
            }
        ]
        label_map_1 = {
            "Response A": {"id": "p1", "name": "WinnerBot"},
            "Response B": {"id": "p2", "name": "LoserBot"},
        }

        record_votes("conv1", votes_1, label_map_1, org_id=org_id)

        # Session 2: WinnerBot #1 again
        votes_2 = [{"model": "judge", "ranking": "A wins", "parsed_ranking": ["Response A"]}]
        label_map_2 = {"Response A": {"id": "p1", "name": "WinnerBot"}}

        record_votes("conv2", votes_2, label_map_2, org_id=org_id)

        # 2. Calculate Table
        table = calculate_league_table(org_id)

        winner = next((p for p in table if p["name"] == "WinnerBot"), None)
        loser = next((p for p in table if p["name"] == "LoserBot"), None)

        assert winner is not None
        assert winner["wins"] == 2
        assert winner["sessions"] == 2
        assert winner["win_rate"] == 100.0
        assert winner["average_rank"] == 1.0

        assert loser is not None
        assert loser["wins"] == 0
        assert loser["sessions"] == 1
        assert loser["win_rate"] == 0.0
        assert loser["average_rank"] == 2.0


@pytest.mark.asyncio
async def test_feedback_summary_privacy(tenant_db_session):
    org_id = "test-org-feedback"
    target_name = "TargetBot"
    target_id = "target-id-123"

    # Mock active personalities to resolve name to ID
    active = [{"id": target_id, "name": target_name, "enabled": True}]

    # Seed DB with a vote containing reasoning
    vote = Vote(
        id=str(uuid.uuid4()),
        conversation_id="conv_private",
        turn_number=1,
        voter_model="Judge",
        candidate_model=target_name,
        candidate_personality_id=target_id,
        rank=1,
        label="Response A",
        reasoning="Response A was excellent and concise.",
    )
    tenant_db_session.add(vote)
    tenant_db_session.commit()

    with (
        patch("backend.ranking_service.get_active_personalities", return_value=active),
        patch("backend.ranking_service.get_active_personalities", return_value=active),
        patch("backend.openrouter.query_model", new_callable=AsyncMock) as mock_llm,
        patch("backend.config.personalities.load_org_system_prompts", return_value={}),
    ):
        mock_llm.return_value = {"content": "Strengths: Excellent."}

        summary = await generate_feedback_summary(org_id, target_name, "key", "url")

        assert "Strengths: Excellent" in summary

        # Verify LLM was called with the reasoning from DB
        call_args = mock_llm.call_args[0]  # model, messages
        messages = call_args[1]
        prompt = messages[0]["content"]
        assert "Response A was excellent and concise" in prompt
