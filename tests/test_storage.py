"""Tests for storage.py file operations."""

import json
import os
import tempfile

import pytest

from backend import storage


class TestStorageOperations:
    """Tests for storage module functions."""

    @pytest.fixture
    def temp_data_dir(self, monkeypatch):
        """Create a temporary data directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch ORGS_DATA_DIR
            orgs_dir = os.path.join(tmpdir, "organizations")
            os.makedirs(orgs_dir, exist_ok=True)
            monkeypatch.setattr("backend.storage.ORGS_DATA_DIR", orgs_dir)

            yield orgs_dir

    def test_create_conversation(self, temp_data_dir):
        """Test creating a new conversation."""
        conversation_id = "test-conv-123"
        conversation = storage.create_conversation(conversation_id, "user1", "org1")

        assert conversation["id"] == conversation_id
        assert "created_at" in conversation
        assert conversation["title"] == "New Conversation"
        assert conversation["messages"] == []

        # Verify file was created
        file_path = storage.get_conversation_path(conversation_id, "org1")
        assert os.path.exists(file_path)

        # Verify file contents
        with open(file_path) as f:
            data = json.load(f)
            assert data["id"] == conversation_id

    def test_get_conversation(self, temp_data_dir):
        """Test retrieving an existing conversation."""
        conversation_id = "test-conv-456"
        created = storage.create_conversation(conversation_id, "user1", "org1")

        retrieved = storage.get_conversation(conversation_id, "org1")

        assert retrieved is not None
        assert retrieved["id"] == conversation_id
        assert retrieved["created_at"] == created["created_at"]
        assert retrieved["title"] == "New Conversation"
        assert retrieved["messages"] == []

    def test_get_conversation_not_found(self, temp_data_dir):
        """Test retrieving non-existent conversation returns None."""
        result = storage.get_conversation("non-existent-id", "org1")
        assert result is None

    def test_add_user_message(self, temp_data_dir):
        """Test adding a user message to a conversation."""
        conversation_id = "test-conv-789"
        storage.create_conversation(conversation_id, "user1", "org1")

        storage.add_user_message(conversation_id, "Hello, world!", "org1")

        conversation = storage.get_conversation(conversation_id, "org1")
        assert len(conversation["messages"]) == 1
        assert conversation["messages"][0]["role"] == "user"
        assert conversation["messages"][0]["content"] == "Hello, world!"

    def test_add_user_message_nonexistent_conversation(self, temp_data_dir):
        """Test that adding message to non-existent conversation raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            storage.add_user_message("non-existent", "Test message", "org1")

    def test_add_assistant_message(self, temp_data_dir):
        """Test adding an assistant message with all 3 stages."""
        conversation_id = "test-conv-assistant"
        storage.create_conversation(conversation_id, "user1", "org1")

        stage1 = [{"model": "model1", "response": "Response 1"}]
        stage2 = [{"model": "model1", "ranking": "Ranking 1"}]
        stage3 = {"model": "model1", "response": "Final answer"}

        storage.add_assistant_message(conversation_id, stage1, stage2, stage3, "org1")

        conversation = storage.get_conversation(conversation_id, "org1")
        assert len(conversation["messages"]) == 1
        assert conversation["messages"][0]["role"] == "assistant"
        assert conversation["messages"][0]["stage1"] == stage1
        assert conversation["messages"][0]["stage2"] == stage2
        assert conversation["messages"][0]["stage3"] == stage3

    def test_add_assistant_message_nonexistent_conversation(self, temp_data_dir):
        """Test that adding assistant message to non-existent conversation raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            storage.add_assistant_message("non-existent", [], [], {}, "org1")

    def test_list_conversations(self, temp_data_dir):
        """Test listing all conversations (metadata only)."""
        # Create multiple conversations
        storage.create_conversation("conv-1", "user1", "org1")
        storage.create_conversation("conv-2", "user1", "org1")
        storage.create_conversation("conv-3", "user1", "org1")

        # Add messages to some conversations
        storage.add_user_message("conv-1", "Message 1", "org1")
        storage.add_user_message("conv-2", "Message 1", "org1")
        storage.add_user_message("conv-2", "Message 2", "org1")

        conversations = storage.list_conversations("user1", "org1")

        assert len(conversations) == 3
        # Should be sorted by creation time, newest first
        assert conversations[0]["created_at"] >= conversations[1]["created_at"]
        assert conversations[1]["created_at"] >= conversations[2]["created_at"]

        # Check metadata structure
        for conv in conversations:
            assert "id" in conv
            assert "created_at" in conv
            assert "title" in conv
            assert "message_count" in conv

        # Verify message counts
        conv1_meta = next(c for c in conversations if c["id"] == "conv-1")
        conv2_meta = next(c for c in conversations if c["id"] == "conv-2")
        assert conv1_meta["message_count"] == 1
        assert conv2_meta["message_count"] == 2

    def test_list_conversations_empty(self, temp_data_dir):
        """Test listing conversations when none exist."""
        conversations = storage.list_conversations("user1", "org1")
        assert conversations == []

    def test_update_conversation_title(self, temp_data_dir):
        """Test updating conversation title."""
        conversation_id = "test-conv-title"
        storage.create_conversation(conversation_id, "user1", "org1")

        storage.update_conversation_title(conversation_id, "New Title", "org1")

        conversation = storage.get_conversation(conversation_id, "org1")
        assert conversation["title"] == "New Title"

    def test_update_conversation_title_nonexistent(self, temp_data_dir):
        """Test that updating title of non-existent conversation raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            storage.update_conversation_title("non-existent", "New Title", "org1")

    def test_multiple_messages(self, temp_data_dir):
        """Test adding multiple messages to a conversation."""
        conversation_id = "test-conv-multi"
        storage.create_conversation(conversation_id, "user1", "org1")

        storage.add_user_message(conversation_id, "First message", "org1")
        storage.add_assistant_message(
            conversation_id,
            [{"model": "m1", "response": "R1"}],
            [{"model": "m1", "ranking": "R1"}],
            {"model": "m1", "response": "Answer 1"},
            "org1",
        )
        storage.add_user_message(conversation_id, "Second message", "org1")
        storage.add_assistant_message(
            conversation_id,
            [{"model": "m1", "response": "R2"}],
            [{"model": "m1", "ranking": "R2"}],
            {"model": "m1", "response": "Answer 2"},
            "org1",
        )

        conversation = storage.get_conversation(conversation_id, "org1")
        assert len(conversation["messages"]) == 4
        assert conversation["messages"][0]["role"] == "user"
        assert conversation["messages"][1]["role"] == "assistant"
        assert conversation["messages"][2]["role"] == "user"
        assert conversation["messages"][3]["role"] == "assistant"

    def test_list_conversations_user_filtering(self, temp_data_dir):
        """Test listing conversations filters by user_id."""
        # Create conversations for different users
        storage.create_conversation("conv-user1", "user1", "org1")
        storage.create_conversation("conv-user2", "user2", "org1")
        storage.create_conversation("conv-user1-2", "user1", "org1")

        # List conversations for user1
        conversations = storage.list_conversations("user1", "org1")
        assert len(conversations) == 2
        assert all(c["id"] in ["conv-user1", "conv-user1-2"] for c in conversations)

        # List conversations for user2
        conversations = storage.list_conversations("user2", "org1")
        assert len(conversations) == 1
        assert conversations[0]["id"] == "conv-user2"

    def test_list_conversations_malformed_json(self, temp_data_dir):
        """Test that list_conversations skips malformed JSON files."""
        # Create a valid conversation
        storage.create_conversation("conv-valid", "user1", "org1")

        # Create a malformed JSON file
        conversations_dir = os.path.join(temp_data_dir, "org1", "conversations")
        os.makedirs(conversations_dir, exist_ok=True)
        malformed_file = os.path.join(conversations_dir, "malformed.json")
        with open(malformed_file, "w") as f:
            f.write("{ invalid json }")

        # Should only return the valid conversation
        conversations = storage.list_conversations("user1", "org1")
        assert len(conversations) == 1
        assert conversations[0]["id"] == "conv-valid"

    def test_list_conversations_non_json_files(self, temp_data_dir):
        """Test that list_conversations skips non-JSON files."""
        # Create a valid conversation
        storage.create_conversation("conv-valid", "user1", "org1")

        # Create a non-JSON file
        conversations_dir = os.path.join(temp_data_dir, "org1", "conversations")
        os.makedirs(conversations_dir, exist_ok=True)
        non_json_file = os.path.join(conversations_dir, "not-a-json.txt")
        with open(non_json_file, "w") as f:
            f.write("This is not JSON")

        # Should only return the valid conversation
        conversations = storage.list_conversations("user1", "org1")
        assert len(conversations) == 1
        assert conversations[0]["id"] == "conv-valid"

    def test_list_conversations_missing_user_id_field(self, temp_data_dir):
        """Test that list_conversations handles conversations missing user_id field."""
        conversations_dir = os.path.join(temp_data_dir, "org1", "conversations")
        os.makedirs(conversations_dir, exist_ok=True)

        # Create a conversation file without user_id
        conv_file = os.path.join(conversations_dir, "no-user-id.json")
        with open(conv_file, "w") as f:
            json.dump({"id": "no-user-id", "created_at": "2024-01-01T00:00:00", "messages": []}, f)

        # When filtering by user_id, should skip conversations without user_id
        conversations = storage.list_conversations("user1", "org1")
        # Should not include the conversation without user_id
        assert all(c["id"] != "no-user-id" for c in conversations)

    def test_save_conversation(self, temp_data_dir):
        """Test save_conversation function."""
        conversation_id = "test-conv-save"
        conversation = storage.create_conversation(conversation_id, "user1", "org1")

        # Modify conversation
        conversation["title"] = "Updated Title"
        conversation["messages"].append({"role": "user", "content": "Test"})

        # Save conversation
        storage.save_conversation(conversation, "org1")

        # Verify saved
        retrieved = storage.get_conversation(conversation_id, "org1")
        assert retrieved["title"] == "Updated Title"
        assert len(retrieved["messages"]) == 1
        assert retrieved["messages"][0]["content"] == "Test"

    def test_save_conversation_creates_directory(self, temp_data_dir):
        """Test that save_conversation creates directory if it doesn't exist."""
        # Remove the org directory to test directory creation
        org_dir = os.path.join(temp_data_dir, "org2")
        if os.path.exists(org_dir):
            import shutil

            shutil.rmtree(org_dir)

        conversation = {
            "id": "test-conv-new-org",
            "created_at": "2024-01-01T00:00:00",
            "title": "Test",
            "messages": [],
            "user_id": "user1",
            "org_id": "org2",
        }

        storage.save_conversation(conversation, "org2")

        # Verify directory was created and file exists
        file_path = storage.get_conversation_path("test-conv-new-org", "org2")
        assert os.path.exists(file_path)

    def test_get_conversation_path(self, temp_data_dir):
        """Test get_conversation_path function."""
        path = storage.get_conversation_path("test-conv", "org1")
        assert "test-conv.json" in path
        assert "org1" in path
        assert "conversations" in path

    def test_ensure_data_dir(self, temp_data_dir):
        """Test ensure_data_dir creates directory structure."""
        # Remove org directory to test creation
        org_dir = os.path.join(temp_data_dir, "org3")
        if os.path.exists(org_dir):
            import shutil

            shutil.rmtree(org_dir)

        storage.ensure_data_dir("org3")

        # Verify directory was created
        conversations_dir = os.path.join(org_dir, "conversations")
        assert os.path.exists(conversations_dir)
        assert os.path.isdir(conversations_dir)
