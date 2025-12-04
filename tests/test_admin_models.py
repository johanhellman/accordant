from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.admin_routes import list_models


@pytest.mark.asyncio
async def test_list_models_success():
    # Mock current user
    mock_user = MagicMock()
    mock_user.org_id = "org-123"

    # Mock get_org_api_config
    with patch("backend.admin_routes.get_org_api_config") as mock_get_config:
        mock_get_config.return_value = ("fake-key", "https://fake.url/v1")

        # Mock get_available_models
        with patch(
            "backend.admin_routes.get_available_models", new_callable=AsyncMock
        ) as mock_get_models:
            mock_get_models.return_value = [{"id": "gpt-4", "name": "GPT-4", "provider": "openai"}]

            # Call the function
            result = await list_models(current_user=mock_user)

            # Assertions
            assert len(result) == 1
            assert result[0]["id"] == "gpt-4"
            mock_get_config.assert_called_once_with("org-123")
            mock_get_models.assert_called_once_with("fake-key", "https://fake.url/v1")


@pytest.mark.asyncio
async def test_list_models_no_config():
    # Mock current user
    mock_user = MagicMock()
    mock_user.org_id = "org-123"

    # Mock get_org_api_config to raise ValueError
    with patch("backend.admin_routes.get_org_api_config") as mock_get_config:
        mock_get_config.side_effect = ValueError("No API key configured")

        # Call the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await list_models(current_user=mock_user)

        assert exc_info.value.status_code == 400
        assert "No API key configured" in str(exc_info.value.detail)
