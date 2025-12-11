"""Tests for storage.py file operations (MIGRATED TO SQLITE)."""

import pytest
from sqlalchemy import text
from backend import storage, models

class TestStorageOperations:
    """Tests for storage module functions using SQLite."""

    # Note: We use 'tenant_db_session' from conftest.py implicitly via our calls
    # but we can also request it to do assertions.
    # storage.py uses 'get_tenant_session' internally, which is patched to return our global engine.
    # To assert things, we should use the same engine/session logic.

    def test_create_conversation(self, tenant_db_session):
        """Test creating a new conversation."""
        conversation_id = "test-conv-123"
        # org_id is arbitrary since we use shared in-memory DB in tests
        conversation = storage.create_conversation(conversation_id, "user1", "org1")

        assert conversation["id"] == conversation_id
        assert "created_at" in conversation
        assert conversation["title"] == "New Conversation"
        assert conversation["messages"] == []

        # Verify DB insertion
        conv_db = tenant_db_session.query(models.Conversation).get(conversation_id)
        assert conv_db is not None
        assert conv_db.id == conversation_id
        assert conv_db.user_id == "user1"

    def test_get_conversation(self, tenant_db_session):
        """Test retrieving an existing conversation."""
        conversation_id = "test-conv-456"
        created = storage.create_conversation(conversation_id, "user1", "org1")

        retrieved = storage.get_conversation(conversation_id, "org1")

        assert retrieved is not None
        assert retrieved["id"] == conversation_id
        assert retrieved["created_at"] == created["created_at"]
        assert retrieved["title"] == "New Conversation"
        assert retrieved["messages"] == []

    def test_get_conversation_not_found(self, tenant_db_session):
        """Test retrieving non-existent conversation returns None."""
        result = storage.get_conversation("non-existent-id", "org1")
        assert result is None

    def test_add_user_message(self, tenant_db_session):
        """Test adding a user message to a conversation."""
        conversation_id = "test-conv-789"
        storage.create_conversation(conversation_id, "user1", "org1")

        storage.add_user_message(conversation_id, "Hello, world!", "org1")

        conversation = storage.get_conversation(conversation_id, "org1")
        assert len(conversation["messages"]) == 1
        assert conversation["messages"][0]["role"] == "user"
        assert conversation["messages"][0]["content"] == "Hello, world!"
        
        # Verify DB
        msg_db = tenant_db_session.query(models.Message).filter_by(conversation_id=conversation_id).first()
        assert msg_db.content == "Hello, world!"

    def test_add_user_message_nonexistent_conversation(self, tenant_db_session):
        """Test that adding message to non-existent conversation raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            storage.add_user_message("non-existent", "Test message", "org1")

    def test_add_assistant_message(self, tenant_db_session):
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

    def test_add_assistant_message_nonexistent_conversation(self, tenant_db_session):
        """Test that adding assistant message to non-existent conversation raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            storage.add_assistant_message("non-existent", [], [], {}, "org1")

    def test_list_conversations(self, tenant_db_session):
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

        # Note: In a shared DB test environment without explicit reset per test (unless fixture does it)
        # previous tests might affect this. Our fixture DOES rollback, so it should be clean.
        assert len(conversations) == 3
        # Should be sorted by creation time, newest first
        # (Though create_conversation is fast, timestamps might be identical, sorting might be unstable if not ensuring delays)
        # But SQLite datetime default is second precision usually or string... SQLAlchemy 'default' is Python side usually?
        # models.py says: default=datetime.utcnow. That is distinct execution time.
        
        assert conversations[0]["created_at"] >= conversations[1]["created_at"]
        assert conversations[1]["created_at"] >= conversations[2]["created_at"]

        # Verify message counts
        conv1_meta = next(c for c in conversations if c["id"] == "conv-1")
        conv2_meta = next(c for c in conversations if c["id"] == "conv-2")
        assert conv1_meta["message_count"] == 1
        assert conv2_meta["message_count"] == 2

    def test_list_conversations_empty(self, tenant_db_session):
        """Test listing conversations when none exist."""
        conversations = storage.list_conversations("user1", "org1")
        assert conversations == []

    def test_update_conversation_title(self, tenant_db_session):
        """Test updating conversation title."""
        conversation_id = "test-conv-title"
        storage.create_conversation(conversation_id, "user1", "org1")

        storage.update_conversation_title(conversation_id, "New Title", "org1")

        conversation = storage.get_conversation(conversation_id, "org1")
        assert conversation["title"] == "New Title"

    def test_update_conversation_title_nonexistent(self, tenant_db_session):
        """Test that updating title of non-existent conversation does nothing (or raises if designed so)."""
        # storage.py doesn't raise, just checks 'if conv:'.
        storage.update_conversation_title("non-existent", "New Title", "org1")
        pass # Should not raise

    def test_multiple_messages(self, tenant_db_session):
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

    def test_list_conversations_user_filtering(self, tenant_db_session):
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

    def test_save_conversation(self, tenant_db_session):
        """
        Test save_conversation function.
        Note: save_conversation in SQLite implementation only updates title.
        Messages are added via add_message.
        """
        conversation_id = "test-conv-save"
        conversation = storage.create_conversation(conversation_id, "user1", "org1")

        # Modify conversation title
        conversation["title"] = "Updated Title"
        # Adding messages here won't persist if using save_conversation for messages
        # because the implementation ignores messages in save_conversation
        
        storage.save_conversation(conversation, "org1")

        # Verify saved
        retrieved = storage.get_conversation(conversation_id, "org1")
        assert retrieved["title"] == "Updated Title"

    def test_delete_conversation(self, tenant_db_session):
        """Test deleting a conversation."""
        conversation_id = "test-conv-del"
        storage.create_conversation(conversation_id, "user1", "org1")
        
        # Verify exists
        assert storage.get_conversation(conversation_id, "org1") is not None
        
        # Delete
        storage.delete_conversation(conversation_id, "org1")
        
        # Verify gone
        assert storage.get_conversation(conversation_id, "org1") is None

    def test_delete_user_conversations(self, tenant_db_session):
        """Test deleting all conversations for a user."""
        storage.create_conversation("c1", "u1", "org1")
        storage.create_conversation("c2", "u1", "org1")
        storage.create_conversation("c3", "u2", "org1")
        
        count = storage.delete_user_conversations("u1", "org1")
        assert count == 2
        
        # u1 should match nothing
        assert len(storage.list_conversations("u1", "org1")) == 0
        # u2 should remain
        assert len(storage.list_conversations("u2", "org1")) == 1

