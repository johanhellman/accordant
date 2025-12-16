"""
Service for handling personality evolution and combination.
"""

import logging
import os
import uuid
from typing import Any

import yaml

from .config.personalities import (
    get_active_personalities,
    get_org_personalities_dir,
)
from .openrouter import query_model
from .ranking_service import generate_feedback_summary

logger = logging.getLogger(__name__)


def _save_personality_file(org_id: str, personality: dict[str, Any]):
    """Save personality to organization directory."""
    personalities_dir = get_org_personalities_dir(org_id)
    os.makedirs(personalities_dir, exist_ok=True)

    file_path = os.path.join(personalities_dir, f"{personality['id']}.yaml")

    try:
        with open(file_path, "w") as f:
            yaml.dump(personality, f, sort_keys=False)
    except Exception as e:
        logger.error(f"Error saving personality {personality['id']}: {e}")
        raise


async def combine_personalities(
    org_id: str, parent_ids: list[str], name_suggestion: str, api_key: str, base_url: str
) -> dict[str, Any]:
    """
    Combine multiple personalities into a new one using LLM synthesis + feedback.
    """
    logger.info(f"Combining personalities {parent_ids} into '{name_suggestion}'")

    # 1. Load active personalities to find parents
    active = get_active_personalities(org_id)
    parents = [p for p in active if p["id"] in parent_ids]

    if len(parents) < 2:
        raise ValueError("At least 2 valid personalities are required for combination.")

    # 2. Gather Data (Profiles + Feedback)
    parent_data = []

    for p in parents:
        # Get qualitative feedback
        feedback = await generate_feedback_summary(org_id, p["name"], api_key, base_url)

        parent_info = f"""
        --- PARENT: {p["name"]} ---
        ID: {p["id"]}
        Description: {p.get("description", "")}

        EXISTING PROFILE:
        {yaml.dump(p.get("personality_prompt", {}), sort_keys=False)}

        PEER FEEDBACK (STRENGTHS & WEAKNESSES):
        {feedback}
        """
        parent_data.append(parent_info)

    # 3. Construct Synthesis Prompt
    from .config.personalities import load_org_system_prompts

    prompts = load_org_system_prompts(org_id)
    evolution_prompt_template = prompts.get("evolution_prompt", "")

    if not evolution_prompt_template:
        raise ValueError("System prompt 'evolution_prompt' is missing configuration.")
        raise ValueError("System prompt 'evolution_prompt' is missing configuration.")

    prompt = evolution_prompt_template.format(
        parent_count=len(parents), offspring_name=name_suggestion, parent_data="".join(parent_data)
    )

    # 4. Call LLM
    # Use the 'chairman_model' (synthesizer) for this architectural task
    from .config.personalities import load_org_models_config

    models_config = load_org_models_config(org_id)
    model = models_config.get("chairman_model", "openai/gpt-4o")  # Fallback if missing

    messages = [{"role": "user", "content": prompt}]

    response = await query_model(model, messages, api_key=api_key, base_url=base_url)

    if not response or not response.get("content"):
        raise RuntimeError("Failed to generate combined personality.")

    content = response["content"].strip()

    # Clean up markdown if present
    if content.startswith("```yaml"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    try:
        new_prompt_sections = yaml.safe_load(content)
        if not isinstance(new_prompt_sections, dict):
            raise ValueError("Parsed YAML is not a dictionary.")
    except Exception as e:
        logger.error(f"Failed to parse LLM output as YAML: {e}\nOutput: {content}")
        raise ValueError("LLM generated invalid YAML configuration.") from e

    # 6. Construct New Personality Object
    new_id = str(uuid.uuid4())
    new_personality = {
        "id": new_id,
        "name": name_suggestion,
        "description": f"Evolution combined from {', '.join([p['name'] for p in parents])}.",
        "model": parents[0]["model"],  # Inherit model from first parent (or default)
        "temperature": 0.7,
        "enabled": True,
        "personality_prompt": new_prompt_sections,
        "ui": {
            "icon": "dna",  # Default icon for evolved?
            "color": "#10B981",
        },
    }

    # 7. Save
    _save_personality_file(org_id, new_personality)

    logger.info(f"Successfully created evolved personality: {new_id}")
    return new_personality
