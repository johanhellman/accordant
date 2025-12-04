"""Tests for configuration module, focusing on personality loading for multi-tenancy."""

import os
import tempfile

import pytest
import yaml

from backend.config.personalities import (
    get_active_personalities,
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

        from backend.config.personalities import (
            DEFAULT_BASE_SYSTEM_PROMPT,
            DEFAULT_CHAIRMAN_PROMPT,
            DEFAULT_RANKING_PROMPT,
            DEFAULT_TITLE_GENERATION_PROMPT,
        )

        assert prompts["base_system_prompt"] == DEFAULT_BASE_SYSTEM_PROMPT
        assert prompts["chairman_prompt"] == DEFAULT_CHAIRMAN_PROMPT
        assert prompts["title_prompt"] == DEFAULT_TITLE_GENERATION_PROMPT
        assert prompts["ranking_prompt"] == DEFAULT_RANKING_PROMPT
