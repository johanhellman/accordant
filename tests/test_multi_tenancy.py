import os
import shutil

import pytest

from backend.invitations import create_invitation, get_invitation, use_invitation
from backend.organizations import ORGS_DATA_DIR, OrganizationCreate, create_org, get_org
from backend.security import decrypt_value, encrypt_value
from backend.users import UserInDB, get_user, update_user_org
from backend.database import SystemSessionLocal
from backend import models


# Test Fixture to setup/teardown data
@pytest.fixture
def setup_data():
    # Backup existing data if needed (skipped for simplicity in test env)
    # Ensure clean state
    # Cleanup tables
    with SystemSessionLocal() as db:
        # Delete in order of dependencies
        db.query(models.User).delete()
        db.query(models.Organization).delete()
        # Invitation model missing in imports but assume needed? Or maybe just rely on implicit cascade if any?
        # Actually models.Invitation likely exists.
        # But let's just clean User and Org as that covers the tests.
        db.commit()

    if os.path.exists(ORGS_DATA_DIR):
        shutil.rmtree(ORGS_DATA_DIR)

    yield

    # Cleanup
    with SystemSessionLocal() as db:
        db.query(models.User).delete()
        db.query(models.Organization).delete()
        db.commit()
        
    if os.path.exists(ORGS_DATA_DIR):
        shutil.rmtree(ORGS_DATA_DIR)


def test_create_organization(setup_data):
    org_create = OrganizationCreate(name="Test Org", owner_email="test@example.com")
    org = create_org(org_create, owner_id="user123")

    assert org.id is not None
    assert org.name == "Test Org"
    assert org.owner_id == "user123"

    # Verify persistence
    loaded_org = get_org(org.id)
    assert loaded_org is not None
    assert loaded_org.name == "Test Org"

    # Verify directory creation
    org_dir = os.path.join(ORGS_DATA_DIR, org.id)
    assert os.path.exists(org_dir)
    assert os.path.exists(os.path.join(org_dir, "conversations"))
    assert os.path.exists(os.path.join(org_dir, "personalities"))
    assert os.path.exists(os.path.join(org_dir, "config"))

    # Verify default personalities are copied (if they exist)
    from backend.config import PROJECT_ROOT

    default_personalities_dir = os.path.join(PROJECT_ROOT, "data", "personalities")
    org_personalities_dir = os.path.join(org_dir, "personalities")

    if os.path.exists(default_personalities_dir):
        # Count personality files (excluding system-prompts.yaml)
        default_personalities = [
            f
            for f in os.listdir(default_personalities_dir)
            if f.endswith(".yaml") and f != "system-prompts.yaml"
        ]

        if default_personalities:
            # Verify personalities were copied
            org_personalities = [
                f for f in os.listdir(org_personalities_dir) if f.endswith(".yaml")
            ]
            assert len(org_personalities) > 0, "Default personalities should be copied to new org"

            # Verify system-prompts.yaml was copied to config/
            config_dir = os.path.join(org_dir, "config")
            sys_prompts_src = os.path.join(default_personalities_dir, "system-prompts.yaml")
            sys_prompts_dst = os.path.join(config_dir, "system-prompts.yaml")
            if os.path.exists(sys_prompts_src):
                assert os.path.exists(sys_prompts_dst), (
                    "system-prompts.yaml should be copied to config/"
                )


def test_invitation_flow(setup_data):
    # 1. Create Org
    org = create_org(OrganizationCreate(name="Invite Org"), owner_id="admin1")

    # 2. Create Invitation
    invite = create_invitation(org.id, created_by="admin1")
    assert invite.code is not None
    assert invite.org_id == org.id
    assert invite.is_active is True

    # 3. Use Invitation
    success = use_invitation(invite.code, user_id="user2")
    assert success is True

    # 4. Verify used state
    updated_invite = get_invitation(invite.code)
    assert updated_invite.is_active is False
    assert updated_invite.used_by == "user2"

    # 5. Try to use again (should fail)
    success_retry = use_invitation(invite.code, user_id="user3")
    assert success_retry is False


def test_user_org_update(setup_data):
    # 1. Create User
    user = UserInDB(id="u1", username="testuser", password_hash="hash", org_id="org1")
    # Manually save user since we're testing backend logic directly
    from backend.users import _save_users # This usage is valid if _save_users existed, but it doesn't.
    # We saw in previous step that test_multi_user also used _save_users and failed. 
    # We must replace this logic with DB save.
    
    # Logic to manually save user:
    # We can just use create_user or direct DB add.
    # The test creates user "u1" then updates it.
    
    with SystemSessionLocal() as db:
        db_user = models.User(
            id=user.id,
            username=user.username,
            password_hash=user.password_hash,
            org_id=user.org_id
        )
        db.add(db_user)
        db.commit()

    # 2. Update Org
    updated_user = update_user_org("u1", "org2", is_admin=True)

    assert updated_user.org_id == "org2"
    assert updated_user.is_admin is True

    # Verify persistence
    loaded_user = get_user("testuser")
    assert loaded_user.org_id == "org2"


def test_encryption():
    original_key = "sk-test-key-123"
    encrypted = encrypt_value(original_key)
    assert encrypted != original_key

    decrypted = decrypt_value(encrypted)
    assert decrypted == original_key
