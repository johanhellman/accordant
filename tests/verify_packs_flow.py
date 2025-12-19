import logging
import os
import sys
import uuid

from fastapi.testclient import TestClient

# Setup path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)


def verify_packs_flow():
    """
    E2E Verification of Council Packs Flow:
    1. Register User & Org
    2. Create Custom Pack
    3. Apply Custom Pack
    4. Verify Active Configuration
    """

    # Unique suffix to avoid collisions if DB persists
    suffix = str(uuid.uuid4())[:8]
    username = f"verify_packs_{suffix}"
    password = "password123"
    org_name = f"Org {suffix}"

    logger.info(f"Step 1: Registering user {username}...")
    reg_resp = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": password,
            "mode": "create_org",
            "org_name": org_name,
        },
    )
    if reg_resp.status_code != 200:
        logger.error(f"Registration failed: {reg_resp.text}")
        sys.exit(1)

    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    logger.info("Step 2: Creating Custom Pack...")
    pack_config = {
        "personalities": [
            "gpt_architect",
            "claude_poet",
        ],  # Assuming these exist or handled gracefully
        "consensus_strategy": "test_strategy",
        "system_prompts": {"base_system_prompt": "You are a test council."},
    }

    create_resp = client.post(
        "/api/config/packs",
        headers=headers,
        json={
            "display_name": "E2E Test Pack",
            "description": "Created by verification script",
            "config": pack_config,
        },
    )

    if create_resp.status_code != 200:
        logger.error(f"Create pack failed: {create_resp.text}")
        # It might fail if personalities don't exist in registry?
        # PackService doesn't validate existence strictly yet, so should pass.
        sys.exit(1)

    pack_id = create_resp.json()["id"]
    logger.info(f"Pack Created: {pack_id}")

    logger.info("Step 3: Applying Pack...")
    apply_resp = client.post(f"/api/config/packs/{pack_id}/apply", headers=headers)

    if apply_resp.status_code != 200:
        logger.error(f"Apply pack failed: {apply_resp.text}")
        sys.exit(1)

    logger.info("Pack Applied.")

    logger.info("Step 4: Verifying Active Configuration...")
    active_resp = client.get("/api/config/active", headers=headers)

    if active_resp.status_code != 200:
        logger.error(f"Get active config failed: {active_resp.text}")
        sys.exit(1)

    active_data = active_resp.json()
    assert active_data["active_pack_id"] == pack_id
    assert active_data["personalities"] == pack_config["personalities"]
    assert active_data["system_prompts"]["base_system_prompt"] == "You are a test council."

    logger.info("Configuration Verified.")

    print("SUCCESS: Council Packs E2E Flow Verified.")


if __name__ == "__main__":
    try:
        verify_packs_flow()
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        sys.exit(1)
