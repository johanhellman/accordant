"""Organization management module."""

import json
import logging
import os
import shutil
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from .config import PROJECT_ROOT

logger = logging.getLogger(__name__)

ORGS_FILE = os.path.join(PROJECT_ROOT, "data", "organizations.json")
ORGS_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "organizations")


class Organization(BaseModel):
    id: str
    name: str
    owner_email: str | None = None
    owner_id: str | None = None
    created_at: str
    settings: dict[str, Any] = {}
    api_config: dict[str, str] | None = None  # Encrypted API configuration


class OrganizationCreate(BaseModel):
    name: str
    owner_email: str | None = None


class OrganizationInDB(Organization):
    pass


def ensure_orgs_dir():
    """Ensure the organizations data directory exists."""
    os.makedirs(ORGS_DATA_DIR, exist_ok=True)


def _load_orgs() -> dict[str, OrganizationInDB]:
    """Load organizations from JSON file."""
    if not os.path.exists(ORGS_FILE):
        return {}
    try:
        with open(ORGS_FILE) as f:
            data = json.load(f)
            return {o["id"]: OrganizationInDB(**o) for o in data}
    except Exception as e:
        logger.error(f"Error loading organizations: {e}")
        return {}


def _save_orgs(orgs: dict[str, OrganizationInDB]):
    """Save organizations to JSON file."""
    try:
        os.makedirs(os.path.dirname(ORGS_FILE), exist_ok=True)
        with open(ORGS_FILE, "w") as f:
            json.dump([o.dict() for o in orgs.values()], f, indent=2)
    except Exception as e:
        logger.error(f"Error saving organizations: {e}")
        raise


def get_org(org_id: str) -> OrganizationInDB | None:
    """Get an organization by ID."""
    orgs = _load_orgs()
    return orgs.get(org_id)


def create_org(org_create: OrganizationCreate, owner_id: str = None) -> OrganizationInDB:
    """Create a new organization."""
    orgs = _load_orgs()

    org_id = str(uuid.uuid4())
    new_org = OrganizationInDB(
        id=org_id,
        name=org_create.name,
        owner_email=org_create.owner_email,
        owner_id=owner_id,
        created_at=datetime.utcnow().isoformat(),
        settings={},
    )

    orgs[org_id] = new_org
    _save_orgs(orgs)

    # Create Org Directory
    org_dir = os.path.join(ORGS_DATA_DIR, org_id)
    os.makedirs(org_dir, exist_ok=True)
    os.makedirs(os.path.join(org_dir, "conversations"), exist_ok=True)
    personalities_dest = os.path.join(org_dir, "personalities")
    os.makedirs(personalities_dest, exist_ok=True)
    config_dest = os.path.join(org_dir, "config")
    os.makedirs(config_dest, exist_ok=True)

    # Copy default personalities from data/personalities/ to the new org
    personalities_src = os.path.join(PROJECT_ROOT, "data", "personalities")
    if os.path.exists(personalities_src):
        # Copy system-prompts.yaml to config/
        sys_prompts_src = os.path.join(personalities_src, "system-prompts.yaml")
        sys_prompts_dst = os.path.join(config_dest, "system-prompts.yaml")

        if os.path.exists(sys_prompts_src):
            try:
                shutil.copy2(sys_prompts_src, sys_prompts_dst)
                logger.info(f"Copied system-prompts.yaml to org {org_id}")
            except Exception as e:
                logger.error(f"Error copying system-prompts.yaml for org {org_id}: {e}")

        # Copy all personality yaml files (except system-prompts.yaml)
        for filename in os.listdir(personalities_src):
            if filename.endswith(".yaml") and filename != "system-prompts.yaml":
                src = os.path.join(personalities_src, filename)
                dst = os.path.join(personalities_dest, filename)
                try:
                    shutil.copy2(src, dst)
                    logger.info(f"Copied personality {filename} to org {org_id}")
                except Exception as e:
                    logger.error(f"Error copying personality {filename} for org {org_id}: {e}")

    return new_org


def list_orgs() -> list[OrganizationInDB]:
    """List all organizations."""
    orgs = _load_orgs()
    return list(orgs.values())


def update_org(org_id: str, updates: dict[str, Any]) -> OrganizationInDB | None:
    """Update an organization."""
    orgs = _load_orgs()
    if org_id not in orgs:
        return None

    org = orgs[org_id]

    # Apply updates
    for key, value in updates.items():
        if hasattr(org, key):
            setattr(org, key, value)

    orgs[org_id] = org
    _save_orgs(orgs)
    return org


def get_org_api_config(org_id: str) -> tuple[str, str]:
    """
    Get the API key and base URL for an organization.
    Raises ValueError if not configured.
    """
    from .config import OPENROUTER_API_KEY
    from .security import decrypt_value

    org = get_org(org_id)
    if not org:
        raise ValueError("Organization not found")

    api_config = org.api_config
    if not api_config or not api_config.get("api_key"):
        # Fallback to global key if available (for migration/default org)
        if OPENROUTER_API_KEY:
            return OPENROUTER_API_KEY, "https://openrouter.ai/api/v1/chat/completions"

        raise ValueError(
            "LLM API Key not configured for this organization. Please ask an admin to configure it in Settings."
        )

    try:
        api_key = decrypt_value(api_config["api_key"])
        base_url = api_config.get("base_url", "https://openrouter.ai/api/v1/chat/completions")
        return api_key, base_url
    except Exception as e:
        raise ValueError("Failed to decrypt API key") from e
