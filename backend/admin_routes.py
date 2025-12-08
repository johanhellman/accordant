"""Admin API routes for managing personalities and system prompts."""

import logging
import os
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import get_current_admin_user, validate_org_access
from .config.personalities import (
    DEFAULT_BASE_SYSTEM_PROMPT,
    DEFAULT_CHAIRMAN_PROMPT,
    DEFAULT_RANKING_MODEL,
    DEFAULT_RANKING_PROMPT,
    DEFAULT_TITLE_GENERATION_PROMPT,
    get_org_personalities_dir,
    _load_defaults,
)
from .llm_service import get_available_models
from .organizations import get_org, get_org_api_config, update_org
from .security import encrypt_value
from .users import User
from .council_helpers import ENFORCED_CONTEXT, ENFORCED_OUTPUT_FORMAT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["admin"])

# --- Pydantic Models ---


class Personality(BaseModel):
    id: str
    name: str
    description: str
    model: str
    temperature: float | None = None
    enabled: bool = True
    ui: dict[str, Any] | None = None
    personality_prompt: dict[str, str]


class ComponentConfig(BaseModel):
    prompt: str
    model: str
    effective_model: str | None = None  # Read-only, from env/config


class SystemPromptsConfig(BaseModel):
    base_system_prompt: str
    ranking: ComponentConfig
    chairman: ComponentConfig
    title_generation: ComponentConfig
    ranking_enforced_context: str | None = None
    ranking_enforced_format: str | None = None
    stage1_response_structure: str | None = None
    stage1_meta_structure: str | None = None


def validate_prompt_tags(prompt: str, required_tags: list[str], prompt_name: str):
    """Validate that a prompt contains all required tags."""
    missing = [tag for tag in required_tags if tag not in prompt]
    if missing:
        raise HTTPException(
            status_code=400, detail=f"{prompt_name} is missing required tags: {', '.join(missing)}"
        )


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str


class OrgSettingsUpdate(BaseModel):
    api_key: str | None = None
    base_url: str | None = None


# --- Helpers ---


def _load_yaml(file_path: str) -> dict[str, Any] | None:
    """Load YAML from a file."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading YAML from {file_path}: {e}")
        # We don't raise here to allow callers to handle specific errors or defaults
        return None


def _save_yaml(file_path: str, data: dict[str, Any]):
    """Save data to a YAML file."""
    try:
        with open(file_path, "w") as f:
            yaml.dump(data, f, sort_keys=False)
    except Exception as e:
        logger.error(f"Error saving YAML to {file_path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save configuration") from e


# --- Routes ---


@router.get("/models", response_model=list[ModelInfo])
async def list_models(current_user: User = Depends(get_current_admin_user)):
    """List available models from the configured provider."""
    try:
        api_key, base_url = get_org_api_config(current_user.org_id)
        return await get_available_models(api_key, base_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/personalities", response_model=list[Personality])
async def list_personalities(current_user: User = Depends(get_current_admin_user)):
    """List all personalities."""
    # Reload from disk to ensure freshness
    personalities_dir = get_org_personalities_dir(current_user.org_id)
    personalities = []
    if os.path.exists(personalities_dir):
        for filename in os.listdir(personalities_dir):
            if filename.endswith(".yaml") and filename != "system-prompts.yaml":
                p = _load_yaml(os.path.join(personalities_dir, filename))
                if p and "id" in p:
                    personalities.append(p)
    return personalities


@router.post("/personalities", response_model=Personality)
async def create_personality(
    personality: Personality, current_user: User = Depends(get_current_admin_user)
):
    """Create a new personality."""
    personalities_dir = get_org_personalities_dir(current_user.org_id)
    os.makedirs(personalities_dir, exist_ok=True)

    file_path = os.path.join(personalities_dir, f"{personality.id}.yaml")
    if os.path.exists(file_path):
        raise HTTPException(
            status_code=400, detail=f"Personality with ID {personality.id} already exists"
        )

    _save_yaml(file_path, personality.dict(exclude_none=True))
    return personality


@router.get("/personalities/{personality_id}", response_model=Personality)
async def get_personality(
    personality_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Get a specific personality."""
    personalities_dir = get_org_personalities_dir(current_user.org_id)
    file_path = os.path.join(personalities_dir, f"{personality_id}.yaml")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Personality not found")

    p = _load_yaml(file_path)
    if not p:
        # Should have been caught by exists check, but safe fallback
        raise HTTPException(status_code=500, detail="Failed to read personality")
    return p


@router.put("/personalities/{personality_id}", response_model=Personality)
async def update_personality(
    personality_id: str,
    personality: Personality,
    current_user: User = Depends(get_current_admin_user),
):
    """Update a personality."""
    if personality_id != personality.id:
        raise HTTPException(status_code=400, detail="ID mismatch")

    personalities_dir = get_org_personalities_dir(current_user.org_id)
    file_path = os.path.join(personalities_dir, f"{personality_id}.yaml")

    _save_yaml(file_path, personality.dict(exclude_none=True))
    return personality


@router.delete("/personalities/{personality_id}")
async def delete_personality(
    personality_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Delete a personality."""
    personalities_dir = get_org_personalities_dir(current_user.org_id)
    file_path = os.path.join(personalities_dir, f"{personality_id}.yaml")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Personality not found")

    try:
        os.remove(file_path)
        return {"status": "success", "message": f"Personality {personality_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting personality: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete personality") from e


@router.get("/system-prompts", response_model=SystemPromptsConfig)
async def get_system_prompts(current_user: User = Depends(get_current_admin_user)):
    """Get current system prompts and configuration."""
    from .config.personalities import get_org_config_dir, load_org_models_config

    config_dir = get_org_config_dir(current_user.org_id)
    file_path = os.path.join(config_dir, "system-prompts.yaml")

    # Load defaults
    models_config = load_org_models_config(current_user.org_id)
    defaults = _load_defaults()

    if not os.path.exists(file_path):
        # Return defaults if file doesn't exist
        return {
            "base_system_prompt": defaults.get("base_system_prompt", DEFAULT_BASE_SYSTEM_PROMPT),
            "ranking": {
                "prompt": DEFAULT_RANKING_PROMPT,
                "model": DEFAULT_RANKING_MODEL,
                "effective_model": models_config["ranking_model"],
            },
            "chairman": {
                "prompt": DEFAULT_CHAIRMAN_PROMPT,
                "model": "gemini/gemini-2.5-pro",
                "effective_model": models_config["chairman_model"],
            },
            "title_generation": {
                "prompt": DEFAULT_TITLE_GENERATION_PROMPT,
                "model": "gemini/gemini-2.5-pro",
                "effective_model": models_config["title_model"],
            },
            "title_generation": {
                "prompt": DEFAULT_TITLE_GENERATION_PROMPT,
                "model": "gemini/gemini-2.5-pro",
                "effective_model": models_config["title_model"],
            },
            "stage1_response_structure": defaults.get("stage1_response_structure", ""),
            "stage1_meta_structure": defaults.get("stage1_meta_structure", ""),
        }

    config = _load_yaml(file_path) or {}

    ranking_conf = config.get("ranking", {})
    # Backwards compat: if legacy top-level `ranking_prompt` exists,
    # surface it through the ComponentConfig shape.
    if not ranking_conf and "ranking_prompt" in config:
        ranking_conf = {
            "prompt": config.get("ranking_prompt", DEFAULT_RANKING_PROMPT),
            "model": DEFAULT_RANKING_MODEL,
        }

    chairman_conf = config.get("chairman", {})
    title_conf = config.get("title_generation", {})

    return {
        "base_system_prompt": config.get("base_system_prompt", DEFAULT_BASE_SYSTEM_PROMPT),
        "ranking": {
            "prompt": ranking_conf.get("prompt", DEFAULT_RANKING_PROMPT),
            "model": ranking_conf.get("model", DEFAULT_RANKING_MODEL),
            "effective_model": models_config["ranking_model"],
        },
        "ranking_enforced_context": ENFORCED_CONTEXT,
        "ranking_enforced_format": ENFORCED_OUTPUT_FORMAT.replace("{FINAL_RANKING_MARKER}", "FINAL RANKING:").replace("{RESPONSE_LABEL_PREFIX}", "Response "),
        "chairman": {
            "prompt": chairman_conf.get("prompt", DEFAULT_CHAIRMAN_PROMPT),
            "model": chairman_conf.get("model", "gemini/gemini-2.5-pro"),
            "effective_model": models_config["chairman_model"],
        },
        "title_generation": {
            "prompt": title_conf.get("prompt", DEFAULT_TITLE_GENERATION_PROMPT),
            "model": title_conf.get("model", "gemini/gemini-2.5-pro"),
            "effective_model": models_config["title_model"],
        },
        "stage1_response_structure": config.get("stage1_response_structure", defaults.get("stage1_response_structure", "")),
        "stage1_meta_structure": config.get("stage1_meta_structure", defaults.get("stage1_meta_structure", "")),
    }


@router.put("/system-prompts", response_model=SystemPromptsConfig)
async def update_system_prompts(
    config: SystemPromptsConfig, current_user: User = Depends(get_current_admin_user)
):
    """Update system prompts and configuration."""
    from .config.personalities import get_org_config_dir, load_org_models_config

    # Validate required tags consistently for all prompts
    # Validate required tags consistently for all prompts
    # Ranking prompt no longer needs tags as they are enforced by the system
    validate_prompt_tags(
        config.chairman.prompt,
        ["{user_query}", "{stage1_text}", "{voting_details_text}"],
        "Chairman Prompt",
    )
    validate_prompt_tags(
        config.title_generation.prompt,
        ["{user_query}"],
        "Title Generation Prompt",
    )

    config_dir = get_org_config_dir(current_user.org_id)
    os.makedirs(config_dir, exist_ok=True)
    file_path = os.path.join(config_dir, "system-prompts.yaml")

    # Construct YAML structure using the explicit values provided
    yaml_data = {
        "base_system_prompt": config.base_system_prompt,
        "ranking": {
            "prompt": config.ranking.prompt,
            "model": config.ranking.model,
        },
        "chairman": {"prompt": config.chairman.prompt, "model": config.chairman.model},
        "title_generation": {
            "prompt": config.title_generation.prompt,
            "model": config.title_generation.model,
        },
        "stage1_response_structure": config.stage1_response_structure,
        "stage1_meta_structure": config.stage1_meta_structure,
    }

    _save_yaml(file_path, yaml_data)

    # Return with effective models (re-inject them)
    models_config = load_org_models_config(current_user.org_id)
    config.ranking.effective_model = models_config["ranking_model"]
    config.chairman.effective_model = models_config["chairman_model"]
    config.title_generation.effective_model = models_config["title_model"]
    return config


@router.get("/votes")
async def get_voting_history(current_user: User = Depends(get_current_admin_user)):
    """
    Get full voting history.
    Enriched with user information.
    """
    from .users import get_all_users
    from .voting_history import load_voting_history as fetch_history

    history = fetch_history(current_user.org_id)
    users = {u.id: u.username for u in get_all_users()}

    # Enrich history with username
    for session in history:
        user_id = session.get("user_id")
        if user_id:
            session["username"] = users.get(user_id, "Unknown User")
        else:
            session["username"] = "Anonymous/Legacy"

    return history


@router.get("/settings")
async def get_org_settings(current_user: User = Depends(get_current_admin_user)):
    """Get organization settings."""
    org = get_org(current_user.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    api_config = org.api_config or {}

    # Mask API Key
    masked_key = None
    if api_config.get("api_key"):
        masked_key = "********"  # Do not return actual key

    return {
        "api_key": masked_key,
        "base_url": api_config.get("base_url", "https://openrouter.ai/api/v1/chat/completions"),
    }


@router.put("/settings")
async def update_org_settings(
    settings: OrgSettingsUpdate, current_user: User = Depends(get_current_admin_user)
):
    """Update organization settings."""
    org = get_org(current_user.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Explicitly validate access (redundant with current_user.org_id usage but good practice)
    validate_org_access(current_user, org.id)

    updates = {}
    current_api_config = org.api_config or {}

    if settings.api_key:
        # Encrypt new key
        encrypted_key = encrypt_value(settings.api_key)
        current_api_config["api_key"] = encrypted_key

    if settings.base_url:
        current_api_config["base_url"] = settings.base_url

    updates["api_config"] = current_api_config

    updated_org = update_org(current_user.org_id, updates)
    if not updated_org:
        raise HTTPException(status_code=500, detail="Failed to update organization")

    return {"status": "success", "message": "Settings updated"}
