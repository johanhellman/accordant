"""Personality loading and system prompt configuration."""

import logging
import os
from typing import Any

import yaml

from .paths import PROJECT_ROOT, validate_directory_path

ORGS_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "organizations")
DEFAULTS_DIR = os.path.join(PROJECT_ROOT, "data", "defaults")
DEFAULTS_FILE = os.path.join(DEFAULTS_DIR, "system-prompts.yaml")

logger = logging.getLogger(__name__)

# --- Personality Configuration ---

# Directory containing personality configuration files
PERSONALITIES_DIR_ENV = os.getenv("COUNCIL_PERSONALITIES_DIR", "data/personalities")
try:
    PERSONALITIES_DIR = validate_directory_path(
        PERSONALITIES_DIR_ENV, base_dir=PROJECT_ROOT, allow_absolute=True
    )
except ValueError as e:
    logger.warning(
        f"Invalid PERSONALITIES_DIR '{PERSONALITIES_DIR_ENV}': {e}. Using default 'data/personalities'."
    )
    PERSONALITIES_DIR = os.path.join(PROJECT_ROOT, "data", "personalities")

    PERSONALITIES_DIR = os.path.join(PROJECT_ROOT, "data", "personalities")

# Ordered list of editable personality sections
# Ordered list of editable personality sections (snake_case keys)
PERSONALITY_SECTIONS = [
    "identity_and_role",
    "interpretation_of_questions",
    "problem_decomposition",
    "analysis_and_reasoning",
    "differentiation_and_bias",
    "tone",
]

# Display headers for the sections
SECTION_HEADERS = {
    "identity_and_role": "IDENTITY & ROLE",
    "interpretation_of_questions": "INTERPRETATION OF QUESTIONS",
    "problem_decomposition": "PROBLEM DECOMPOSITION",
    "analysis_and_reasoning": "ANALYSIS & REASONING",
    "differentiation_and_bias": "DIFFERENTIATION & BIAS",
    "tone": "TONE",
}

def format_personality_prompt(personality: dict[str, Any], system_prompts: dict[str, str], include_enforced: bool = True) -> str:
    """
    Format a personality into a string system prompt.
    appends the enforced global structure.
    """
    p_prompt = personality.get("personality_prompt")
    
    parts = []
    
    # 1. User Editable Sections
    if isinstance(p_prompt, dict):
        for i, section_key in enumerate(PERSONALITY_SECTIONS, 1):
            content = p_prompt.get(section_key, "")
            # Fallback to old keys if strictly migrating on the fly (optional safety)
            # if not content:
            #     old_key = SECTION_HEADERS[section_key]
            #     content = p_prompt.get(old_key, "")
            
            if content:
                header = SECTION_HEADERS[section_key]
                parts.append(f"**{i}. {header}**\n{content}")
    else:
        # Fallback for legacy string (though migration should have caught this)
        parts.append(f"**1. IDENTITY & ROLE**\n{str(p_prompt)}")
        
    if not include_enforced:
        return "\n\n".join(parts)
    
    # 2. Key for next section
    # Logic assumes 6 fixed sections.
    
    # 3. Enforced Sections
    start_index = 7 # Since we have 6 sections above
    
    # 3. Enforced Sections
    response_structure = system_prompts.get("stage1_response_structure")
    if response_structure:
        # Header is already in the default text usually, but let's ensure consistency?
        # The default text has "**7. RESPONSE STRUCTURE**". 
        # If user changed it, it might duplicate or be missing.
        # Ideally we just append the text.
        parts.append(response_structure)
        
    meta_structure = system_prompts.get("stage1_meta_structure")
    if meta_structure:
        parts.append(meta_structure)
        
    return "\n\n".join(parts)


# Load personalities and system prompts
PERSONALITY_REGISTRY = {}

# Default Ranking Prompt
DEFAULT_RANKING_PROMPT = "First, evaluate each response individually. For each response, explain what it does well and what it does poorly."

# Default Base System Prompt
DEFAULT_BASE_SYSTEM_PROMPT = """You are a member of the **LLM Council**, a diverse group of AI intelligences assembled to provide comprehensive, multi-faceted answers to user queries.

Your goal is not just to answer the question, but to contribute a unique perspective to the collective discussion. You will later review each other's answers, so be thorough and distinct."""

# Default Chairman Prompt
DEFAULT_CHAIRMAN_PROMPT = """You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.

Original Question: {user_query}

STAGE 1 - Individual Responses:
{stage1_text}

STAGE 2 - Peer Rankings (Detailed Votes):
{voting_details_text}

Your task is to provide a final response in two parts:

## PART 1: COUNCIL REPORT
- **Voting Results**: Create a standard MARKDOWN TABLE showing how each model voted.
  - Columns: Voter, 1st Choice, 2nd Choice.
  - **IMPORTANT**: In the table, you MUST use the **Personality Name** for all entries (Voter, 1st Choice, 2nd Choice).
  - Do NOT include model names or IDs, as they are not provided to you.
  - Ensure there is a newline after each row.
- **Brief Rationale**: Briefly explain why the winner was preferred.

## PART 2: FINAL ANSWER
- Provide the single, comprehensive, best possible answer to the user's question.
- This should be a direct answer to the user, ready to be used.

Begin:"""

# Default Title Generation Prompt
DEFAULT_TITLE_GENERATION_PROMPT = """Generate a very short title (3-5 words maximum) that summarizes the following question.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.

Question: {user_query}

# Default Evolution Prompt
DEFAULT_EVOLUTION_PROMPT = """You are an expert AI Personality Architect. 
Your task is to COMBINE the traits of {parent_count} existing "Parent" personalities into a new, superior "Offspring" personality.

NAME OF NEW PERSONALITY: {offspring_name}

GOAL:
- Create a coherent, integrated personality, not just a concatenation.
- PRESERVE the STRENGTHS identified in the peer feedback for each parent.
- MITIGATE the WEAKNESSES identified in the peer feedback.
- The new personality should feel like a natural evolution.

SOURCE MATERIAL:
{parent_data}

OUTPUT FORMAT:
You must output a valid YAML object for the 'personality_prompt' section.
It must have EXACTLY these keys:
- identity_and_role
- interpretation_of_questions
- problem_decomposition
- analysis_and_reasoning
- differentiation_and_bias
- tone

Do not include markdown code fence. Just the raw YAML.

YAML:"""

# Default models for special components
DEFAULT_RANKING_MODEL = "openai/gpt-4o"


# --- Dynamic Configuration Loading ---


def _load_yaml_file(filepath: str) -> dict[str, Any] | None:
    """Load a YAML file safely."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath) as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading YAML file {filepath}: {e}")
        return None


def _load_defaults() -> dict[str, Any]:
    """Load default system prompts from data/defaults/system-prompts.yaml."""
    defaults_file = os.path.join(DEFAULTS_DIR, "system-prompts.yaml")
    defaults = _load_yaml_file(defaults_file)
    if not defaults:
        logger.warning(f"Defaults file not found at {defaults_file}. Using empty defaults.")
        return {}
    return defaults


def _load_org_config_file(org_id: str) -> dict[str, Any] | None:
    """
    Load the system-prompts.yaml configuration file for an organization.
    
    Args:
        org_id: Organization ID
        
    Returns:
        Parsed YAML config dict, or None if file does not exist or parsing fails.
    """
    config_dir = get_org_config_dir(org_id)
    system_prompts_file = os.path.join(config_dir, "system-prompts.yaml")
    return _load_yaml_file(system_prompts_file)


def _get_nested_config_value(config: dict[str, Any], section: str, key: str, default: Any) -> Any:
    """
    Extract a nested configuration value with fallback.

    Args:
        config: The configuration dict
        section: The section name (e.g., "chairman", "title_generation")
        key: The key within the section (e.g., "prompt", "model")
        default: Default value if not found

    Returns:
        The configuration value or default
    """
    section_config = config.get(section, {})
    if isinstance(section_config, dict):
        return section_config.get(key, default)
    return default


def get_org_personalities_dir(org_id: str) -> str:
    """Get the personalities directory for an organization."""
    return os.path.join(ORGS_DATA_DIR, org_id, "personalities")


def get_org_config_dir(org_id: str) -> str:
    """Get the config directory for an organization."""
    return os.path.join(ORGS_DATA_DIR, org_id, "config")


def load_org_system_prompts(org_id: str) -> dict[str, str]:
    """
    Load system prompts for an organization with fallback to defaults.
    Returns a dict of final prompt values (strings).
    """
    config_data = load_org_system_prompts_config(org_id)
    
    # Flatten structure for consumers
    prompts = {}
    for key, item in config_data.items():
        if isinstance(item, dict) and "value" in item:
            prompts[key] = item["value"]
            
    return prompts


def load_org_system_prompts_config(org_id: str) -> dict[str, dict[str, Any]]:
    """
    Load system prompts configuration with metadata (value, is_default, source).
    This allows the UI to know if a value is inherited or custom.
    """
    defaults = _load_defaults()
    org_config = _load_org_config_file(org_id) or {}
    
    # helper to construct the metadata object
    def _create_entry(key: str, default_val: str, org_val: str | None, section: str = None) -> dict[str, Any]:
        is_custom = False
        value = default_val
        
        # Check if org has an override
        if section:
            # Nested check logic matching _get_nested_config_value but checking existence
            if section in org_config and isinstance(org_config[section], dict) and key in org_config[section]:
                 value = org_config[section][key]
                 is_custom = True
        else:
            # Top level check
            if key in org_config:
                value = org_config[key]
                is_custom = True
                
        # Special case for ranking which moved from nested to top level in some versions
        # logic handled in specific construction below
        
        return {
            "value": value,
            "is_default": not is_custom,
            "source": "default" if not is_custom else "custom"
        }

    # Extract Defaults
    default_base = defaults.get("base_system_prompt", "")
    default_ranking = defaults.get("ranking_prompt", "")
    default_chairman = _get_nested_config_value(defaults, "chairman", "prompt", "")
    default_title = _get_nested_config_value(defaults, "title_generation", "prompt", "")
    default_evolution = defaults.get("evolution_prompt", DEFAULT_EVOLUTION_PROMPT)
    default_struct_resp = defaults.get("stage1_response_structure", "")
    default_struct_meta = defaults.get("stage1_meta_structure", "")

    # Build Result
    result = {}
    
    result["base_system_prompt"] = _create_entry("base_system_prompt", default_base, None)
    result["chairman_prompt"] = _create_entry("prompt", default_chairman, None, section="chairman")
    result["title_prompt"] = _create_entry("prompt", default_title, None, section="title_generation")
    result["evolution_prompt"] = _create_entry("evolution_prompt", default_evolution, None)
    result["stage1_response_structure"] = _create_entry("stage1_response_structure", default_struct_resp, None)
    result["stage1_meta_structure"] = _create_entry("stage1_meta_structure", default_struct_meta, None)
    
    # Ranking prompt requires flexible handling (nested vs top-level)
    # We will prioritize the unified "ranking_prompt" key for new overrides, but check legacy "ranking.prompt" too
    ranking_custom = False
    ranking_val = default_ranking
    
    if "ranking_prompt" in org_config:
        ranking_val = org_config["ranking_prompt"]
        ranking_custom = True
    elif "ranking" in org_config and isinstance(org_config["ranking"], dict) and "prompt" in org_config["ranking"]:
        ranking_val = org_config["ranking"]["prompt"]
        ranking_custom = True
        
    result["ranking_prompt"] = {
        "value": ranking_val,
        "is_default": not ranking_custom,
        "source": "default" if not ranking_custom else "custom"
    }

    return result


def load_org_models_config(org_id: str) -> dict[str, str]:
    # Load model configuration for an organization.
    # Returns a dict with keys: chairman_model, title_model, ranking_model
    defaults = _load_defaults()
    
    default_chairman_model = _get_nested_config_value(defaults, "chairman", "model", "gemini/gemini-2.5-pro")
    default_title_model = _get_nested_config_value(defaults, "title_generation", "model", "gemini/gemini-2.5-pro")
    # Ranking model default is hardcoded for now as it's not in the prompt file usually, 
    # but let's check if we want to put it there. The prompt file has models too.
    # Yes, the new defaults file has models.
    default_ranking_model = DEFAULT_RANKING_MODEL

    models = {
        "chairman_model": default_chairman_model,
        "title_model": default_title_model,
        "ranking_model": default_ranking_model,
    }

    config = _load_org_config_file(org_id)
    if config is None:
        return models

    # Load nested model configurations with fallback
    models["chairman_model"] = _get_nested_config_value(
        config, "chairman", "model", models["chairman_model"]
    )
    models["title_model"] = _get_nested_config_value(
        config, "title_generation", "model", models["title_model"]
    )
    models["ranking_model"] = _get_nested_config_value(
        config, "ranking", "model", models["ranking_model"]
    )

    return models


def get_all_personalities(org_id: str) -> list[dict[str, Any]]:
    # Get all personalities for an organization, merging Defaults + Custom.
    # Returns ALL personalities (enabled or disabled), with 'source' and 'is_editable' flags.
    org_personalities_dir = get_org_personalities_dir(org_id)
    defaults_personalities_dir = os.path.join(DEFAULTS_DIR, "personalities")
    
    # Load Org Config to check for disabled system personalities
    # (Note: For the 'all' list, we might want to return them but marked as disabled? 
    #  But the current requirement is to show everything. 
    #  If a system personality is disabled in org config, it should still appear in the list so it can be re-enabled.
    #  The 'disabled_system_personalities' config might be a legacy/alternative way to 'delete' them from view,
    #  but typically 'enabled: false' is the way. Let's assume we want to show everything.)
    
    registry = {}
    
    # 1. Load Defaults (System Personalities)
    if os.path.exists(defaults_personalities_dir):
        for filename in os.listdir(defaults_personalities_dir):
            if filename.endswith(".yaml"):
                filepath = os.path.join(defaults_personalities_dir, filename)
                try:
                    with open(filepath) as f:
                        p = yaml.safe_load(f)
                        if p and "id" in p:
                            p["source"] = "system"
                            # System personalities are not editable directly in the Org view (must be shadowed)
                            p["is_editable"] = False 
                            registry[p["id"]] = p
                except Exception as e:
                    logger.error(f"Error loading default personality {filename}: {e}")

    # 2. Load Org Overrides (Custom Personalities)
    # These will overwrite registry entries if IDs match (Shadowing)
    if os.path.exists(org_personalities_dir):
        for filename in os.listdir(org_personalities_dir):
            if filename.endswith(".yaml") and filename != "system-prompts.yaml":
                filepath = os.path.join(org_personalities_dir, filename)
                try:
                    with open(filepath) as f:
                        p = yaml.safe_load(f)
                        if p and "id" in p:
                            p["source"] = "custom"
                            p["is_editable"] = True
                            registry[p["id"]] = p # Overwrites system version
                except Exception as e:
                    logger.error(f"Error loading org personality {filename} for org {org_id}: {e}")

    return list(registry.values())


def get_active_personalities(org_id: str) -> list[dict[str, Any]]:
    # Get active personalities for an organization.
    # Wraps get_all_personalities and filters for enabled=True.
    all_personalities = get_all_personalities(org_id)
    
    # We also need to respect the 'disabled_system_personalities' from org config if used
    org_config = _load_org_config_file(org_id) or {}
    disabled_ids = org_config.get("disabled_system_personalities", [])
    
    active = []
    for p in all_personalities:
        if p.get("id") in disabled_ids:
            continue
        if p.get("enabled", True):
            active.append(p)
            
    return active
