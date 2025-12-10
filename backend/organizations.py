"""Organization management module (SQLAlchemy)."""

import logging
import os
import shutil
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session
from pydantic import BaseModel

from .config import PROJECT_ROOT
from . import models
from .database import SessionLocal

logger = logging.getLogger(__name__)

# Legacy paths - kept only for cleanup or file-based artifacts (personalities/config)
ORGS_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "organizations")


class Organization(BaseModel):
    id: str
    name: str
    owner_email: str | None = None
    owner_id: str | None = None
    created_at: str | datetime
    settings: dict[str, Any] = {}
    api_config: dict[str, str] | None = None

    class Config:
        from_attributes = True

class OrganizationCreate(BaseModel):
    name: str
    owner_email: str | None = None

class OrganizationInDB(Organization):
    pass


def ensure_orgs_dir():
    """Ensure the organizations data directory exists (for file-based artifacts)."""
    os.makedirs(ORGS_DATA_DIR, exist_ok=True)


def get_org(org_id: str, db: Session = None) -> OrganizationInDB | None:
    """Get an organization by ID."""
    if db:
       return _get_org_with_session(db, org_id)
        
    with SessionLocal() as session:
        return _get_org_with_session(session, org_id)

def _get_org_with_session(db: Session, org_id: str) -> OrganizationInDB | None:
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if org:
        return OrganizationInDB.from_orm(org)
    return None


def create_org(org_create: OrganizationCreate, owner_id: str = None, db: Session = None) -> OrganizationInDB:
    """Create a new organization."""
    # Logic: DB Entry + File Folder logic (for personalities/config)
    
    is_ephemeral = False
    if db is None:
        db = SessionLocal()
        is_ephemeral = True

    try:
        org_id = str(uuid.uuid4())
        new_org = models.Organization(
            id=org_id,
            name=org_create.name,
            owner_id=owner_id,
            # owner_email is not in model? Check models.py. 
            # Reviewing models.py: owner_email was NOT in Organisation model.
            # Storing it in settings for now if needed, or ignoring.
            # created_at defaults to utcnow in model
            settings={},
            api_config={}
        )
        db.add(new_org)
        
        if is_ephemeral:
            db.commit()
            db.refresh(new_org)

        # Still create directories for personalities/config/assets
        org_dir = os.path.join(ORGS_DATA_DIR, org_id)
        os.makedirs(org_dir, exist_ok=True)
        # os.makedirs(os.path.join(org_dir, "conversations"), exist_ok=True) # No longer needed for files!
        os.makedirs(os.path.join(org_dir, "personalities"), exist_ok=True)
        os.makedirs(os.path.join(org_dir, "config"), exist_ok=True)

        return OrganizationInDB.from_orm(new_org)
    except Exception as e:
        if is_ephemeral:
            db.rollback()
        logger.error(f"Error creating org: {e}")
        raise
    finally:
        if is_ephemeral:
            db.close()


def list_orgs() -> list[OrganizationInDB]:
    """List all organizations."""
    with SessionLocal() as db:
        orgs = db.query(models.Organization).all()
        return [OrganizationInDB.from_orm(o) for o in orgs]


def update_org(org_id: str, updates: dict[str, Any]) -> OrganizationInDB | None:
    """Update an organization."""
    with SessionLocal() as db:
        org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
        if not org:
            return None
            
        for key, value in updates.items():
            if hasattr(org, key):
                setattr(org, key, value)
        
        db.commit()
        db.refresh(org)
        return OrganizationInDB.from_orm(org)


def get_org_api_config(org_id: str) -> tuple[str, str]:
    """
    Get the API key and base URL for an organization.
    Prioritizes organization settings, falls back to environment variables.
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
            raise ValueError("Failed to decrypt organization API key. Please update settings.")
            
    if not api_key:
        api_key = OPENROUTER_API_KEY

    if not api_key:
         # Simplified error for dev environment?
         pass # Caller handles nulls if needed, or raises later.

    # 2. Determine Base URL
    base_url = api_config.get("base_url") or OPENROUTER_API_URL
    
    return api_key, base_url
