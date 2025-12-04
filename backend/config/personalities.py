"""Personality loading and system prompt configuration."""

import logging
import os
from typing import Any

import yaml

from .paths import PROJECT_ROOT, validate_directory_path

ORGS_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "organizations")

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

# Load personalities and system prompts
PERSONALITY_REGISTRY = {}

# Start with empty prompts; we'll populate them only if the personalities
# directory exists. This allows environments/tests with a missing directory
# to detect that no prompts were loaded.
BASE_SYSTEM_PROMPT = ""
CHAIRMAN_PROMPT = ""
TITLE_GENERATION_PROMPT = ""
RANKING_PROMPT = ""

# Default models for special components
DEFAULT_RANKING_MODEL = "gemini/gemini-2.5-pro"

# Default Ranking Prompt
DEFAULT_RANKING_PROMPT = """You are evaluating different responses to the following question:

Question: {user_query}

Here are the responses from {peer_text}:

{responses_text}

Your task:
1. First, evaluate each response individually. For each response, explain what it does well and what it does poorly.
2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "{FINAL_RANKING_MARKER}" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. {RESPONSE_LABEL_PREFIX}A")
- Do not add any other text or explanations in the ranking section

Example of the correct format for your ENTIRE response:

{RESPONSE_LABEL_PREFIX}A provides good detail on X but misses Y...
{RESPONSE_LABEL_PREFIX}B is accurate but lacks depth on Z...
{RESPONSE_LABEL_PREFIX}C offers the most comprehensive answer...

{FINAL_RANKING_MARKER}
1. {RESPONSE_LABEL_PREFIX}C
2. {RESPONSE_LABEL_PREFIX}A
3. {RESPONSE_LABEL_PREFIX}B

Now provide your evaluation and ranking:"""

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

# --- Dynamic Configuration Loading ---


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

    if not os.path.exists(system_prompts_file):
        return None

    try:
        with open(system_prompts_file) as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading system prompts config for org {org_id}: {e}")
        return None


def _get_nested_config_value(config: dict[str, Any], section: str, key: str, default: str) -> str:
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
    prompts = {
        "base_system_prompt": DEFAULT_BASE_SYSTEM_PROMPT,
        "chairman_prompt": DEFAULT_CHAIRMAN_PROMPT,
        "title_prompt": DEFAULT_TITLE_GENERATION_PROMPT,
        "ranking_prompt": DEFAULT_RANKING_PROMPT,
    }

    config = _load_org_config_file(org_id)
    if config is None:
        return prompts

    # Load base system prompt
    prompts["base_system_prompt"] = config.get("base_system_prompt", DEFAULT_BASE_SYSTEM_PROMPT)

    # Load nested prompts with fallback
    prompts["chairman_prompt"] = _get_nested_config_value(
        config, "chairman", "prompt", DEFAULT_CHAIRMAN_PROMPT
    )
    prompts["title_prompt"] = _get_nested_config_value(
        config, "title_generation", "prompt", DEFAULT_TITLE_GENERATION_PROMPT
    )

    # Ranking prompt can be nested or top-level
    ranking_conf = config.get("ranking")
    if isinstance(ranking_conf, dict):
        prompts["ranking_prompt"] = ranking_conf.get("prompt", DEFAULT_RANKING_PROMPT)
    else:
        prompts["ranking_prompt"] = config.get("ranking_prompt", DEFAULT_RANKING_PROMPT)

    return prompts


def load_org_models_config(org_id: str) -> dict[str, str]:
    """
    Load model configuration for an organization.
    Returns a dict with keys: chairman_model, title_model, ranking_model
    """
    models = {
        "chairman_model": "gemini/gemini-2.5-pro",
        "title_model": "gemini/gemini-2.5-pro",
        "ranking_model": DEFAULT_RANKING_MODEL,
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
