"""Admin API routes for managing personalities and system prompts."""

import logging
import os
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import get_current_admin_user, get_current_instance_admin, validate_org_access
from .config.personalities import (
    get_org_personalities_dir,
    get_all_personalities,
    _load_defaults,
    DEFAULTS_DIR,
)
from .llm_service import get_available_models
from .organizations import get_org, get_org_api_config, update_org
from .security import encrypt_value
from .users import User
from .council_helpers import ENFORCED_CONTEXT, ENFORCED_OUTPUT_FORMAT
from .ranking_service import calculate_league_table, calculate_instance_league_table, generate_feedback_summary
from .evolution_service import combine_personalities

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
    source: str | None = None # "system" or "custom"
    is_editable: bool | None = None


from typing import Generic, TypeVar

T = TypeVar("T")

class ConfigValue(BaseModel, Generic[T]):
    value: T
    is_default: bool
    source: str  # "default" or "custom"


class ComponentConfig(BaseModel):
    prompt: ConfigValue[str]
    model: str # Simplification: Models are not yet fully inherited-aware in the UI schema, but loaded via config
    effective_model: str | None = None


class SystemPromptsConfig(BaseModel):
    base_system_prompt: ConfigValue[str]
    ranking: ComponentConfig
    chairman: ComponentConfig
    title_generation: ComponentConfig
    evolution_prompt: ConfigValue[str]
    ranking_enforced_context: str | None = None
    ranking_enforced_format: str | None = None
    stage1_response_structure: ConfigValue[str] | None = None
    stage1_meta_structure: ConfigValue[str] | None = None


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


class CombineRequest(BaseModel):
    parent_ids: list[str]
    name_suggestion: str
    model: str | None = None  # Optional override



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
    # Use get_all_personalities to include system defaults
    return get_all_personalities(current_user.org_id)


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
    # Search in combined list (to support system personalities retrieval)
    all_ps = get_all_personalities(current_user.org_id)
    p = next((x for x in all_ps if x["id"] == personality_id), None)
    
    if not p:
        raise HTTPException(status_code=404, detail="Personality not found")
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
    """Get current system prompts and configuration with inheritance metadata."""
    from .config.personalities import load_org_system_prompts_config, load_org_models_config

    prompts_data = load_org_system_prompts_config(current_user.org_id)
    models_config = load_org_models_config(current_user.org_id)
    
    # Helper to mapping dict to ConfigValue
    def to_cv(key_name):
        d = prompts_data.get(key_name, {"value": "", "is_default": True, "source": "default"})
        return {"value": d["value"], "is_default": d["is_default"], "source": d["source"]}

    return {
        "base_system_prompt": to_cv("base_system_prompt"),
        "ranking": {
            "prompt": to_cv("ranking_prompt"),
            "model": models_config["ranking_model"], 
            "effective_model": models_config["ranking_model"],
        },
        "ranking_enforced_context": ENFORCED_CONTEXT,
        "ranking_enforced_format": ENFORCED_OUTPUT_FORMAT.replace("{FINAL_RANKING_MARKER}", "FINAL RANKING:").replace("{RESPONSE_LABEL_PREFIX}", "Response "),
        "chairman": {
            "prompt": to_cv("chairman_prompt"),
            "model": models_config["chairman_model"], 
            "effective_model": models_config["chairman_model"],
        },
        "title_generation": {
            "prompt": to_cv("title_prompt"),
            "model": models_config["title_model"],
            "effective_model": models_config["title_model"],
        },
        "evolution_prompt": to_cv("evolution_prompt"),
        "stage1_response_structure": to_cv("stage1_response_structure"),
        "stage1_meta_structure": to_cv("stage1_meta_structure"),
    }


@router.get("/defaults/system-prompts", response_model=SystemPromptsConfig)
async def get_default_system_prompts(current_user: User = Depends(get_current_instance_admin)):
    """Get GLOBAL DEFAULT system prompts (Instance Admin only)."""
    defaults = _load_defaults()
    
    # Helper to mapping dict to ConfigValue (always default, always source=default)
    def to_cv(val):
        return {"value": val if val else "", "is_default": True, "source": "default"}

    # Extract nested values safely
    chairman_prompt = defaults.get("chairman", {}).get("prompt", "") if isinstance(defaults.get("chairman"), dict) else ""
    title_prompt = defaults.get("title_generation", {}).get("prompt", "") if isinstance(defaults.get("title_generation"), dict) else ""
    ranking_prompt = defaults.get("ranking_prompt", "")
    evolution_prompt = defaults.get("evolution_prompt", "")

    return {
        "base_system_prompt": to_cv(defaults.get("base_system_prompt", "")),
        "ranking": { 
            "prompt": to_cv(ranking_prompt),
            "model": "openai/gpt-4o", 
            "effective_model": "openai/gpt-4o",
        },
        "ranking_enforced_context": ENFORCED_CONTEXT,
        "ranking_enforced_format": ENFORCED_OUTPUT_FORMAT.replace("{FINAL_RANKING_MARKER}", "FINAL RANKING:").replace("{RESPONSE_LABEL_PREFIX}", "Response "),
        "chairman": {
            "prompt": to_cv(chairman_prompt),
            "model": "gemini/gemini-2.5-pro",
            "effective_model": "gemini/gemini-2.5-pro",
        },
        "title_generation": {
            "prompt": to_cv(title_prompt),
            "model": "gemini/gemini-2.5-pro",
            "effective_model": "gemini/gemini-2.5-pro",
        },
        "evolution_prompt": to_cv(evolution_prompt),
        "stage1_response_structure": to_cv(defaults.get("stage1_response_structure", "")),
        "stage1_meta_structure": to_cv(defaults.get("stage1_meta_structure", "")),
    }


@router.put("/defaults/system-prompts", response_model=SystemPromptsConfig)
async def update_default_system_prompts(
    config: dict, current_user: User = Depends(get_current_instance_admin)
):
    """
    Update GLOBAL DEFAULT system prompts.
    Writes directly to data/defaults/system-prompts.yaml.
    """
    from .config.personalities import DEFAULTS_FILE
    
    # Load existing to preserve keys
    current_defaults = _load_yaml(DEFAULTS_FILE) or {}
    
    # Helper to update key from ConfigValue or direct value
    def get_val(incoming):
        if not incoming: return None
        if isinstance(incoming, dict) and "value" in incoming:
             return incoming["value"] # Extract value from ConfigValue
        return incoming

    # Top Level
    if "base_system_prompt" in config:
        current_defaults["base_system_prompt"] = get_val(config["base_system_prompt"])
    if "stage1_response_structure" in config:
        current_defaults["stage1_response_structure"] = get_val(config["stage1_response_structure"])
    if "stage1_meta_structure" in config:
        current_defaults["stage1_meta_structure"] = get_val(config["stage1_meta_structure"])
    if "evolution_prompt" in config:
        current_defaults["evolution_prompt"] = get_val(config["evolution_prompt"])

    if config.get("ranking") and isinstance(config["ranking"], dict):
         current_defaults["ranking_prompt"] = get_val(config["ranking"].get("prompt"))
    
    # Nested Updates
    if config.get("chairman") and isinstance(config["chairman"], dict):
         if "chairman" not in current_defaults or not isinstance(current_defaults["chairman"], dict):
             current_defaults["chairman"] = {}
         current_defaults["chairman"]["prompt"] = get_val(config["chairman"].get("prompt"))
         
    if config.get("title_generation") and isinstance(config["title_generation"], dict):
         if "title_generation" not in current_defaults or not isinstance(current_defaults["title_generation"], dict):
             current_defaults["title_generation"] = {}
         current_defaults["title_generation"]["prompt"] = get_val(config["title_generation"].get("prompt"))

    _save_yaml(DEFAULTS_FILE, current_defaults)
    
    return await get_default_system_prompts(current_user)


@router.put("/system-prompts", response_model=SystemPromptsConfig)
async def update_system_prompts(
    config: dict, current_user: User = Depends(get_current_admin_user)
):
    """
    Update system prompts.
    Accepts a raw dict to handle the 'is_default' toggle logic.
    If 'is_default' is True for a field, we REMOVE it from the org config to revert to inheritance.
    """
    from .config.personalities import get_org_config_dir, _load_defaults

    config_dir = get_org_config_dir(current_user.org_id)
    os.makedirs(config_dir, exist_ok=True)
    file_path = os.path.join(config_dir, "system-prompts.yaml")
    
    # Load existing config to preserve other fields (like models not being edited here)
    current_config = _load_yaml(file_path) or {}
    
    # Helper to update or remove a key based on 'is_default'
    def update_field(target_dict, key, incoming_data):
        if not isinstance(incoming_data, dict):
            return # Should be ConfigValue dict
        
        if incoming_data.get("is_default"):
            # Revert to default -> Remove from org config
            target_dict.pop(key, None)
        else:
            # Set custom value
            target_dict[key] = incoming_data.get("value")

    # update base prompts
    update_field(current_config, "base_system_prompt", config.get("base_system_prompt"))
    update_field(current_config, "stage1_response_structure", config.get("stage1_response_structure"))
    update_field(current_config, "stage1_meta_structure", config.get("stage1_meta_structure"))
    update_field(current_config, "evolution_prompt", config.get("evolution_prompt"))
    
    # Handle nested components
    # Chairman
    if "chairman" not in current_config: current_config["chairman"] = {}
    if isinstance(config.get("chairman"), dict):
        chairman_in = config["chairman"]
        if "prompt" in chairman_in: # it's the ConfigValue object
             update_field(current_config["chairman"], "prompt", chairman_in["prompt"])
        # Persist model if sent (UI might send it)
        if "model" in chairman_in and isinstance(chairman_in["model"], str):
             current_config["chairman"]["model"] = chairman_in["model"]

    # Title Gen
    if "title_generation" not in current_config: current_config["title_generation"] = {}
    if isinstance(config.get("title_generation"), dict):
        title_in = config["title_generation"]
        if "prompt" in title_in:
             update_field(current_config["title_generation"], "prompt", title_in["prompt"])
        if "model" in title_in and isinstance(title_in["model"], str):
             current_config["title_generation"]["model"] = title_in["model"]

    # Ranking
    # For ranking, we prioritize the new top-level "ranking_prompt" key for clarity, but support nested.
    # To keep it clean, let's use "ranking_prompt" at top level if possible, or stick to nested "ranking.prompt"
    # match existing structure.
    if "ranking" not in current_config: current_config["ranking"] = {}
    if isinstance(config.get("ranking"), dict):
        ranking_in = config["ranking"]
        if "prompt" in ranking_in:
             # We use the nested 'ranking' dict for storage to keep models and prompts together
             update_field(current_config["ranking"], "prompt", ranking_in["prompt"]) 
        if "model" in ranking_in and isinstance(ranking_in["model"], str):
             current_config["ranking"]["model"] = ranking_in["model"]
             
    # Clean up empty nested dicts if they become empty?
    # No, keep them for potential model configs.

    _save_yaml(file_path, current_config)

    # Return the new state (which effectively re-reads defaults + overrides)
    # We call the GET logic to ensure full consistency
    return await get_system_prompts(current_user)


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
    # If user has no organization, return default settings
    if not current_user.org_id:
        return {
            "api_key": None,
            "base_url": "https://openrouter.ai/api/v1/chat/completions",
        }
    
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
    # Users without organizations cannot update settings
    if not current_user.org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization to update settings")
    
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


# --- League Table & Evolution Routes ---


@router.get("/league-table")
async def get_org_league_table(current_user: User = Depends(get_current_admin_user)):
    """Get the league table for the current organization."""
    return calculate_league_table(current_user.org_id)


@router.get("/instance-league-table")
async def get_global_league_table(current_user: User = Depends(get_current_instance_admin)):
    """Get the global aggregated league table (Instance Admin Only)."""
    return calculate_instance_league_table()


@router.get("/personalities/{personality_id}/feedback")
async def get_personality_feedback(
    personality_id: str, current_user: User = Depends(get_current_admin_user)
):
    """
    Get qualitative feedback summary (Strengths, Weaknesses) for a personality.
    """
    # Verify personality exists in Org context
    # (Checking visibility implicit by passing org_id to generator)
    
    # We need the name to find votes.
    # Load personality to get name
    all_ps = get_all_personalities(current_user.org_id)
    p = next((x for x in all_ps if x["id"] == personality_id), None)
    if not p:
        raise HTTPException(status_code=404, detail="Personality not found")
        
    api_key, base_url = get_org_api_config(current_user.org_id)
    
    summary = await generate_feedback_summary(
        current_user.org_id, p["name"], api_key, base_url
    )
    return {"summary": summary}


@router.post("/evolution/combine")
async def combine_personalities_route(
    request: CombineRequest, current_user: User = Depends(get_current_admin_user)
):
    """Combine multiple personalities into a new one."""
    try:
        api_key, base_url = get_org_api_config(current_user.org_id)
        
        new_personality = await combine_personalities(
            current_user.org_id,
            request.parent_ids,
            request.name_suggestion,
            api_key,
            base_url
        )
        return new_personality
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error combining personalities: {e}")
        raise HTTPException(status_code=500, detail="Failed to combine personalities")


@router.post("/evolution/deactivate/{personality_id}")
async def deactivate_personality(
    personality_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Deactivate (disable) a personality."""
    personalities_dir = get_org_personalities_dir(current_user.org_id)
    file_path = os.path.join(personalities_dir, f"{personality_id}.yaml")
    
    # Check if custom exists
    if os.path.exists(file_path):
        data = _load_yaml(file_path)
        data["enabled"] = False
        _save_yaml(file_path, data)
        return {"status": "success", "message": f"Personality {personality_id} deactivated"}
        
    # If it's a System Personality, we must Shadow it to disable it?
    # Or we use the 'disabled_system_personalities' list in org config.
    # Implementation Plan says "Deactivate (sets enabled: false)".
    # If it's a system personality, we can't edit the file directly.
    # We should create a shadow copy with enabled=False OR update an org-level blacklist.
    # For simplicity/consistency with "Shadowing", creating a shadow file with enabled=False is easiest logic
    # because get_active_personalities loads custom files and overwrites system ones.
    
    # 1. Load the personality (System or Custom)
    all_ps = get_all_personalities(current_user.org_id)
    p = next((x for x in all_ps if x["id"] == personality_id), None)
    
    if not p:
        raise HTTPException(status_code=404, detail="Personality not found")
        
    # 2. Save as custom with enabled=False
    p["enabled"] = False
    p["source"] = "custom" # Now it's custom
    p["is_editable"] = True
    
    # Ensure dir exists
    os.makedirs(personalities_dir, exist_ok=True)
    _save_yaml(file_path, p)
    
    return {"status": "success", "message": f"Personality {personality_id} deactivated"}


@router.get("/defaults/personalities", response_model=list[Personality])
async def list_default_personalities(current_user: User = Depends(get_current_instance_admin)):
    """List GLOBAL DEFAULT personalities (Instance Admin only)."""
    defaults_personalities_dir = os.path.join(DEFAULTS_DIR, "personalities")
    personalities = []
    if os.path.exists(defaults_personalities_dir):
        for filename in os.listdir(defaults_personalities_dir):
            if filename.endswith(".yaml"):
                p = _load_yaml(os.path.join(defaults_personalities_dir, filename))
                if p and "id" in p:
                    p["source"] = "system" # Explicitly mark as system source 
                    personalities.append(p)
    return personalities


@router.post("/defaults/personalities", response_model=Personality)
async def create_default_personality(
    personality: Personality, current_user: User = Depends(get_current_instance_admin)
):
    """Create a new GLOBAL DEFAULT personality."""
    defaults_personalities_dir = os.path.join(DEFAULTS_DIR, "personalities")
    os.makedirs(defaults_personalities_dir, exist_ok=True)

    file_path = os.path.join(defaults_personalities_dir, f"{personality.id}.yaml")
    if os.path.exists(file_path):
        raise HTTPException(
            status_code=400, detail=f"Default Personality with ID {personality.id} already exists"
        )
    
    # Ensure it's marked as enabled by default usually, but we accept payload
    _save_yaml(file_path, personality.dict(exclude_none=True))
    return personality


@router.put("/defaults/personalities/{personality_id}", response_model=Personality)
async def update_default_personality(
    personality_id: str,
    personality: Personality,
    current_user: User = Depends(get_current_instance_admin),
):
    """Update a GLOBAL DEFAULT personality."""
    if personality_id != personality.id:
        raise HTTPException(status_code=400, detail="ID mismatch")

    defaults_personalities_dir = os.path.join(DEFAULTS_DIR, "personalities")
    file_path = os.path.join(defaults_personalities_dir, f"{personality_id}.yaml")

    # For update, it should exist? Or we allow upsert? Let's strictly force existence for PUT logic usually
    # But files might be missing if manually messed with.
    # Let's save.
    os.makedirs(defaults_personalities_dir, exist_ok=True)
    _save_yaml(file_path, personality.dict(exclude_none=True))
    return personality


@router.delete("/defaults/personalities/{personality_id}")
async def delete_default_personality(
    personality_id: str, current_user: User = Depends(get_current_instance_admin)
):
    """Delete a GLOBAL DEFAULT personality."""
    defaults_personalities_dir = os.path.join(DEFAULTS_DIR, "personalities")
    file_path = os.path.join(defaults_personalities_dir, f"{personality_id}.yaml")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Default Personality not found")

    try:
        os.remove(file_path)
        return {"status": "success", "message": f"Default Personality {personality_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting default personality: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete default personality") from e
