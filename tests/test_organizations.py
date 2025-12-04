"""Tests for organization management functions."""

import os
import tempfile
from unittest.mock import patch

import pytest

from backend.organizations import (
    OrganizationCreate,
    create_org,
    get_org,
    get_org_api_config,
    list_orgs,
    update_org,
)
from backend.security import decrypt_value, encrypt_value


class TestOrganizations:
    """Tests for organization management functions."""

    @pytest.fixture
    def temp_data_dir(self, monkeypatch):
        """Create a temporary data directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orgs_file = os.path.join(tmpdir, "organizations.json")
            orgs_data_dir = os.path.join(tmpdir, "organizations")
            os.makedirs(orgs_data_dir, exist_ok=True)
            monkeypatch.setattr("backend.organizations.ORGS_FILE", orgs_file)
            monkeypatch.setattr("backend.organizations.ORGS_DATA_DIR", orgs_data_dir)
            monkeypatch.setattr("backend.config.PROJECT_ROOT", tmpdir)
            yield tmpdir

    def test_get_org_api_config_with_encrypted_key(self, temp_data_dir):
        """Test get_org_api_config returns decrypted API key and base URL."""
        # Create org with encrypted API config
        org_create = OrganizationCreate(name="Test Org")
        org = create_org(org_create, owner_id="user1")

        # Set encrypted API config
        encrypted_key = encrypt_value("test-api-key-123")
        org_updates = {
            "api_config": {
                "api_key": encrypted_key,
                "base_url": "https://custom.api.com/v1/chat/completions",
            }
        }
        update_org(org.id, org_updates)

        # Get API config
        api_key, base_url = get_org_api_config(org.id)

        assert api_key == "test-api-key-123"
        assert base_url == "https://custom.api.com/v1/chat/completions"

    def test_get_org_api_config_with_default_base_url(self, temp_data_dir):
        """Test get_org_api_config uses default base URL when not specified."""
        # Create org with encrypted API config
        org_create = OrganizationCreate(name="Test Org")
        org = create_org(org_create, owner_id="user1")

        # Set encrypted API config without base_url
        encrypted_key = encrypt_value("test-api-key-123")
        org_updates = {"api_config": {"api_key": encrypted_key}}
        update_org(org.id, org_updates)

        # Get API config
        api_key, base_url = get_org_api_config(org.id)

        assert api_key == "test-api-key-123"
        assert base_url == "https://openrouter.ai/api/v1/chat/completions"

    def test_get_org_api_config_fallback_to_global_key(self, temp_data_dir):
        """Test get_org_api_config falls back to global OPENROUTER_API_KEY if org not configured."""
        # Create org without API config
        org_create = OrganizationCreate(name="Test Org")
        org = create_org(org_create, owner_id="user1")

        # Mock global OPENROUTER_API_KEY (it's imported from config inside the function)
        with patch("backend.config.OPENROUTER_API_KEY", "global-key-123"):
            api_key, base_url = get_org_api_config(org.id)

            assert api_key == "global-key-123"
            assert base_url == "https://openrouter.ai/api/v1/chat/completions"

    def test_get_org_api_config_org_not_found(self, temp_data_dir):
        """Test get_org_api_config raises ValueError when org doesn't exist."""
        with pytest.raises(ValueError, match="Organization not found"):
            get_org_api_config("non-existent-org-id")

    def test_get_org_api_config_no_api_key_configured(self, temp_data_dir):
        """Test get_org_api_config raises ValueError when no API key is configured."""
        # Create org without API config
        org_create = OrganizationCreate(name="Test Org")
        org = create_org(org_create, owner_id="user1")

        # Mock no global key (it's imported from config inside the function)
        with patch("backend.config.OPENROUTER_API_KEY", None):
            with pytest.raises(ValueError, match="LLM API Key not configured"):
                get_org_api_config(org.id)

    def test_get_org_api_config_decryption_error(self, temp_data_dir):
        """Test get_org_api_config handles decryption errors gracefully."""
        # Create org with invalid encrypted API config
        org_create = OrganizationCreate(name="Test Org")
        org = create_org(org_create, owner_id="user1")

        # Set invalid encrypted API config
        org_updates = {"api_config": {"api_key": "invalid-encrypted-data"}}
        update_org(org.id, org_updates)

        # Should raise ValueError on decryption failure
        with pytest.raises(ValueError, match="Failed to decrypt"):
            get_org_api_config(org.id)

    def test_update_org_success(self, temp_data_dir):
        """Test update_org successfully updates organization fields."""
        # Create org
        org_create = OrganizationCreate(name="Original Name")
        org = create_org(org_create, owner_id="user1")

        # Update org
        updates = {"name": "Updated Name", "settings": {"key": "value"}}
        updated_org = update_org(org.id, updates)

        assert updated_org is not None
        assert updated_org.name == "Updated Name"
        assert updated_org.settings == {"key": "value"}

        # Verify persistence
        retrieved = get_org(org.id)
        assert retrieved.name == "Updated Name"
        assert retrieved.settings == {"key": "value"}

    def test_update_org_not_found(self, temp_data_dir):
        """Test update_org returns None when org doesn't exist."""
        result = update_org("non-existent-org-id", {"name": "New Name"})
        assert result is None

    def test_update_org_partial_update(self, temp_data_dir):
        """Test update_org can update only specific fields."""
        # Create org
        org_create = OrganizationCreate(name="Test Org", owner_email="test@example.com")
        org = create_org(org_create, owner_id="user1")

        # Update only name
        updates = {"name": "New Name"}
        updated_org = update_org(org.id, updates)

        assert updated_org.name == "New Name"
        assert updated_org.owner_email == "test@example.com"  # Should remain unchanged

    def test_update_org_api_config(self, temp_data_dir):
        """Test update_org can update API config."""
        # Create org
        org_create = OrganizationCreate(name="Test Org")
        org = create_org(org_create, owner_id="user1")

        # Update API config
        encrypted_key = encrypt_value("new-api-key")
        updates = {
            "api_config": {
                "api_key": encrypted_key,
                "base_url": "https://new.api.com/v1",
            }
        }
        updated_org = update_org(org.id, updates)

        assert updated_org.api_config is not None
        assert updated_org.api_config["api_key"] == encrypted_key
        assert updated_org.api_config["base_url"] == "https://new.api.com/v1"

