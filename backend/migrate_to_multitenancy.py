"""Migration script for multi-tenancy."""

import logging
import os
import shutil

from .config import DATA_DIR, PROJECT_ROOT
from .organizations import OrganizationCreate, create_org, list_orgs
from .users import _save_users, get_all_users

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Migrate data to multi-tenancy structure."""
    logger.info("Starting migration to multi-tenancy...")

    # 1. Check if Default Org exists
    orgs = list_orgs()
    default_org = None
    if orgs:
        default_org = orgs[0]
        logger.info(f"Found existing organization: {default_org.name} ({default_org.id})")
    else:
        logger.info("Creating Default Organization...")
        default_org = create_org(OrganizationCreate(name="Default Organization"))
        logger.info(f"Created Default Organization: {default_org.id}")

    org_dir = os.path.join(DATA_DIR, "organizations", default_org.id)

    # 2. Migrate Users
    logger.info("Migrating users...")
    users = get_all_users()
    updated_users = {}
    for user in users:
        if not user.org_id:
            user.org_id = default_org.id
            # First user becomes instance admin if not already
            if user.is_admin:  # Assuming existing admins should be instance admins for now?
                # Or strictly follow plan: "First user is always admin and instance admin"
                # Let's make all existing admins instance admins for safety in migration
                user.is_instance_admin = True
            logger.info(f"Assigned user {user.username} to org {default_org.id}")
        updated_users[user.username] = user

    if updated_users:
        _save_users(updated_users)

    # 3. Migrate Conversations
    logger.info("Migrating conversations...")
    conversations_dest = os.path.join(org_dir, "conversations")
    os.makedirs(conversations_dest, exist_ok=True)

    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json") and filename not in [
            "users.json",
            "voting_history.json",
            "organizations.json",
        ]:
            src = os.path.join(DATA_DIR, filename)
            dst = os.path.join(conversations_dest, filename)
            if not os.path.exists(dst):
                shutil.move(src, dst)
                logger.info(f"Moved conversation {filename}")
            else:
                logger.warning(f"Conversation {filename} already exists in destination, skipping.")

    # 4. Migrate Personalities
    logger.info("Migrating personalities...")
    personalities_src = os.path.join(PROJECT_ROOT, "data", "personalities")
    personalities_dest = os.path.join(org_dir, "personalities")
    os.makedirs(personalities_dest, exist_ok=True)

    if os.path.exists(personalities_src):
        # Move system-prompts.yaml to config/
        config_dest = os.path.join(org_dir, "config")
        os.makedirs(config_dest, exist_ok=True)

        sys_prompts_src = os.path.join(personalities_src, "system-prompts.yaml")
        sys_prompts_dst = os.path.join(config_dest, "system-prompts.yaml")

        if os.path.exists(sys_prompts_src) and not os.path.exists(sys_prompts_dst):
            shutil.copy2(
                sys_prompts_src, sys_prompts_dst
            )  # Copy to preserve original for now? Or move?
            # Let's copy for safety, user can delete old folder later
            logger.info("Copied system-prompts.yaml")

        # Move personality yamls
        for filename in os.listdir(personalities_src):
            if filename.endswith(".yaml") and filename != "system-prompts.yaml":
                src = os.path.join(personalities_src, filename)
                dst = os.path.join(personalities_dest, filename)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    logger.info(f"Copied personality {filename}")

    # 5. Migrate Voting History
    logger.info("Migrating voting history...")
    voting_src = os.path.join(PROJECT_ROOT, "data", "voting_history.json")
    voting_dst = os.path.join(org_dir, "voting_history.json")

    if os.path.exists(voting_src) and not os.path.exists(voting_dst):
        shutil.copy2(voting_src, voting_dst)
        logger.info("Copied voting_history.json")

    logger.info("Migration complete.")


if __name__ == "__main__":
    migrate()
