import pytest
from unittest.mock import patch, MagicMock
from backend.evolution_service import combine_personalities
import yaml

@pytest.fixture
def mock_active_personalities():
    return [
        {"id": "p1", "name": "Parent A", "model": "gpt-4", "personality_prompt": {"role": "ParentA"}, "enabled": True},
        {"id": "p2", "name": "Parent B", "model": "gpt-4", "personality_prompt": {"role": "ParentB"}, "enabled": True},
    ]

@pytest.mark.asyncio
async def test_combine_personalities_success(mock_active_personalities):
    org_id = "test-org"
    parent_ids = ["p1", "p2"]
    name_suggestion = "Offspring"
    api_key = "key"
    base_url = "url"
    
    # Mock LLM response
    llm_response_content = """
    ```yaml
    role: You are Offspring.
    style: Diplomatic
    ```
    """
    
    with patch("backend.evolution_service.get_active_personalities", return_value=mock_active_personalities), \
         patch("backend.evolution_service.generate_feedback_summary", side_effect=["Feedback A", "Feedback B"]), \
         patch("backend.evolution_service.query_model", return_value={"content": llm_response_content}), \
         patch("backend.config.personalities.load_org_system_prompts", return_value={"evolution_prompt": "Prompt: {parent_data}"}), \
         patch("backend.config.personalities.load_org_models_config", return_value={"chairman_model": "gpt-4"}), \
         patch("backend.evolution_service._save_personality_file") as mock_save:

        result = await combine_personalities(org_id, parent_ids, name_suggestion, api_key, base_url)

        # Assertions
        assert result["name"] == name_suggestion
        assert result["model"] == "gpt-4" # Inherited from first parent
        assert result["personality_prompt"]["role"] == "You are Offspring."
        
        # Verify save called
        mock_save.assert_called_once()
        saved_personality = mock_save.call_args[0][1]
        assert saved_personality["id"] == result["id"]

@pytest.mark.asyncio
async def test_combine_personalities_not_enough_parents(mock_active_personalities):
    org_id = "test-org"
    parent_ids = ["p1"] # Only 1
    
    with patch("backend.evolution_service.get_active_personalities", return_value=mock_active_personalities):
        with pytest.raises(ValueError, match="At least 2 valid personalities"):
            await combine_personalities(org_id, parent_ids, "Name", "key", "url")

@pytest.mark.asyncio
async def test_combine_personalities_missing_prompt(mock_active_personalities):
    org_id = "test-org"
    parent_ids = ["p1", "p2"]
    
    with patch("backend.evolution_service.get_active_personalities", return_value=mock_active_personalities), \
         patch("backend.evolution_service.generate_feedback_summary", return_value="Feedback"), \
         patch("backend.config.personalities.load_org_system_prompts", return_value={}): # Empty config
        
        with pytest.raises(ValueError, match="System prompt 'evolution_prompt' is missing"):
             await combine_personalities(org_id, parent_ids, "Name", "key", "url")

@pytest.mark.asyncio
async def test_combine_personalities_invalid_yaml(mock_active_personalities):
    org_id = "test-org"
    parent_ids = ["p1", "p2"]
    
    with patch("backend.evolution_service.get_active_personalities", return_value=mock_active_personalities), \
         patch("backend.evolution_service.generate_feedback_summary", return_value="Feedback"), \
         patch("backend.config.personalities.load_org_system_prompts", return_value={"evolution_prompt": "Prompt"}), \
         patch("backend.config.personalities.load_org_models_config", return_value={"chairman_model": "gpt-4"}), \
         patch("backend.evolution_service.query_model", return_value={"content": "Not YAML"}):
         
         with pytest.raises(ValueError, match="LLM generated invalid YAML"):
              await combine_personalities(org_id, parent_ids, "Name", "key", "url")
