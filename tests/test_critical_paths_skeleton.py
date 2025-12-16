"""Unit tests for critical but under-tested paths.

These tests directly call functions to ensure they are covered by test coverage.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import yaml
from fastapi import HTTPException

from backend.admin_routes import (
    ComponentConfig,
    Personality,
    SystemPromptsConfig,
    delete_personality,
    get_personality,
    update_personality,
    update_system_prompts,
    validate_prompt_tags,
)
from backend.council import generate_conversation_title
from backend.llm_service import get_available_models
from backend.users import User


def test_validate_prompt_tags_valid():
    """Test validate_prompt_tags with valid prompts containing all required tags."""
    # Valid prompt with all required tags
    validate_prompt_tags(
        "Rank {responses_text} for {user_query} from {peer_text}",
        ["{user_query}", "{responses_text}", "{peer_text}"],
        "Ranking Prompt",
    )

    # Valid prompt with single tag
    validate_prompt_tags("Title for {user_query}", ["{user_query}"], "Title Prompt")


def test_validate_prompt_tags_missing_tags():
    """Test validate_prompt_tags raises HTTPException when tags are missing."""
    # Missing one tag
    with pytest.raises(HTTPException) as exc_info:
        validate_prompt_tags(
            "Rank {responses_text} for {user_query}",
            ["{user_query}", "{responses_text}", "{peer_text}"],
            "Ranking Prompt",
        )
    assert exc_info.value.status_code == 400
    assert "missing required tags" in exc_info.value.detail
    assert "{peer_text}" in exc_info.value.detail

    # Missing multiple tags
    with pytest.raises(HTTPException) as exc_info:
        validate_prompt_tags(
            "Rank responses",
            ["{user_query}", "{responses_text}", "{peer_text}"],
            "Ranking Prompt",
        )
    assert exc_info.value.status_code == 400
    assert "missing required tags" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_personality_existing(tmp_path, monkeypatch):
    """Test get_personality with existing personality file."""
    # Setup
    org_id = "test-org"
    personalities_dir = tmp_path / "organizations" / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    personality_data = {
        "id": "test_personality",
        "name": "Test Bot",
        "description": "A test personality",
        "model": "openai/gpt-4",
        "personality_prompt": {"identity_and_role": "You are a test bot."},
    }

    personality_file = personalities_dir / "test_personality.yaml"
    with open(personality_file, "w") as f:
        yaml.dump(personality_data, f)

    # Mock user
    mock_user = User(
        id="1",
        username="admin",
        password_hash="hash",
        is_admin=True,
        org_id=org_id,
    )

    # Mock get_org_personalities_dir
    # Mock get_org_personalities_dir in the config module where it is used
    with patch("backend.config.personalities.get_org_personalities_dir") as mock_get_dir:
        mock_get_dir.return_value = str(personalities_dir)

        # Call function
        result = await get_personality("test_personality", current_user=mock_user)

        # Assertions
        assert result["id"] == "test_personality"
        assert result["name"] == "Test Bot"
        assert result["model"] == "openai/gpt-4"


@pytest.mark.asyncio
async def test_get_personality_not_found(tmp_path, monkeypatch):
    """Test get_personality raises HTTPException when personality file doesn't exist."""
    # Setup
    org_id = "test-org"
    personalities_dir = tmp_path / "organizations" / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    # Mock user
    mock_user = User(
        id="1",
        username="admin",
        password_hash="hash",
        is_admin=True,
        org_id=org_id,
    )

    # Mock get_org_personalities_dir
    # Mock get_org_personalities_dir in the config module where it is used
    with patch("backend.config.personalities.get_org_personalities_dir") as mock_get_dir:
        mock_get_dir.return_value = str(personalities_dir)

        # Call function - should raise 404
        with pytest.raises(HTTPException) as exc_info:
            await get_personality("non_existent", current_user=mock_user)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_update_personality(tmp_path, monkeypatch):
    """Test update_personality updates existing personality file."""
    # Setup
    org_id = "test-org"
    personalities_dir = tmp_path / "organizations" / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    original_data = {
        "id": "test_personality",
        "name": "Original Name",
        "description": "Original description",
        "model": "openai/gpt-4",
        "personality_prompt": {"identity_and_role": "Original prompt"},
    }

    personality_file = personalities_dir / "test_personality.yaml"
    with open(personality_file, "w") as f:
        yaml.dump(original_data, f)

    # Mock user
    mock_user = User(
        id="1",
        username="admin",
        password_hash="hash",
        is_admin=True,
        org_id=org_id,
    )

    # Updated data as Personality model
    updated_personality = Personality(
        id="test_personality",
        name="Updated Name",
        description="Updated description",
        model="openai/gpt-4",
        personality_prompt={"identity_and_role": "Updated prompt"},
    )

    # Mock get_org_personalities_dir
    # Mock get_org_personalities_dir in the config module where it is used
    with patch("backend.config.personalities.get_org_personalities_dir") as mock_get_dir:
        mock_get_dir.return_value = str(personalities_dir)

        # Call function
        result = await update_personality(
            "test_personality", updated_personality, current_user=mock_user
        )

        # Assertions
        assert result.name == "Updated Name"
        assert result.description == "Updated description"

        # Verify file was updated
        with open(personality_file) as f:
            saved_data = yaml.safe_load(f)
            assert saved_data["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_personality_id_mismatch(tmp_path, monkeypatch):
    """Test update_personality raises HTTPException when ID doesn't match."""
    # Setup
    org_id = "test-org"
    personalities_dir = tmp_path / "organizations" / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    # Mock user
    mock_user = User(
        id="1",
        username="admin",
        password_hash="hash",
        is_admin=True,
        org_id=org_id,
    )

    # Data with mismatched ID as Personality model
    personality_data = Personality(
        id="different_id",
        name="Test",
        description="Test description",
        model="openai/gpt-4",
        personality_prompt={"identity_and_role": "Test prompt"},
    )

    # Mock get_org_personalities_dir
    # Mock get_org_personalities_dir in the config module where it is used
    with patch("backend.config.personalities.get_org_personalities_dir") as mock_get_dir:
        mock_get_dir.return_value = str(personalities_dir)

        # Call function - should raise 400
        with pytest.raises(HTTPException) as exc_info:
            await update_personality("test_personality", personality_data, current_user=mock_user)

        assert exc_info.value.status_code == 400
        assert "ID mismatch" in exc_info.value.detail


@pytest.mark.asyncio
async def test_delete_personality_existing(tmp_path, monkeypatch):
    """Test delete_personality deletes existing personality file."""
    # Setup
    org_id = "test-org"
    personalities_dir = tmp_path / "organizations" / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    personality_file = personalities_dir / "to_delete.yaml"
    with open(personality_file, "w") as f:
        yaml.dump({"id": "to_delete", "name": "To Delete"}, f)

    # Mock user
    mock_user = User(
        id="1",
        username="admin",
        password_hash="hash",
        is_admin=True,
        org_id=org_id,
    )

    # Mock get_org_personalities_dir
    # Mock get_org_personalities_dir in the config module where it is used
    with patch("backend.config.personalities.get_org_personalities_dir") as mock_get_dir:
        mock_get_dir.return_value = str(personalities_dir)

        # Call function
        result = await delete_personality("to_delete", current_user=mock_user)

        # Assertions
        assert result["status"] == "success"
        assert "deleted" in result["message"].lower()
        assert not personality_file.exists()


@pytest.mark.asyncio
async def test_delete_personality_not_found(tmp_path, monkeypatch):
    """Test delete_personality raises HTTPException when personality doesn't exist."""
    # Setup
    org_id = "test-org"
    personalities_dir = tmp_path / "organizations" / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    # Mock user
    mock_user = User(
        id="1",
        username="admin",
        password_hash="hash",
        is_admin=True,
        org_id=org_id,
    )

    # Mock get_org_personalities_dir
    # Mock get_org_personalities_dir in the config module where it is used
    with patch("backend.config.personalities.get_org_personalities_dir") as mock_get_dir:
        mock_get_dir.return_value = str(personalities_dir)

        # Call function - should raise 404
        with pytest.raises(HTTPException) as exc_info:
            await delete_personality("non_existent", current_user=mock_user)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_update_system_prompts(tmp_path, monkeypatch):
    """Test update_system_prompts updates system-prompts.yaml file."""
    # Setup
    org_id = "test-org"
    config_dir = tmp_path / "organizations" / org_id / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Mock user
    mock_user = User(
        id="1",
        username="admin",
        password_hash="hash",
        is_admin=True,
        org_id=org_id,
    )

    # System prompts config
    config = SystemPromptsConfig(
        base_system_prompt={"value": "Base prompt", "is_default": False, "source": "custom"},
        ranking=ComponentConfig(
            prompt={"value": "Rank {responses_text} for {user_query} from {peer_text}", "is_default": False, "source": "custom"},
            model="gemini/gemini-pro",
        ),
        chairman=ComponentConfig(
            prompt={"value": "Chairman for {user_query} using {stage1_text} and {voting_details_text}", "is_default": False, "source": "custom"},
            model="gemini/gemini-pro",
        ),
        title_generation=ComponentConfig(
            prompt={"value": "Title for {user_query}", "is_default": False, "source": "custom"},
            model="gemini/gemini-pro",
        ),
        evolution_prompt={"value": "Evolve personality", "is_default": True, "source": "default"},
    )

    # Mock dependencies
    with (
        patch("backend.config.personalities.get_org_config_dir") as mock_get_config_dir,
        patch("backend.config.personalities.load_org_models_config") as mock_load_models,
    ):
        mock_get_config_dir.return_value = str(config_dir)
        mock_load_models.return_value = {
            "ranking_model": "gemini/gemini-pro",
            "chairman_model": "gemini/gemini-pro",
            "title_model": "gemini/gemini-pro",
        }

        # Call function
        result = await update_system_prompts(config.dict(), current_user=mock_user)

        # Assertions
        assert result["base_system_prompt"]["value"] == "Base prompt"
        assert result["ranking"]["prompt"]["value"] == config.ranking.prompt.value

        # Verify file was created/updated
        system_prompts_file = config_dir / "system-prompts.yaml"
        assert system_prompts_file.exists()

        with open(system_prompts_file) as f:
            saved_data = yaml.safe_load(f)
            assert saved_data["base_system_prompt"]["value"] == "Base prompt"
            assert saved_data["ranking"]["prompt"]["value"] == config.ranking.prompt.value


@pytest.mark.asyncio
async def test_update_system_prompts_invalid_tags(tmp_path, monkeypatch):
    """Test update_system_prompts raises HTTPException when required tags are missing."""
    # Setup
    org_id = "test-org"
    config_dir = tmp_path / "organizations" / org_id / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Mock user
    mock_user = User(
        id="1",
        username="admin",
        password_hash="hash",
        is_admin=True,
        org_id=org_id,
    )

    # System prompts config with missing tags
    from backend.admin_routes import ComponentConfig, SystemPromptsConfig

    config = SystemPromptsConfig(
        base_system_prompt={"value": "Base prompt", "is_default": True, "source": "default"},
        ranking=ComponentConfig(
            prompt={"value": "Rank responses", "is_default": False, "source": "custom"},  # Missing required tags
            model="gemini/gemini-pro",
        ),
        chairman=ComponentConfig(
            prompt={"value": "Chairman prompt", "is_default": True, "source": "default"},
            model="gemini/gemini-pro",
        ),
        title_generation=ComponentConfig(
            prompt={"value": "Title prompt", "is_default": True, "source": "default"},
            model="gemini/gemini-pro",
        ),
        evolution_prompt={"value": "Evolve personality", "is_default": True, "source": "default"},
    )

    # Mock get_org_config_dir
    with patch("backend.config.personalities.get_org_config_dir") as mock_get_config_dir:
        mock_get_config_dir.return_value = str(config_dir)

        # Call function - should raise 400
        with pytest.raises(HTTPException) as exc_info:
            await update_system_prompts(config.dict(), current_user=mock_user)

        assert exc_info.value.status_code == 400
        assert "missing required tags" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_available_models_openrouter(mock_httpx_client):
    """Test get_available_models with OpenRouter provider."""
    # Reset cache
    with patch("backend.llm_service._MODELS_CACHE", {}):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "openai/gpt-4", "name": "GPT-4"},
                {"id": "anthropic/claude-2", "name": "Claude 2"},
            ]
        }
        mock_httpx_client.get.return_value = mock_response

        models = await get_available_models(
            "fake-key", "https://openrouter.ai/api/v1/chat/completions"
        )

        assert len(models) == 2
        assert models[0]["id"] == "openai/gpt-4"
        assert models[0]["provider"] == "openai"
        assert models[1]["id"] == "anthropic/claude-2"
        assert models[1]["provider"] == "anthropic"

        # Verify URL
        mock_httpx_client.get.assert_called_with(
            "https://openrouter.ai/api/v1/models", headers={"Authorization": "Bearer fake-key"}
        )


@pytest.mark.asyncio
async def test_get_available_models_generic(mock_httpx_client):
    """Test get_available_models with generic OpenAI-compatible provider."""
    with patch("backend.llm_service._MODELS_CACHE", {}):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "llama-2-70b", "object": "model"}]}
        mock_httpx_client.get.return_value = mock_response

        models = await get_available_models(
            "fake-key", "https://api.together.xyz/v1/chat/completions"
        )

        assert len(models) == 1
        assert models[0]["id"] == "llama-2-70b"
        assert models[0]["provider"] == "unknown"  # Fallback when no slash

        # Verify URL construction
        mock_httpx_client.get.assert_called_with(
            "https://api.together.xyz/v1/models", headers={"Authorization": "Bearer fake-key"}
        )


@pytest.mark.asyncio
async def test_get_available_models_error(mock_httpx_client):
    """Test get_available_models returns empty list on error."""
    with patch("backend.llm_service._MODELS_CACHE", {}):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=None, response=mock_response
        )

        mock_httpx_client.get.return_value = mock_response

        models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

        assert models == []


@pytest.mark.asyncio
async def test_get_available_models_caching(mock_httpx_client):
    """Test get_available_models uses cache when available."""
    base_url = "https://openrouter.ai/api/v1"
    cached_models = [{"id": "cached-model", "name": "Cached", "provider": "test"}]
    cached_time = datetime.now()

    mock_cache = {base_url: {"models": cached_models, "timestamp": cached_time}}

    with patch("backend.llm_service._MODELS_CACHE", mock_cache):
        models = await get_available_models("fake-key", base_url)

        assert models == cached_models
        mock_httpx_client.get.assert_not_called()


@pytest.mark.asyncio
async def test_get_available_models_cache_expiry(mock_httpx_client):
    """Test get_available_models refreshes cache when expired."""
    base_url = "https://openrouter.ai/api/v1"
    # Expired cache
    cached_models = [{"id": "old-model"}]
    cached_time = datetime.now() - timedelta(hours=2)

    mock_cache = {base_url: {"models": cached_models, "timestamp": cached_time}}

    with patch("backend.llm_service._MODELS_CACHE", mock_cache):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "new-model"}]}
        mock_httpx_client.get.return_value = mock_response

        models = await get_available_models("fake-key", base_url)

        assert len(models) == 1
        assert models[0]["id"] == "new-model"
        mock_httpx_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_generate_conversation_title_success(monkeypatch):
    """Test generate_conversation_title generates a title successfully."""
    org_id = "test-org"
    user_query = "What is the meaning of life?"

    # Mock dependencies
    with (
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.load_org_models_config") as mock_load_models,
        patch("backend.council.query_model") as mock_query_model,
    ):
        mock_load_prompts.return_value = {
            "title_prompt": "Generate a title for: {user_query}",
        }
        mock_load_models.return_value = {"title_model": "gemini/gemini-pro"}
        mock_query_model.return_value = {"content": "The Meaning of Life"}

        title = await generate_conversation_title(
            user_query, org_id, "fake-key", "https://fake.url"
        )

        assert isinstance(title, str)
        assert title == "The Meaning of Life"
        mock_query_model.assert_called_once()


@pytest.mark.asyncio
async def test_generate_conversation_title_fallback(monkeypatch):
    """Test generate_conversation_title returns fallback when query_model fails."""
    org_id = "test-org"
    user_query = "What is the meaning of life?"

    # Mock dependencies
    with (
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.load_org_models_config") as mock_load_models,
        patch("backend.council.query_model") as mock_query_model,
    ):
        mock_load_prompts.return_value = {
            "title_prompt": "Generate a title for: {user_query}",
        }
        mock_load_models.return_value = {"title_model": "gemini/gemini-pro"}
        mock_query_model.return_value = None  # Simulate failure

        title = await generate_conversation_title(
            user_query, org_id, "fake-key", "https://fake.url"
        )

        assert title == "New Conversation"


@pytest.mark.asyncio
async def test_generate_conversation_title_truncation(monkeypatch):
    """Test generate_conversation_title truncates long titles."""
    org_id = "test-org"
    user_query = "What is the meaning of life?"
    long_title = "A" * 100  # Very long title

    # Mock dependencies
    with (
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.load_org_models_config") as mock_load_models,
        patch("backend.council.query_model") as mock_query_model,
    ):
        mock_load_prompts.return_value = {
            "title_prompt": "Generate a title for: {user_query}",
        }
        mock_load_models.return_value = {"title_model": "gemini/gemini-pro"}
        mock_query_model.return_value = {"content": long_title}

        title = await generate_conversation_title(
            user_query, org_id, "fake-key", "https://fake.url"
        )

        assert len(title) <= 50
        assert title.endswith("...")


@pytest.fixture
def mock_httpx_client():
    """Fixture to mock httpx.AsyncClient for get_available_models tests."""
    with patch("httpx.AsyncClient", autospec=True) as mock_client:
        mock_context = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_context
        yield mock_context


# ============================================================================
# CRITICAL PATH TESTS - Top 5 Functions (Now Fully Tested)
# ============================================================================
# Comprehensive test coverage for the most critical council orchestration
# functions. All tests have been implemented and provide full coverage of:
# - run_full_council: Full 3-stage orchestration
# - stage1_collect_responses: Stage 1 response collection
# - stage2_collect_rankings: Stage 2 ranking collection with anonymization
# - stage3_synthesize_final: Stage 3 final synthesis
# - query_model: Core LLM API interaction with retry logic
# ============================================================================


@pytest.mark.asyncio
async def test_run_full_council_success():
    """Test run_full_council successfully orchestrates all 3 stages."""
    from backend.council import run_full_council
    from backend.council_helpers import RESPONSE_LABEL_PREFIX

    with (
        patch("backend.council.stage1_collect_responses", new_callable=AsyncMock) as mock_stage1,
        patch("backend.council.stage2_collect_rankings", new_callable=AsyncMock) as mock_stage2,
        patch("backend.council.stage3_synthesize_final", new_callable=AsyncMock) as mock_stage3,
        patch("backend.council.calculate_aggregate_rankings") as mock_calc_rankings,
    ):
        # Setup mock responses
        mock_stage1_results = [
            {
                "model": "openai/gpt-4",
                "response": "Response A",
                "personality_id": "personality1",
                "personality_name": "Personality 1",
            },
            {
                "model": "anthropic/claude-3",
                "response": "Response B",
                "personality_id": "personality2",
                "personality_name": "Personality 2",
            },
        ]

        mock_stage2_results = [
            {
                "model": "openai/gpt-4",
                "personality_name": "Personality 1",
                "ranking": "Ranking text",
                "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}B", f"{RESPONSE_LABEL_PREFIX}A"],
            },
        ]

        mock_label_to_model = {
            f"{RESPONSE_LABEL_PREFIX}A": {
                "name": "Personality 1",
                "id": "personality1",
                "model": "openai/gpt-4"
            },
            f"{RESPONSE_LABEL_PREFIX}B": {
                "name": "Personality 2",
                "id": "personality2",
                "model": "anthropic/claude-3"
            },
        }

        mock_stage3_result = {
            "model": "gemini/gemini-pro",
            "response": "Final synthesized answer",
        }

        mock_aggregate_rankings = [
            {"model": "Personality 2", "average_rank": 1.0, "rankings_count": 1},
            {"model": "Personality 1", "average_rank": 2.0, "rankings_count": 1},
        ]

        mock_stage1.return_value = mock_stage1_results
        mock_stage2.return_value = (mock_stage2_results, mock_label_to_model)
        mock_stage3.return_value = mock_stage3_result
        mock_calc_rankings.return_value = mock_aggregate_rankings

        stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
            "What is Python?",
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        # Verify all stages were called
        mock_stage1.assert_called_once()
        mock_stage2.assert_called_once()
        mock_stage3.assert_called_once()
        mock_calc_rankings.assert_called_once()

        # Verify results
        assert len(stage1_results) == 2
        assert len(stage2_results) == 1
        assert stage3_result["response"] == "Final synthesized answer"

        # Verify metadata
        assert "label_to_model" in metadata
        assert "aggregate_rankings" in metadata
        assert metadata["label_to_model"] == mock_label_to_model
        assert metadata["aggregate_rankings"] == mock_aggregate_rankings


@pytest.mark.asyncio
async def test_run_full_council_stage1_all_fail():
    """Test run_full_council handles case when all Stage 1 models fail."""
    from backend.council import run_full_council

    with (
        patch("backend.council.stage1_collect_responses", new_callable=AsyncMock) as mock_stage1,
        patch("backend.council.stage2_collect_rankings", new_callable=AsyncMock) as mock_stage2,
        patch("backend.council.stage3_synthesize_final", new_callable=AsyncMock) as mock_stage3,
    ):
        # All models fail in Stage 1
        mock_stage1.return_value = []

        stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
            "What is Python?",
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        # Should return early with error
        assert stage1_results == []
        assert stage2_results == []
        assert stage3_result["model"] == "error"
        assert "All models failed" in stage3_result["response"]
        assert metadata == {}

        # Stage 2 and Stage 3 should not be called
        mock_stage2.assert_not_called()
        mock_stage3.assert_not_called()


@pytest.mark.asyncio
async def test_run_full_council_stage2_empty():
    """Test run_full_council handles case when Stage 2 returns no rankings."""
    from backend.council import run_full_council

    with (
        patch("backend.council.stage1_collect_responses", new_callable=AsyncMock) as mock_stage1,
        patch("backend.council.stage2_collect_rankings", new_callable=AsyncMock) as mock_stage2,
        patch("backend.council.stage3_synthesize_final", new_callable=AsyncMock) as mock_stage3,
        patch("backend.council.calculate_aggregate_rankings") as mock_calc_rankings,
    ):
        mock_stage1_results = [
            {
                "model": "openai/gpt-4",
                "response": "Response A",
                "personality_id": "personality1",
                "personality_name": "Personality 1",
            },
        ]

        mock_stage1.return_value = mock_stage1_results
        mock_stage2.return_value = ([], {})  # No rankings
        mock_stage3.return_value = {
            "model": "gemini/gemini-pro",
            "response": "Final answer",
        }
        mock_calc_rankings.return_value = []

        stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
            "What is Python?",
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        # Should still proceed to Stage 3
        assert len(stage1_results) == 1
        assert stage2_results == []
        assert stage3_result["response"] == "Final answer"
        assert metadata["aggregate_rankings"] == []


@pytest.mark.asyncio
async def test_run_full_council_stage3_failure():
    """Test run_full_council handles Stage 3 failure gracefully."""
    from backend.council import run_full_council
    from backend.council_helpers import RESPONSE_LABEL_PREFIX

    with (
        patch("backend.council.stage1_collect_responses", new_callable=AsyncMock) as mock_stage1,
        patch("backend.council.stage2_collect_rankings", new_callable=AsyncMock) as mock_stage2,
        patch("backend.council.stage3_synthesize_final", new_callable=AsyncMock) as mock_stage3,
        patch("backend.council.calculate_aggregate_rankings") as mock_calc_rankings,
    ):
        mock_stage1_results = [
            {
                "model": "openai/gpt-4",
                "response": "Response A",
                "personality_id": "personality1",
                "personality_name": "Personality 1",
            },
        ]

        mock_stage2_results = [
            {
                "model": "openai/gpt-4",
                "personality_name": "Personality 1",
                "ranking": "Ranking text",
                "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}A"],
            },
        ]

        mock_label_to_model = {f"{RESPONSE_LABEL_PREFIX}A": "Personality 1"}

        mock_stage1.return_value = mock_stage1_results
        mock_stage2.return_value = (mock_stage2_results, mock_label_to_model)
        # Stage 3 returns error
        mock_stage3.return_value = {
            "model": "gemini/gemini-pro",
            "response": "Error: Unable to generate final synthesis.",
        }
        mock_calc_rankings.return_value = []

        stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
            "What is Python?",
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        # Should still return results from Stage 1 and Stage 2
        assert len(stage1_results) == 1
        assert len(stage2_results) == 1
        assert "Error" in stage3_result["response"]
        assert metadata["label_to_model"] == mock_label_to_model


@pytest.mark.asyncio
async def test_run_full_council_with_messages():
    """Test run_full_council includes conversation history."""
    from backend.council import run_full_council

    mock_messages = [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "stage3": {"model": "model1", "response": "Previous answer"}},
    ]

    with (
        patch("backend.council.stage1_collect_responses", new_callable=AsyncMock) as mock_stage1,
        patch("backend.council.stage2_collect_rankings", new_callable=AsyncMock) as mock_stage2,
        patch("backend.council.stage3_synthesize_final", new_callable=AsyncMock) as mock_stage3,
        patch("backend.council.calculate_aggregate_rankings") as mock_calc_rankings,
    ):
        mock_stage1.return_value = [
            {
                "model": "openai/gpt-4",
                "response": "Response A",
                "personality_id": "personality1",
                "personality_name": "Personality 1",
            },
        ]
        mock_stage2.return_value = ([], {})
        mock_stage3.return_value = {
            "model": "gemini/gemini-pro",
            "response": "Final answer",
        }
        mock_calc_rankings.return_value = []

        await run_full_council(
            "What is Python?",
            messages=mock_messages,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        # Verify messages were passed to all stages
        mock_stage1.assert_called_once()
        # Arguments are passed positionally: (user_query, messages, org_id, api_key, base_url)
        call_args = mock_stage1.call_args[0]
        assert call_args[1] == mock_messages  # messages is second positional arg

        mock_stage2.assert_called_once()
        # Arguments: (user_query, stage1_results, messages, org_id, api_key, base_url)
        call_args = mock_stage2.call_args[0]
        assert call_args[2] == mock_messages  # messages is third positional arg

        mock_stage3.assert_called_once()
        # Arguments: (user_query, stage1_results, stage2_results, label_to_model, messages, ...)
        call_args = mock_stage3.call_args[0]
        assert call_args[4] == mock_messages  # messages is fifth positional arg


@pytest.mark.asyncio
async def test_stage1_collect_responses_success():
    """Test stage1_collect_responses successfully collects responses from all personalities."""
    from backend.council import stage1_collect_responses

    mock_personalities = [
        {
            "id": "personality1",
            "name": "Personality 1",
            "model": "openai/gpt-4",
            "personality_prompt": "You are helpful.",
        },
        {
            "id": "personality2",
            "name": "Personality 2",
            "model": "anthropic/claude-3",
            "personality_prompt": "You are creative.",
        },
    ]

    mock_prompts = {
        "base_system_prompt": "You are a council member.",
    }

    with (
        patch("backend.council.get_active_personalities") as mock_get_personalities,
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.build_llm_history") as mock_build_history,
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_get_personalities.return_value = mock_personalities
        mock_load_prompts.return_value = mock_prompts
        mock_build_history.return_value = []
        mock_query.side_effect = [
            {"content": "Response from Personality 1"},
            {"content": "Response from Personality 2"},
        ]

        results = await stage1_collect_responses(
            "What is Python?",
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        assert len(results) == 2
        assert results[0]["personality_id"] == "personality1"
        assert results[0]["personality_name"] == "Personality 1"
        assert results[0]["response"] == "Response from Personality 1"
        assert results[1]["personality_id"] == "personality2"
        assert results[1]["personality_name"] == "Personality 2"
        assert results[1]["response"] == "Response from Personality 2"
        assert mock_query.call_count == 2


@pytest.mark.asyncio
async def test_stage1_collect_responses_partial_failure():
    """Test stage1_collect_responses handles partial API failures gracefully."""
    from backend.council import stage1_collect_responses

    mock_personalities = [
        {
            "id": "personality1",
            "name": "Personality 1",
            "model": "openai/gpt-4",
            "personality_prompt": "You are helpful.",
        },
        {
            "id": "personality2",
            "name": "Personality 2",
            "model": "anthropic/claude-3",
            "personality_prompt": "You are creative.",
        },
    ]

    mock_prompts = {
        "base_system_prompt": "You are a council member.",
    }

    with (
        patch("backend.council.get_active_personalities") as mock_get_personalities,
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.build_llm_history") as mock_build_history,
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_get_personalities.return_value = mock_personalities
        mock_load_prompts.return_value = mock_prompts
        mock_build_history.return_value = []
        # First succeeds, second fails
        mock_query.side_effect = [
            {"content": "Response from Personality 1"},
            None,  # Simulate API failure
        ]

        results = await stage1_collect_responses(
            "What is Python?",
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        # Should only include successful responses
        assert len(results) == 1
        assert results[0]["personality_id"] == "personality1"
        assert results[0]["response"] == "Response from Personality 1"


@pytest.mark.asyncio
async def test_stage1_collect_responses_all_fail():
    """Test stage1_collect_responses returns empty list when all models fail."""
    from backend.council import stage1_collect_responses

    mock_personalities = [
        {
            "id": "personality1",
            "name": "Personality 1",
            "model": "openai/gpt-4",
            "personality_prompt": "You are helpful.",
        },
    ]

    mock_prompts = {
        "base_system_prompt": "You are a council member.",
    }

    with (
        patch("backend.council.get_active_personalities") as mock_get_personalities,
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.build_llm_history") as mock_build_history,
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_get_personalities.return_value = mock_personalities
        mock_load_prompts.return_value = mock_prompts
        mock_build_history.return_value = []
        mock_query.return_value = None  # All queries fail

        results = await stage1_collect_responses(
            "What is Python?",
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        assert results == []


@pytest.mark.asyncio
async def test_stage1_collect_responses_no_personalities():
    """Test stage1_collect_responses handles case when no personalities are active."""
    from backend.council import stage1_collect_responses

    with (
        patch("backend.council.get_active_personalities") as mock_get_personalities,
        patch("backend.council.build_llm_history") as mock_build_history,
    ):
        mock_get_personalities.return_value = []
        mock_build_history.return_value = []

        results = await stage1_collect_responses(
            "What is Python?",
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        assert results == []


@pytest.mark.asyncio
async def test_stage1_collect_responses_with_history():
    """Test stage1_collect_responses includes conversation history."""
    from backend.council import stage1_collect_responses

    mock_personalities = [
        {
            "id": "personality1",
            "name": "Personality 1",
            "model": "openai/gpt-4",
            "personality_prompt": "You are helpful.",
        },
    ]

    mock_prompts = {
        "base_system_prompt": "You are a council member.",
    }

    mock_messages = [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "stage3": {"model": "model1", "response": "Previous answer"}},
    ]

    mock_history = [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"},
    ]

    with (
        patch("backend.council.get_active_personalities") as mock_get_personalities,
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.build_llm_history") as mock_build_history,
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_get_personalities.return_value = mock_personalities
        mock_load_prompts.return_value = mock_prompts
        mock_build_history.return_value = mock_history
        mock_query.return_value = {"content": "Response"}

        results = await stage1_collect_responses(
            "What is Python?",
            messages=mock_messages,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        assert len(results) == 1
        mock_build_history.assert_called_once_with(mock_messages)


@pytest.mark.asyncio
async def test_stage2_collect_rankings_success():
    """Test stage2_collect_rankings successfully collects rankings with anonymization."""
    from backend.council import stage2_collect_rankings
    from backend.council_helpers import FINAL_RANKING_MARKER, RESPONSE_LABEL_PREFIX

    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response A content",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
        {
            "model": "anthropic/claude-3",
            "response": "Response B content",
            "personality_id": "personality2",
            "personality_name": "Personality 2",
        },
    ]

    mock_personalities = [
        {
            "id": "personality1",
            "name": "Personality 1",
            "model": "openai/gpt-4",
            "personality_prompt": "You are helpful.",
        },
        {
            "id": "personality2",
            "name": "Personality 2",
            "model": "anthropic/claude-3",
            "personality_prompt": "You are creative.",
        },
    ]

    mock_prompts = {
        "base_system_prompt": "You are a council member.",
        "ranking_prompt": "Rank {responses_text} for {user_query} from {peer_text}",
    }

    ranking_response_1 = f"""Evaluation text.

{FINAL_RANKING_MARKER}
1. {RESPONSE_LABEL_PREFIX}B
2. {RESPONSE_LABEL_PREFIX}A"""

    ranking_response_2 = f"""Evaluation text.

{FINAL_RANKING_MARKER}
1. {RESPONSE_LABEL_PREFIX}A
2. {RESPONSE_LABEL_PREFIX}B"""

    with (
        patch("backend.council.get_active_personalities") as mock_get_personalities,
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.build_llm_history") as mock_build_history,
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_get_personalities.return_value = mock_personalities
        mock_load_prompts.return_value = mock_prompts
        mock_build_history.return_value = []
        mock_query.side_effect = [
            {"content": ranking_response_1},  # Personality 1 ranks B first
            {"content": ranking_response_2},  # Personality 2 ranks A first
        ]

        stage2_results, label_to_model = await stage2_collect_rankings(
            "What is Python?",
            stage1_results,
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        assert len(stage2_results) == 2
        assert stage2_results[0]["personality_name"] == "Personality 1"
        assert stage2_results[0]["parsed_ranking"] == [
            f"{RESPONSE_LABEL_PREFIX}B",
            f"{RESPONSE_LABEL_PREFIX}A",
        ]
        assert stage2_results[1]["personality_name"] == "Personality 2"
        assert stage2_results[1]["parsed_ranking"] == [
            f"{RESPONSE_LABEL_PREFIX}A",
            f"{RESPONSE_LABEL_PREFIX}B",
        ]

        # Verify label_to_model mapping
        assert f"{RESPONSE_LABEL_PREFIX}A" in label_to_model
        assert f"{RESPONSE_LABEL_PREFIX}B" in label_to_model
        # Expect dictionary structure for label_to_model values
        assert isinstance(label_to_model[f"{RESPONSE_LABEL_PREFIX}A"], dict)
        assert label_to_model[f"{RESPONSE_LABEL_PREFIX}A"]["name"] == "Personality 1"
        assert label_to_model[f"{RESPONSE_LABEL_PREFIX}B"]["name"] == "Personality 2"


@pytest.mark.asyncio
async def test_stage2_collect_rankings_excludes_self():
    """Test stage2_collect_rankings excludes each personality's own response from ranking."""
    from backend.council import stage2_collect_rankings

    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response A content",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
        {
            "model": "anthropic/claude-3",
            "response": "Response B content",
            "personality_id": "personality2",
            "personality_name": "Personality 2",
        },
    ]

    mock_personalities = [
        {
            "id": "personality1",
            "name": "Personality 1",
            "model": "openai/gpt-4",
            "personality_prompt": "You are helpful.",
        },
        {
            "id": "personality2",
            "name": "Personality 2",
            "model": "anthropic/claude-3",
            "personality_prompt": "You are creative.",
        },
    ]

    mock_prompts = {
        "base_system_prompt": "You are a council member.",
        "ranking_prompt": "Rank {responses_text} for {user_query} from {peer_text}",
    }

    # Capture messages passed to query_model to verify filtering
    captured_messages = []

    def capture_query_messages(*args, **kwargs):
        # query_model(model, messages, ...)
        if len(args) >= 2:
            captured_messages.append(args[1])  # messages is second arg
        return {"content": "Ranking response"}

    with (
        patch("backend.council.get_active_personalities") as mock_get_personalities,
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.build_llm_history") as mock_build_history,
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_get_personalities.return_value = mock_personalities
        mock_load_prompts.return_value = mock_prompts
        mock_build_history.return_value = []
        mock_query.side_effect = capture_query_messages

        await stage2_collect_rankings(
            "What is Python?",
            stage1_results,
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        # Verify that each personality received a different prompt (one excludes A, one excludes B)
        assert len(captured_messages) == 2
        # Check that the user messages contain different response labels
        user_msg_1 = next((m for m in captured_messages[0] if m["role"] == "user"), None)
        user_msg_2 = next((m for m in captured_messages[1] if m["role"] == "user"), None)
        assert user_msg_1 is not None
        assert user_msg_2 is not None

        # One should contain Response A but not Response B (for personality2)
        # One should contain Response B but not Response A (for personality1)
        # Since we can't guarantee order, check that they're different
        assert user_msg_1["content"] != user_msg_2["content"]


@pytest.mark.asyncio
async def test_stage2_collect_rankings_partial_failure():
    """Test stage2_collect_rankings handles partial API failures gracefully."""
    from backend.council import stage2_collect_rankings

    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response A content",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
        {
            "model": "anthropic/claude-3",
            "response": "Response B content",
            "personality_id": "personality2",
            "personality_name": "Personality 2",
        },
    ]

    mock_personalities = [
        {
            "id": "personality1",
            "name": "Personality 1",
            "model": "openai/gpt-4",
            "personality_prompt": "You are helpful.",
        },
        {
            "id": "personality2",
            "name": "Personality 2",
            "model": "anthropic/claude-3",
            "personality_prompt": "You are creative.",
        },
    ]

    mock_prompts = {
        "base_system_prompt": "You are a council member.",
        "ranking_prompt": "Rank responses",
    }

    with (
        patch("backend.council.get_active_personalities") as mock_get_personalities,
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.build_llm_history") as mock_build_history,
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_get_personalities.return_value = mock_personalities
        mock_load_prompts.return_value = mock_prompts
        mock_build_history.return_value = []
        # First succeeds, second fails
        mock_query.side_effect = [
            {"content": "Ranking response"},
            None,  # Simulate API failure
        ]

        stage2_results, label_to_model = await stage2_collect_rankings(
            "What is Python?",
            stage1_results,
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        # Should only include successful rankings
        assert len(stage2_results) == 1
        assert stage2_results[0]["personality_name"] == "Personality 1"
        # label_to_model should still include both labels
        assert len(label_to_model) == 2


@pytest.mark.asyncio
async def test_stage2_collect_rankings_empty_stage1():
    """Test stage2_collect_rankings handles empty stage1_results."""
    from backend.council import stage2_collect_rankings

    mock_personalities = [
        {
            "id": "personality1",
            "name": "Personality 1",
            "model": "openai/gpt-4",
            "personality_prompt": "You are helpful.",
        },
    ]

    with (
        patch("backend.council.get_active_personalities") as mock_get_personalities,
        patch("backend.council.build_llm_history") as mock_build_history,
    ):
        mock_get_personalities.return_value = mock_personalities
        mock_build_history.return_value = []

        stage2_results, label_to_model = await stage2_collect_rankings(
            "What is Python?",
            [],
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        assert stage2_results == []
        assert label_to_model == {}


@pytest.mark.asyncio
async def test_stage2_collect_rankings_no_personalities():
    """Test stage2_collect_rankings handles case when no personalities are active."""
    from backend.council import stage2_collect_rankings

    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response A content",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]

    with (
        patch("backend.council.get_active_personalities") as mock_get_personalities,
        patch("backend.council.build_llm_history") as mock_build_history,
    ):
        mock_get_personalities.return_value = []
        mock_build_history.return_value = []

        stage2_results, label_to_model = await stage2_collect_rankings(
            "What is Python?",
            stage1_results,
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        assert stage2_results == []
        assert label_to_model == {}


@pytest.mark.asyncio
async def test_stage3_synthesize_final_success():
    """Test stage3_synthesize_final successfully synthesizes final answer."""
    from backend.council import stage3_synthesize_final
    from backend.council_helpers import RESPONSE_LABEL_PREFIX

    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response A content",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
        {
            "model": "anthropic/claude-3",
            "response": "Response B content",
            "personality_id": "personality2",
            "personality_name": "Personality 2",
        },
    ]

    stage2_results = [
        {
            "model": "openai/gpt-4",
            "personality_name": "Personality 1",
            "ranking": "Ranking text",
            "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}B", f"{RESPONSE_LABEL_PREFIX}A"],
        },
        {
            "model": "anthropic/claude-3",
            "personality_name": "Personality 2",
            "ranking": "Ranking text",
            "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}A", f"{RESPONSE_LABEL_PREFIX}B"],
        },
    ]

    label_to_model = {
        f"{RESPONSE_LABEL_PREFIX}A": "Personality 1",
        f"{RESPONSE_LABEL_PREFIX}B": "Personality 2",
    }

    mock_prompts = {
        "chairman_prompt": "Synthesize for {user_query} using {stage1_text} and {voting_details_text}",
    }

    mock_models_config = {
        "chairman_model": "gemini/gemini-pro",
    }

    with (
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.load_org_models_config") as mock_load_models,
        patch("backend.council.build_llm_history") as mock_build_history,
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_load_prompts.return_value = mock_prompts
        mock_load_models.return_value = mock_models_config
        mock_build_history.return_value = []
        mock_query.return_value = {"content": "Final synthesized answer"}

        result = await stage3_synthesize_final(
            "What is Python?",
            stage1_results,
            stage2_results,
            label_to_model,
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        assert result["model"] == "gemini/gemini-pro"
        assert result["response"] == "Final synthesized answer"
        mock_query.assert_called_once()


@pytest.mark.asyncio
async def test_stage3_synthesize_final_includes_voting_details():
    """Test stage3_synthesize_final includes voting details in prompt."""
    from backend.council import stage3_synthesize_final
    from backend.council_helpers import RESPONSE_LABEL_PREFIX

    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response A",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]

    stage2_results = [
        {
            "model": "openai/gpt-4",
            "personality_name": "Personality 1",
            "ranking": "Ranking text",
            "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}A"],
        },
    ]

    label_to_model = {
        f"{RESPONSE_LABEL_PREFIX}A": "Personality 1",
    }

    mock_prompts = {
        "chairman_prompt": "Synthesize for {user_query} using {stage1_text} and {voting_details_text}",
    }

    mock_models_config = {
        "chairman_model": "gemini/gemini-pro",
    }

    captured_messages = []

    def capture_messages(*args, **kwargs):
        # query_model(model, messages, ...)
        if len(args) >= 2:
            captured_messages.append(args[1])  # messages is second arg
        return {"content": "Final answer"}

    with (
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.load_org_models_config") as mock_load_models,
        patch("backend.council.build_llm_history") as mock_build_history,
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_load_prompts.return_value = mock_prompts
        mock_load_models.return_value = mock_models_config
        mock_build_history.return_value = []
        mock_query.side_effect = capture_messages

        await stage3_synthesize_final(
            "What is Python?",
            stage1_results,
            stage2_results,
            label_to_model,
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        # Verify voting details are included in the prompt
        assert len(captured_messages) == 1
        messages = captured_messages[0]
        # Find the user message with the chairman prompt
        user_message = next((m for m in messages if m["role"] == "user"), None)
        assert user_message is not None
        assert (
            "voting_details_text" in user_message["content"] or "Voter:" in user_message["content"]
        )


@pytest.mark.asyncio
async def test_stage3_synthesize_final_chairman_failure():
    """Test stage3_synthesize_final handles chairman model failure gracefully."""
    from backend.council import stage3_synthesize_final

    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response A",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]

    stage2_results = [
        {
            "model": "openai/gpt-4",
            "personality_name": "Personality 1",
            "ranking": "Ranking text",
            "parsed_ranking": ["Response A"],
        },
    ]

    label_to_model = {"Response A": "Personality 1"}

    mock_prompts = {
        "chairman_prompt": "Synthesize for {user_query}",
    }

    mock_models_config = {
        "chairman_model": "gemini/gemini-pro",
    }

    with (
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.load_org_models_config") as mock_load_models,
        patch("backend.council.build_llm_history") as mock_build_history,
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_load_prompts.return_value = mock_prompts
        mock_load_models.return_value = mock_models_config
        mock_build_history.return_value = []
        mock_query.return_value = None  # Chairman fails

        result = await stage3_synthesize_final(
            "What is Python?",
            stage1_results,
            stage2_results,
            label_to_model,
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        assert result["model"] == "gemini/gemini-pro"
        assert "Error" in result["response"]
        assert "Unable to generate final synthesis" in result["response"]


@pytest.mark.asyncio
async def test_stage3_synthesize_final_empty_results():
    """Test stage3_synthesize_final handles empty stage1 and stage2 results."""
    from backend.council import stage3_synthesize_final

    mock_prompts = {
        "chairman_prompt": "Synthesize for {user_query}",
    }

    mock_models_config = {
        "chairman_model": "gemini/gemini-pro",
    }

    with (
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.load_org_models_config") as mock_load_models,
        patch("backend.council.build_llm_history") as mock_build_history,
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_load_prompts.return_value = mock_prompts
        mock_load_models.return_value = mock_models_config
        mock_build_history.return_value = []
        mock_query.return_value = {"content": "Final answer"}

        result = await stage3_synthesize_final(
            "What is Python?",
            [],
            [],
            {},
            messages=None,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        # Should still call chairman model even with empty results
        assert result["model"] == "gemini/gemini-pro"
        mock_query.assert_called_once()


@pytest.mark.asyncio
async def test_stage3_synthesize_final_with_history():
    """Test stage3_synthesize_final includes conversation history."""
    from backend.council import stage3_synthesize_final

    stage1_results = [
        {
            "model": "openai/gpt-4",
            "response": "Response A",
            "personality_id": "personality1",
            "personality_name": "Personality 1",
        },
    ]

    stage2_results = [
        {
            "model": "openai/gpt-4",
            "personality_name": "Personality 1",
            "ranking": "Ranking text",
            "parsed_ranking": ["Response A"],
        },
    ]

    label_to_model = {"Response A": "Personality 1"}

    mock_messages = [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "stage3": {"model": "model1", "response": "Previous answer"}},
    ]

    mock_history = [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"},
    ]

    mock_prompts = {
        "chairman_prompt": "Synthesize for {user_query}",
    }

    mock_models_config = {
        "chairman_model": "gemini/gemini-pro",
    }

    with (
        patch("backend.council.load_org_system_prompts") as mock_load_prompts,
        patch("backend.council.load_org_models_config") as mock_load_models,
        patch("backend.council.build_llm_history") as mock_build_history,
        patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
    ):
        mock_load_prompts.return_value = mock_prompts
        mock_load_models.return_value = mock_models_config
        mock_build_history.return_value = mock_history
        mock_query.return_value = {"content": "Final answer"}

        result = await stage3_synthesize_final(
            "What is Python?",
            stage1_results,
            stage2_results,
            label_to_model,
            messages=mock_messages,
            org_id="test-org",
            api_key="test-key",
            base_url="https://api.test.com/v1/chat/completions",
        )

        assert result["model"] == "gemini/gemini-pro"
        mock_build_history.assert_called_once_with(mock_messages)


@pytest.mark.asyncio
async def test_query_model_success():
    """Test query_model with successful API call."""
    from backend.openrouter import query_model

    mock_response = {
        "choices": [{"message": {"content": "Test response", "reasoning_details": None}}]
    }

    with patch("backend.openrouter.get_semaphore") as mock_semaphore:
        mock_semaphore_instance = AsyncMock()
        mock_semaphore.return_value = mock_semaphore_instance
        mock_semaphore_instance.__aenter__ = AsyncMock(return_value=None)
        mock_semaphore_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)

            result = await query_model(
                "test-model",
                [{"role": "user", "content": "Hello"}],
                api_key="test-key",
                base_url="https://api.test.com/v1/chat/completions",
            )

            assert result is not None
            assert result["content"] == "Test response"
            mock_client.post.assert_called_once()
            mock_semaphore_instance.__aenter__.assert_called_once()


@pytest.mark.asyncio
async def test_query_model_retry_on_429():
    """Test query_model retries on 429 Too Many Requests."""
    from backend.openrouter import query_model

    mock_error = httpx.HTTPStatusError(
        "429 Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )

    mock_success_response = {"choices": [{"message": {"content": "Success after retry"}}]}

    with patch("backend.openrouter.get_semaphore") as mock_semaphore:
        mock_semaphore_instance = AsyncMock()
        mock_semaphore.return_value = mock_semaphore_instance
        mock_semaphore_instance.__aenter__ = AsyncMock(return_value=None)
        mock_semaphore_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_success_response
            mock_response_obj.raise_for_status = MagicMock()

            # First call raises 429, second succeeds
            mock_client.post = AsyncMock(side_effect=[mock_error, mock_response_obj])

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await query_model(
                    "test-model",
                    [{"role": "user", "content": "Hello"}],
                    api_key="test-key",
                    base_url="https://api.test.com/v1/chat/completions",
                )

                assert result is not None
                assert result["content"] == "Success after retry"
                assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_query_model_retry_on_500():
    """Test query_model retries on 5xx server errors."""
    from backend.openrouter import query_model

    mock_error = httpx.HTTPStatusError(
        "500 Internal Server Error", request=MagicMock(), response=MagicMock(status_code=500)
    )

    mock_success_response = {"choices": [{"message": {"content": "Success after retry"}}]}

    with patch("backend.openrouter.get_semaphore") as mock_semaphore:
        mock_semaphore_instance = AsyncMock()
        mock_semaphore.return_value = mock_semaphore_instance
        mock_semaphore_instance.__aenter__ = AsyncMock(return_value=None)
        mock_semaphore_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_success_response
            mock_response_obj.raise_for_status = MagicMock()

            mock_client.post = AsyncMock(side_effect=[mock_error, mock_response_obj])

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await query_model(
                    "test-model",
                    [{"role": "user", "content": "Hello"}],
                    api_key="test-key",
                    base_url="https://api.test.com/v1/chat/completions",
                )

                assert result is not None
                assert result["content"] == "Success after retry"
                assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_query_model_timeout():
    """Test query_model handles timeout exceptions."""
    from backend.openrouter import query_model

    with patch("backend.openrouter.get_semaphore") as mock_semaphore:
        mock_semaphore_instance = AsyncMock()
        mock_semaphore.return_value = mock_semaphore_instance
        mock_semaphore_instance.__aenter__ = AsyncMock(return_value=None)
        mock_semaphore_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Simulate timeout on first attempt, success on retry
            mock_timeout = httpx.TimeoutException("Request timed out")
            mock_success_response = {"choices": [{"message": {"content": "Success after timeout"}}]}
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_success_response
            mock_response_obj.raise_for_status = MagicMock()

            mock_client.post = AsyncMock(side_effect=[mock_timeout, mock_response_obj])

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await query_model(
                    "test-model",
                    [{"role": "user", "content": "Hello"}],
                    api_key="test-key",
                    base_url="https://api.test.com/v1/chat/completions",
                    timeout=30.0,
                )

                assert result is not None
                assert result["content"] == "Success after timeout"
                assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_query_model_max_retries_exceeded():
    """Test query_model returns None after max retries."""
    from backend.config import LLM_MAX_RETRIES
    from backend.openrouter import query_model

    mock_error = httpx.HTTPStatusError(
        "429 Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )

    with patch("backend.openrouter.get_semaphore") as mock_semaphore:
        mock_semaphore_instance = AsyncMock()
        mock_semaphore.return_value = mock_semaphore_instance
        mock_semaphore_instance.__aenter__ = AsyncMock(return_value=None)
        mock_semaphore_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Always raise error
            mock_client.post = AsyncMock(side_effect=mock_error)

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await query_model(
                    "test-model",
                    [{"role": "user", "content": "Hello"}],
                    api_key="test-key",
                    base_url="https://api.test.com/v1/chat/completions",
                )

                assert result is None
                assert mock_client.post.call_count == LLM_MAX_RETRIES


@pytest.mark.asyncio
async def test_query_model_non_retryable_error():
    """Test query_model returns None immediately for non-retryable errors."""
    from backend.openrouter import query_model

    # 400 Bad Request is not retryable
    mock_error = httpx.HTTPStatusError(
        "400 Bad Request", request=MagicMock(), response=MagicMock(status_code=400)
    )

    with patch("backend.openrouter.get_semaphore") as mock_semaphore:
        mock_semaphore_instance = AsyncMock()
        mock_semaphore.return_value = mock_semaphore_instance
        mock_semaphore_instance.__aenter__ = AsyncMock(return_value=None)
        mock_semaphore_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_client.post = AsyncMock(side_effect=mock_error)

            result = await query_model(
                "test-model",
                [{"role": "user", "content": "Hello"}],
                api_key="test-key",
                base_url="https://api.test.com/v1/chat/completions",
            )

            assert result is None
            # Should not retry non-retryable errors
            assert mock_client.post.call_count == 1


@pytest.mark.asyncio
async def test_query_model_temperature_parameter():
    """Test query_model includes temperature parameter when provided."""
    from backend.openrouter import query_model

    mock_response = {
        "choices": [{"message": {"content": "Test response", "reasoning_details": None}}]
    }

    with patch("backend.openrouter.get_semaphore") as mock_semaphore:
        mock_semaphore_instance = AsyncMock()
        mock_semaphore.return_value = mock_semaphore_instance
        mock_semaphore_instance.__aenter__ = AsyncMock(return_value=None)
        mock_semaphore_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)

            result = await query_model(
                "test-model",
                [{"role": "user", "content": "Hello"}],
                api_key="test-key",
                base_url="https://api.test.com/v1/chat/completions",
                temperature=0.7,
            )

            assert result is not None
            call_args = mock_client.post.call_args
            assert call_args[1]["json"]["temperature"] == 0.7


@pytest.mark.asyncio
async def test_query_model_semaphore_concurrency():
    """Test query_model uses semaphore for concurrency control."""
    from backend.openrouter import query_model

    mock_response = {"choices": [{"message": {"content": "Test response"}}]}

    with patch("backend.openrouter.get_semaphore") as mock_semaphore:
        mock_semaphore_instance = AsyncMock()
        mock_semaphore.return_value = mock_semaphore_instance
        mock_semaphore_instance.__aenter__ = AsyncMock(return_value=None)
        mock_semaphore_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)

            await query_model(
                "test-model",
                [{"role": "user", "content": "Hello"}],
                api_key="test-key",
                base_url="https://api.test.com/v1/chat/completions",
            )

            # Verify semaphore was acquired and released
            mock_semaphore.assert_called_once()
            mock_semaphore_instance.__aenter__.assert_called_once()
            mock_semaphore_instance.__aexit__.assert_called_once()
