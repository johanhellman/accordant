"""Tests for instance admin endpoints in admin_routes.py.

These tests cover the instance admin-only endpoints:
- get_default_system_prompts
- update_default_system_prompts
"""

import os
from unittest.mock import MagicMock, patch

import pytest
import yaml
from fastapi import HTTPException

from backend.admin_routes import (
    get_default_system_prompts,
    update_default_system_prompts,
)
from backend.config.personalities import DEFAULTS_FILE
from backend.users import User


@pytest.fixture
def instance_admin_user():
    """Create an instance admin user for testing."""
    return User(
        id="1",
        username="instance_admin",
        password_hash="hash",
        is_admin=True,
        is_instance_admin=True,
        org_id="test-org",
    )


@pytest.fixture
def regular_admin_user():
    """Create a regular admin user (not instance admin) for testing."""
    return User(
        id="2",
        username="regular_admin",
        password_hash="hash",
        is_admin=True,
        is_instance_admin=False,
        org_id="test-org",
    )


class TestGetDefaultSystemPrompts:
    """Tests for get_default_system_prompts endpoint."""

    @pytest.mark.asyncio
    async def test_get_default_system_prompts_success(self, instance_admin_user, tmp_path):
        """Test get_default_system_prompts returns default prompts successfully."""
        defaults_file = tmp_path / "defaults" / "system-prompts.yaml"
        defaults_file.parent.mkdir(parents=True, exist_ok=True)

        defaults_data = {
            "base_system_prompt": "Default base prompt",
            "ranking_prompt": "Default ranking prompt {user_query} {responses_text} {peer_text}",
            "chairman": {"prompt": "Default chairman prompt {user_query} {stage1_text} {voting_details_text}"},
            "title_generation": {"prompt": "Default title prompt {user_query}"},
            "stage1_response_structure": "Default structure",
            "stage1_meta_structure": "Default meta structure",
        }

        with open(defaults_file, "w") as f:
            yaml.dump(defaults_data, f)

        with patch("backend.admin_routes.DEFAULTS_FILE", str(defaults_file)):
            result = await get_default_system_prompts(current_user=instance_admin_user)

            assert result["base_system_prompt"]["value"] == "Default base prompt"
            assert result["base_system_prompt"]["is_default"] is True
            assert result["base_system_prompt"]["source"] == "default"
            assert result["ranking"]["prompt"]["value"] == "Default ranking prompt {user_query} {responses_text} {peer_text}"
            assert result["chairman"]["prompt"]["value"] == "Default chairman prompt {user_query} {stage1_text} {voting_details_text}"
            assert result["title_generation"]["prompt"]["value"] == "Default title prompt {user_query}"
            assert result["stage1_response_structure"]["value"] == "Default structure"
            assert result["stage1_meta_structure"]["value"] == "Default meta structure"

    @pytest.mark.asyncio
    async def test_get_default_system_prompts_empty_file(self, instance_admin_user, tmp_path):
        """Test get_default_system_prompts handles empty defaults file."""
        defaults_file = tmp_path / "defaults" / "system-prompts.yaml"
        defaults_file.parent.mkdir(parents=True, exist_ok=True)
        defaults_file.touch()

        with patch("backend.admin_routes.DEFAULTS_FILE", str(defaults_file)):
            result = await get_default_system_prompts(current_user=instance_admin_user)

            # Should return empty strings for missing values
            assert result["base_system_prompt"]["value"] == ""
            assert result["base_system_prompt"]["is_default"] is True
            assert result["ranking"]["prompt"]["value"] == ""
            assert result["chairman"]["prompt"]["value"] == ""
            assert result["title_generation"]["prompt"]["value"] == ""

    @pytest.mark.asyncio
    async def test_get_default_system_prompts_missing_file(self, instance_admin_user, tmp_path):
        """Test get_default_system_prompts handles missing defaults file."""
        defaults_file = tmp_path / "defaults" / "system-prompts.yaml"
        # Don't create the file

        with patch("backend.admin_routes.DEFAULTS_FILE", str(defaults_file)):
            result = await get_default_system_prompts(current_user=instance_admin_user)

            # Should return empty strings for missing values
            assert result["base_system_prompt"]["value"] == ""
            assert result["base_system_prompt"]["is_default"] is True

    @pytest.mark.asyncio
    async def test_get_default_system_prompts_partial_config(self, instance_admin_user, tmp_path):
        """Test get_default_system_prompts handles partial config."""
        defaults_file = tmp_path / "defaults" / "system-prompts.yaml"
        defaults_file.parent.mkdir(parents=True, exist_ok=True)

        # Only set base_system_prompt
        defaults_data = {"base_system_prompt": "Only base prompt"}

        with open(defaults_file, "w") as f:
            yaml.dump(defaults_data, f)

        with patch("backend.admin_routes.DEFAULTS_FILE", str(defaults_file)):
            result = await get_default_system_prompts(current_user=instance_admin_user)

            assert result["base_system_prompt"]["value"] == "Only base prompt"
            # Other fields should be empty strings
            assert result["ranking"]["prompt"]["value"] == ""
            assert result["chairman"]["prompt"]["value"] == ""

    @pytest.mark.asyncio
    async def test_get_default_system_prompts_non_dict_chairman(self, instance_admin_user, tmp_path):
        """Test get_default_system_prompts handles non-dict chairman value."""
        defaults_file = tmp_path / "defaults" / "system-prompts.yaml"
        defaults_file.parent.mkdir(parents=True, exist_ok=True)

        # Set chairman as a string instead of dict
        defaults_data = {"chairman": "not a dict"}

        with open(defaults_file, "w") as f:
            yaml.dump(defaults_data, f)

        with patch("backend.admin_routes.DEFAULTS_FILE", str(defaults_file)):
            result = await get_default_system_prompts(current_user=instance_admin_user)

            # Should handle gracefully and return empty string
            assert result["chairman"]["prompt"]["value"] == ""

    @pytest.mark.asyncio
    async def test_get_default_system_prompts_non_dict_title_generation(self, instance_admin_user, tmp_path):
        """Test get_default_system_prompts handles non-dict title_generation value."""
        defaults_file = tmp_path / "defaults" / "system-prompts.yaml"
        defaults_file.parent.mkdir(parents=True, exist_ok=True)

        # Set title_generation as a string instead of dict
        defaults_data = {"title_generation": "not a dict"}

        with open(defaults_file, "w") as f:
            yaml.dump(defaults_data, f)

        with patch("backend.admin_routes.DEFAULTS_FILE", str(defaults_file)):
            result = await get_default_system_prompts(current_user=instance_admin_user)

            # Should handle gracefully and return empty string
            assert result["title_generation"]["prompt"]["value"] == ""


class TestUpdateDefaultSystemPrompts:
    """Tests for update_default_system_prompts endpoint."""

    @pytest.mark.asyncio
    async def test_update_default_system_prompts_success(self, instance_admin_user, tmp_path):
        """Test update_default_system_prompts updates defaults successfully."""
        defaults_file = tmp_path / "defaults" / "system-prompts.yaml"
        defaults_file.parent.mkdir(parents=True, exist_ok=True)

        # Initial defaults
        initial_data = {
            "base_system_prompt": "Initial base prompt",
            "ranking_prompt": "Initial ranking prompt",
        }

        with open(defaults_file, "w") as f:
            yaml.dump(initial_data, f)

        # Update config with ConfigValue format
        update_config = {
            "base_system_prompt": {"value": "Updated base prompt", "is_default": True, "source": "default"},
            "ranking": {"prompt": {"value": "Updated ranking prompt", "is_default": True, "source": "default"}},
            "chairman": {"prompt": {"value": "Updated chairman prompt", "is_default": True, "source": "default"}},
            "title_generation": {"prompt": {"value": "Updated title prompt", "is_default": True, "source": "default"}},
            "stage1_response_structure": {"value": "Updated structure", "is_default": True, "source": "default"},
            "stage1_meta_structure": {"value": "Updated meta", "is_default": True, "source": "default"},
        }

        with patch("backend.admin_routes.DEFAULTS_FILE", str(defaults_file)):
            result = await update_default_system_prompts(update_config, current_user=instance_admin_user)

            # Verify updates
            assert result["base_system_prompt"]["value"] == "Updated base prompt"
            assert result["ranking"]["prompt"]["value"] == "Updated ranking prompt"
            assert result["chairman"]["prompt"]["value"] == "Updated chairman prompt"
            assert result["title_generation"]["prompt"]["value"] == "Updated title prompt"
            assert result["stage1_response_structure"]["value"] == "Updated structure"
            assert result["stage1_meta_structure"]["value"] == "Updated meta"

            # Verify file was updated
            with open(defaults_file) as f:
                saved = yaml.safe_load(f)
                assert saved["base_system_prompt"] == "Updated base prompt"
                assert saved["ranking_prompt"] == "Updated ranking prompt"
                assert saved["chairman"]["prompt"] == "Updated chairman prompt"
                assert saved["title_generation"]["prompt"] == "Updated title prompt"

    @pytest.mark.asyncio
    async def test_update_default_system_prompts_direct_value(self, instance_admin_user, tmp_path):
        """Test update_default_system_prompts accepts direct values (not ConfigValue)."""
        defaults_file = tmp_path / "defaults" / "system-prompts.yaml"
        defaults_file.parent.mkdir(parents=True, exist_ok=True)

        # Update config with direct values
        update_config = {
            "base_system_prompt": "Direct value",
            "ranking": {"prompt": "Direct ranking prompt"},
        }

        with patch("backend.admin_routes.DEFAULTS_FILE", str(defaults_file)):
            result = await update_default_system_prompts(update_config, current_user=instance_admin_user)

            assert result["base_system_prompt"]["value"] == "Direct value"
            assert result["ranking"]["prompt"]["value"] == "Direct ranking prompt"

    @pytest.mark.asyncio
    async def test_update_default_system_prompts_partial_update(self, instance_admin_user, tmp_path):
        """Test update_default_system_prompts preserves existing values when partially updating."""
        defaults_file = tmp_path / "defaults" / "system-prompts.yaml"
        defaults_file.parent.mkdir(parents=True, exist_ok=True)

        # Initial defaults with multiple fields
        initial_data = {
            "base_system_prompt": "Initial base",
            "ranking_prompt": "Initial ranking",
            "chairman": {"prompt": "Initial chairman"},
            "title_generation": {"prompt": "Initial title"},
            "stage1_response_structure": "Initial structure",
        }

        with open(defaults_file, "w") as f:
            yaml.dump(initial_data, f)

        # Only update base_system_prompt
        update_config = {
            "base_system_prompt": {"value": "Updated base only", "is_default": True, "source": "default"},
        }

        with patch("backend.admin_routes.DEFAULTS_FILE", str(defaults_file)):
            result = await update_default_system_prompts(update_config, current_user=instance_admin_user)

            # Updated field should be changed
            assert result["base_system_prompt"]["value"] == "Updated base only"
            # Other fields should be preserved
            assert result["ranking"]["prompt"]["value"] == "Initial ranking"
            assert result["chairman"]["prompt"]["value"] == "Initial chairman"

    @pytest.mark.asyncio
    async def test_update_default_system_prompts_none_value(self, instance_admin_user, tmp_path):
        """Test update_default_system_prompts handles None values."""
        defaults_file = tmp_path / "defaults" / "system-prompts.yaml"
        defaults_file.parent.mkdir(parents=True, exist_ok=True)

        initial_data = {"base_system_prompt": "Initial"}

        with open(defaults_file, "w") as f:
            yaml.dump(initial_data, f)

        # Update with None value
        update_config = {
            "base_system_prompt": None,
            "ranking": {"prompt": None},
        }

        with patch("backend.admin_routes.DEFAULTS_FILE", str(defaults_file)):
            result = await update_default_system_prompts(update_config, current_user=instance_admin_user)

            # None values should be handled gracefully
            assert result is not None

    @pytest.mark.asyncio
    async def test_update_default_system_prompts_empty_dict(self, instance_admin_user, tmp_path):
        """Test update_default_system_prompts handles empty update dict."""
        defaults_file = tmp_path / "defaults" / "system-prompts.yaml"
        defaults_file.parent.mkdir(parents=True, exist_ok=True)

        initial_data = {"base_system_prompt": "Initial"}

        with open(defaults_file, "w") as f:
            yaml.dump(initial_data, f)

        # Empty update config
        update_config = {}

        with patch("backend.admin_routes.DEFAULTS_FILE", str(defaults_file)):
            result = await update_default_system_prompts(update_config, current_user=instance_admin_user)

            # Should preserve existing values
            assert result["base_system_prompt"]["value"] == "Initial"

    @pytest.mark.asyncio
    async def test_update_default_system_prompts_creates_nested_dicts(self, instance_admin_user, tmp_path):
        """Test update_default_system_prompts creates nested dicts when they don't exist."""
        defaults_file = tmp_path / "defaults" / "system-prompts.yaml"
        defaults_file.parent.mkdir(parents=True, exist_ok=True)

        # Initial defaults without nested dicts
        initial_data = {"base_system_prompt": "Initial"}

        with open(defaults_file, "w") as f:
            yaml.dump(initial_data, f)

        # Update with nested configs
        update_config = {
            "chairman": {"prompt": {"value": "New chairman prompt", "is_default": True, "source": "default"}},
            "title_generation": {"prompt": {"value": "New title prompt", "is_default": True, "source": "default"}},
        }

        with patch("backend.admin_routes.DEFAULTS_FILE", str(defaults_file)):
            result = await update_default_system_prompts(update_config, current_user=instance_admin_user)

            # Should create nested dicts
            assert result["chairman"]["prompt"]["value"] == "New chairman prompt"
            assert result["title_generation"]["prompt"]["value"] == "New title prompt"

            # Verify file structure
            with open(defaults_file) as f:
                saved = yaml.safe_load(f)
                assert isinstance(saved["chairman"], dict)
                assert saved["chairman"]["prompt"] == "New chairman prompt"
                assert isinstance(saved["title_generation"], dict)
                assert saved["title_generation"]["prompt"] == "New title prompt"

    @pytest.mark.asyncio
    async def test_update_default_system_prompts_save_error(self, instance_admin_user, tmp_path):
        """Test update_default_system_prompts handles save errors."""
        defaults_file = tmp_path / "defaults" / "system-prompts.yaml"
        defaults_file.parent.mkdir(parents=True, exist_ok=True)

        update_config = {
            "base_system_prompt": {"value": "Updated", "is_default": True, "source": "default"},
        }

        with (
            patch("backend.admin_routes.DEFAULTS_FILE", str(defaults_file)),
            patch("backend.admin_routes._save_yaml", side_effect=Exception("Save error")),
        ):
            with pytest.raises(Exception):
                await update_default_system_prompts(update_config, current_user=instance_admin_user)
