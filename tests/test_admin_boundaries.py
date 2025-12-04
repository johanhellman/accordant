import pytest
from fastapi import HTTPException

from backend.auth import validate_org_access
from backend.users import User


def test_validate_org_access_success():
    """Test that access is granted when org_ids match."""
    user = User(id="u1", username="admin", password_hash="hash", is_admin=True, org_id="org1")
    # Should not raise
    validate_org_access(user, "org1")


def test_validate_org_access_instance_admin():
    """Test that instance admin can access any org."""
    user = User(
        id="u1",
        username="sysadmin",
        password_hash="hash",
        is_admin=True,
        is_instance_admin=True,
        org_id="org1",
    )
    # Should not raise for any org
    validate_org_access(user, "org2")


def test_validate_org_access_denied():
    """Test that access is denied when org_ids mismatch."""
    user = User(id="u1", username="admin", password_hash="hash", is_admin=True, org_id="org1")

    with pytest.raises(HTTPException) as exc:
        validate_org_access(user, "org2")

    assert exc.value.status_code == 403
    assert "Access denied" in exc.value.detail
