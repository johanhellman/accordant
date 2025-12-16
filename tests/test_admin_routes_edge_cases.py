"""Edge case tests for admin_routes.py to improve coverage.

These tests cover error paths, edge cases, and boundary conditions
that may not be covered by existing integration tests.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
import yaml
from fastapi import HTTPException

from backend.admin_routes import (
    _load_yaml,
    _save_yaml,
    delete_personality,
    get_org_settings,
    get_system_prompts,
    get_voting_history,
    update_org_settings,
)
from backend.users import User


class TestLoadYaml:
    """Tests for _load_yaml helper function."""

    def test_load_yaml_file_not_exists(self, tmp_path):
        """Test _load_yaml returns None when file doesn't exist."""
        file_path = tmp_path / "nonexistent.yaml"
        result = _load_yaml(str(file_path))
        assert result is None

    def test_load_yaml_valid_file(self, tmp_path):
        """Test _load_yaml loads valid YAML file."""
        file_path = tmp_path / "test.yaml"
        test_data = {"key": "value", "number": 42}
        with open(file_path, "w") as f:
            yaml.dump(test_data, f)

        result = _load_yaml(str(file_path))
        assert result == test_data

    def test_load_yaml_invalid_yaml(self, tmp_path):
        """Test _load_yaml returns None on invalid YAML."""
        file_path = tmp_path / "invalid.yaml"
        with open(file_path, "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        result = _load_yaml(str(file_path))
        assert result is None

    def test_load_yaml_empty_file(self, tmp_path):
        """Test _load_yaml handles empty file."""
        file_path = tmp_path / "empty.yaml"
        file_path.touch()

        result = _load_yaml(str(file_path))
        assert result is None or result == {}


class TestSaveYaml:
    """Tests for _save_yaml helper function."""

    def test_save_yaml_success(self, tmp_path):
        """Test _save_yaml successfully saves data."""
        file_path = tmp_path / "test.yaml"
        test_data = {"key": "value", "nested": {"inner": "data"}}

        _save_yaml(str(file_path), test_data)

        assert file_path.exists()
        with open(file_path) as f:
            loaded = yaml.safe_load(f)
            assert loaded == test_data

    def test_save_yaml_permission_error(self, tmp_path):
        """Test _save_yaml raises HTTPException on permission error."""
        # Create a directory path instead of file path to simulate permission error
        dir_path = tmp_path / "readonly_dir"
        dir_path.mkdir()
        file_path = dir_path / "test.yaml"

        # Make directory read-only (Unix only)
        if os.name != "nt":
            os.chmod(dir_path, 0o444)
            try:
                with pytest.raises(HTTPException) as exc_info:
                    _save_yaml(str(file_path), {"key": "value"})
                assert exc_info.value.status_code == 500
                assert "Failed to save configuration" in exc_info.value.detail
            finally:
                os.chmod(dir_path, 0o755)


class TestGetSystemPrompts:
    """Edge case tests for get_system_prompts."""

    @pytest.mark.asyncio
    async def test_get_system_prompts_backwards_compat(self, tmp_path):
        """Test get_system_prompts handles legacy ranking_prompt format."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create legacy format file
        legacy_config = {
            "ranking_prompt": "Legacy ranking prompt {user_query} {responses_text} {peer_text}",
            "base_system_prompt": "Base prompt",
        }
        system_prompts_file = config_dir / "system-prompts.yaml"
        with open(system_prompts_file, "w") as f:
            yaml.dump(legacy_config, f)

        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id=org_id
        )

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

            result = await get_system_prompts(current_user=mock_user)

            assert result["ranking"]["prompt"]["value"] == legacy_config["ranking_prompt"]
            assert result["ranking"]["model"] == "gemini/gemini-pro"

    @pytest.mark.asyncio
    async def test_get_system_prompts_partial_config(self, tmp_path):
        """Test get_system_prompts handles partial config with missing fields."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Partial config missing some fields
        partial_config = {
            "base_system_prompt": "Custom base prompt",
            # Missing ranking, chairman, title_generation
        }
        system_prompts_file = config_dir / "system-prompts.yaml"
        with open(system_prompts_file, "w") as f:
            yaml.dump(partial_config, f)

        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id=org_id
        )

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

            result = await get_system_prompts(current_user=mock_user)

            assert result["base_system_prompt"]["value"] == "Custom base prompt"
            # Should use defaults for missing fields
            assert "prompt" in result["ranking"]
            assert "prompt" in result["chairman"]
            assert "prompt" in result["title_generation"]

    @pytest.mark.asyncio
    async def test_get_system_prompts_invalid_yaml(self, tmp_path):
        """Test get_system_prompts handles invalid YAML gracefully."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create invalid YAML file
        system_prompts_file = config_dir / "system-prompts.yaml"
        with open(system_prompts_file, "w") as f:
            f.write("invalid: yaml: [unclosed")

        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id=org_id
        )

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

            # Should return defaults when YAML is invalid
            result = await get_system_prompts(current_user=mock_user)
            assert result is not None
            assert "base_system_prompt" in result


class TestGetOrgSettings:
    """Edge case tests for get_org_settings."""

    @pytest.mark.asyncio
    async def test_get_org_settings_org_not_found(self):
        """Test get_org_settings raises 404 when org not found."""
        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id="nonexistent"
        )

        with patch("backend.admin_routes.get_org", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_org_settings(current_user=mock_user)

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_org_settings_no_api_config(self):
        """Test get_org_settings handles missing api_config."""
        org_id = "test-org"
        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id=org_id
        )

        mock_org = MagicMock()
        mock_org.id = org_id
        mock_org.api_config = None  # No api_config

        with patch("backend.admin_routes.get_org", return_value=mock_org):
            result = await get_org_settings(current_user=mock_user)

            assert result["api_key"] is None
            assert "base_url" in result

    @pytest.mark.asyncio
    async def test_get_org_settings_empty_api_config(self):
        """Test get_org_settings handles empty api_config."""
        org_id = "test-org"
        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id=org_id
        )

        mock_org = MagicMock()
        mock_org.id = org_id
        mock_org.api_config = {}  # Empty api_config

        with patch("backend.admin_routes.get_org", return_value=mock_org):
            result = await get_org_settings(current_user=mock_user)

            assert result["api_key"] is None
            assert "base_url" in result


class TestUpdateOrgSettings:
    """Edge case tests for update_org_settings."""

    @pytest.mark.asyncio
    async def test_update_org_settings_org_not_found(self):
        """Test update_org_settings raises 404 when org not found."""
        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id="nonexistent"
        )

        from backend.admin_routes import OrgSettingsUpdate

        settings = OrgSettingsUpdate(api_key="new_key", base_url="https://new.url")

        with patch("backend.admin_routes.get_org", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await update_org_settings(settings, current_user=mock_user)

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_update_org_settings_update_failure(self):
        """Test update_org_settings raises 500 when update fails."""
        org_id = "test-org"
        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id=org_id
        )

        from backend.admin_routes import OrgSettingsUpdate

        settings = OrgSettingsUpdate(api_key="new_key")

        mock_org = MagicMock()
        mock_org.id = org_id
        mock_org.api_config = {}

        with (
            patch("backend.admin_routes.get_org", return_value=mock_org),
            patch("backend.admin_routes.update_org", return_value=None),  # Update fails
            patch("backend.admin_routes.encrypt_value", return_value="encrypted"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await update_org_settings(settings, current_user=mock_user)

            assert exc_info.value.status_code == 500
            assert "Failed to update" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_org_settings_only_api_key(self):
        """Test update_org_settings updates only api_key when base_url not provided."""
        org_id = "test-org"
        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id=org_id
        )

        from backend.admin_routes import OrgSettingsUpdate

        settings = OrgSettingsUpdate(api_key="new_key", base_url=None)

        mock_org = MagicMock()
        mock_org.id = org_id
        mock_org.api_config = {"base_url": "https://existing.url"}

        updated_org = MagicMock()
        updated_org.id = org_id

        with (
            patch("backend.admin_routes.get_org", return_value=mock_org),
            patch("backend.admin_routes.update_org", return_value=updated_org),
            patch("backend.admin_routes.encrypt_value", return_value="encrypted_new"),
        ):
            result = await update_org_settings(settings, current_user=mock_user)

            assert result["status"] == "success"
            # Verify base_url was preserved
            assert mock_org.api_config["base_url"] == "https://existing.url"

    @pytest.mark.asyncio
    async def test_update_org_settings_only_base_url(self):
        """Test update_org_settings updates only base_url when api_key not provided."""
        org_id = "test-org"
        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id=org_id
        )

        from backend.admin_routes import OrgSettingsUpdate

        settings = OrgSettingsUpdate(api_key=None, base_url="https://new.url")

        mock_org = MagicMock()
        mock_org.id = org_id
        mock_org.api_config = {"api_key": "existing_encrypted_key"}

        updated_org = MagicMock()
        updated_org.id = org_id

        with (
            patch("backend.admin_routes.get_org", return_value=mock_org),
            patch("backend.admin_routes.update_org", return_value=updated_org),
        ):
            result = await update_org_settings(settings, current_user=mock_user)

            assert result["status"] == "success"
            # Verify api_key was preserved
            assert mock_org.api_config["api_key"] == "existing_encrypted_key"
            assert mock_org.api_config["base_url"] == "https://new.url"


class TestGetVotingHistory:
    """Edge case tests for get_voting_history."""

    @pytest.mark.asyncio
    async def test_get_voting_history_no_user_id(self):
        """Test get_voting_history handles sessions without user_id."""
        org_id = "test-org"
        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id=org_id
        )

        history_data = [
            {"vote": "A", "session_id": "s1"},  # No user_id
            {"user_id": "u1", "vote": "B", "session_id": "s2"},
        ]

        with (
            patch("backend.voting_history.load_voting_history", return_value=history_data),
            patch("backend.users.get_all_users", return_value=[]),
        ):
            result = await get_voting_history(current_user=mock_user)

            assert len(result) == 2
            assert result[0]["username"] == "Anonymous/Legacy"
            assert result[1]["username"] == "Unknown User"

    @pytest.mark.asyncio
    async def test_get_voting_history_no_users(self):
        """Test get_voting_history handles case when no users exist."""
        org_id = "test-org"
        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id=org_id
        )

        history_data = [{"user_id": "u1", "vote": "A", "session_id": "s1"}]

        with (
            patch("backend.voting_history.load_voting_history", return_value=history_data),
            patch("backend.users.get_all_users", return_value=[]),  # No users
        ):
            result = await get_voting_history(current_user=mock_user)

            assert len(result) == 1
            assert result[0]["username"] == "Unknown User"

    @pytest.mark.asyncio
    async def test_get_voting_history_empty_history(self):
        """Test get_voting_history handles empty voting history."""
        org_id = "test-org"
        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id=org_id
        )

        with (
            patch("backend.voting_history.load_voting_history", return_value=[]),
            patch("backend.users.get_all_users", return_value=[]),
        ):
            result = await get_voting_history(current_user=mock_user)

            assert result == []


class TestDeletePersonality:
    """Edge case tests for delete_personality."""

    @pytest.mark.asyncio
    async def test_delete_personality_file_removal_error(self, tmp_path):
        """Test delete_personality handles file removal errors."""
        org_id = "test-org"
        personalities_dir = tmp_path / "organizations" / org_id / "personalities"
        personalities_dir.mkdir(parents=True, exist_ok=True)

        personality_file = personalities_dir / "to_delete.yaml"
        personality_file.touch()

        mock_user = User(
            id="1", username="admin", password_hash="hash", is_admin=True, org_id=org_id
        )

        with (
            patch("backend.admin_routes.get_org_personalities_dir") as mock_get_dir,
            patch("os.remove") as mock_remove,
        ):
            mock_get_dir.return_value = str(personalities_dir)
            mock_remove.side_effect = OSError("Permission denied")

            with pytest.raises(HTTPException) as exc_info:
                await delete_personality("to_delete", current_user=mock_user)

            assert exc_info.value.status_code == 500
            assert "Failed to delete" in exc_info.value.detail


class TestGenerateConversationTitle:
    """Edge case tests for generate_conversation_title."""

    @pytest.mark.asyncio
    async def test_generate_conversation_title_empty_content(self):
        """Test generate_conversation_title handles empty content."""
        from backend.council import generate_conversation_title

        org_id = "test-org"
        user_query = "Test query"

        with (
            patch("backend.council.load_org_system_prompts") as mock_load_prompts,
            patch("backend.council.load_org_models_config") as mock_load_models,
            patch("backend.council.query_model") as mock_query_model,
        ):
            mock_load_prompts.return_value = {"title_prompt": "Title: {user_query}"}
            mock_load_models.return_value = {"title_model": "gemini/gemini-pro"}
            mock_query_model.return_value = {"content": ""}  # Empty content

            title = await generate_conversation_title(
                user_query, org_id, "fake-key", "https://fake.url"
            )

            assert title == "New Conversation"

    @pytest.mark.asyncio
    async def test_generate_conversation_title_whitespace_only(self):
        """Test generate_conversation_title handles whitespace-only content."""
        from backend.council import generate_conversation_title

        org_id = "test-org"
        user_query = "Test query"

        with (
            patch("backend.council.load_org_system_prompts") as mock_load_prompts,
            patch("backend.council.load_org_models_config") as mock_load_models,
            patch("backend.council.query_model") as mock_query_model,
        ):
            mock_load_prompts.return_value = {"title_prompt": "Title: {user_query}"}
            mock_load_models.return_value = {"title_model": "gemini/gemini-pro"}
            mock_query_model.return_value = {"content": "   \n\t  "}  # Whitespace only

            title = await generate_conversation_title(
                user_query, org_id, "fake-key", "https://fake.url"
            )

            assert title == "New Conversation"

    @pytest.mark.asyncio
    async def test_generate_conversation_title_with_quotes(self):
        """Test generate_conversation_title removes quotes from title."""
        from backend.council import generate_conversation_title

        org_id = "test-org"
        user_query = "Test query"

        with (
            patch("backend.council.load_org_system_prompts") as mock_load_prompts,
            patch("backend.council.load_org_models_config") as mock_load_models,
            patch("backend.council.query_model") as mock_query_model,
        ):
            mock_load_prompts.return_value = {"title_prompt": "Title: {user_query}"}
            mock_load_models.return_value = {"title_model": "gemini/gemini-pro"}
            mock_query_model.return_value = {"content": '"Quoted Title"'}

            title = await generate_conversation_title(
                user_query, org_id, "fake-key", "https://fake.url"
            )

            assert title == "Quoted Title"
            assert not title.startswith('"')
            assert not title.endswith('"')

    @pytest.mark.asyncio
    async def test_generate_conversation_title_exactly_50_chars(self):
        """Test generate_conversation_title handles exactly 50 character title."""
        from backend.council import generate_conversation_title

        org_id = "test-org"
        user_query = "Test query"
        exact_50_chars = "A" * 50

        with (
            patch("backend.council.load_org_system_prompts") as mock_load_prompts,
            patch("backend.council.load_org_models_config") as mock_load_models,
            patch("backend.council.query_model") as mock_query_model,
        ):
            mock_load_prompts.return_value = {"title_prompt": "Title: {user_query}"}
            mock_load_models.return_value = {"title_model": "gemini/gemini-pro"}
            mock_query_model.return_value = {"content": exact_50_chars}

            title = await generate_conversation_title(
                user_query, org_id, "fake-key", "https://fake.url"
            )

            assert len(title) == 50
            assert not title.endswith("...")

    @pytest.mark.asyncio
    async def test_generate_conversation_title_exactly_51_chars(self):
        """Test generate_conversation_title truncates 51 character title."""
        from backend.council import generate_conversation_title

        org_id = "test-org"
        user_query = "Test query"
        exact_51_chars = "A" * 51

        with (
            patch("backend.council.load_org_system_prompts") as mock_load_prompts,
            patch("backend.council.load_org_models_config") as mock_load_models,
            patch("backend.council.query_model") as mock_query_model,
        ):
            mock_load_prompts.return_value = {"title_prompt": "Title: {user_query}"}
            mock_load_models.return_value = {"title_model": "gemini/gemini-pro"}
            mock_query_model.return_value = {"content": exact_51_chars}

            title = await generate_conversation_title(
                user_query, org_id, "fake-key", "https://fake.url"
            )

            assert len(title) == 50
            assert title.endswith("...")

    @pytest.mark.asyncio
    async def test_generate_conversation_title_missing_content_key(self):
        """Test generate_conversation_title handles response without content key."""
        from backend.council import generate_conversation_title

        org_id = "test-org"
        user_query = "Test query"

        with (
            patch("backend.council.load_org_system_prompts") as mock_load_prompts,
            patch("backend.council.load_org_models_config") as mock_load_models,
            patch("backend.council.query_model") as mock_query_model,
        ):
            mock_load_prompts.return_value = {"title_prompt": "Title: {user_query}"}
            mock_load_models.return_value = {"title_model": "gemini/gemini-pro"}
            mock_query_model.return_value = {}  # No content key

            title = await generate_conversation_title(
                user_query, org_id, "fake-key", "https://fake.url"
            )

            assert title == "New Conversation"


class TestGetAvailableModels:
    """Edge case tests for get_available_models."""

    @pytest.mark.asyncio
    async def test_get_available_models_missing_model_id(self, mock_httpx_client):
        """Test get_available_models skips models without id."""
        from backend.llm_service import get_available_models

        with patch("backend.llm_service._MODELS_CACHE", {}):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [
                    {"id": "valid-model", "name": "Valid Model"},
                    {"name": "No ID Model"},  # Missing id
                    {"id": "another-valid", "name": "Another Valid"},
                ]
            }
            mock_httpx_client.get.return_value = mock_response

            models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

            assert len(models) == 2
            assert models[0]["id"] == "valid-model"
            assert models[1]["id"] == "another-valid"

    @pytest.mark.asyncio
    async def test_get_available_models_empty_data(self, mock_httpx_client):
        """Test get_available_models handles empty data array."""
        from backend.llm_service import get_available_models

        with patch("backend.llm_service._MODELS_CACHE", {}):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_httpx_client.get.return_value = mock_response

            models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

            assert models == []

    @pytest.mark.asyncio
    async def test_get_available_models_missing_data_key(self, mock_httpx_client):
        """Test get_available_models handles response without data key."""
        from backend.llm_service import get_available_models

        with patch("backend.llm_service._MODELS_CACHE", {}):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}  # No data key
            mock_httpx_client.get.return_value = mock_response

            models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

            assert models == []

    @pytest.mark.asyncio
    async def test_get_available_models_malformed_response(self, mock_httpx_client):
        """Test get_available_models handles malformed JSON response."""
        from backend.llm_service import get_available_models

        with patch("backend.llm_service._MODELS_CACHE", {}):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_httpx_client.get.return_value = mock_response

            models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

            assert models == []

    @pytest.mark.asyncio
    async def test_get_available_models_network_error(self, mock_httpx_client):
        """Test get_available_models handles network errors."""
        from backend.llm_service import get_available_models

        with patch("backend.llm_service._MODELS_CACHE", {}):
            mock_httpx_client.get.side_effect = Exception("Network error")

            models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

            assert models == []

    @pytest.mark.asyncio
    async def test_get_available_models_model_without_name(self, mock_httpx_client):
        """Test get_available_models uses model id as name when name missing."""
        from backend.llm_service import get_available_models

        with patch("backend.llm_service._MODELS_CACHE", {}):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"id": "model-without-name"}]  # No name field
            }
            mock_httpx_client.get.return_value = mock_response

            models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

            assert len(models) == 1
            assert models[0]["id"] == "model-without-name"
            assert models[0]["name"] == "model-without-name"  # Uses id as name

    @pytest.mark.asyncio
    async def test_get_available_models_single_part_model_id(self, mock_httpx_client):
        """Test get_available_models handles model id without slash."""
        from backend.llm_service import get_available_models

        with patch("backend.llm_service._MODELS_CACHE", {}):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"id": "simple-model", "name": "Simple Model"}]
            }
            mock_httpx_client.get.return_value = mock_response

            models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

            assert len(models) == 1
            assert models[0]["id"] == "simple-model"
            assert models[0]["provider"] == "unknown"  # No slash, so provider is unknown


@pytest.fixture
def mock_httpx_client():
    """Fixture to mock httpx.AsyncClient for get_available_models tests."""
    from unittest.mock import AsyncMock, patch

    with patch("httpx.AsyncClient", autospec=True) as mock_client:
        mock_context = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_context
        yield mock_context
