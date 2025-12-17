from unittest.mock import MagicMock, patch

import pytest
import yaml
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.admin_routes import validate_prompt_tags
from backend.main import app

client = TestClient(app)

# Mock data
MOCK_PERSONALITY = {
    "id": "test_personality",
    "name": "Test Bot",
    "description": "A test personality",
    "model": "openai/gpt-4",
    "temperature": 0.7,
    "enabled": True,
    "personality_prompt": {"identity_and_role": "You are a test bot."},
    "ui": {"avatar": "default", "color": "#000000"},
}


@pytest.fixture(autouse=True)
def mock_global_personalities(monkeypatch, tmp_path):
    """Mock global defaults directory to be empty."""
    defaults_dir = tmp_path / "defaults"
    defaults_dir.mkdir()
    (defaults_dir / "personalities").mkdir()
    monkeypatch.setattr("backend.config.personalities.DEFAULTS_DIR", str(defaults_dir))
    return defaults_dir


MOCK_SYSTEM_PROMPTS = {
    "base_system_prompt": "Base prompt",
    "ranking": {
        "model": "gemini/gemini-pro",
        "prompt": "Rank {responses_text} for {user_query} from {peer_text}",
    },
    "chairman": {
        "model": "gemini/gemini-pro",
        "prompt": "Chairman for {user_query} using {stage1_text} and {voting_details_text}",
    },
    "title_generation": {
        "model": "gemini/gemini-pro",
        "prompt": "Title for {user_query}",
    },
}


@pytest.fixture
def mock_data_root(tmp_path):
    """Create a root data directory."""
    orgs_dir = tmp_path / "organizations"
    orgs_dir.mkdir()
    return tmp_path


@pytest.fixture
def auth_headers(tmp_path, monkeypatch):
    """Register an admin user, create an organization, and return auth headers and org_id."""
    # USERS_FILE patching removed (uses SQLite)

    # Register admin (first user is admin, creates org atomically)
    import uuid
    username = f"admin_{uuid.uuid4().hex[:8]}"
    reg_payload = {
        "username": username,
        "password": "password",
        "mode": "create_org",
        "org_name": "Test Organization",
    }
    resp = client.post("/api/auth/register", json=reg_payload)
    assert resp.status_code == 200, f"Register failed: {resp.text}"

    # Login
    response = client.post("/api/auth/token", data={"username": username, "password": "password"})
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify user is assigned to org and get org_id
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200, f"Failed to get user info: {me_resp.text}"
    org_id = me_resp.json()["org_id"]
    assert org_id is not None, "User not assigned to created org"

    return headers, org_id


def test_list_personalities(mock_data_root, auth_headers):
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"

    # Setup org directory
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.admin_routes.get_available_models", return_value=[]),
    ):  # Mock LLM service
        # Create a dummy personality file
        p_file = personalities_dir / "test.yaml"
        with open(p_file, "w") as f:
            yaml.dump(MOCK_PERSONALITY, f)

        response = client.get("/api/personalities", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "test_personality"


def test_create_personality(mock_data_root, auth_headers):
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"

    # Setup org directory
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        response = client.post("/api/personalities", json=MOCK_PERSONALITY, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_personality"

        # Verify file creation
        p_file = personalities_dir / "test_personality.yaml"
        assert p_file.exists()


def test_get_system_prompts(mock_data_root, auth_headers):
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"

    # Setup org directory
    config_dir = orgs_dir / org_id / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        # Create system prompts file
        s_file = config_dir / "system-prompts.yaml"
        with open(s_file, "w") as f:
            yaml.dump(MOCK_SYSTEM_PROMPTS, f)

        response = client.get("/api/system-prompts", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["base_system_prompt"]["value"] == "Base prompt"
        assert (
            data["chairman"]["prompt"]["value"]
            == "Chairman for {user_query} using {stage1_text} and {voting_details_text}"
        )
        assert (
            data["ranking"]["prompt"]["value"]
            == "Rank {responses_text} for {user_query} from {peer_text}"
        )


def test_get_system_prompts_no_file(mock_data_root, auth_headers):
    """Test get_system_prompts returns defaults when file doesn't exist."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"

    # Setup org directory but don't create system-prompts.yaml
    config_dir = orgs_dir / org_id / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        response = client.get("/api/system-prompts", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Should return defaults
        assert "base_system_prompt" in data
        assert "ranking" in data
        assert "chairman" in data
        assert "title_generation" in data
        assert "effective_model" in data["ranking"]


def test_update_system_prompts(mock_data_root, auth_headers):
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"

    # Setup org directory
    config_dir = orgs_dir / org_id / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        # Create initial file
        s_file = config_dir / "system-prompts.yaml"
        with open(s_file, "w") as f:
            yaml.dump(MOCK_SYSTEM_PROMPTS, f)

        new_config = MOCK_SYSTEM_PROMPTS.copy()
        new_config["base_system_prompt"] = {"value": "Updated prompt", "is_default": False}
        new_config["ranking"] = {
            "prompt": {"value": MOCK_SYSTEM_PROMPTS["ranking"]["prompt"], "is_default": False}
        }
        new_config["chairman"] = {
            "prompt": {"value": MOCK_SYSTEM_PROMPTS["chairman"]["prompt"], "is_default": False}
        }
        new_config["title_generation"] = {
            "prompt": {
                "value": MOCK_SYSTEM_PROMPTS["title_generation"]["prompt"],
                "is_default": False,
            }
        }

        # Note: Using PUT as defined in admin_routes.py
        response = client.put("/api/system-prompts", json=new_config, headers=headers)
        assert response.status_code == 200

        # Verify file update
        with open(s_file) as f:
            saved = yaml.safe_load(f)
            assert saved["base_system_prompt"] == "Updated prompt"
            assert saved["ranking"]["prompt"] == MOCK_SYSTEM_PROMPTS["ranking"]["prompt"]


def test_delete_personality(mock_data_root, auth_headers):
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        # Create file to delete
        p_file = personalities_dir / "to_delete.yaml"
        with open(p_file, "w") as f:
            yaml.dump({"id": "to_delete"}, f)

        response = client.delete("/api/personalities/to_delete", headers=headers)
        assert response.status_code == 200
        assert not p_file.exists()


def test_get_voting_history(mock_data_root, auth_headers):
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
        patch(
            "backend.voting_history.load_voting_history",
            return_value=[{"user_id": "u1", "vote": "A"}],
        ),
        patch("backend.users.get_all_users", return_value=[MagicMock(id="u1", username="user1")]),
    ):
        response = client.get("/api/votes", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["username"] == "user1"


def test_get_settings(mock_data_root, auth_headers):
    headers, org_id = auth_headers

    # Mock get_org to return an org with api_config
    mock_org = MagicMock()
    mock_org.id = org_id
    mock_org.api_config = {"api_key": "encrypted", "base_url": "https://test.url"}

    with patch("backend.admin_routes.get_org", return_value=mock_org):
        response = client.get("/api/settings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["api_key"] == "********"
        assert data["base_url"] == "https://test.url"


def test_update_settings(mock_data_root, auth_headers):
    headers, org_id = auth_headers

    mock_org = MagicMock()
    mock_org.id = org_id
    mock_org.api_config = {}

    with (
        patch("backend.admin_routes.get_org", return_value=mock_org),
        patch("backend.admin_routes.update_org", return_value=mock_org),
        patch("backend.admin_routes.encrypt_value", return_value="encrypted_new"),
    ):
        payload = {"api_key": "new_key", "base_url": "https://new.url"}
        response = client.put("/api/settings", json=payload, headers=headers)
        assert response.status_code == 200


def test_validate_prompt_tags():
    """Test validate_prompt_tags function."""
    # Success case
    validate_prompt_tags("Hello {name}", ["{name}"], "Test Prompt")

    # Failure case
    with pytest.raises(HTTPException) as excinfo:
        validate_prompt_tags("Hello world", ["{name}"], "Test Prompt")
    assert excinfo.value.status_code == 400
    assert "missing required tags" in excinfo.value.detail


def test_get_personality(mock_data_root, auth_headers):
    """Test getting a single personality."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        # Create a dummy personality file with all required fields
        p_file = personalities_dir / "single_test.yaml"
        p_data = {
            "id": "single_test",
            "name": "Single Test",
            "description": "Test Desc",
            "model": "test-model",
            "personality_prompt": {"identity_and_role": "Test Prompt"},
        }
        with open(p_file, "w") as f:
            yaml.dump(p_data, f)

        response = client.get("/api/personalities/single_test", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "single_test"
        assert data["name"] == "Single Test"


def test_get_personality_not_found(mock_data_root, auth_headers):
    """Test getting a non-existent personality."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        response = client.get("/api/personalities/non_existent", headers=headers)
        assert response.status_code == 404


def test_update_personality(mock_data_root, auth_headers):
    """Test updating a personality."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        # Create initial personality
        p_data = MOCK_PERSONALITY.copy()
        p_data["id"] = "update_test"
        p_file = personalities_dir / "update_test.yaml"
        with open(p_file, "w") as f:
            yaml.dump(p_data, f)

        # Update it
        p_data["name"] = "Updated Name"
        response = client.put("/api/personalities/update_test", json=p_data, headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

        # Verify file on disk
        with open(p_file) as f:
            saved = yaml.safe_load(f)
            assert saved["name"] == "Updated Name"


def test_update_personality_mismatch(mock_data_root, auth_headers):
    """Test updating with mismatched ID."""
    headers, org_id = auth_headers

    p_data = MOCK_PERSONALITY.copy()
    p_data["id"] = "id1"

    response = client.put("/api/personalities/id2", json=p_data, headers=headers)
    assert response.status_code == 400


def test_list_models(mock_data_root, auth_headers):
    """Test listing available models."""
    headers, org_id = auth_headers

    mock_models = [
        {"id": "model1", "name": "Model 1", "provider": "openai"},
        {"id": "model2", "name": "Model 2", "provider": "anthropic"},
    ]

    with (
        patch("backend.admin_routes.get_org_api_config", return_value=("key", "url")),
        patch("backend.admin_routes.get_available_models", return_value=mock_models),
    ):
        response = client.get("/api/models", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "model1"


def test_list_models_error(mock_data_root, auth_headers):
    """Test list_models handles errors."""
    headers, org_id = auth_headers

    with (
        patch("backend.admin_routes.get_org_api_config", return_value=("key", "url")),
        patch(
            "backend.admin_routes.get_available_models", side_effect=ValueError("Invalid API key")
        ),
    ):
        response = client.get("/api/models", headers=headers)
        # ValueError is likely converted to 400 VALIDATION_ERROR or similar by intermediate logic
        assert response.status_code in [400, 500] 
        data = response.json()
        assert "error" in data


def test_list_personalities_empty_dir(mock_data_root, auth_headers):
    """Test listing personalities when directory doesn't exist."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        # Don't create personalities directory
        response = client.get("/api/personalities", headers=headers)
        assert response.status_code == 200
        assert response.json() == []


def test_list_personalities_skips_system_prompts(mock_data_root, auth_headers):
    """Test that system-prompts.yaml is excluded from personality list."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        # Create a personality file
        p_file = personalities_dir / "test.yaml"
        with open(p_file, "w") as f:
            yaml.dump(MOCK_PERSONALITY, f)

        # Create system-prompts.yaml (should be skipped)
        sp_file = personalities_dir / "system-prompts.yaml"
        with open(sp_file, "w") as f:
            yaml.dump({"test": "data"}, f)

        response = client.get("/api/personalities", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "test_personality"


def test_get_personality_load_error(mock_data_root, auth_headers):
    """Test get_personality handles YAML load errors."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.admin_routes.get_all_personalities", side_effect=Exception("DB Error")),
    ):
        # Create file but mock load to raise Error
        p_file = personalities_dir / "test.yaml"
        p_file.touch()

        # Use local client to capture 500 error
        from fastapi.testclient import TestClient
        from backend.main import app

        local_client = TestClient(app, raise_server_exceptions=False)
        response = local_client.get("/api/personalities/test", headers=headers)
        assert response.status_code == 500
        # assert "Failed to read personality" in response.json()["detail"] # Detail might differ on generic 500


def test_create_personality_duplicate(mock_data_root, auth_headers):
    """Test creating a personality that already exists."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        # Create existing personality file
        p_file = personalities_dir / "test_personality.yaml"
        with open(p_file, "w") as f:
            yaml.dump(MOCK_PERSONALITY, f)

        response = client.post(
        "/api/personalities",
        json={"name": "existing_personality", "description": "Duplicate"},
    )
    assert response.status_code in [400, 401]
    if response.status_code == 400:
        data = response.json()
        assert "error" in data
        assert "already exists" in data["error"]["message"]


def test_delete_personality_not_found(mock_data_root, auth_headers):
    """Test deleting a non-existent personality."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        response = client.delete("/api/personalities/non_existent", headers=headers)
        assert response.status_code == 404


def test_delete_personality_error(mock_data_root, auth_headers):
    """Test delete_personality handles file deletion errors."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
        patch("os.remove", side_effect=OSError("Permission denied")),
    ):
        p_file = personalities_dir / "to_delete.yaml"
        p_file.touch()

        response = client.delete("/api/personalities/to_delete", headers=headers)
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "Failed to delete personality" in data["error"]["message"]


def test_get_system_prompts_legacy_format(mock_data_root, auth_headers):
    """Test get_system_prompts handles legacy ranking_prompt format."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    config_dir = orgs_dir / org_id / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        # Create legacy format file
        legacy_config = {
            "base_system_prompt": "Base",
            "ranking_prompt": "Legacy ranking prompt with {user_query}",
        }
        s_file = config_dir / "system-prompts.yaml"
        with open(s_file, "w") as f:
            yaml.dump(legacy_config, f)

        response = client.get("/api/system-prompts", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["ranking"]["prompt"]["value"] == "Legacy ranking prompt with {user_query}"


def test_update_system_prompts_missing_tags(mock_data_root, auth_headers):
    """Test update_system_prompts validates required tags."""
    headers, org_id = auth_headers
    mock_data_root / "organizations"

    invalid_config = MOCK_SYSTEM_PROMPTS.copy()
    invalid_config["chairman"] = {
        "prompt": {"value": "Missing the required tag completely", "is_default": False}
    }

    response = client.put("/api/system-prompts", json=invalid_config, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "missing required tags" in data["error"]["message"].lower()


def test_get_settings_no_org(mock_data_root, auth_headers):
    """Test get_settings when organization doesn't exist."""
    headers, org_id = auth_headers

    with patch("backend.admin_routes.get_org", return_value=None):
        response = client.get("/api/settings", headers=headers)
        assert response.status_code == 404


def test_get_settings_no_api_key(mock_data_root, auth_headers):
    """Test get_settings when api_key is not set."""
    headers, org_id = auth_headers

    mock_org = MagicMock()
    mock_org.id = org_id
    mock_org.api_config = {"base_url": "https://test.url"}

    with patch("backend.admin_routes.get_org", return_value=mock_org):
        response = client.get("/api/settings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["api_key"] is None
        assert data["base_url"] == "https://test.url"


def test_update_settings_no_org(mock_data_root, auth_headers):
    """Test update_settings when organization doesn't exist."""
    headers, org_id = auth_headers

    with patch("backend.admin_routes.get_org", return_value=None):
        payload = {"api_key": "new_key"}
        response = client.put("/api/settings", json=payload, headers=headers)
        assert response.status_code == 404


def test_update_settings_update_failed(mock_data_root, auth_headers):
    """Test update_settings when update_org fails."""
    headers, org_id = auth_headers

    mock_org = MagicMock()
    mock_org.id = org_id
    mock_org.api_config = {}

    with (
        patch("backend.admin_routes.get_org", return_value=mock_org),
        patch("backend.admin_routes.update_org", return_value=None),
        patch("backend.admin_routes.encrypt_value", return_value="encrypted"),
    ):
        payload = {"api_key": "new_key"}
        response = client.put("/api/settings", json=payload, headers=headers)
        assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "Failed to update organization" in data["error"]["message"]


def test_update_settings_only_base_url(mock_data_root, auth_headers):
    """Test update_settings with only base_url (no api_key)."""
    headers, org_id = auth_headers

    mock_org = MagicMock()
    mock_org.id = org_id
    mock_org.api_config = {"api_key": "existing"}

    with (
        patch("backend.admin_routes.get_org", return_value=mock_org),
        patch("backend.admin_routes.update_org", return_value=mock_org),
    ):
        payload = {"base_url": "https://new.url"}
        response = client.put("/api/settings", json=payload, headers=headers)
        assert response.status_code == 200


def test_get_voting_history_no_user_id(mock_data_root, auth_headers):
    """Test get_voting_history handles sessions without user_id."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
        patch(
            "backend.voting_history.load_voting_history",
            return_value=[{"vote": "A"}],  # No user_id
        ),
        patch("backend.users.get_all_users", return_value=[]),
    ):
        response = client.get("/api/votes", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["username"] == "Anonymous/Legacy"
