"""Admin API routes for user management."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import get_current_admin_user
from .users import User, UserResponse, get_all_users, update_user_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


class UserRoleUpdate(BaseModel):
    is_admin: bool


@router.get("", response_model=list[UserResponse])
async def list_users(current_user: User = Depends(get_current_admin_user)):
    """List all users."""
    users = get_all_users()
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            is_admin=u.is_admin,
            is_instance_admin=u.is_instance_admin,
            org_id=u.org_id,
        )
        for u in users
    ]


@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role_endpoint(
    user_id: str, role_update: UserRoleUpdate, current_user: User = Depends(get_current_admin_user)
):
    """Update a user's role (promote/demote admin)."""
    # Prevent self-demotion to avoid locking out the only admin
    if user_id == current_user.id and not role_update.is_admin:
        raise HTTPException(status_code=400, detail="You cannot remove your own admin privileges.")

    updated_user = update_user_role(user_id, role_update.is_admin)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        is_admin=updated_user.is_admin,
        org_id=updated_user.org_id,
    )


@router.delete("/{user_id}")
async def delete_user_route(user_id: str, current_user: User = Depends(get_current_admin_user)):
    """
    Delete a user.
    Org Admins can only delete users in their own org.
    Instance Admins can delete anyone.
    """
    from .users import delete_user, get_user_by_id

    target_user = get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Permission Check
    if not current_user.is_instance_admin:
        # Org Admin check
        if target_user.org_id != current_user.org_id:
            raise HTTPException(
                status_code=403, detail="Cannot delete user from another organization"
            )

    # Prevent self-deletion via this route
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Cannot delete yourself via admin route. Use settings."
        )

    success = delete_user(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user")

    return {"status": "success", "message": f"User {user_id} deleted"}
