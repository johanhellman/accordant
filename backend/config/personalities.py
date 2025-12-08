"""Personality loading and system prompt configuration."""

import logging
import os
from typing import Any

import yaml

from .paths import PROJECT_ROOT, validate_directory_path

ORGS_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "organizations")
DEFAULTS_DIR = os.path.join(PROJECT_ROOT, "data", "defaults")

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

Title:"""

# Default models for special components
DEFAULT_RANKING_MODEL = "gemini/gemini-2.5-pro"


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
        Parsed YAML config dict, or None if file doesn't exist or parsing fails
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
    Load system prompts for an organization.
    Returns a dict with keys: base_system_prompt, chairman_prompt, title_prompt, ranking_prompt
    """
    defaults = _load_defaults()
    
    # Extract defaults
    default_base = defaults.get("base_system_prompt", "")
    default_ranking = defaults.get("ranking_prompt", "")
    default_chairman = _get_nested_config_value(defaults, "chairman", "prompt", "")
    default_title = _get_nested_config_value(defaults, "title_generation", "prompt", "")

    prompts = {
        "base_system_prompt": default_base,
        "chairman_prompt": default_chairman,
        "title_prompt": default_title,
        "ranking_prompt": default_ranking,
        "stage1_response_structure": defaults.get("stage1_response_structure", ""),
        "stage1_meta_structure": defaults.get("stage1_meta_structure", ""),
    }

    config = _load_org_config_file(org_id)
    if config is None:
        return prompts

    # Load base system prompt
    prompts["base_system_prompt"] = config.get("base_system_prompt", default_base)

    # Load nested prompts with fallback
    prompts["chairman_prompt"] = _get_nested_config_value(
        config, "chairman", "prompt", default_chairman
    )
    prompts["title_prompt"] = _get_nested_config_value(
        config, "title_generation", "prompt", default_title
    )

    # Ranking prompt can be nested or top-level
    ranking_conf = config.get("ranking")
    if isinstance(ranking_conf, dict):
        prompts["ranking_prompt"] = ranking_conf.get("prompt", default_ranking)
    else:
        prompts["ranking_prompt"] = config.get("ranking_prompt", default_ranking)


    # Load Stage 1 structures
    prompts["stage1_response_structure"] = config.get(
        "stage1_response_structure", prompts["stage1_response_structure"]
    )
    prompts["stage1_meta_structure"] = config.get(
        "stage1_meta_structure", prompts["stage1_meta_structure"]
    )

    return prompts


def load_org_models_config(org_id: str) -> dict[str, str]:
    """
    Load model configuration for an organization.
    Returns a dict with keys: chairman_model, title_model, ranking_model
    """
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


def get_active_personalities(org_id: str) -> list[dict[str, Any]]:
    """
    Get active personalities for an organization.
    """
    personalities_dir = get_org_personalities_dir(org_id)
    registry = {}

    if os.path.exists(personalities_dir):
        for filename in os.listdir(personalities_dir):
            if filename.endswith(".yaml") and filename != "system-prompts.yaml":
                filepath = os.path.join(personalities_dir, filename)
                try:
                    with open(filepath) as f:
                        p = yaml.safe_load(f)
                        if p and "id" in p and p.get("enabled", True):
                            registry[p["id"]] = p
                except Exception as e:
                    logger.error(f"Error loading personality {filename} for org {org_id}: {e}")

    # In future, we might filter by an "active_personalities" setting in org config
    # For now, return all enabled personalities in the folder
    return list(registry.values())
