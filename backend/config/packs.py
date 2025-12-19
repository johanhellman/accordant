import json
import logging
import os
import uuid

import yaml
from sqlalchemy.orm import Session

from backend.config.paths import PROJECT_ROOT
from backend.config.personalities import get_all_personalities
from backend.models import CouncilConfiguration, CouncilPack

logger = logging.getLogger(__name__)

DEFAULTS_PACKS_DIR = os.path.join(PROJECT_ROOT, "data", "defaults", "packs")


class PackService:
    """Service for managing Council Packs (System + Custom)."""

    @staticmethod
    def get_all_packs(session: Session, org_id: str) -> list[dict]:
        """
        Get all available packs for an organization.
        Merges System Packs (YAML) and Custom Packs (DB).
        """
        packs = {}

        # 1. Load System Packs (YAML)
        if os.path.exists(DEFAULTS_PACKS_DIR):
            for filename in os.listdir(DEFAULTS_PACKS_DIR):
                if filename.endswith(".yaml"):
                    try:
                        filepath = os.path.join(DEFAULTS_PACKS_DIR, filename)
                        with open(filepath) as f:
                            data = yaml.safe_load(f)
                            if data and "id" in data:
                                # Ensure minimal fields
                                packs[data["id"]] = {
                                    "id": data["id"],
                                    "display_name": data.get("display_name", data["id"]),
                                    "description": data.get("description", ""),
                                    "is_system": True,
                                    "source": "system",
                                    # We keep the raw config inside 'config' for API consistency?
                                    # Or just flatten? Let's keep it structured.
                                    "config": {
                                        "personalities": data.get("personalities", []),
                                        "consensus_strategy": data.get("consensus_strategy"),
                                        "system_prompts": data.get("system_prompts", {}),
                                    },
                                }
                    except Exception as e:
                        logger.error(f"Failed to load system pack {filename}: {e}")

        # 2. Load Custom Packs (DB)
        # Note: We filter by 'is_system=False' usually, but here we just fetch all rows.
        # Ideally, we should add an ORG_ID column to council_packs if we want strict multi-tenant filtering
        # beyond DB isolation. But since it's Tenant DB, all rows are for this org.
        db_packs = session.query(CouncilPack).all()
        for p in db_packs:
            try:
                config = json.loads(p.config_json)
                packs[p.id] = {
                    "id": p.id,
                    "display_name": p.display_name,
                    "description": p.description,
                    "is_system": False,
                    "source": "custom",
                    "config": config,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
            except Exception as e:
                logger.error(f"Failed to parse custom pack {p.id}: {e}")

        return list(packs.values())

    @staticmethod
    def create_custom_pack(
        session: Session, display_name: str, config: dict, description: str = None
    ) -> dict:
        """Create a new custom pack in the DB."""
        new_id = str(uuid.uuid4())

        # Validate config structure basic check
        if "personalities" not in config:
            config["personalities"] = []

        config_json = json.dumps(config)

        new_pack = CouncilPack(
            id=new_id,
            display_name=display_name,
            description=description,
            config_json=config_json,
            is_system=False,
        )
        session.add(new_pack)
        session.commit()
        session.refresh(new_pack)

        return {
            "id": new_pack.id,
            "display_name": new_pack.display_name,
            "description": new_pack.description,
            "is_system": False,
            "source": "custom",
            "config": config,
            "created_at": new_pack.created_at.isoformat(),
        }

    @staticmethod
    def apply_pack(session: Session, user_id: str, pack_id: str, org_id: str) -> dict:
        """
        Apply a pack to the user's active configuration.
        Resolves the pack details (System or Custom) and writes to council_configuration.
        """
        # 1. Resolve Pack
        pack_data = None

        # Check DB first
        db_pack = session.query(CouncilPack).filter_by(id=pack_id).first()
        if db_pack:
            pack_data = json.loads(db_pack.config_json)
        else:
            # Check System Packs
            if os.path.exists(DEFAULTS_PACKS_DIR):
                for filename in os.listdir(DEFAULTS_PACKS_DIR):
                    if filename.endswith(".yaml"):
                        try:
                            with open(os.path.join(DEFAULTS_PACKS_DIR, filename)) as f:
                                data = yaml.safe_load(f)
                                if data.get("id") == pack_id:
                                    pack_data = {
                                        "personalities": data.get("personalities", []),
                                        "consensus_strategy": data.get("consensus_strategy"),
                                        "system_prompts": data.get("system_prompts", {}),
                                    }
                                    break
                        except Exception:
                            pass

        if not pack_data:
            raise ValueError(f"Pack {pack_id} not found.")

        # 2. Update Configuration
        config = session.query(CouncilConfiguration).filter_by(user_id=user_id).first()
        if not config:
            config = CouncilConfiguration(user_id=user_id)
            session.add(config)

        config.active_pack_id = pack_id
        config.active_personalities_json = json.dumps(pack_data.get("personalities", []))
        config.active_strategy_id = pack_data.get("consensus_strategy")
        config.active_system_prompts_json = json.dumps(pack_data.get("system_prompts", {}))

        session.commit()
        session.refresh(config)

        return {
            "user_id": config.user_id,
            "active_pack_id": config.active_pack_id,
            "active_personalities": json.loads(config.active_personalities_json),
            "active_strategy_id": config.active_strategy_id,
        }

    @staticmethod
    def get_active_configuration(session: Session, user_id: str, org_id: str) -> dict:
        """
        Get the active configuration for a user.
        Falls back to default system behavior if no config exists.
        """
        config = session.query(CouncilConfiguration).filter_by(user_id=user_id).first()

        if config:
            return {
                "active_pack_id": config.active_pack_id,
                "personalities": json.loads(config.active_personalities_json or "[]"),
                "strategy_id": config.active_strategy_id,
                "system_prompts": json.loads(config.active_system_prompts_json or "{}"),
            }

        # Fallback: All enabled personalities from the Org Config (Legacy/Default behavior)
        # We need to compute this dynamically.
        # This mimics 'get_active_personalities(org_id)' behavior essentially.

        # But wait, PackService should return IDs, not full objects?
        # The consumer (council.py) needs full objects.
        # This service method returns CONFIG (IDs), consumer enriches it.

        # Default Fallback:
        # If no per-user config, we consider "All System Personalities" as enabled?
        # Or we should migrate on first read?

        # Better: Return None or specific structure indicating "Use Defaults"
        all_personas = get_all_personalities(org_id)
        enabled_ids = [p["id"] for p in all_personas if p.get("enabled", True)]

        return {
            "active_pack_id": None,
            "personalities": enabled_ids,
            "strategy_id": None,  # or default
            "system_prompts": {},
        }
