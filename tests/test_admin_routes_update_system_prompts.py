"""Comprehensive edge case tests for update_system_prompts endpoint.

These tests cover the complex logic in update_system_prompts including:
- is_default toggle logic (reverting to inheritance)
- Nested component updates (chairman, title_generation, ranking)
- Model updates within nested components
- Creating nested dicts when they don't exist
- Non-dict incoming_data handling
"""

from unittest.mock import patch

import pytest
import yaml

from backend.admin_routes import update_system_prompts
from backend.users import User


@pytest.fixture
def admin_user():
    """Create an admin user for testing."""
    return User(
        id="1",
        username="admin",
        password_hash="hash",
        is_admin=True,
        org_id="test-org",
    )


class TestUpdateSystemPromptsIsDefaultToggle:
    """Tests for is_default toggle logic in update_system_prompts."""

    @pytest.mark.asyncio
    async def test_update_system_prompts_revert_to_default(self, admin_user, tmp_path):
        """Test that setting is_default=True removes field from org config."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create org config with custom value
        org_config = {"base_system_prompt": "Custom org prompt"}
        config_file = config_dir / "system-prompts.yaml"
        with open(config_file, "w") as f:
            yaml.dump(org_config, f)

        # Update with is_default=True to revert to default
        update_config = {
            "base_system_prompt": {
                "value": "Should be ignored",
                "is_default": True,
                "source": "default",
            },
        }

        with (
            patch("backend.config.personalities.get_org_config_dir", return_value=str(config_dir)),
            patch("backend.admin_routes.get_system_prompts") as mock_get,
        ):
            mock_get.return_value = {
                "base_system_prompt": {"value": "Default prompt", "is_default": True}
            }

            await update_system_prompts(update_config, current_user=admin_user)

            # Verify field was removed from org config
            with open(config_file) as f:
                saved = yaml.safe_load(f)
                assert "base_system_prompt" not in saved

    @pytest.mark.asyncio
    async def test_update_system_prompts_set_custom_value(self, admin_user, tmp_path):
        """Test that setting is_default=False sets custom value."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "system-prompts.yaml"
        config_file.touch()

        # Update with is_default=False to set custom value
        update_config = {
            "base_system_prompt": {
                "value": "Custom org prompt",
                "is_default": False,
                "source": "custom",
            },
        }

        with (
            patch("backend.config.personalities.get_org_config_dir", return_value=str(config_dir)),
            patch("backend.admin_routes.get_system_prompts") as mock_get,
        ):
            mock_get.return_value = {
                "base_system_prompt": {"value": "Custom org prompt", "is_default": False}
            }

            await update_system_prompts(update_config, current_user=admin_user)

            # Verify custom value was saved
            with open(config_file) as f:
                saved = yaml.safe_load(f)
                assert saved["base_system_prompt"] == "Custom org prompt"

    @pytest.mark.asyncio
    async def test_update_system_prompts_non_dict_incoming_data(self, admin_user, tmp_path):
        """Test that non-dict incoming_data is ignored."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        initial_config = {"base_system_prompt": "Initial"}
        config_file = config_dir / "system-prompts.yaml"
        with open(config_file, "w") as f:
            yaml.dump(initial_config, f)

        # Update with non-dict value (should be ignored)
        update_config = {
            "base_system_prompt": "Not a dict",  # Should be ignored
        }

        with (
            patch("backend.config.personalities.get_org_config_dir", return_value=str(config_dir)),
            patch("backend.admin_routes.get_system_prompts") as mock_get,
        ):
            mock_get.return_value = {
                "base_system_prompt": {"value": "Initial", "is_default": False}
            }

            await update_system_prompts(update_config, current_user=admin_user)

            # Verify value was not changed
            with open(config_file) as f:
                saved = yaml.safe_load(f)
                assert saved["base_system_prompt"] == "Initial"


class TestUpdateSystemPromptsNestedComponents:
    """Tests for nested component updates (chairman, title_generation, ranking)."""

    @pytest.mark.asyncio
    async def test_update_system_prompts_chairman_prompt(self, admin_user, tmp_path):
        """Test updating chairman prompt."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "system-prompts.yaml"
        config_file.touch()

        update_config = {
            "chairman": {
                "prompt": {
                    "value": "Custom chairman prompt {user_query}",
                    "is_default": False,
                    "source": "custom",
                },
            },
        }

        with (
            patch("backend.config.personalities.get_org_config_dir", return_value=str(config_dir)),
            patch("backend.admin_routes.get_system_prompts") as mock_get,
        ):
            mock_get.return_value = {
                "chairman": {
                    "prompt": {"value": "Custom chairman prompt {user_query}", "is_default": False}
                }
            }

            await update_system_prompts(update_config, current_user=admin_user)

            # Verify nested dict was created and prompt was saved
            with open(config_file) as f:
                saved = yaml.safe_load(f)
                assert isinstance(saved["chairman"], dict)
                assert saved["chairman"]["prompt"] == "Custom chairman prompt {user_query}"

    @pytest.mark.asyncio
    async def test_update_system_prompts_chairman_model(self, admin_user, tmp_path):
        """Test updating chairman model."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        initial_config = {"chairman": {"prompt": "Existing prompt"}}
        config_file = config_dir / "system-prompts.yaml"
        with open(config_file, "w") as f:
            yaml.dump(initial_config, f)

        update_config = {
            "chairman": {
                "model": "custom-chairman-model",
            },
        }

        with (
            patch("backend.config.personalities.get_org_config_dir", return_value=str(config_dir)),
            patch("backend.admin_routes.get_system_prompts") as mock_get,
        ):
            mock_get.return_value = {"chairman": {"model": "custom-chairman-model"}}

            await update_system_prompts(update_config, current_user=admin_user)

            # Verify model was saved
            with open(config_file) as f:
                saved = yaml.safe_load(f)
                assert saved["chairman"]["model"] == "custom-chairman-model"
                assert saved["chairman"]["prompt"] == "Existing prompt"  # Preserved

    @pytest.mark.asyncio
    async def test_update_system_prompts_title_generation_prompt(self, admin_user, tmp_path):
        """Test updating title_generation prompt."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "system-prompts.yaml"
        config_file.touch()

        update_config = {
            "title_generation": {
                "prompt": {
                    "value": "Custom title prompt {user_query}",
                    "is_default": False,
                    "source": "custom",
                },
            },
        }

        with (
            patch("backend.config.personalities.get_org_config_dir", return_value=str(config_dir)),
            patch("backend.admin_routes.get_system_prompts") as mock_get,
        ):
            mock_get.return_value = {
                "title_generation": {
                    "prompt": {"value": "Custom title prompt {user_query}", "is_default": False}
                }
            }

            await update_system_prompts(update_config, current_user=admin_user)

            # Verify nested dict was created and prompt was saved
            with open(config_file) as f:
                saved = yaml.safe_load(f)
                assert isinstance(saved["title_generation"], dict)
                assert saved["title_generation"]["prompt"] == "Custom title prompt {user_query}"

    @pytest.mark.asyncio
    async def test_update_system_prompts_ranking_prompt(self, admin_user, tmp_path):
        """Test updating ranking prompt."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "system-prompts.yaml"
        config_file.touch()

        update_config = {
            "ranking": {
                "prompt": {
                    "value": "Custom ranking prompt {responses_text} {user_query}",
                    "is_default": False,
                    "source": "custom",
                },
            },
        }

        with (
            patch("backend.config.personalities.get_org_config_dir", return_value=str(config_dir)),
            patch("backend.admin_routes.get_system_prompts") as mock_get,
        ):
            mock_get.return_value = {
                "ranking": {
                    "prompt": {
                        "value": "Custom ranking prompt {responses_text} {user_query}",
                        "is_default": False,
                    }
                }
            }

            await update_system_prompts(update_config, current_user=admin_user)

            # Verify nested dict was created and prompt was saved
            with open(config_file) as f:
                saved = yaml.safe_load(f)
                assert isinstance(saved["ranking"], dict)
                assert (
                    saved["ranking"]["prompt"]
                    == "Custom ranking prompt {responses_text} {user_query}"
                )

    @pytest.mark.asyncio
    async def test_update_system_prompts_ranking_model(self, admin_user, tmp_path):
        """Test updating ranking model."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        initial_config = {"ranking": {"prompt": "Existing ranking prompt"}}
        config_file = config_dir / "system-prompts.yaml"
        with open(config_file, "w") as f:
            yaml.dump(initial_config, f)

        update_config = {
            "ranking": {
                "model": "custom-ranking-model",
            },
        }

        with (
            patch("backend.config.personalities.get_org_config_dir", return_value=str(config_dir)),
            patch("backend.admin_routes.get_system_prompts") as mock_get,
        ):
            mock_get.return_value = {"ranking": {"model": "custom-ranking-model"}}

            await update_system_prompts(update_config, current_user=admin_user)

            # Verify model was saved
            with open(config_file) as f:
                saved = yaml.safe_load(f)
                assert saved["ranking"]["model"] == "custom-ranking-model"
                assert saved["ranking"]["prompt"] == "Existing ranking prompt"  # Preserved

    @pytest.mark.asyncio
    async def test_update_system_prompts_revert_chairman_to_default(self, admin_user, tmp_path):
        """Test reverting chairman prompt to default removes it from org config."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create org config with custom chairman prompt
        org_config = {"chairman": {"prompt": "Custom chairman prompt"}}
        config_file = config_dir / "system-prompts.yaml"
        with open(config_file, "w") as f:
            yaml.dump(org_config, f)

        # Revert to default
        update_config = {
            "chairman": {
                "prompt": {"value": "Ignored", "is_default": True, "source": "default"},
            },
        }

        with (
            patch("backend.config.personalities.get_org_config_dir", return_value=str(config_dir)),
            patch("backend.admin_routes.get_system_prompts") as mock_get,
        ):
            mock_get.return_value = {
                "chairman": {"prompt": {"value": "Default chairman prompt", "is_default": True}}
            }

            await update_system_prompts(update_config, current_user=admin_user)

            # Verify prompt was removed from org config
            with open(config_file) as f:
                saved = yaml.safe_load(f)
                # Chairman dict might still exist but prompt should be removed
                if "chairman" in saved:
                    assert "prompt" not in saved["chairman"]


class TestUpdateSystemPromptsEdgeCases:
    """Edge case tests for update_system_prompts."""

    @pytest.mark.asyncio
    async def test_update_system_prompts_empty_config(self, admin_user, tmp_path):
        """Test update_system_prompts handles empty update config."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        initial_config = {"base_system_prompt": "Initial"}
        config_file = config_dir / "system-prompts.yaml"
        with open(config_file, "w") as f:
            yaml.dump(initial_config, f)

        update_config = {}

        with (
            patch("backend.config.personalities.get_org_config_dir", return_value=str(config_dir)),
            patch("backend.admin_routes.get_system_prompts") as mock_get,
        ):
            mock_get.return_value = {
                "base_system_prompt": {"value": "Initial", "is_default": False}
            }

            await update_system_prompts(update_config, current_user=admin_user)

            # Verify initial config was preserved
            with open(config_file) as f:
                saved = yaml.safe_load(f)
                assert saved["base_system_prompt"] == "Initial"

    @pytest.mark.asyncio
    async def test_update_system_prompts_chairman_not_dict(self, admin_user, tmp_path):
        """Test update_system_prompts handles non-dict chairman config."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "system-prompts.yaml"
        config_file.touch()

        # Chairman is not a dict
        update_config = {
            "chairman": "not a dict",
        }

        with (
            patch("backend.config.personalities.get_org_config_dir", return_value=str(config_dir)),
            patch("backend.admin_routes.get_system_prompts") as mock_get,
        ):
            mock_get.return_value = {}

            await update_system_prompts(update_config, current_user=admin_user)

            # Should handle gracefully without error

    @pytest.mark.asyncio
    async def test_update_system_prompts_model_not_string(self, admin_user, tmp_path):
        """Test update_system_prompts ignores non-string model values."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        initial_config = {"chairman": {"prompt": "Existing"}}
        config_file = config_dir / "system-prompts.yaml"
        with open(config_file, "w") as f:
            yaml.dump(initial_config, f)

        # Model is not a string
        update_config = {
            "chairman": {
                "model": 123,  # Not a string
            },
        }

        with (
            patch("backend.config.personalities.get_org_config_dir", return_value=str(config_dir)),
            patch("backend.admin_routes.get_system_prompts") as mock_get,
        ):
            mock_get.return_value = {}

            await update_system_prompts(update_config, current_user=admin_user)

            # Verify model was not saved
            with open(config_file) as f:
                saved = yaml.safe_load(f)
                assert "model" not in saved.get("chairman", {})

    @pytest.mark.asyncio
    async def test_update_system_prompts_multiple_fields(self, admin_user, tmp_path):
        """Test update_system_prompts updates multiple fields at once."""
        org_id = "test-org"
        config_dir = tmp_path / "organizations" / org_id / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "system-prompts.yaml"
        config_file.touch()

        update_config = {
            "base_system_prompt": {
                "value": "Updated base",
                "is_default": False,
                "source": "custom",
            },
            "stage1_response_structure": {
                "value": "Updated structure",
                "is_default": False,
                "source": "custom",
            },
            "stage1_meta_structure": {
                "value": "Updated meta",
                "is_default": False,
                "source": "custom",
            },
            "chairman": {
                "prompt": {
                    "value": "Updated chairman {user_query}",
                    "is_default": False,
                    "source": "custom",
                },
                "model": "chairman-model",
            },
            "title_generation": {
                "prompt": {
                    "value": "Updated title {user_query}",
                    "is_default": False,
                    "source": "custom",
                },
                "model": "title-model",
            },
            "ranking": {
                "prompt": {
                    "value": "Updated ranking {user_query} {responses_text}",
                    "is_default": False,
                    "source": "custom",
                },
                "model": "ranking-model",
            },
        }

        with (
            patch("backend.config.personalities.get_org_config_dir", return_value=str(config_dir)),
            patch("backend.admin_routes.get_system_prompts") as mock_get,
        ):
            mock_get.return_value = {
                "base_system_prompt": {"value": "Updated base", "is_default": False},
                "chairman": {
                    "prompt": {"value": "Updated chairman {user_query}", "is_default": False}
                },
            }

            await update_system_prompts(update_config, current_user=admin_user)

            # Verify all fields were saved
            with open(config_file) as f:
                saved = yaml.safe_load(f)
                assert saved["base_system_prompt"] == "Updated base"
                assert saved["stage1_response_structure"] == "Updated structure"
                assert saved["stage1_meta_structure"] == "Updated meta"
                assert saved["chairman"]["prompt"] == "Updated chairman {user_query}"
                assert saved["chairman"]["model"] == "chairman-model"
                assert saved["title_generation"]["prompt"] == "Updated title {user_query}"
                assert saved["title_generation"]["model"] == "title-model"
                assert saved["ranking"]["prompt"] == "Updated ranking {user_query} {responses_text}"
                assert saved["ranking"]["model"] == "ranking-model"
