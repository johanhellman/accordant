"""Tests for configuration module, focusing on personality loading for multi-tenancy."""

import os
import tempfile

import pytest
import yaml

from backend.config.personalities import (
    _get_nested_config_value,
    _load_defaults,
    _load_org_config_file,
    get_active_personalities,
    get_org_config_dir,
    get_org_personalities_dir,
    load_org_models_config,
    load_org_system_prompts,
)


class TestPersonalityLoading:
    """Tests for personality loading from org directory."""

    @pytest.fixture
    def temp_org_dir(self, monkeypatch):
        """Create a temporary org directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch ORGS_DATA_DIR to use temp dir
            monkeypatch.setattr("backend.config.personalities.ORGS_DATA_DIR", tmpdir)

            # Patch DEFAULTS_DIR to prevent loading system defaults
            defaults_dir = os.path.join(tmpdir, "defaults")
            os.makedirs(defaults_dir, exist_ok=True)
            monkeypatch.setattr("backend.config.personalities.DEFAULTS_DIR", defaults_dir)

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

        defaults = _load_defaults()
        assert prompts["base_system_prompt"] == defaults.get("base_system_prompt", "")
        assert prompts["chairman_prompt"] == _get_nested_config_value(
            defaults, "chairman", "prompt", ""
        )
        # Note: ranking prompt key logic might vary, checking main key
        # In load_org_system_prompts, it uses default_ranking for ranking_prompt
        default_ranking = defaults.get("ranking_prompt", "")
        if not default_ranking:
            default_ranking = _get_nested_config_value(defaults, "ranking", "prompt", "")
        assert prompts["ranking_prompt"] == default_ranking
        assert prompts["title_prompt"] == _get_nested_config_value(
            defaults, "title_generation", "prompt", ""
        )

    def test_get_active_personalities_invalid_yaml(self, temp_org_dir, caplog):
        """Test handling of invalid YAML files."""
        _, org_id, personalities_dir, _ = temp_org_dir

        # Create invalid YAML file
        with open(os.path.join(personalities_dir, "invalid.yaml"), "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        get_active_personalities(org_id)

        # Should skip invalid file and return empty list (or other valid personalities)
        # Error should be logged
        assert "Error loading org personality" in caplog.text

    def test_get_active_personalities_missing_id(self, temp_org_dir):
        """Test that personalities without 'id' field are skipped."""
        _, org_id, personalities_dir, _ = temp_org_dir

        # Create personality without id field
        with open(os.path.join(personalities_dir, "no_id.yaml"), "w") as f:
            yaml.dump({"name": "Personality Without ID", "model": "test/model", "enabled": True}, f)

        active = get_active_personalities(org_id)

        # Should skip personality without id
        assert len(active) == 0

    def test_get_active_personalities_disabled_by_default(self, temp_org_dir):
        """Test that personalities without 'enabled' field default to enabled=True."""
        _, org_id, personalities_dir, _ = temp_org_dir

        # Create personality without enabled field (should default to enabled)
        with open(os.path.join(personalities_dir, "default_enabled.yaml"), "w") as f:
            yaml.dump(
                {"id": "default_enabled", "name": "Default Enabled", "model": "test/model"}, f
            )

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
                {
                    "id": "valid",
                    "name": "Valid Personality",
                    "model": "test/model",
                    "enabled": True,
                },
                f,
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

        _, org_id, _, config_dir = temp_org_dir

        # Create invalid YAML file
        with open(os.path.join(config_dir, "system-prompts.yaml"), "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        result = _load_org_config_file(org_id)

        # Should return None and log error
        assert result is None
        assert "Error loading" in caplog.text

    def test_load_org_system_prompts_file_read_error(self, temp_org_dir, monkeypatch, caplog):
        """Test handling of file read errors."""

        _, org_id, _, config_dir = temp_org_dir

        # Create valid file
        system_prompts_file = os.path.join(config_dir, "system-prompts.yaml")
        with open(system_prompts_file, "w") as f:
            yaml.dump({"base_system_prompt": "Test"}, f)

        # Mock open to raise IOError
        original_open = open

        def mock_open(*args, **kwargs):
            if args[0] == system_prompts_file:
                raise OSError("Permission denied")
            return original_open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        result = _load_org_config_file(org_id)

        # Should return None and log error
        assert result is None
        assert "Error loading" in caplog.text

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
        # Should fall back to default since ranking is not a dict
        defaults = _load_defaults()
        default_ranking = defaults.get("ranking_prompt", "")
        if not default_ranking:
            default_ranking = _get_nested_config_value(defaults, "ranking", "prompt", "")

        assert prompts["ranking_prompt"] == default_ranking


class TestNestedConfigValue:
    """Tests for _get_nested_config_value helper function."""

    def test_get_nested_config_value_exists(self):
        """Test _get_nested_config_value when value exists."""
        config = {"section": {"key": "value"}}
        result = _get_nested_config_value(config, "section", "key", "default")
        assert result == "value"

    def test_get_nested_config_value_missing_key(self):
        """Test _get_nested_config_value when key is missing."""
        config = {"section": {}}
        result = _get_nested_config_value(config, "section", "key", "default")
        assert result == "default"

    def test_get_nested_config_value_missing_section(self):
        """Test _get_nested_config_value when section is missing."""
        config = {}
        result = _get_nested_config_value(config, "section", "key", "default")
        assert result == "default"

    def test_get_nested_config_value_non_dict_section(self):
        """Test _get_nested_config_value when section is not a dict."""
        config = {"section": "not a dict"}
        result = _get_nested_config_value(config, "section", "key", "default")
        assert result == "default"

    def test_get_nested_config_value_none_section(self):
        """Test _get_nested_config_value when section is None."""
        config = {"section": None}
        result = _get_nested_config_value(config, "section", "key", "default")
        assert result == "default"


class TestOrgModelsConfig:
    """Tests for load_org_models_config function."""

    @pytest.fixture
    def temp_org_dir(self, monkeypatch):
        """Create a temporary org directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch ORGS_DATA_DIR to use temp dir
            monkeypatch.setattr("backend.config.personalities.ORGS_DATA_DIR", tmpdir)

            # Create org structure
            org_id = "test-org"
            org_dir = os.path.join(tmpdir, org_id)
            config_dir = os.path.join(org_dir, "config")

            os.makedirs(config_dir, exist_ok=True)

            yield tmpdir, org_id, config_dir

    def test_load_org_models_config_defaults(self, temp_org_dir):
        """Test load_org_models_config returns defaults when no config exists."""
        _, org_id, _ = temp_org_dir

        models = load_org_models_config(org_id)

        assert models["chairman_model"] == "gemini/gemini-2.5-pro"
        assert models["title_model"] == "gemini/gemini-2.5-pro"
        assert models["ranking_model"] == "openai/gpt-4o"

    def test_load_org_models_config_nested(self, temp_org_dir):
        """Test load_org_models_config loads nested model config."""
        _, org_id, config_dir = temp_org_dir

        models_config = {
            "chairman": {"model": "custom/chairman-model"},
            "title_generation": {"model": "custom/title-model"},
            "ranking": {"model": "custom/ranking-model"},
        }

        with open(os.path.join(config_dir, "system-prompts.yaml"), "w") as f:
            yaml.dump(models_config, f)

        models = load_org_models_config(org_id)

        assert models["chairman_model"] == "custom/chairman-model"
        assert models["title_model"] == "custom/title-model"
        assert models["ranking_model"] == "custom/ranking-model"

    def test_load_org_models_config_partial_nested(self, temp_org_dir):
        """Test load_org_models_config with partial nested config."""
        _, org_id, config_dir = temp_org_dir

        models_config = {
            "chairman": {"model": "custom/chairman-model"},
            # title_generation and ranking missing - should use defaults
        }

        with open(os.path.join(config_dir, "system-prompts.yaml"), "w") as f:
            yaml.dump(models_config, f)

        models = load_org_models_config(org_id)

        assert models["chairman_model"] == "custom/chairman-model"
        assert models["title_model"] == "gemini/gemini-2.5-pro"  # Default
        assert models["ranking_model"] == "openai/gpt-4o"  # Default

    def test_load_org_models_config_non_dict_section(self, temp_org_dir):
        """Test load_org_models_config handles non-dict sections."""
        _, org_id, config_dir = temp_org_dir

        models_config = {
            "chairman": "not a dict",  # Should fall back to default
        }

        with open(os.path.join(config_dir, "system-prompts.yaml"), "w") as f:
            yaml.dump(models_config, f)

        models = load_org_models_config(org_id)

        # Should use defaults when section is not a dict
        assert models["chairman_model"] == "gemini/gemini-2.5-pro"
        assert models["title_model"] == "gemini/gemini-2.5-pro"
        assert models["ranking_model"] == "openai/gpt-4o"

    def test_load_org_models_config_missing_model_key(self, temp_org_dir):
        """Test load_org_models_config handles missing model key in section."""
        _, org_id, config_dir = temp_org_dir

        models_config = {
            "chairman": {},  # Empty dict - should fall back to default
        }

        with open(os.path.join(config_dir, "system-prompts.yaml"), "w") as f:
            yaml.dump(models_config, f)

        models = load_org_models_config(org_id)

        # Should use defaults when model key is missing
        assert models["chairman_model"] == "gemini/gemini-2.5-pro"
        assert models["title_model"] == "gemini/gemini-2.5-pro"
        assert models["ranking_model"] == "openai/gpt-4o"


class TestOrgDirectoryHelpers:
    """Tests for get_org_personalities_dir and get_org_config_dir helper functions."""

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

    def test_get_org_personalities_dir(self, temp_org_dir):
        """Test get_org_personalities_dir returns correct path."""
        tmpdir, org_id, expected_dir, _ = temp_org_dir

        result = get_org_personalities_dir(org_id)

        assert result == expected_dir
        assert os.path.exists(result)

    def test_get_org_config_dir(self, temp_org_dir):
        """Test get_org_config_dir returns correct path."""
        tmpdir, org_id, _, expected_dir = temp_org_dir

        result = get_org_config_dir(org_id)

        assert result == expected_dir
        assert os.path.exists(result)

    def test_get_org_personalities_dir_different_org(self, temp_org_dir):
        """Test get_org_personalities_dir with different org ID."""
        tmpdir, _, _, _ = temp_org_dir

        org_id = "different-org"
        result = get_org_personalities_dir(org_id)

        expected = os.path.join(tmpdir, org_id, "personalities")
        assert result == expected

    def test_get_org_config_dir_different_org(self, temp_org_dir):
        """Test get_org_config_dir with different org ID."""
        tmpdir, _, _, _ = temp_org_dir

        org_id = "different-org"
        result = get_org_config_dir(org_id)

        expected = os.path.join(tmpdir, org_id, "config")
        assert result == expected
