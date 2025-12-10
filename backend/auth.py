"""Authentication logic (JWT, Hashing)."""

import logging
import os
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from .users import User, get_user

# Configuration
_ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
_SECRET_KEY = os.getenv("SECRET_KEY")

if not _SECRET_KEY:
    # In production, SECRET_KEY is required
    if _ENVIRONMENT.lower() in ("production", "prod"):
        raise ValueError(
            "SECRET_KEY environment variable is required in production. "
            "Please set it in your .env file. See .env.example for reference."
        )
    # In development/test, allow a test default with a warning
    import logging

    logger = logging.getLogger(__name__)
    logger.warning(
        "⚠️  SECURITY WARNING: SECRET_KEY not set. Using insecure default for development/testing only. "
        "Set SECRET_KEY environment variable for production use."
    )
    _SECRET_KEY = "insecure-secret-key-change-me-development-only"  # nosec B105

SECRET_KEY = _SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get current authenticated user.
    Ensures user belongs to an organization (architecture requirement).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except PyJWTError as e:
        raise credentials_exception from e

    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    
    # Architecture requirement: Users must always belong to an organization
    # Auto-fix: If user has no org but is instance admin (first user), assign to default org
    if user.org_id is None:
        from .organizations import list_orgs
        from .users import update_user_org
        
        orgs = list_orgs()
        if orgs and user.is_instance_admin:
            # First user without org - assign to first/default org
            logger = logging.getLogger(__name__)
            logger.warning(
                f"User {user.username} (instance admin) has no organization. "
                f"Auto-assigning to default organization {orgs[0].id}"
            )
            update_user_org(user.id, orgs[0].id, is_admin=True)
            # Reload user to get updated org_id
            user = get_user(username=token_data.username)
        elif not orgs and user.is_instance_admin:
            # No orgs exist - create default org for instance admin
            logger = logging.getLogger(__name__)
            logger.warning(
                f"User {user.username} (instance admin) has no organization and no orgs exist. "
                "This should not happen - registration should have created default org."
            )
            # This is a data inconsistency - log warning but don't fail auth
            # The user should create an org via the UI
        elif user.org_id is None:
            # Non-admin user without org - this violates architecture
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to an organization. Please create or join an organization."
            )
    
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    # Instance admins and org admins both have admin privileges
    if not (current_user.is_admin or current_user.is_instance_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
        )
    return current_user


async def get_current_instance_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_instance_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Instance Admin privileges required"
        )
    return current_user


def validate_org_access(user: User, target_org_id: str):
    """
    Validate that the user has access to the target organization.
    Instance admins can access any organization.
    Org admins can only access their own organization.
    """
    if user.is_instance_admin:
        return

    if user.org_id != target_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this organization"
        )
