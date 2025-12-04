"""Organization and Invitation routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .auth import (
    get_current_admin_user,
    get_current_user,
)
from .invitations import create_invitation, get_invitation, list_org_invitations, use_invitation
from .organizations import (
    Organization,
    OrganizationCreate,
    create_org,
    list_orgs,
)
from .users import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


class CreateOrgRequest(BaseModel):
    name: str
    owner_email: str


class JoinOrgRequest(BaseModel):
    invite_code: str


class InvitationResponse(BaseModel):
    code: str
    expires_at: str
    is_active: bool


# --- Org Management (Authenticated Users) ---


@router.post("/", response_model=Organization)
async def create_new_organization(
    request: CreateOrgRequest, current_user: User = Depends(get_current_user)
):
    """Create a new organization."""
    # Check if this is the first organization being created
    # The first org becomes the "default" organization (first org in the system)
    existing_orgs = list_orgs()
    is_first_org = len(existing_orgs) == 0

    if is_first_org:
        logger.info(
            f"Creating first organization '{request.name}' by user {current_user.username}. "
            "This organization will be the default organization."
        )

    org_create = OrganizationCreate(name=request.name, owner_email=request.owner_email)
    new_org = create_org(org_create, owner_id=current_user.id)

    # Update user's org_id and make them admin of the new org
    from .users import update_user_org

    update_user_org(current_user.id, new_org.id, is_admin=True)

    return new_org


@router.post("/join")
async def join_organization(
    request: JoinOrgRequest, current_user: User = Depends(get_current_user)
):
    """Join an organization using an invite code."""
    invitation = get_invitation(request.invite_code)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid invitation code")

    if not invitation.is_active:
        raise HTTPException(status_code=400, detail="Invitation code expired or already used")

    # Mark as used
    success = use_invitation(request.invite_code, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to use invitation")

    # Update user's org
    from .users import update_user_org

    update_user_org(current_user.id, invitation.org_id, is_admin=False)

    return {"status": "success", "org_id": invitation.org_id}


# --- Organization Listing (Instance Admins) ---


@router.get("/list", response_model=list[Organization])
async def list_organizations(current_user: User = Depends(get_current_admin_user)):
    """List all organizations. Instance admins only."""
    if not current_user.is_instance_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instance admins can list all organizations",
        )
    return list_orgs()


# --- Invitation Management (Org Admins) ---


@router.post("/invitations", response_model=InvitationResponse)
async def create_org_invitation(current_user: User = Depends(get_current_admin_user)):
    """Generate a new invitation code for the current organization."""
    invitation = create_invitation(current_user.org_id, current_user.id)
    return {
        "code": invitation.code,
        "expires_at": invitation.expires_at,
        "is_active": invitation.is_active,
    }


@router.get("/invitations", response_model=list[InvitationResponse])
async def get_org_invitations(current_user: User = Depends(get_current_admin_user)):
    """List active invitations for the current organization."""
    invitations = list_org_invitations(current_user.org_id)
    return [
        {"code": i.code, "expires_at": i.expires_at, "is_active": i.is_active} for i in invitations
    ]
