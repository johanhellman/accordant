from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.llm_service import get_available_models
from backend.main import send_message
from backend.schema import SendMessageRequest
from backend.streaming import run_council_generator


@pytest.mark.asyncio
async def test_stale_conversation_snapshot_main():
    """
    Test that run_full_council receives the updated message list including the new user message.
    """
    # Mock dependencies
    mock_user = MagicMock()
    mock_user.id = "user1"
    mock_user.org_id = "org1"

    mock_conversation = {
        "id": "conv1",
        "user_id": "user1",
        "messages": [{"role": "assistant", "content": "Hello"}],
    }

    with (
        patch("backend.main.storage.get_conversation", return_value=mock_conversation),
        patch("backend.main.storage.add_user_message") as mock_add_msg,
        patch("backend.main.get_org_api_config", return_value=("key", "url")),
        patch("backend.main.run_full_council", new_callable=AsyncMock) as mock_run_council,
        patch("backend.main.record_votes"),
        patch("backend.main.storage.add_assistant_message"),
    ):
        mock_run_council.return_value = ([], [], {}, {"label_to_model": {}})

        mock_request = MagicMock()
        await send_message(
            mock_request,
            "conv1",
            SendMessageRequest(content="New User Msg"),
            current_user=mock_user,
        )

        # Verify add_user_message was called
        mock_add_msg.assert_called_once()

        # Verify run_full_council was called with the UPDATED messages list
        # The bug is that it's currently called with the OLD list
        call_args = mock_run_council.call_args
        messages_arg = call_args[0][1]

        # If the bug exists, this assertion will fail because messages_arg will only have 1 message
        # We expect 2 messages: existing assistant msg + new user msg
        assert len(messages_arg) == 2, f"Expected 2 messages, got {len(messages_arg)}"
        assert messages_arg[-1]["content"] == "New User Msg"


@pytest.mark.asyncio
async def test_stale_conversation_snapshot_streaming():
    """
    Test that streaming council receives the updated message list.
    """
    mock_conversation = {
        "id": "conv1",
        "user_id": "user1",
        "messages": [{"role": "assistant", "content": "Hello"}],
    }

    # Reset singleton to ensure fresh state using patch
    # We patch the class attribute on the *class itself* in the module
    with (
        patch("backend.streaming.CouncilManager._instance", None),
        patch("backend.streaming.run_council_cycle") as mock_run_cycle,
        patch("backend.streaming.update_conversation_status"),
        patch("backend.streaming.add_user_message"),
        patch("backend.streaming.record_votes"),
        patch("backend.streaming.add_assistant_message"),
        patch("backend.streaming.generate_conversation_title", new_callable=AsyncMock),
    ):

        async def mock_generator(*args, **kwargs):
            if False:
                yield None

        mock_run_cycle.side_effect = mock_generator
        async for _ in run_council_generator(
            "conv1", "New User Msg", mock_conversation, "org1", "key", "url"
        ):
            pass

        # Verify run_council_cycle was called with updated messages
        if mock_run_cycle.call_args:
            messages_arg = mock_run_cycle.call_args[0][1]
            assert len(messages_arg) == 2, f"Expected 2 messages, got {len(messages_arg)}"
            assert messages_arg[-1]["content"] == "New User Msg"
        else:
            pytest.fail("run_council_cycle was not called")


@pytest.mark.asyncio
async def test_model_cache_collision():
    """
    Test that models are cached separately for different base_urls.
    """
    # Reset cache
    import backend.llm_service

    backend.llm_service._MODELS_CACHE = {}
    # backend.llm_service._MODELS_CACHE_TIMESTAMP = None # Removed in new impl

    with patch("httpx.AsyncClient.get") as mock_get:
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "model1"}]}
        mock_get.return_value = mock_response

        # Call with Org A
        await get_available_models("key1", "https://org-a.com/v1")

        # Call with Org B
        mock_response.json.return_value = {"data": [{"id": "model2"}]}
        await get_available_models("key2", "https://org-b.com/v1")

        # If bug exists, the second call might return cached result from Org A (model1)
        # or overwrite the cache globally.
        # Ideally, we want to verify that we can retrieve Org A's models again without re-fetching if valid,
        # BUT crucially, that Org B got its OWN models.

        # However, with the current global list implementation, the second call will likely hit the cache
        # (if we don't clear it) and return Org A's models if the TTL hasn't expired.
        # Or if we force a fetch, it overwrites the global cache.

        # Let's inspect the cache directly to see if it supports multiple keys.
        # The current implementation is a List, so it definitely doesn't support multiple keys.
        # So we can just assert that the cache structure is capable of holding multiple orgs,
        # which it currently IS NOT.

        # But for a behavioral test:
        # 1. Fetch Org A -> Cache populated with Model 1
        # 2. Fetch Org B -> Should return Model 2 (but currently returns Model 1 because of cache hit)

        # We need to manually reset the timestamp to force a fetch for Org B to prove the collision?
        # No, the bug IS that it returns the cached result.

        # Let's verify that the second call returns Model 2.
        # In the buggy version, it will return Model 1 because it hits the cache.

        res_b = await get_available_models("key2", "https://org-b.com/v1")
        assert res_b[0]["id"] == "model2", f"Expected model2, got {res_b[0]['id']}"
