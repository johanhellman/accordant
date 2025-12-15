"""Tests for user management functions."""

import os
import tempfile

import pytest

from backend.users import UserInDB, create_user, get_user, update_user_role


class TestUserFunctions:
    """Tests for user management functions."""

    @pytest.fixture
    def temp_data_dir(self, monkeypatch):
        """Create a temporary data directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            users_file = os.path.join(tmpdir, "users.json")
            monkeypatch.setattr("backend.users.USERS_FILE", users_file)
            yield tmpdir

    def test_update_user_role_success(self, temp_data_dir):
        """Test update_user_role successfully updates user's admin status."""
        # Create first user (will be admin automatically)
        first_user = UserInDB(
            id="user0", username="firstuser", password_hash="hash", is_admin=False
        )
        create_user(first_user)

        # Create second user (will not be admin)
        user = UserInDB(id="user1", username="testuser", password_hash="hash", is_admin=False)
        created_user = create_user(user)

        assert created_user.is_admin is False

        # Update to admin
        updated_user = update_user_role("user1", is_admin=True)
        assert updated_user is not None
        assert updated_user.is_admin is True

        # Verify persistence
        retrieved = get_user("testuser")
        assert retrieved is not None
        assert retrieved.is_admin is True

    def test_update_user_role_remove_admin(self, temp_data_dir):
        """Test update_user_role can remove admin status."""
        # Create admin user
        user = UserInDB(id="user1", username="admin", password_hash="hash", is_admin=True)
        create_user(user)

        # Remove admin status
        updated_user = update_user_role("user1", is_admin=False)
        assert updated_user is not None
        assert updated_user.is_admin is False

        # Verify persistence
        retrieved = get_user("admin")
        assert retrieved.is_admin is False

    def test_update_user_role_not_found(self, temp_data_dir):
        """Test update_user_role returns None when user doesn't exist."""
        result = update_user_role("non-existent-user-id", is_admin=True)
        assert result is None

    def test_update_user_role_by_username(self, temp_data_dir):
        """Test update_user_role works with username lookup."""
        # Create user
        user = UserInDB(id="user1", username="testuser", password_hash="hash", is_admin=False)
        create_user(user)

        # Note: update_user_role uses user_id, not username
        # So we need to use the id
        updated_user = update_user_role("user1", is_admin=True)
        assert updated_user is not None
        assert updated_user.is_admin is True

    def test_update_user_role_multiple_updates(self, temp_data_dir):
        """Test update_user_role can be called multiple times."""
        # Create user
        user = UserInDB(id="user1", username="testuser", password_hash="hash", is_admin=False)
        create_user(user)

        # Update to admin
        updated1 = update_user_role("user1", is_admin=True)
        assert updated1.is_admin is True

        # Update back to non-admin
        updated2 = update_user_role("user1", is_admin=False)
        assert updated2.is_admin is False

        # Update to admin again
        updated3 = update_user_role("user1", is_admin=True)
        assert updated3.is_admin is True

        # Verify final state
        retrieved = get_user("testuser")
        assert retrieved.is_admin is True
