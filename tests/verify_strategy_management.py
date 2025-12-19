from unittest.mock import MagicMock, patch

import pytest

from backend.config_routes import (
    CreateStrategyRequest,
    create_strategy,
    get_strategy,
    list_strategies,
)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_admin():
    user = MagicMock()
    user.is_admin = True
    user.org_id = "org1"
    return user


@pytest.mark.asyncio
async def test_create_and_get_strategy(mock_db, mock_admin):
    # Mock Service calls via the route logic (which calls service)
    # Since routes call Service static methods, we can mock Service or just mock DB interactions
    # But routes call ConsensusStrategyService.create_custom_strategy directly.

    # Let's mock the service methods to isolate API logic
    with patch("backend.config_routes.ConsensusStrategyService") as MockService:
        # 1. Create
        req = CreateStrategyRequest(
            id="new_strat", display_name="New", description="Desc", prompt_content="Content"
        )
        expected_resp = {
            "id": "new_strat",
            "display_name": "New",
            "description": "Desc",
            "prompt_content": "Content",
            "source": "custom",
            "is_editable": True,
        }
        MockService.create_custom_strategy.return_value = expected_resp

        resp = await create_strategy(req, mock_admin, mock_db)
        assert resp["id"] == "new_strat"
        MockService.create_custom_strategy.assert_called_with(
            mock_db, "new_strat", "New", "Content", "Desc"
        )

        # 2. Get
        MockService.get_strategy.return_value = expected_resp
        got = await get_strategy("new_strat", mock_admin, mock_db)
        assert got["id"] == "new_strat"


@pytest.mark.asyncio
async def test_list_strategies_api(mock_db, mock_admin):
    with patch("backend.config_routes.ConsensusStrategyService") as MockService:
        MockService.get_all_strategies.return_value = [
            {
                "id": "s1",
                "display_name": "S1",
                "source": "system",
                "prompt_content": "P1",
                "is_editable": False,
                "description": "D1",
            }
        ]

        resp = await list_strategies(mock_admin, mock_db)
        assert len(resp) == 1
        assert resp[0]["id"] == "s1"
