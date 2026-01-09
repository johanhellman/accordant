"""User management module (SQLAlchemy)."""

import logging

from sqlalchemy.orm import Session

from . import models
from .database import SystemSessionLocal, system_engine

# Create tables if they don't exist
models.SystemBase.metadata.create_all(bind=system_engine)

logger = logging.getLogger(__name__)

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    id: str
    username: str
    password_hash: str
    is_admin: bool = False
    is_instance_admin: bool = False
    org_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


# --- DB Operations ---


def get_user(username: str, db: Session = None) -> UserInDB | None:
    """Get a user by username."""
    if db:
        return _get_user_with_session(db, username)

    with SystemSessionLocal() as session:
        return _get_user_with_session(session, username)


def _get_user_with_session(db: Session, username: str) -> UserInDB | None:
    user_model = db.query(models.User).filter(models.User.username == username).first()
    if user_model:
        return UserInDB.model_validate(user_model)
    return None


def get_user_by_id(user_id: str, db: Session = None) -> UserInDB | None:
    if db:
        user_model = db.query(models.User).filter(models.User.id == user_id).first()
        if user_model:
            return UserInDB.model_validate(user_model)
        return None

    with SystemSessionLocal() as session:
        user_model = session.query(models.User).filter(models.User.id == user_id).first()
        if user_model:
            return UserInDB.model_validate(user_model)
        return None


def create_user(user: UserInDB, db: Session = None) -> UserInDB:
    """Create a new user. WARNING: Should be used within a transaction in main.py ideally."""
    is_ephemeral = False
    if db is None:
        db = SystemSessionLocal()
        is_ephemeral = True

    try:
        db_user = models.User(
            id=user.id,
            username=user.username,
            password_hash=user.password_hash,
            is_admin=user.is_admin,
            is_instance_admin=user.is_instance_admin,
            org_id=user.org_id,
        )
        db.add(db_user)
        if is_ephemeral:
            db.commit()
            db.refresh(db_user)
        return UserInDB.model_validate(db_user)
    except Exception as e:
        if is_ephemeral:
            db.rollback()
        logger.error(f"Error creating user: {e}")
        raise
    finally:
        if is_ephemeral:
            db.close()


def get_all_users() -> list[UserInDB]:
    """Get all users."""
    with SystemSessionLocal() as db:
        users = db.query(models.User).all()
        return [UserInDB.model_validate(u) for u in users]


def update_user_role(user_id: str, is_admin: bool) -> UserInDB | None:
    """Update a user's admin status."""
    with SystemSessionLocal() as db:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user.is_admin = is_admin
            db.commit()
            db.refresh(user)
            return UserInDB.model_validate(user)
    return None


def update_user_org(user_id: str, org_id: str, is_admin: bool = False) -> UserInDB | None:
    """Update a user's organization and admin status."""
    with SystemSessionLocal() as db:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user.org_id = org_id
            user.is_admin = is_admin
            db.commit()
            db.refresh(user)
            return UserInDB.model_validate(user)
    return None


def delete_user(user_id: str) -> bool:
    """Delete a user by ID."""
    with SystemSessionLocal() as db:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
            return True
    return False


def update_user_password(user_id: str, password_hash: str) -> bool:
    """Update a user's password hash."""
    with SystemSessionLocal() as db:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user.password_hash = password_hash
            db.commit()
            return True
    return False
