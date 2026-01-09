"""Tests for invitations.py invitation management."""

import json
import os
import tempfile
from datetime import UTC, datetime, timedelta

import pytest

from backend.invitations import (
    Invitation,
    InvitationCreate,
    create_invitation,
    get_invitation,
    list_org_invitations,
    use_invitation,
)


class TestInvitations:
    """Tests for invitation management functions."""

    @pytest.fixture
    def temp_invitations_file(self, monkeypatch):
        """Create a temporary invitations file for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invitations_file = os.path.join(tmpdir, "invitations.json")
            monkeypatch.setattr("backend.invitations.INVITATIONS_FILE", invitations_file)
            yield invitations_file

    def test_create_invitation(self, temp_invitations_file):
        """Test creating a new invitation."""
        invitation = create_invitation("org1", "user1", expires_in_days=7)

        assert invitation.org_id == "org1"
        assert invitation.created_by == "user1"
        assert invitation.code is not None
        assert len(invitation.code) > 0
        assert invitation.is_active is True
        assert invitation.used_by is None
        assert invitation.created_at is not None
        assert invitation.expires_at is not None

        # Verify file was created
        assert os.path.exists(temp_invitations_file)

        # Verify invitation was saved
        with open(temp_invitations_file) as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["code"] == invitation.code

    def test_create_invitation_custom_expiry(self, temp_invitations_file):
        """Test creating invitation with custom expiry days."""
        invitation = create_invitation("org1", "user1", expires_in_days=30)

        expires_at = datetime.fromisoformat(invitation.expires_at)
        created_at = datetime.fromisoformat(invitation.created_at)
        days_diff = (expires_at - created_at).days

        # Allow for small timing differences (29-30 days)
        assert 29 <= days_diff <= 30

    def test_get_invitation_existing(self, temp_invitations_file):
        """Test retrieving an existing invitation."""
        created = create_invitation("org1", "user1")

        retrieved = get_invitation(created.code)

        assert retrieved is not None
        assert retrieved.code == created.code
        assert retrieved.org_id == created.org_id
        assert retrieved.created_by == created.created_by

    def test_get_invitation_not_found(self, temp_invitations_file):
        """Test retrieving non-existent invitation returns None."""
        result = get_invitation("non-existent-code")
        assert result is None

    def test_use_invitation_success(self, temp_invitations_file):
        """Test successfully using an invitation."""
        invitation = create_invitation("org1", "user1")

        result = use_invitation(invitation.code, "user2")

        assert result is True

        # Verify invitation was marked as used
        updated = get_invitation(invitation.code)
        assert updated is not None
        assert updated.used_by == "user2"
        assert updated.is_active is False

    def test_use_invitation_already_used(self, temp_invitations_file):
        """Test using an already-used invitation returns False."""
        invitation = create_invitation("org1", "user1")
        use_invitation(invitation.code, "user2")

        # Try to use again
        result = use_invitation(invitation.code, "user3")

        assert result is False

    def test_use_invitation_expired(self, temp_invitations_file):
        """Test using an expired invitation returns False."""
        # Create invitation with past expiry
        invitation = create_invitation("org1", "user1", expires_in_days=-1)

        result = use_invitation(invitation.code, "user2")

        assert result is False

    def test_use_invitation_not_found(self, temp_invitations_file):
        """Test using non-existent invitation returns False."""
        result = use_invitation("non-existent-code", "user1")
        assert result is False

    def test_use_invitation_inactive(self, temp_invitations_file):
        """Test using an inactive invitation returns False."""
        invitation = create_invitation("org1", "user1")
        # Manually mark as inactive
        invitation.is_active = False
        with open(temp_invitations_file, "w") as f:
            json.dump([invitation.model_dump()], f)

        result = use_invitation(invitation.code, "user2")

        assert result is False

    def test_list_org_invitations(self, temp_invitations_file):
        """Test listing invitations for an organization."""
        # Create invitations for different orgs
        inv1 = create_invitation("org1", "user1")
        inv2 = create_invitation("org1", "user1")
        inv3 = create_invitation("org2", "user2")

        invitations = list_org_invitations("org1")

        assert len(invitations) == 2
        assert all(inv.org_id == "org1" for inv in invitations)
        assert inv1.code in [inv.code for inv in invitations]
        assert inv2.code in [inv.code for inv in invitations]
        assert inv3.code not in [inv.code for inv in invitations]

    def test_list_org_invitations_empty(self, temp_invitations_file):
        """Test listing invitations when none exist."""
        invitations = list_org_invitations("org1")
        assert invitations == []

    def test_list_org_invitations_filters_by_org(self, temp_invitations_file):
        """Test that list_org_invitations only returns invitations for specified org."""
        create_invitation("org1", "user1")
        create_invitation("org2", "user2")
        create_invitation("org2", "user2")

        invitations = list_org_invitations("org2")

        assert len(invitations) == 2
        assert all(inv.org_id == "org2" for inv in invitations)

    def test_invitation_model_validation(self):
        """Test that Invitation model validates correctly."""
        now = datetime.now(UTC).isoformat()
        expires = (datetime.now(UTC) + timedelta(days=7)).isoformat()

        invitation = Invitation(
            code="test-code",
            org_id="org1",
            created_by="user1",
            created_at=now,
            expires_at=expires,
        )

        assert invitation.code == "test-code"
        assert invitation.org_id == "org1"
        assert invitation.is_active is True
        assert invitation.used_by is None

    def test_invitation_create_model(self):
        """Test InvitationCreate model."""
        create = InvitationCreate(org_id="org1", expires_in_days=14)

        assert create.org_id == "org1"
        assert create.expires_in_days == 14

    def test_invitation_create_default_expiry(self):
        """Test InvitationCreate defaults to 7 days."""
        create = InvitationCreate(org_id="org1")

        assert create.expires_in_days == 7
