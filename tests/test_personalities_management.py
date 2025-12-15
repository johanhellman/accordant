from unittest.mock import patch

import pytest

# We need a proper app to wrap the router for TestClient
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Assuming main app is importable as `app` from `main` or similar.
# Since I don't see `main.py` in recent file views, I'll assume standard structure or mock the router.
# But for integration tests, I need the app.
# Let's check `backend/main.py` first to be sure, or just rely on router testing if I can't start full app.
# Actually, I can search for where `app` is defined. Usually `backend/main.py`.
# I will write a test that mocks the filesystem calls to avoid messing with real data
# inside `tests/test_personalities.py`.
from backend.admin_routes import router
from backend.users import User

test_app = FastAPI()
test_app.include_router(router)

client = TestClient(test_app)


# Mock User Dependencies
async def mock_get_current_admin_user():
    return User(
        id="admin",
        username="admin",
        role="admin",
        org_id="test-org",
        is_instance_admin=False,
        password_hash="hash",
    )


async def mock_get_current_instance_admin():
    # Instance admin has org_id="test-org" (or system org) but is_instance_admin=True
    return User(
        id="sysadmin",
        username="sysadmin",
        role="admin",
        org_id="test-org",
        is_instance_admin=True,
        password_hash="hash",
    )


# test_app.dependency_overrides[router.dependencies[0]] = mock_get_current_admin_user # Removed as it causes IndexError if no deps

# Let's override purely by patching the auth functions where used in routes
from backend import admin_routes


@pytest.fixture
def mock_fs(tmp_path):
    # Setup mock directories
    org_dir = tmp_path / "data" / "organizations" / "test-org" / "personalities"
    org_dir.mkdir(parents=True)
    defaults_dir = tmp_path / "data" / "defaults" / "personalities"
    defaults_dir.mkdir(parents=True)

    # Mock helpers in config
    with (
        patch("backend.config.personalities.get_org_personalities_dir", return_value=str(org_dir)),
        patch("backend.admin_routes.get_org_personalities_dir", return_value=str(org_dir)),
        patch("backend.config.personalities.DEFAULTS_DIR", str(tmp_path / "data" / "defaults")),
        patch("backend.admin_routes.DEFAULTS_DIR", str(tmp_path / "data" / "defaults")),
    ):
        yield org_dir, defaults_dir


def test_list_personalities_merges_defaults(mock_fs):
    org_dir, defaults_dir = mock_fs

    # Create Default
    (defaults_dir / "default1.yaml").write_text(
        "id: default1\nname: Default 1\ndescription: Desc\nmodel: gpt-4\nenabled: true\npersonality_prompt: {}"
    )

    # Create Custom
    (org_dir / "custom1.yaml").write_text(
        "id: custom1\nname: Custom 1\ndescription: Desc custom\nmodel: gpt-4\nenabled: true\npersonality_prompt: {}"
    )

    # Override Default (Shadow)
    (org_dir / "default1.yaml").write_text(
        "id: default1\nname: Default 1 Shadowed\ndescription: Desc shadow\nmodel: gpt-4\nenabled: true\npersonality_prompt: {}"
    )

    # Mock Auth as Admin
    test_app.dependency_overrides[admin_routes.get_current_admin_user] = mock_get_current_admin_user

    response = client.get("/api/personalities")
    assert response.status_code == 200
    data = response.json()

    ids = {p["id"]: p for p in data}
    assert "default1" in ids
    assert "custom1" in ids

    # Verify Shadowing
    assert ids["default1"]["name"] == "Default 1 Shadowed"
    assert ids["default1"]["source"] == "custom"  # Since it exists in org dir

    assert ids["custom1"]["source"] == "custom"


def test_list_defaults_as_instance_admin(mock_fs):
    org_dir, defaults_dir = mock_fs

    # Create Default
    (defaults_dir / "sys1.yaml").write_text(
        "id: sys1\nname: System 1\ndescription: Desc sys\nmodel: gpt-4\nenabled: true\npersonality_prompt: {}"
    )

    # Mock Auth as Instance Admin
    test_app.dependency_overrides[admin_routes.get_current_instance_admin] = (
        mock_get_current_instance_admin
    )

    response = client.get("/api/defaults/personalities")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == "sys1"
    assert data[0]["source"] == "system"


def test_create_default_personality(mock_fs):
    org_dir, defaults_dir = mock_fs
    test_app.dependency_overrides[admin_routes.get_current_instance_admin] = (
        mock_get_current_instance_admin
    )

    new_p = {
        "id": "new_sys_p",
        "name": "New System P",
        "description": "Desc",
        "model": "gpt-4",
        "personality_prompt": {"ROLE": "You are a system."},
    }

    response = client.post("/api/defaults/personalities", json=new_p)
    assert response.status_code == 200

    saved_file = defaults_dir / "new_sys_p.yaml"
    assert saved_file.exists()
    assert "New System P" in saved_file.read_text()
