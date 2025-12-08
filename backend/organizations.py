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

    # Note: We no longer copy default personalities or system prompts.
    # The system now uses runtime inheritance from data/defaults/.
    # This allows global updates to propagate to all organizations 
    # unless they have explicitly overridden a value.

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
    Prioritizes organization settings, falls back to environment variables.
    Allows mixing (e.g., Global Key + Custom URL).
    """
    from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL
    from .security import decrypt_value

    org = get_org(org_id)
    if not org:
        raise ValueError("Organization not found")

    api_config = org.api_config or {}
    
    # 1. Determine API Key
    api_key = None
    if api_config.get("api_key"):
        try:
            api_key = decrypt_value(api_config["api_key"])
        except Exception:
            # If decryption fails (e.g. key rotation), log invalid but continue to fallback?
            # Or raise? If stored key is bad, we probably shouldn't fallback to global silently 
            # unless we explicitly decide to. But for robustness let's try fallback if decryption fails?
            # No, standard security practice: if configured key fails, fail hard. 
            # However, here we have a known issue with temp keys on restart.
            # If we raise, the user is stuck. If we fallback, they might use global key.
            # Given the dev environment context, failing hard is safer to alert user.
            raise ValueError("Failed to decrypt organization API key. Please update settings.")
            
    if not api_key:
        api_key = OPENROUTER_API_KEY

    if not api_key:
         raise ValueError(
            "LLM API Key not configured. Please set 'api_key' in Organization Settings or 'LLM_API_KEY' in environment."
        )

    # 2. Determine Base URL
    # Use Org URL if present, else Global URL (env var), else Default
    base_url = api_config.get("base_url") or OPENROUTER_API_URL
    
    return api_key, base_url
