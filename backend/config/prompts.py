"""
Configuration loading for Prompt-based strategies (e.g., Consensus).
"""

import logging
import os

from .paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

CONSENSUS_PROMPTS_DIR = os.path.join(PROJECT_ROOT, "data", "defaults", "consensus")


def get_available_consensus_strategies() -> list[str]:
    """
    List all available consensus strategies (filenames in data/prompts/consensus without .md).
    """
    if not os.path.exists(CONSENSUS_PROMPTS_DIR):
        return []

    strategies = []
    for f in os.listdir(CONSENSUS_PROMPTS_DIR):
        if f.endswith(".md"):
            strategies.append(f.replace(".md", ""))
    return sorted(strategies)


def load_consensus_prompt(strategy_name: str) -> str:
    """
    Load a consensus prompt by name.
    """
    filepath = os.path.join(CONSENSUS_PROMPTS_DIR, f"{strategy_name}.md")
    if not os.path.exists(filepath):
        # Fallback to balanced if not found
        logger.warning(
            f"Consensus strategy '{strategy_name}' not found. Falling back to 'balanced'."
        )
        filepath = os.path.join(CONSENSUS_PROMPTS_DIR, "balanced.md")

    if not os.path.exists(filepath):
        return "ERROR: Consensus prompt not found."

    with open(filepath) as f:
        return f.read()


def get_active_consensus_prompt(org_id: str) -> tuple[str, str]:
    """
    Determine the active consensus prompt for an organization.

    Order of operations:
    1. Check Org Config for 'consensus_strategy' key.
    2. Fallback to System Default (balanced).

    Returns:
        (strategy_name, prompt_content)
    """
    from .personalities import _load_org_config_file

    org_config = _load_org_config_file(org_id) or {}

    # Check for direct override in org config
    strategy = org_config.get("consensus_strategy", "balanced")

    prompt_content = load_consensus_prompt(strategy)
    return strategy, prompt_content
