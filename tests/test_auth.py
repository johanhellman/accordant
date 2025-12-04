"""Tests for authentication and user management."""

import os
import tempfile

import pytest

from backend.auth import (
    create_access_token,
    get_current_admin_user,
    get_password_hash,
    verify_password,
)
from backend.users import User, UserInDB, create_user, get_user


class TestUserManagement:
    def test_create_and_get_user(self, monkeypatch):
        with tempfile.TemporaryDirectory() as temp_dir:
            users_file = os.path.join(temp_dir, "users.json")
            monkeypatch.setattr("backend.users.USERS_FILE", users_file)

            # Create first user (should be admin and instance admin)
            user1 = UserInDB(id="1", username="admin", password_hash="hash")
            created1 = create_user(user1)
            assert created1.is_admin is True
            assert created1.is_instance_admin is True

            # Create second user (should not be admin)
            user2 = UserInDB(id="2", username="user", password_hash="hash")
            created2 = create_user(user2)
            assert created2.is_admin is False

            # Get user
            fetched = get_user("admin")
            assert fetched.username == "admin"
            assert fetched.is_admin is True

            fetched2 = get_user("user")
            assert fetched2.username == "user"
            assert fetched2.is_admin is False

    def test_duplicate_username(self, monkeypatch):
        with tempfile.TemporaryDirectory() as temp_dir:
            users_file = os.path.join(temp_dir, "users.json")
            monkeypatch.setattr("backend.users.USERS_FILE", users_file)

            user1 = UserInDB(id="1", username="test", password_hash="hash")
            create_user(user1)

            with pytest.raises(ValueError):
                create_user(user1)


class TestAuthLogic:
    def test_password_hashing(self):
        password = "secret"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)
        assert not verify_password("wrong", hashed)

    def test_jwt_token(self):
        data = {"sub": "testuser"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_instance_admin_access(self):
        """Test that instance admins can access admin endpoints."""
        # Instance admin without org admin flag should still have access
        instance_admin = User(
            id="1",
            username="instance_admin",
            password_hash="hash",
            is_admin=False,
            is_instance_admin=True,
            org_id="org1",
        )

        # Should not raise - instance admins have admin access
        result = await get_current_admin_user(instance_admin)
        assert result == instance_admin

        # Regular org admin should also have access
        org_admin = User(
            id="2",
            username="org_admin",
            password_hash="hash",
            is_admin=True,
            is_instance_admin=False,
            org_id="org1",
        )

        result = await get_current_admin_user(org_admin)
        assert result == org_admin

        # Regular user should be denied
        regular_user = User(
            id="3",
            username="regular",
            password_hash="hash",
            is_admin=False,
            is_instance_admin=False,
            org_id="org1",
        )

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            await get_current_admin_user(regular_user)
        assert exc.value.status_code == 403
