"""Tests for organization route endpoints."""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from backend.main import app


class TestOrgRoutes:
    """Tests for organization route endpoints."""

    @pytest.fixture
    def temp_data_dir(self, monkeypatch):
        """Create a temporary data directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orgs_file = os.path.join(tmpdir, "organizations.json")
            orgs_data_dir = os.path.join(tmpdir, "organizations")
            users_file = os.path.join(tmpdir, "users.json")
            invitations_file = os.path.join(tmpdir, "invitations.json")
            os.makedirs(orgs_data_dir, exist_ok=True)
            monkeypatch.setattr("backend.organizations.ORGS_FILE", orgs_file)
            monkeypatch.setattr("backend.organizations.ORGS_DATA_DIR", orgs_data_dir)
            monkeypatch.setattr("backend.config.PROJECT_ROOT", tmpdir)
            monkeypatch.setattr("backend.users.USERS_FILE", users_file)
            monkeypatch.setattr("backend.invitations.INVITATIONS_FILE", invitations_file)
            yield tmpdir

    def get_auth_headers(self, client, username="testuser", password="password"):
        """Helper to register and login, returning auth headers."""
        # Register
        client.post("/api/auth/register", json={"username": username, "password": password})
        # Login
        response = client.post("/api/auth/token", data={"username": username, "password": password})
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        return headers

    def test_join_organization_success(self, temp_data_dir):
        """Test joining organization with valid invitation code."""
        client = TestClient(app)

        # Create org and admin user
        admin_headers = self.get_auth_headers(client, username="admin", password="admin")
        org_resp = client.post(
            "/api/organizations/",
            json={"name": "Test Org", "owner_email": "admin@test.com"},
            headers=admin_headers,
        )
        org_id = org_resp.json()["id"]

        # Create invitation as admin
        invite_resp = client.post("/api/organizations/invitations", headers=admin_headers)
        invite_code = invite_resp.json()["code"]

        # Create new user to join
        user_headers = self.get_auth_headers(client, username="newuser", password="newpass")

        # Join organization
        response = client.post(
            "/api/organizations/join", json={"invite_code": invite_code}, headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["org_id"] == org_id

        # Verify user's org_id was updated
        me_resp = client.get("/api/auth/me", headers=user_headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["org_id"] == org_id

    def test_join_organization_invalid_code(self, temp_data_dir):
        """Test joining organization with invalid invitation code returns 404."""
        client = TestClient(app)
        headers = self.get_auth_headers(client)

        response = client.post(
            "/api/organizations/join", json={"invite_code": "invalid-code"}, headers=headers
        )

        assert response.status_code == 404
        assert "Invalid invitation code" in response.json()["detail"]

    def test_join_organization_expired_code(self, temp_data_dir):
        """Test joining organization with expired invitation code returns 400."""
        client = TestClient(app)

        # Create org and admin user
        admin_headers = self.get_auth_headers(client, username="admin", password="admin")
        client.post(
            "/api/organizations/",
            json={"name": "Test Org", "owner_email": "admin@test.com"},
            headers=admin_headers,
        )

        # Create invitation
        invite_resp = client.post("/api/organizations/invitations", headers=admin_headers)
        invite_code = invite_resp.json()["code"]

        # Mark invitation as used/expired
        from backend.invitations import get_invitation, use_invitation

        invitation = get_invitation(invite_code)
        if invitation:
            use_invitation(invite_code, "some-user-id")

        # Try to join with expired code
        user_headers = self.get_auth_headers(client, username="newuser", password="newpass")
        response = client.post(
            "/api/organizations/join", json={"invite_code": invite_code}, headers=user_headers
        )

        assert response.status_code == 400
        assert (
            "expired" in response.json()["detail"].lower()
            or "already used" in response.json()["detail"].lower()
        )

    def test_join_organization_updates_user_org(self, temp_data_dir):
        """Test join_organization updates user's org_id."""
        client = TestClient(app)

        # Create org and admin user
        admin_headers = self.get_auth_headers(client, username="admin", password="admin")
        org_resp = client.post(
            "/api/organizations/",
            json={"name": "Test Org", "owner_email": "admin@test.com"},
            headers=admin_headers,
        )
        org_id = org_resp.json()["id"]

        # Create invitation
        invite_resp = client.post("/api/organizations/invitations", headers=admin_headers)
        invite_code = invite_resp.json()["code"]

        # Create new user
        user_headers = self.get_auth_headers(client, username="newuser", password="newpass")

        # Verify user starts with no org_id or different org_id
        me_before = client.get("/api/auth/me", headers=user_headers)
        initial_org_id = me_before.json().get("org_id")

        # Join organization
        response = client.post(
            "/api/organizations/join", json={"invite_code": invite_code}, headers=user_headers
        )
        assert response.status_code == 200

        # Verify user's org_id was updated
        me_after = client.get("/api/auth/me", headers=user_headers)
        assert me_after.json()["org_id"] == org_id
        assert me_after.json()["org_id"] != initial_org_id
