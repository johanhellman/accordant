import pytest
from unittest.mock import MagicMock, patch
import os
import json
from backend.ranking_service import calculate_league_table, generate_feedback_summary
from backend.evolution_service import combine_personalities
from backend.voting_history import record_votes, save_voting_history, get_voting_history_path

@pytest.fixture
def mock_org_data(tmp_path):
    org_id = "test-org"
    org_dir = tmp_path / org_id
    org_dir.mkdir()
    
    # Mock personalities
    p_dir = org_dir / "personalities"
    p_dir.mkdir()
    
    with patch("backend.ranking_service.ORGS_DATA_DIR", str(tmp_path)), \
         patch("backend.voting_history.ORGS_DATA_DIR", str(tmp_path)), \
         patch("backend.evolution_service.get_org_personalities_dir", return_value=str(p_dir)), \
         patch("backend.config.personalities.ORGS_DATA_DIR", str(tmp_path)):
         
        yield org_id, tmp_path

def test_league_table_calculation(mock_org_data):
    org_id, tmp_path = mock_org_data
    
    # Create fake active personalities
    mock_active = [
        {"id": "p1", "name": "WinnerBot", "enabled": True}, 
        {"id": "p2", "name": "LoserBot", "enabled": True}
    ]
    
    with patch("backend.ranking_service.get_active_personalities", return_value=mock_active):
        # 1. Record some votes
        # Session 1: WinnerBot #1, LoserBot #2
        votes_1 = [
            {"model": "judge", "ranking": "A is better", "parsed_ranking": ["Response A", "Response B"]}
        ]
        label_map_1 = {"Response A": "WinnerBot", "Response B": "LoserBot"}
        
        record_votes("conv1", votes_1, label_map_1, org_id=org_id)
        
        # Session 2: WinnerBot #1 again
        votes_2 = [
             {"model": "judge", "ranking": "A wins", "parsed_ranking": ["Response A"]}
        ]
        label_map_2 = {"Response A": "WinnerBot"}
        record_votes("conv2", votes_2, label_map_2, org_id=org_id)
        
        # 2. Calculate Table
        table = calculate_league_table(org_id)
        
        winner = next(p for p in table if p["name"] == "WinnerBot")
        loser = next(p for p in table if p["name"] == "LoserBot")
        
        assert winner["wins"] == 2
        assert winner["sessions"] == 2
        assert winner["win_rate"] == 100.0
        assert winner["average_rank"] == 1.0
        
        assert loser["wins"] == 0
        assert loser["sessions"] == 1
        assert loser["win_rate"] == 0.0
        assert loser["average_rank"] == 2.0


@pytest.mark.asyncio
async def test_feedback_summary_privacy(mock_org_data):
    org_id, _ = mock_org_data
    
    # Mock voting history showing a session
    mock_history = [
        {
            "conversation_id": "conv_private",
            "votes": [
                {
                    "rankings": [{"candidate": "TargetBot", "rank": 1, "label": "Response A"}],
                    "reasoning": "Should be ignored by generator in favor of secure storage fetch if we were strict, but service currently uses what it has or fetches." 
                    # Actually service.py currently prefers fetching from storage to ensure we get the full text if history is metadata-only.
                }
            ]
        }
    ]
    
    with patch("backend.ranking_service.load_voting_history", return_value=mock_history), \
         patch("backend.ranking_service.get_conversation") as mock_get_conv, \
         patch("backend.openrouter.query_model") as mock_llm:
         
        # Mock Conversation Storage returning the text
        mock_get_conv.return_value = {
            "messages": [
                {
                    "role": "assistant",
                    "metadata": {
                        "stage2": [
                            {"model": "Judge", "ranking": "Response A (TargetBot) was excellent."}
                        ]
                    }
                }
            ]
        }
        
        mock_llm.return_value = {"content": "Strengths: Excellent."}
        
        summary = await generate_feedback_summary(org_id, "TargetBot", "key", "url")
        
        assert "Strengths: Excellent" in summary
        # Verify it called storage to get the text
        mock_get_conv.assert_called_with("conv_private", org_id)


@pytest.mark.asyncio
async def test_combine_personalities(mock_org_data):
    org_id, tmp_path = mock_org_data
    
    # Mock parents
    parents = [
        {"id": "p1", "name": "Parent A", "model": "gpt-4", "personality_prompt": {"ROLE": "A"}},
        {"id": "p2", "name": "Parent B", "model": "gpt-4", "personality_prompt": {"ROLE": "B"}}
    ]
    
    with patch("backend.evolution_service.get_active_personalities", return_value=parents), \
         patch("backend.evolution_service.generate_feedback_summary", return_value="Good job"), \
         patch("backend.evolution_service.query_model") as mock_llm:
         
        # Mock LLM returning valid YAML
        mock_llm.return_value = {
            "content": "```yaml\nidentity_and_role: New Role\ntone: Balanced\n```"
        }
        
        result = await combine_personalities(org_id, ["p1", "p2"], "Child Bot", "key", "url")
        
        assert result["name"] == "Child Bot"
        assert result["personality_prompt"]["identity_and_role"] == "New Role"
        
        # Verify file saved
        p_dir = tmp_path / org_id / "personalities"
        saved_file = p_dir / f"{result['id']}.yaml"
        assert saved_file.exists()
