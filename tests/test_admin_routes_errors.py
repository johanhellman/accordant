from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app, raise_server_exceptions=False)


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

    # Register admin (first user is admin)
    client.post(
        "/api/auth/register",
        json={
            "username": "admin",
            "password": "password",
            "mode": "create_org",
            "org_name": "Admin Org",
        },
    )

    # Login
    response = client.post("/api/auth/token", data={"username": "admin", "password": "password"})
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create organization (user must create/join org after registration)
    org_resp = client.post(
        "/api/organizations/",
        json={"name": "Test Organization", "owner_email": "admin@test.com"},
        headers=headers,
    )
    assert org_resp.status_code == 200, f"Failed to create org: {org_resp.text}"
    org_id = org_resp.json()["id"]

    # Verify user is assigned to org
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200, f"Failed to get user info: {me_resp.text}"
    assert me_resp.json()["org_id"] == org_id, "User not assigned to created org"

    return headers, org_id


def test_create_personality_exists(auth_headers, mock_data_root):
    """Test creating a personality that already exists."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        # Create the file first
        p_file = personalities_dir / "test.yaml"
        p_file.touch()

        response = client.post(
            "/api/personalities",
            json={
                "id": "test",
                "name": "Test",
                "description": "Desc",
                "model": "model",
                "personality_prompt": {"identity_and_role": "prompt"},
            },
            headers=headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


def test_get_personality_not_found(auth_headers, mock_data_root):
    """Test getting a non-existent personality."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        response = client.get("/api/personalities/test", headers=headers)
        assert response.status_code == 404


def test_delete_personality_not_found(auth_headers, mock_data_root):
    """Test deleting a non-existent personality."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        response = client.delete("/api/personalities/test", headers=headers)
        assert response.status_code == 404


def test_update_personality_mismatch(auth_headers, mock_data_root):
    """Test updating a personality with ID mismatch."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        response = client.put(
            "/api/personalities/test",
            json={
                "id": "other",
                "name": "Test",
                "description": "Desc",
                "model": "model",
                "personality_prompt": {"identity_and_role": "prompt"},
            },
            headers=headers,
        )
        assert response.status_code == 400
        assert "ID mismatch" in response.json()["detail"]


def test_create_personality_file_error(auth_headers, mock_data_root):
    """Test file I/O error during creation."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.admin_routes.yaml.dump", side_effect=Exception("YAML error")),
    ):
        response = client.post(
            "/api/personalities",
            json={
                "id": "test",
                "name": "Test",
                "description": "Desc",
                "model": "model",
                "personality_prompt": {"identity_and_role": "prompt"},
            },
            headers=headers,
        )
        assert response.status_code == 500
        assert "Failed to save configuration" in response.json()["detail"]


def test_get_personality_read_error(auth_headers, mock_data_root):
    """Test file I/O error during read."""
    headers, org_id = auth_headers
    orgs_dir = mock_data_root / "organizations"
    personalities_dir = orgs_dir / org_id / "personalities"
    personalities_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch("backend.config.personalities.ORGS_DATA_DIR", str(orgs_dir)),
        patch("backend.organizations.ORGS_DATA_DIR", str(orgs_dir)),
    ):
        # Create file so exists check passes
        p_file = personalities_dir / "test.yaml"
        p_file.touch()

        # Patch yaml.safe_load to raise exception
        with patch("backend.admin_routes.yaml.safe_load", side_effect=Exception("YAML error")):
            response = client.get("/api/personalities/test", headers=headers)
            assert response.status_code == 404
            # assert "Failed to read personality" in response.json()["detail"]
