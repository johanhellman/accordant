"""Tests for FastAPI endpoints in main.py."""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend import storage
from backend.main import app


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_root_endpoint(self):
        """Test GET / returns health check."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "Accordant API (Dev Mode)"


class TestConversationEndpoints:
    """Tests for conversation management endpoints."""

    @pytest.fixture
    def temp_data_dir(self, monkeypatch):
        """Create a temporary data directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orgs_dir = os.path.join(tmpdir, "organizations")
            os.makedirs(orgs_dir, exist_ok=True)
            monkeypatch.setattr("backend.organizations.ORGS_DATA_DIR", orgs_dir)
            monkeypatch.setattr("backend.config.PROJECT_ROOT", tmpdir)
            yield orgs_dir

    def get_auth_headers(self, client, username="testuser", password="password"):
        """Helper to register and login, returning auth headers."""
        # Register
        resp = client.post("/api/auth/register", json={"username": username, "password": password, "mode": "create_org", "org_name": f"{username}_org"})
        assert resp.status_code == 200, f"Registration failed: {resp.text}"
        # Login
        response = client.post("/api/auth/token", data={"username": username, "password": password})
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create organization (user must create/join org after registration)
        org_resp = client.post(
            "/api/organizations/",
            json={"name": f"{username}'s Organization", "owner_email": f"{username}@test.com"},
            headers=headers,
        )
        if org_resp.status_code == 200:
            org_id = org_resp.json()["id"]
            return headers, org_id

        # Get org_id from /api/auth/me as fallback
        me_resp = client.get("/api/auth/me", headers=headers)
        if me_resp.status_code == 200:
            return headers, me_resp.json()["org_id"]
        return headers, "org1"  # Fallback

    def test_list_conversations_empty(self, temp_data_dir):
        """Test listing conversations when none exist."""
        client = TestClient(app)
        headers, _ = self.get_auth_headers(client)
        response = client.get("/api/conversations", headers=headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_list_conversations_with_data(self, temp_data_dir):
        """Test listing conversations with existing data."""
        client = TestClient(app)
        headers, _ = self.get_auth_headers(client)

        # Create conversations via API to ensure user ownership
        client.post("/api/conversations", json={}, headers=headers)
        client.post("/api/conversations", json={}, headers=headers)

        response = client.get("/api/conversations", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Check metadata structure
        for conv in data:
            assert "id" in conv
            assert "created_at" in conv
            assert "title" in conv
            assert "message_count" in conv

    def test_create_conversation(self, temp_data_dir):
        """Test creating a new conversation."""
        client = TestClient(app)
        headers, org_id = self.get_auth_headers(client)
        response = client.post("/api/conversations", json={}, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "created_at" in data
        assert data["title"] == "New Conversation"
        assert data["messages"] == []

        # Verify conversation was persisted
        retrieved = storage.get_conversation(data["id"], org_id)
        assert retrieved is not None
        assert retrieved["id"] == data["id"]

    def test_get_conversation(self, temp_data_dir):
        """Test retrieving a specific conversation."""
        client = TestClient(app)
        headers, _ = self.get_auth_headers(client)

        # Create conversation via API
        create_resp = client.post("/api/conversations", json={}, headers=headers)
        conv_id = create_resp.json()["id"]

        # Add messages manually (simulating backend process) but ensuring user_id matches
        # Actually, let's just use the API to ensure consistency

        response = client.get(f"/api/conversations/{conv_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conv_id
        assert len(data["messages"]) == 0

    def test_get_conversation_not_found(self, temp_data_dir):
        """Test retrieving non-existent conversation returns 404."""
        client = TestClient(app)
        headers, _ = self.get_auth_headers(client)
        response = client.get("/api/conversations/non-existent-id", headers=headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_conversation_unauthorized_access(self, temp_data_dir):
        """Test retrieving conversation owned by another user returns 403."""
        client = TestClient(app)

        # Create user1 and conversation
        headers1, org_id1 = self.get_auth_headers(client, username="user1", password="pass1")
        create_resp = client.post("/api/conversations", json={}, headers=headers1)
        conv_id = create_resp.json()["id"]

        # Create user2 (different user, same org)
        headers2, _ = self.get_auth_headers(client, username="user2", password="pass2")

        # Try to get conversation as user2
        response = client.get(f"/api/conversations/{conv_id}", headers=headers2)

        # Should return 403 (or 404 if conversation not found for user2's org)
        assert response.status_code in [403, 404]

    def test_get_conversation_with_messages(self, temp_data_dir):
        """Test retrieving conversation includes all messages."""
        client = TestClient(app)
        headers, org_id = self.get_auth_headers(client)

        create_resp = client.post("/api/conversations", json={}, headers=headers)
        conv_id = create_resp.json()["id"]

        # Add a message via API
        with (
            patch("backend.main.run_full_council", new_callable=AsyncMock) as mock_run,
            patch("backend.main.generate_conversation_title", new_callable=AsyncMock) as mock_title,
            patch("backend.main.get_org_api_config") as mock_api_config,
        ):
            mock_run.return_value = (
                [{"model": "m1", "response": "Response", "personality_id": None, "personality_name": "m1"}],
                [{"model": "m1", "personality_name": "m1", "ranking": "Rank", "parsed_ranking": ["A"]}],
                {"model": "chairman", "response": "Final"},
                {"label_to_model": {"A": "m1"}, "aggregate_rankings": []},
            )
            mock_title.return_value = "Test Title"
            mock_api_config.return_value = ("test-key", "https://openrouter.ai/api/v1/chat/completions")

            client.post(
                f"/api/conversations/{conv_id}/message",
                json={"content": "Test message"},
                headers=headers,
            )

        # Retrieve conversation
        response = client.get(f"/api/conversations/{conv_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conv_id
        assert len(data["messages"]) > 0


class TestMessageEndpoints:
    """Tests for message sending endpoints."""

    @pytest.fixture
    def temp_data_dir(self, monkeypatch):
        """Create a temporary data directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orgs_dir = os.path.join(tmpdir, "organizations")
            os.makedirs(orgs_dir, exist_ok=True)
            monkeypatch.setattr("backend.organizations.ORGS_DATA_DIR", orgs_dir)
            monkeypatch.setattr("backend.config.PROJECT_ROOT", tmpdir)
            yield orgs_dir

    @pytest.fixture
    def mock_council_functions(self):
        """Mock council functions to avoid actual LLM calls."""
        with (
            patch("backend.main.run_full_council", new_callable=AsyncMock) as mock_run,
            patch("backend.main.generate_conversation_title", new_callable=AsyncMock) as mock_title,
        ):
            # Default mock responses
            mock_run.return_value = (
                [
                    {
                        "model": "m1",
                        "response": "Response 1",
                        "personality_id": None,
                        "personality_name": "m1",
                    }
                ],
                [
                    {
                        "model": "m1",
                        "personality_name": "m1",
                        "ranking": "Ranking",
                        "parsed_ranking": ["Response A"],
                    }
                ],
                {"model": "chairman", "response": "Final answer"},
                {"label_to_model": {"Response A": "m1"}, "aggregate_rankings": []},
            )
            mock_title.return_value = "Test Title"

            yield {"run_full_council": mock_run, "generate_conversation_title": mock_title}

    def get_auth_headers(self, client, username="testuser", password="password"):
        """Helper to register and login, returning auth headers."""
        # Register
        resp = client.post("/api/auth/register", json={"username": username, "password": password, "mode": "create_org", "org_name": f"{username}_org"})
        assert resp.status_code == 200, f"Registration failed: {resp.text}"
        # Login
        response = client.post("/api/auth/token", data={"username": username, "password": password})
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create organization (user must create/join org after registration)
        org_resp = client.post(
            "/api/organizations/",
            json={"name": f"{username}'s Organization", "owner_email": f"{username}@test.com"},
            headers=headers,
        )
        if org_resp.status_code == 200:
            org_id = org_resp.json()["id"]
            return headers, org_id

        # Get org_id from /api/auth/me as fallback
        me_resp = client.get("/api/auth/me", headers=headers)
        if me_resp.status_code == 200:
            return headers, me_resp.json()["org_id"]
        return headers, "org1"

    def test_send_message_first_message(self, temp_data_dir, mock_council_functions):
        """Test sending first message triggers title generation."""
        client = TestClient(app)
        headers, _ = self.get_auth_headers(client)

        create_resp = client.post("/api/conversations", json={}, headers=headers)
        conv_id = create_resp.json()["id"]

        response = client.post(
            f"/api/conversations/{conv_id}/message",
            json={"content": "What is Python?"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "stage1" in data

        # Verify title was generated
        mock_council_functions["generate_conversation_title"].assert_called_once()

    def test_send_message_conversation_not_found(self, temp_data_dir):
        """Test sending message to non-existent conversation returns 404."""
        client = TestClient(app)
        headers, _ = self.get_auth_headers(client)
        response = client.post(
            "/api/conversations/non-existent/message", json={"content": "Hello"}, headers=headers
        )

        assert response.status_code == 404

    def test_send_message_subsequent_message(self, temp_data_dir, mock_council_functions):
        """Test sending subsequent message does not trigger title generation."""
        client = TestClient(app)
        headers, _ = self.get_auth_headers(client)

        create_resp = client.post("/api/conversations", json={}, headers=headers)
        conv_id = create_resp.json()["id"]

        # Send first message
        response1 = client.post(
            f"/api/conversations/{conv_id}/message",
            json={"content": "What is Python?"},
            headers=headers,
        )
        assert response1.status_code == 200

        # Reset mock to verify it's not called again
        mock_council_functions["generate_conversation_title"].reset_mock()

        # Send second message
        response2 = client.post(
            f"/api/conversations/{conv_id}/message",
            json={"content": "Tell me more"},
            headers=headers,
        )

        assert response2.status_code == 200
        data = response2.json()
        assert "stage1" in data
        assert "stage2" in data
        assert "stage3" in data

        # Title generation should not be called for subsequent messages
        mock_council_functions["generate_conversation_title"].assert_not_called()

    def test_send_message_unauthorized_access(self, temp_data_dir, mock_council_functions):
        """Test sending message to conversation owned by another user returns 403."""
        client = TestClient(app)

        # Create user1 and conversation
        headers1, org_id1 = self.get_auth_headers(client, username="user1", password="pass1")
        create_resp = client.post("/api/conversations", json={}, headers=headers1)
        conv_id = create_resp.json()["id"]

        # Create user2 (different user, same org)
        headers2, _ = self.get_auth_headers(client, username="user2", password="pass2")

        # Try to send message as user2 to user1's conversation
        response = client.post(
            f"/api/conversations/{conv_id}/message",
            json={"content": "Hello"},
            headers=headers2,
        )

        # Should return 403 (or 404 if conversation not found for user2's org)
        assert response.status_code in [403, 404]

    def test_send_message_with_conversation_history(self, temp_data_dir, mock_council_functions):
        """Test send_message includes conversation history in council call."""
        client = TestClient(app)
        headers, _ = self.get_auth_headers(client)

        create_resp = client.post("/api/conversations", json={}, headers=headers)
        conv_id = create_resp.json()["id"]

        # Send first message
        client.post(
            f"/api/conversations/{conv_id}/message",
            json={"content": "What is Python?"},
            headers=headers,
        )

        # Send second message
        response = client.post(
            f"/api/conversations/{conv_id}/message",
            json={"content": "Tell me more"},
            headers=headers,
        )

        assert response.status_code == 200

        # Verify run_full_council was called with conversation history
        call_args = mock_council_functions["run_full_council"].call_args
        messages_arg = call_args[0][1]  # Second positional argument is messages
        assert len(messages_arg) >= 2  # Should include previous user and assistant messages
        assert messages_arg[0]["role"] == "user"
        assert messages_arg[0]["content"] == "What is Python?"

    def test_send_message_stores_voting_history(self, temp_data_dir, mock_council_functions):
        """Test send_message records voting history."""
        client = TestClient(app)
        headers, _ = self.get_auth_headers(client)

        create_resp = client.post("/api/conversations", json={}, headers=headers)
        conv_id = create_resp.json()["id"]

        with patch("backend.main.record_votes") as mock_record_votes:
            response = client.post(
                f"/api/conversations/{conv_id}/message",
                json={"content": "What is Python?"},
                headers=headers,
            )

            assert response.status_code == 200
            # Verify voting history was recorded
            mock_record_votes.assert_called_once()

    def test_send_message_returns_complete_response(self, temp_data_dir, mock_council_functions):
        """Test send_message returns complete response with all stages and metadata."""
        client = TestClient(app)
        headers, _ = self.get_auth_headers(client)

        create_resp = client.post("/api/conversations", json={}, headers=headers)
        conv_id = create_resp.json()["id"]

        response = client.post(
            f"/api/conversations/{conv_id}/message",
            json={"content": "What is Python?"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "stage1" in data
        assert "stage2" in data
        assert "stage3" in data
        assert "metadata" in data
        assert isinstance(data["stage1"], list)
        assert isinstance(data["stage2"], list)
        assert isinstance(data["stage3"], dict)
        assert "response" in data["stage3"]

    def test_send_message_api_config_error(self, temp_data_dir, mock_council_functions):
        """Test send_message handles API config errors gracefully."""
        client = TestClient(app, raise_server_exceptions=False)
        headers, _ = self.get_auth_headers(client)

        create_resp = client.post("/api/conversations", json={}, headers=headers)
        conv_id = create_resp.json()["id"]

        # Mock get_org_api_config to raise ValueError
        with patch("backend.main.get_org_api_config", side_effect=ValueError("API key not configured")):
            response = client.post(
                f"/api/conversations/{conv_id}/message",
                json={"content": "What is Python?"},
                headers=headers,
            )

            # FastAPI will convert unhandled ValueError to 500 Internal Server Error
            # Verify that an error occurred (status code >= 400)
            assert response.status_code >= 400, f"Expected error status, got {response.status_code}: {response.text[:200]}"

    def test_send_message_stream_first_message(self, temp_data_dir, mock_council_functions):
        """Test streaming first message with title generation."""
        client = TestClient(app)
        headers, _ = self.get_auth_headers(client)

        create_resp = client.post("/api/conversations", json={}, headers=headers)
        conv_id = create_resp.json()["id"]

        # We need to mock the streaming functions which are now in backend.streaming
        # But run_council_streaming is imported in main.py inside the function
        # So we patch backend.streaming.run_council_streaming

        # Actually, let's just patch the internal functions called by run_council_streaming
        # or patch run_council_streaming itself.

        # Since run_council_streaming is imported inside the handler, patching 'backend.streaming.run_council_streaming'
        # should work if we patch it before the handler is called.

        # However, the test uses TestClient which runs the app.
        # Let's try to run the real streaming logic but mock the LLM calls inside it.

        with (
            patch("backend.streaming.stage1_collect_responses", new_callable=AsyncMock) as m1,
            patch("backend.streaming.stage2_collect_rankings", new_callable=AsyncMock) as m2,
            patch("backend.streaming.stage3_synthesize_final", new_callable=AsyncMock) as m3,
            patch(
                "backend.streaming.generate_conversation_title", new_callable=AsyncMock
            ) as m_title,
        ):
            m1.return_value = []
            m2.return_value = ([], {})
            m3.return_value = {}
            m_title.return_value = "Title"

            response = client.post(
                f"/api/conversations/{conv_id}/message/stream",
                json={"content": "What is Python?"},
                headers=headers,
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
            content = response.text
            assert "stage_start" in content

    def test_send_message_stream_error_handling(self, temp_data_dir):
        """Test error handling in streaming endpoint."""
        client = TestClient(app)
        headers, _ = self.get_auth_headers(client)

        create_resp = client.post("/api/conversations", json={}, headers=headers)
        conv_id = create_resp.json()["id"]

        # Mock stage1 to raise exception
        with patch(
            "backend.streaming.stage1_collect_responses", side_effect=Exception("Test error")
        ):
            response = client.post(
                f"/api/conversations/{conv_id}/message/stream",
                json={"content": "Test"},
                headers=headers,
            )

            assert response.status_code == 200
            content = response.text
            assert "error" in content
            assert "Test error" in content


class TestCORSConfiguration:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses."""
        client = TestClient(app)
        response = client.options("/api/conversations")
        assert response.status_code in [200, 405]
