from datetime import datetime
from unittest.mock import patch

import pytest

from backend.database import get_tenant_session
from backend.models import Vote
from backend.ranking_service import calculate_league_table, generate_feedback_summary


@pytest.fixture
def mock_active_personalities():
    return [
        {"id": "p1", "name": "Personality A", "enabled": True},
        {"id": "p2", "name": "Personality B", "enabled": True},
    ]


@pytest.mark.asyncio
async def test_calculate_league_table(system_engine, tenant_engine, mock_active_personalities):
    org_id = "test-org"

    # 1. Setup Data
    # We need to ensure we are writing to the correct tenant DB
    # The get_tenant_session helper uses the engine factory.
    # In tests, we often patch get_tenant_engine or use the session directly.
    # Given conftest.py usually patches things, let's see.
    # But calculate_league_table calls get_tenant_session internally.

    # We will rely on the fact that existing tests (e.g. test_storage) work.
    # Usually conftest patches get_tenant_engine to return the shared in-memory engine.

    with get_tenant_session(org_id) as db:
        # Add Votes
        # Add Votes
        v1 = Vote(
            id="v1",
            conversation_id="conv1",
            turn_number=1,
            voter_model="judge",
            candidate_personality_id="p1",  # A
            candidate_model="Personality A",
            rank=1,
            reasoning="Good",
            timestamp=datetime.utcnow(),
        )
        v2 = Vote(
            id="v2",
            conversation_id="conv1",
            turn_number=1,
            voter_model="judge",
            candidate_personality_id="p2",  # B
            candidate_model="Personality B",
            rank=2,
            reasoning="Okay",
            timestamp=datetime.utcnow(),
        )
        # Session 2: Tie or swap
        v3 = Vote(
            id="v3",
            conversation_id="conv2",
            turn_number=1,
            voter_model="judge",
            candidate_personality_id="p1",  # A
            candidate_model="Personality A",
            rank=2,
            reasoning="Worse",
            timestamp=datetime.utcnow(),
        )
        v4 = Vote(
            id="v4",
            conversation_id="conv2",
            turn_number=1,
            voter_model="judge",
            candidate_personality_id="p2",  # B
            candidate_model="Personality B",
            rank=1,
            reasoning="Better",
            timestamp=datetime.utcnow(),
        )
        db.add_all([v1, v2, v3, v4])
        db.commit()

    # 2. Mock Active Personalities
    with patch(
        "backend.ranking_service.get_active_personalities", return_value=mock_active_personalities
    ):
        results = calculate_league_table(org_id)

    # 3. Assertions
    # Both have 1 win, 2 sessions, avg rank 1.5
    assert len(results) == 2

    p1_stats = next(r for r in results if r["id"] == "p1")
    assert p1_stats["wins"] == 1
    assert p1_stats["sessions"] == 2
    assert p1_stats["average_rank"] == 1.5
    assert p1_stats["votes_received"] == 2

    p2_stats = next(r for r in results if r["id"] == "p2")
    assert p2_stats["wins"] == 1
    assert p2_stats["sessions"] == 2
    assert p2_stats["average_rank"] == 1.5


@pytest.mark.asyncio
async def test_generate_feedback_summary(system_engine, tenant_engine, mock_active_personalities):
    org_id = "test-org"
    personality_name = "Personality A"

    # 1. Setup Data with reasoning
    with get_tenant_session(org_id) as db:
        v1 = Vote(
            id="v5",
            conversation_id="conv1",
            turn_number=1,
            voter_model="judge",
            candidate_personality_id="p1",
            candidate_model="Personality A",
            rank=1,
            reasoning="Great concise answer.",
            timestamp=datetime.utcnow(),
        )
        db.add(v1)
        db.commit()

    # 2. Mock LLM and Config
    with (
        patch(
            "backend.ranking_service.get_active_personalities",
            return_value=mock_active_personalities,
        ),
        patch(
            "backend.config.personalities.load_org_system_prompts",
            return_value={"feedback_synthesis_prompt": "Synthesize: {feedback_text}"},
        ),
        patch("backend.openrouter.query_model") as mock_query,
    ):
        mock_query.return_value = {"content": "Summary: Concise answers."}

        summary = await generate_feedback_summary(org_id, personality_name, "key", "url")

    # 3. Assertions
    assert summary == "Summary: Concise answers."

    # Verify mock call arguments
    args, _ = mock_query.call_args
    # args[1] is messages list
    prompt_sent = args[1][0]["content"]
    assert "Great concise answer." in prompt_sent
