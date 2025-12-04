"""Tests for configuration module, focusing on personality loading for multi-tenancy."""

import os
import tempfile

import pytest
import yaml

from backend.config.personalities import (
    DEFAULT_BASE_SYSTEM_PROMPT,
    DEFAULT_CHAIRMAN_PROMPT,
    DEFAULT_RANKING_PROMPT,
    DEFAULT_TITLE_GENERATION_PROMPT,
    get_active_personalities,
    load_org_system_prompts,
    _load_org_config_file,
)


class TestPersonalityLoading:
    """Tests for personality loading from org directory."""

    @pytest.fixture
    def temp_org_dir(self, monkeypatch):
        """Create a temporary org directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch ORGS_DATA_DIR to use temp dir
            monkeypatch.setattr("backend.config.personalities.ORGS_DATA_DIR", tmpdir)

            # Create org structure
            org_id = "test-org"
            org_dir = os.path.join(tmpdir, org_id)
            personalities_dir = os.path.join(org_dir, "personalities")
            config_dir = os.path.join(org_dir, "config")

            os.makedirs(personalities_dir, exist_ok=True)
            os.makedirs(config_dir, exist_ok=True)

            yield tmpdir, org_id, personalities_dir, config_dir

    def test_get_active_personalities(self, temp_org_dir):
        """Test loading active personalities for an org."""
        _, org_id, personalities_dir, _ = temp_org_dir

        # Create personality 1
        with open(os.path.join(personalities_dir, "p1.yaml"), "w") as f:
            yaml.dump(
                {"id": "p1", "name": "Personality 1", "model": "test/model1", "enabled": True}, f
            )

        # Create personality 2 (disabled)
        with open(os.path.join(personalities_dir, "p2.yaml"), "w") as f:
            yaml.dump(
                {"id": "p2", "name": "Personality 2", "model": "test/model2", "enabled": False}, f
            )

        # Create personality 3
        with open(os.path.join(personalities_dir, "p3.yaml"), "w") as f:
            yaml.dump(
                {"id": "p3", "name": "Personality 3", "model": "test/model3", "enabled": True}, f
            )

        active = get_active_personalities(org_id)

        assert len(active) == 2
        ids = [p["id"] for p in active]
        assert "p1" in ids
        assert "p3" in ids
        assert "p2" not in ids

    def test_get_active_personalities_empty(self, temp_org_dir):
        """Test loading when no personalities exist."""
        _, org_id, _, _ = temp_org_dir
        active = get_active_personalities(org_id)
        assert active == []

    def test_load_org_system_prompts(self, temp_org_dir):
        """Test loading system prompts for an org."""
        _, org_id, _, config_dir = temp_org_dir

        prompts_config = {
            "base_system_prompt": "Custom Base Prompt",
            "chairman": {"prompt": "Custom Chairman Prompt"},
            "title_generation": {"prompt": "Custom Title Prompt"},
            "ranking": {"prompt": "Custom Ranking Prompt"},
        }

        with open(os.path.join(config_dir, "system-prompts.yaml"), "w") as f:
            yaml.dump(prompts_config, f)

        prompts = load_org_system_prompts(org_id)

        assert prompts["base_system_prompt"] == "Custom Base Prompt"
        assert prompts["chairman_prompt"] == "Custom Chairman Prompt"
        assert prompts["title_prompt"] == "Custom Title Prompt"
        assert prompts["ranking_prompt"] == "Custom Ranking Prompt"

    def test_load_org_system_prompts_defaults(self, temp_org_dir):
        """Test loading system prompts falls back to defaults."""
        _, org_id, _, _ = temp_org_dir
        # No system-prompts.yaml created

        prompts = load_org_system_prompts(org_id)

        assert prompts["base_system_prompt"] == DEFAULT_BASE_SYSTEM_PROMPT
        assert prompts["chairman_prompt"] == DEFAULT_CHAIRMAN_PROMPT
        assert prompts["title_prompt"] == DEFAULT_TITLE_GENERATION_PROMPT
        assert prompts["ranking_prompt"] == DEFAULT_RANKING_PROMPT

    def test_get_active_personalities_invalid_yaml(self, temp_org_dir, caplog):
        """Test handling of invalid YAML files."""
        _, org_id, personalities_dir, _ = temp_org_dir

        # Create invalid YAML file
        with open(os.path.join(personalities_dir, "invalid.yaml"), "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        active = get_active_personalities(org_id)

        # Should skip invalid file and return empty list (or other valid personalities)
        # Error should be logged
        assert "Error loading personality" in caplog.text

    def test_get_active_personalities_missing_id(self, temp_org_dir):
        """Test that personalities without 'id' field are skipped."""
        _, org_id, personalities_dir, _ = temp_org_dir

        # Create personality without id field
        with open(os.path.join(personalities_dir, "no_id.yaml"), "w") as f:
            yaml.dump(
                {"name": "Personality Without ID", "model": "test/model", "enabled": True}, f
            )

        active = get_active_personalities(org_id)

        # Should skip personality without id
        assert len(active) == 0

    def test_get_active_personalities_disabled_by_default(self, temp_org_dir):
        """Test that personalities without 'enabled' field default to enabled=True."""
        _, org_id, personalities_dir, _ = temp_org_dir

        # Create personality without enabled field (should default to enabled)
        with open(os.path.join(personalities_dir, "default_enabled.yaml"), "w") as f:
            yaml.dump({"id": "default_enabled", "name": "Default Enabled", "model": "test/model"}, f)

        active = get_active_personalities(org_id)

        # Should include personality (defaults to enabled=True)
        assert len(active) == 1
        assert active[0]["id"] == "default_enabled"

    def test_get_active_personalities_excludes_system_prompts_yaml(self, temp_org_dir):
        """Test that system-prompts.yaml is excluded from personalities."""
        _, org_id, personalities_dir, _ = temp_org_dir

        # Create system-prompts.yaml file (should be excluded)
        with open(os.path.join(personalities_dir, "system-prompts.yaml"), "w") as f:
            yaml.dump({"id": "should_not_appear", "name": "System Prompts"}, f)

        # Create valid personality
        with open(os.path.join(personalities_dir, "valid.yaml"), "w") as f:
            yaml.dump(
                {"id": "valid", "name": "Valid Personality", "model": "test/model", "enabled": True}, f
            )

        active = get_active_personalities(org_id)

        # Should only include valid personality, not system-prompts.yaml
        assert len(active) == 1
        assert active[0]["id"] == "valid"
        assert "should_not_appear" not in [p["id"] for p in active]

    def test_get_active_personalities_empty_file(self, temp_org_dir):
        """Test handling of empty YAML file."""
        _, org_id, personalities_dir, _ = temp_org_dir

        # Create empty YAML file
        with open(os.path.join(personalities_dir, "empty.yaml"), "w") as f:
            f.write("")

        active = get_active_personalities(org_id)

        # Should skip empty file
        assert len(active) == 0

    def test_load_org_system_prompts_invalid_yaml(self, temp_org_dir, caplog):
        """Test handling of invalid YAML in system-prompts.yaml."""
        from backend.config.personalities import _load_org_config_file

        _, org_id, _, config_dir = temp_org_dir

        # Create invalid YAML file
        with open(os.path.join(config_dir, "system-prompts.yaml"), "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        result = _load_org_config_file(org_id)

        # Should return None and log error
        assert result is None
        assert "Error loading system prompts config" in caplog.text

    def test_load_org_system_prompts_file_read_error(self, temp_org_dir, monkeypatch, caplog):
        """Test handling of file read errors."""
        from backend.config.personalities import _load_org_config_file

        _, org_id, _, config_dir = temp_org_dir

        # Create valid file
        system_prompts_file = os.path.join(config_dir, "system-prompts.yaml")
        with open(system_prompts_file, "w") as f:
            yaml.dump({"base_system_prompt": "Test"}, f)

        # Mock open to raise IOError
        original_open = open

        def mock_open(*args, **kwargs):
            if args[0] == system_prompts_file:
                raise IOError("Permission denied")
            return original_open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        result = _load_org_config_file(org_id)

        # Should return None and log error
        assert result is None
        assert "Error loading system prompts config" in caplog.text

    def test_load_org_system_prompts_nested_ranking_prompt(self, temp_org_dir):
        """Test loading ranking prompt from nested config."""
        _, org_id, _, config_dir = temp_org_dir

        prompts_config = {
            "ranking": {"prompt": "Nested Ranking Prompt"},
        }

        with open(os.path.join(config_dir, "system-prompts.yaml"), "w") as f:
            yaml.dump(prompts_config, f)

        prompts = load_org_system_prompts(org_id)

        assert prompts["ranking_prompt"] == "Nested Ranking Prompt"

    def test_load_org_system_prompts_top_level_ranking_prompt(self, temp_org_dir):
        """Test loading ranking prompt from top-level config."""
        _, org_id, _, config_dir = temp_org_dir

        prompts_config = {
            "ranking_prompt": "Top-level Ranking Prompt",
        }

        with open(os.path.join(config_dir, "system-prompts.yaml"), "w") as f:
            yaml.dump(prompts_config, f)

        prompts = load_org_system_prompts(org_id)

        assert prompts["ranking_prompt"] == "Top-level Ranking Prompt"

    def test_load_org_system_prompts_nested_non_dict_ranking(self, temp_org_dir):
        """Test handling when ranking config is not a dict."""
        _, org_id, _, config_dir = temp_org_dir

        prompts_config = {
            "ranking": "String instead of dict",  # Not a dict
        }

        with open(os.path.join(config_dir, "system-prompts.yaml"), "w") as f:
            yaml.dump(prompts_config, f)

        prompts = load_org_system_prompts(org_id)

        # Should fall back to default since ranking is not a dict
        assert prompts["ranking_prompt"] == DEFAULT_RANKING_PROMPT
