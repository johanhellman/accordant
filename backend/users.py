"""User management module."""

import json
import logging
import os

from pydantic import BaseModel

from .config import PROJECT_ROOT

logger = logging.getLogger(__name__)

USERS_FILE = os.path.join(PROJECT_ROOT, "data", "users.json")


class User(BaseModel):
    id: str
    username: str
    password_hash: str
    is_admin: bool = False  # Org Admin
    is_instance_admin: bool = False  # System Admin
    org_id: str | None = None


class UserCreate(BaseModel):
    username: str
    password: str


class UserInDB(User):
    pass


class UserResponse(BaseModel):
    id: str
    username: str
    is_admin: bool
    is_instance_admin: bool = False
    org_id: str | None = None

    class Config:
        orm_mode = True


def _load_users() -> dict[str, UserInDB]:
    """Load users from JSON file."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE) as f:
            data = json.load(f)
            return {u["username"]: UserInDB(**u) for u in data}
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        return {}


def _save_users(users: dict[str, UserInDB]):
    """Save users to JSON file."""
    try:
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, "w") as f:
            json.dump([u.dict() for u in users.values()], f, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {e}")
        raise


def get_user(username: str) -> UserInDB | None:
    """Get a user by username."""
    users = _load_users()
    return users.get(username)


def create_user(user: UserInDB) -> UserInDB:
    """Create a new user."""
    users = _load_users()
    if user.username in users:
        raise ValueError("Username already exists")

    # First user is always admin and instance admin
    if not users:
        user.is_admin = True
        user.is_instance_admin = True

    users[user.username] = user
    _save_users(users)
    return user


def get_all_users() -> list[UserInDB]:
    """Get all users."""
    users = _load_users()
    return list(users.values())


def update_user_role(user_id: str, is_admin: bool) -> UserInDB | None:
    """Update a user's admin status."""
    users = _load_users()
    target_user = None

    for u in users.values():
        if u.id == user_id:
            target_user = u
            break

    if target_user:
        target_user.is_admin = is_admin
        users[target_user.username] = target_user
        _save_users(users)
        return target_user

    return None


def update_user_org(user_id: str, org_id: str, is_admin: bool = False) -> UserInDB | None:
    """Update a user's organization and admin status."""
    users = _load_users()
    target_user = None

    for u in users.values():
        if u.id == user_id:
            target_user = u
            break

    if target_user:
        target_user.org_id = org_id
        target_user.is_admin = is_admin
        users[target_user.username] = target_user
        _save_users(users)
        return target_user

    return None
