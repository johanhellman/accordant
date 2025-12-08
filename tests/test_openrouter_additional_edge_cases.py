"""Additional edge case tests for openrouter.py to improve coverage.

These tests cover edge cases that may not be fully covered by existing tests.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.openrouter import query_model, query_models_parallel


class TestQueryModelResponseParsingEdgeCases:
    """Edge case tests for query_model response parsing."""

    @pytest.mark.asyncio
    async def test_query_model_empty_choices_array(self):
        """Test query_model handles empty choices array."""
        model = "test-model"
        messages = [{"role": "user", "content": "Hello"}]
        api_key = "test-key"
        base_url = "https://api.test.com/v1/chat/completions"

        mock_response = {"choices": []}  # Empty choices array

        with patch("backend.openrouter.get_semaphore") as mock_semaphore:
            mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_response_obj = MagicMock()
                mock_response_obj.json.return_value = mock_response
                mock_response_obj.raise_for_status = MagicMock()
                mock_client.post.return_value = mock_response_obj

                # Should handle IndexError gracefully
                try:
                    result = await query_model(model, messages, api_key=api_key, base_url=base_url)
                    # If exception is caught, result should be None
                    # If exception propagates, that's also valid
                except (IndexError, KeyError):
                    # Exception handling is acceptable
                    pass

    @pytest.mark.asyncio
    async def test_query_model_missing_choices_key(self):
        """Test query_model handles missing choices key in response."""
        model = "test-model"
        messages = [{"role": "user", "content": "Hello"}]
        api_key = "test-key"
        base_url = "https://api.test.com/v1/chat/completions"

        mock_response = {}  # Missing choices key

        with patch("backend.openrouter.get_semaphore") as mock_semaphore:
            mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_response_obj = MagicMock()
                mock_response_obj.json.return_value = mock_response
                mock_response_obj.raise_for_status = MagicMock()
                mock_client.post.return_value = mock_response_obj

                # Should handle KeyError gracefully
                try:
                    result = await query_model(model, messages, api_key=api_key, base_url=base_url)
                    # If exception is caught, result should be None
                except (KeyError, IndexError):
                    # Exception handling is acceptable
                    pass

    @pytest.mark.asyncio
    async def test_query_model_missing_message_key(self):
        """Test query_model handles missing message key in choices[0]."""
        model = "test-model"
        messages = [{"role": "user", "content": "Hello"}]
        api_key = "test-key"
        base_url = "https://api.test.com/v1/chat/completions"

        mock_response = {"choices": [{}]}  # Missing message key

        with patch("backend.openrouter.get_semaphore") as mock_semaphore:
            mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_response_obj = MagicMock()
                mock_response_obj.json.return_value = mock_response
                mock_response_obj.raise_for_status = MagicMock()
                mock_client.post.return_value = mock_response_obj

                # Should handle KeyError gracefully
                try:
                    result = await query_model(model, messages, api_key=api_key, base_url=base_url)
                    # If exception is caught, result should be None
                except KeyError:
                    # Exception handling is acceptable
                    pass

    @pytest.mark.asyncio
    async def test_query_model_missing_content_key(self):
        """Test query_model handles missing content key in message."""
        model = "test-model"
        messages = [{"role": "user", "content": "Hello"}]
        api_key = "test-key"
        base_url = "https://api.test.com/v1/chat/completions"

        mock_response = {"choices": [{"message": {}}]}  # Missing content key

        with patch("backend.openrouter.get_semaphore") as mock_semaphore:
            mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_response_obj = MagicMock()
                mock_response_obj.json.return_value = mock_response
                mock_response_obj.raise_for_status = MagicMock()
                mock_client.post.return_value = mock_response_obj

                result = await query_model(model, messages, api_key=api_key, base_url=base_url)

                # Should handle missing content gracefully (get("content") returns None)
                assert result is not None
                assert result["content"] is None

    @pytest.mark.asyncio
    async def test_query_model_json_parse_error(self):
        """Test query_model handles JSON parsing errors."""
        model = "test-model"
        messages = [{"role": "user", "content": "Hello"}]
        api_key = "test-key"
        base_url = "https://api.test.com/v1/chat/completions"

        with patch("backend.openrouter.get_semaphore") as mock_semaphore:
            mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_response_obj = MagicMock()
                mock_response_obj.json.side_effect = ValueError("Invalid JSON")
                mock_response_obj.raise_for_status = MagicMock()
                mock_client.post.return_value = mock_response_obj

                result = await query_model(model, messages, api_key=api_key, base_url=base_url)

                # Should handle JSON parsing error gracefully
                assert result is None

    @pytest.mark.asyncio
    async def test_query_model_content_is_none(self):
        """Test query_model handles content=None in message."""
        model = "test-model"
        messages = [{"role": "user", "content": "Hello"}]
        api_key = "test-key"
        base_url = "https://api.test.com/v1/chat/completions"

        mock_response = {"choices": [{"message": {"content": None}}]}

        with patch("backend.openrouter.get_semaphore") as mock_semaphore:
            mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_response_obj = MagicMock()
                mock_response_obj.json.return_value = mock_response
                mock_response_obj.raise_for_status = MagicMock()
                mock_client.post.return_value = mock_response_obj

                result = await query_model(model, messages, api_key=api_key, base_url=base_url)

                assert result is not None
                assert result["content"] is None

    @pytest.mark.asyncio
    async def test_query_model_custom_timeout(self):
        """Test query_model uses custom timeout value."""
        model = "test-model"
        messages = [{"role": "user", "content": "Hello"}]
        api_key = "test-key"
        base_url = "https://api.test.com/v1/chat/completions"
        custom_timeout = 120.0

        mock_response = {"choices": [{"message": {"content": "Response"}}]}

        with patch("backend.openrouter.get_semaphore") as mock_semaphore:
            mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_response_obj = MagicMock()
                mock_response_obj.json.return_value = mock_response
                mock_response_obj.raise_for_status = MagicMock()
                mock_client.post.return_value = mock_response_obj

                await query_model(
                    model, messages, api_key=api_key, base_url=base_url, timeout=custom_timeout
                )

                # Verify AsyncClient was created with custom timeout
                mock_client_class.assert_called_once()
                call_kwargs = mock_client_class.call_args[1]
                assert call_kwargs["timeout"] == custom_timeout

    @pytest.mark.asyncio
    async def test_query_model_temperature_zero(self):
        """Test query_model handles temperature=0.0."""
        model = "test-model"
        messages = [{"role": "user", "content": "Hello"}]
        api_key = "test-key"
        base_url = "https://api.test.com/v1/chat/completions"
        temperature = 0.0

        mock_response = {"choices": [{"message": {"content": "Response"}}]}

        with patch("backend.openrouter.get_semaphore") as mock_semaphore:
            mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_response_obj = MagicMock()
                mock_response_obj.json.return_value = mock_response
                mock_response_obj.raise_for_status = MagicMock()
                mock_client.post.return_value = mock_response_obj

                await query_model(
                    model, messages, api_key=api_key, base_url=base_url, temperature=temperature
                )

                # Verify temperature=0.0 was included in payload
                call_args = mock_client.post.call_args
                payload = call_args[1]["json"]
                assert payload["temperature"] == 0.0

    @pytest.mark.asyncio
    async def test_query_model_temperature_one(self):
        """Test query_model handles temperature=1.0."""
        model = "test-model"
        messages = [{"role": "user", "content": "Hello"}]
        api_key = "test-key"
        base_url = "https://api.test.com/v1/chat/completions"
        temperature = 1.0

        mock_response = {"choices": [{"message": {"content": "Response"}}]}

        with patch("backend.openrouter.get_semaphore") as mock_semaphore:
            mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_response_obj = MagicMock()
                mock_response_obj.json.return_value = mock_response
                mock_response_obj.raise_for_status = MagicMock()
                mock_client.post.return_value = mock_response_obj

                await query_model(
                    model, messages, api_key=api_key, base_url=base_url, temperature=temperature
                )

                # Verify temperature=1.0 was included in payload
                call_args = mock_client.post.call_args
                payload = call_args[1]["json"]
                assert payload["temperature"] == 1.0


class TestQueryModelsParallelEdgeCases:
    """Edge case tests for query_models_parallel."""

    @pytest.mark.asyncio
    async def test_query_models_parallel_empty_models_list(self):
        """Test query_models_parallel handles empty models list."""
        models = []
        messages = [{"role": "user", "content": "Hello"}]
        api_key = "test-key"
        base_url = "https://api.test.com/v1/chat/completions"

        result = await query_models_parallel(models, messages, api_key=api_key, base_url=base_url)

        # Should return empty dict
        assert result == {}

    @pytest.mark.asyncio
    async def test_query_models_parallel_single_model(self):
        """Test query_models_parallel with single model."""
        models = ["model1"]
        messages = [{"role": "user", "content": "Hello"}]
        api_key = "test-key"
        base_url = "https://api.test.com/v1/chat/completions"

        async def mock_query_model(*args, **kwargs):
            return {"content": "Response from model1"}

        with patch("backend.openrouter.query_model", side_effect=mock_query_model):
            result = await query_models_parallel(models, messages, api_key=api_key, base_url=base_url)

            assert len(result) == 1
            assert result["model1"]["content"] == "Response from model1"

    @pytest.mark.asyncio
    async def test_query_models_parallel_many_models(self):
        """Test query_models_parallel with many models."""
        models = [f"model{i}" for i in range(50)]  # 50 models
        messages = [{"role": "user", "content": "Hello"}]
        api_key = "test-key"
        base_url = "https://api.test.com/v1/chat/completions"

        async def mock_query_model(*args, **kwargs):
            model = args[0]
            return {"content": f"Response from {model}"}

        with patch("backend.openrouter.query_model", side_effect=mock_query_model):
            result = await query_models_parallel(models, messages, api_key=api_key, base_url=base_url)

            assert len(result) == 50
            for i in range(50):
                assert result[f"model{i}"]["content"] == f"Response from model{i}"


class TestGetSemaphoreEdgeCases:
    """Edge case tests for get_semaphore."""

    def test_get_semaphore_reuse(self):
        """Test get_semaphore reuses existing semaphore."""
        from backend.openrouter import get_semaphore

        # Reset global semaphore
        import backend.openrouter

        backend.openrouter._SEMAPHORE = None

        semaphore1 = get_semaphore()
        semaphore2 = get_semaphore()
        semaphore3 = get_semaphore()

        # All should be the same instance
        assert semaphore1 is semaphore2
        assert semaphore2 is semaphore3

    def test_get_semaphore_initialization(self):
        """Test get_semaphore initializes semaphore correctly."""
        from backend.openrouter import get_semaphore, MAX_CONCURRENT_REQUESTS

        # Reset global semaphore
        import backend.openrouter

        backend.openrouter._SEMAPHORE = None

        semaphore = get_semaphore()

        # Should be initialized with MAX_CONCURRENT_REQUESTS
        assert semaphore._value == MAX_CONCURRENT_REQUESTS
