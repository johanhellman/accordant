from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.auth import get_current_user
from backend.main import app
from backend.models import User

client = TestClient(app)


# Mock Auth
@pytest.fixture
def mock_auth():
    user = User(
        id="user1", username="testuser", is_admin=True, is_instance_admin=False, org_id="org1"
    )
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)


# Mock DB Session
@pytest.fixture
def mock_db_session():
    # We need to override the dependency used in the router: get_org_session
    # Ideally import it from the router module or main if re-exported
    from backend.config_routes import get_org_session

    session = MagicMock()
    app.dependency_overrides[get_org_session] = lambda: session
    yield session
    app.dependency_overrides.pop(get_org_session, None)


def test_list_packs(mock_auth, mock_db_session):
    with patch(
        "backend.config.packs.PackService.get_all_packs",
        return_value=[
            {
                "id": "sys",
                "display_name": "System",
                "is_system": True,
                "source": "system",
                "description": "desc",
                "created_at": None,
                "config": {"personalities": [], "consensus_strategy": None, "system_prompts": {}},
            }
        ],
    ):
        response = client.get("/api/config/packs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "sys"


def test_create_pack(mock_auth, mock_db_session):
    payload = {
        "display_name": "New Pack",
        "description": "Desc",
        "config": {"personalities": ["p1"], "consensus_strategy": "s1", "system_prompts": {}},
    }

    with patch(
        "backend.config.packs.PackService.create_custom_pack",
        return_value={
            "id": "new",
            "display_name": "New Pack",
            "description": "Desc",
            "is_system": False,
            "source": "custom",
            "config": payload["config"],
            "created_at": None,
        },
    ):
        response = client.post("/api/config/packs", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == "new"


def test_apply_pack(mock_auth, mock_db_session):
    with patch("backend.config.packs.PackService.apply_pack", return_value={"status": "ok"}):
        response = client.post("/api/config/packs/p1/apply")
        assert response.status_code == 200
        assert response.json()["status"] == "success"


def test_get_active_config(mock_auth, mock_db_session):
    with patch(
        "backend.config.packs.PackService.get_active_configuration",
        return_value={
            "active_pack_id": "p1",
            "personalities": ["a"],
            "strategy_id": "s",
            "system_prompts": {},
        },
    ):
        response = client.get("/api/config/active")
        assert response.status_code == 200
        assert response.json()["active_pack_id"] == "p1"


def test_list_strategies(mock_auth):
    with patch(
        "backend.config_routes.get_available_consensus_strategies",
        return_value=["strat1", "strat2"],
    ):
        response = client.get("/api/config/strategies")
        assert response.status_code == 200
        assert response.json() == ["strat1", "strat2"]
