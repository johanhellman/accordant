import os
import shutil
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.auth import create_access_token
from backend.main import app
from backend.users import UserInDB, create_user

client = TestClient(app)


@pytest.fixture
def clean_data():
    # Backup
    # Note: This is a simplified backup that might not cover all orgs in a real scenario
    # but sufficient for this test which uses specific orgs.
    # We'll skip backup/restore of file-based storage for now as it's complex with multi-tenancy
    # and instead rely on the test creating unique data or cleaning up what it creates.

    # Clean
    from backend import models
    from backend.database import SystemSessionLocal

    with SystemSessionLocal() as db:
        db.query(models.User).delete()
        db.commit()

    # Clean up test-org data
    from backend.organizations import ORGS_DATA_DIR

    test_org_path = os.path.join(ORGS_DATA_DIR, "test-org")
    if os.path.exists(test_org_path):
        shutil.rmtree(test_org_path)

    yield

    # Cleanup after test
    if os.path.exists(test_org_path):
        shutil.rmtree(test_org_path)


def test_multi_user_voting_attribution(clean_data):
    # 1. Create two users
    user1 = UserInDB(
        id=str(uuid.uuid4()),
        username="user1",
        password_hash="hash",
        is_admin=True,
        org_id="test-org",
    )
    user2 = UserInDB(
        id=str(uuid.uuid4()),
        username="user2",
        password_hash="hash",
        is_admin=False,
        org_id="test-org",
    )
    create_user(user1)
    create_user(user2)

    # 2. Login as User 1
    token1 = create_access_token(data={"sub": "user1"})
    headers1 = {"Authorization": f"Bearer {token1}"}

    # 3. Create conversation and vote as User 1
    # We'll simulate a vote by manually calling the internal function or mocking the full flow.
    # For simplicity, let's use the API flow but mock the LLM part if possible,
    # or just manually inject a vote record to test the retrieval logic if the recording logic is too complex to integration test here.
    # Actually, let's test the admin endpoint's enrichment logic.

    from backend.voting_history import record_votes
    from backend.storage import create_conversation

    # Create conversations first so the JOIN works
    create_conversation("conv1", user_id=user1.id, org_id="test-org")

    record_votes(
        conversation_id="conv1",
        stage2_results=[{"model": "gpt-4", "parsed_ranking": ["A"]}],
        label_to_model={"A": "claude-3"},
        user_id=user1.id,
        org_id="test-org",
    )

    # 4. Record vote for User 2
    create_conversation("conv2", user_id=user2.id, org_id="test-org")
    record_votes(
        conversation_id="conv2",
        stage2_results=[{"model": "gpt-4", "parsed_ranking": ["A"]}],
        label_to_model={"A": "claude-3"},
        user_id=user2.id,
        org_id="test-org",
    )

    # 5. Fetch voting history as Admin (User 1)
    response = client.get("/api/votes", headers=headers1)
    assert response.status_code == 200
    history = response.json()

    assert len(history) == 2
    # Verify enrichment
    usernames = {h["username"] for h in history}
    assert "user1" in usernames
    assert "user2" in usernames


def test_admin_user_management(clean_data):
    # 1. Create Admin and Normal User
    admin = UserInDB(
        id=str(uuid.uuid4()),
        username="admin",
        password_hash="hash",
        is_admin=True,
        org_id="test-org",
    )
    user = UserInDB(
        id=str(uuid.uuid4()),
        username="user",
        password_hash="hash",
        is_admin=False,
        org_id="test-org",
    )
    create_user(admin)
    create_user(user)

    token = create_access_token(data={"sub": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    # 2. List users
    response = client.get("/api/admin/users", headers=headers)
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 2

    # 3. Promote user
    response = client.put(
        f"/api/admin/users/{user.id}/role", json={"is_admin": True}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["is_admin"]

    # Verify persistence
    response = client.get("/api/admin/users", headers=headers)
    updated_user = next(u for u in response.json() if u["id"] == user.id)
    assert updated_user["is_admin"]
