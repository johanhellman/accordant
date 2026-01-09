"""Invitation management module."""

import json
import logging
import os
import secrets
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

from .config import PROJECT_ROOT

logger = logging.getLogger(__name__)

INVITATIONS_FILE = os.path.join(PROJECT_ROOT, "data", "invitations.json")


class Invitation(BaseModel):
    code: str
    org_id: str
    created_by: str  # User ID of creator
    created_at: str
    expires_at: str
    used_by: str | None = None  # User ID who used it
    is_active: bool = True


class InvitationCreate(BaseModel):
    org_id: str
    expires_in_days: int = 7


class InvitationInDB(Invitation):
    pass


def _load_invitations() -> dict[str, InvitationInDB]:
    """Load invitations from JSON file."""
    if not os.path.exists(INVITATIONS_FILE):
        return {}
    try:
        with open(INVITATIONS_FILE) as f:
            data = json.load(f)
            return {i["code"]: InvitationInDB(**i) for i in data}
    except Exception as e:
        logger.error(f"Error loading invitations: {e}")
        return {}


def _save_invitations(invitations: dict[str, InvitationInDB]):
    """Save invitations to JSON file."""
    try:
        os.makedirs(os.path.dirname(INVITATIONS_FILE), exist_ok=True)
        with open(INVITATIONS_FILE, "w") as f:
            json.dump([i.dict() for i in invitations.values()], f, indent=2)
    except Exception as e:
        logger.error(f"Error saving invitations: {e}")
        raise


def create_invitation(org_id: str, created_by: str, expires_in_days: int = 7) -> InvitationInDB:
    """Create a new invitation code."""
    invitations = _load_invitations()

    # Generate a secure random code
    code = secrets.token_urlsafe(16)

    expires_at = (datetime.now(UTC) + timedelta(days=expires_in_days)).isoformat()

    new_invitation = InvitationInDB(
        code=code,
        org_id=org_id,
        created_by=created_by,
        created_at=datetime.now(UTC).isoformat(),
        expires_at=expires_at,
    )

    invitations[code] = new_invitation
    _save_invitations(invitations)
    return new_invitation


def get_invitation(code: str) -> InvitationInDB | None:
    """Get an invitation by code."""
    invitations = _load_invitations()
    return invitations.get(code)


def use_invitation(code: str, user_id: str) -> bool:
    """Mark an invitation as used."""
    invitations = _load_invitations()
    if code not in invitations:
        return False

    invitation = invitations[code]

    # Check if valid
    if not invitation.is_active:
        return False
    if invitation.used_by:
        return False
    if datetime.fromisoformat(invitation.expires_at) < datetime.now(UTC):
        return False

    invitation.used_by = user_id
    invitation.is_active = False  # One-time use? Or multi-use? Plan didn't specify.
    # Usually invite links are multi-use or single-use.
    # Actually, "Invite Link" usually implies multi-use for a team.
    # But "Secret Code" might be single use.
    # Let's make it single-use for now for stricter control, or add a flag.
    # Let's assume single-use for this implementation to be safe.

    invitations[code] = invitation
    _save_invitations(invitations)
    return True


def list_org_invitations(org_id: str) -> list[InvitationInDB]:
    """List all invitations for an organization."""
    invitations = _load_invitations()
    return [i for i in invitations.values() if i.org_id == org_id]
