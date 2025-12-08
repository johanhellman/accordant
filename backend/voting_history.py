"""
Persistent storage for voting history.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any

from .organizations import ORGS_DATA_DIR

logger = logging.getLogger(__name__)

VOTING_HISTORY_FILE = "voting_history.json"


def get_voting_history_path(org_id: str) -> str:
    """Get path to voting history file."""
    return os.path.join(ORGS_DATA_DIR, org_id, "voting_history.json")


def load_voting_history(org_id: str) -> list[dict[str, Any]]:
    """Load voting history from JSON file."""
    path = get_voting_history_path(org_id)
    if not os.path.exists(path):
        return []

    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading voting history for org {org_id}: {e}")
        return []


def save_voting_history(history: list[dict[str, Any]], org_id: str):
    """Save voting history to JSON file."""
    path = get_voting_history_path(org_id)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving voting history for org {org_id}: {e}")


def record_votes(
    conversation_id: str,
    stage2_results: list[dict[str, Any]],
    label_to_model: dict[str, str],
    conversation_title: str = "Unknown",
    turn_number: int = 1,
    user_id: str = None,
    org_id: str = None,
):
    """
    Extract votes from Stage 2 results and append to history as a new session.

    Args:
        conversation_id: The ID of the conversation
        stage2_results: The results from Stage 2 (rankings)
        label_to_model: Mapping from anonymous labels (Response A) to model names
        conversation_title: Title of the conversation
        turn_number: The turn number of this voting session
        user_id: The ID of the user who owns the conversation
        org_id: The ID of the organization
    """
    logger.info(f"Recording votes for conversation {conversation_id} (Turn {turn_number})")

    votes = []

    for result in stage2_results:
        voter_model = result["model"]
        voter_personality = result.get("personality_name", voter_model)
        parsed_ranking = result.get("parsed_ranking", [])
        # Save the full text reasoning if available, but ensure privacy downstream
        reasoning_text = result.get("ranking", "")

        # Convert ranked labels to model names
        ranked_candidates = []
        for rank, label in enumerate(parsed_ranking, start=1):
            candidate_name = label_to_model.get(label)
            if candidate_name:
                ranked_candidates.append(
                    {"rank": rank, "candidate": candidate_name, "label": label}
                )

        if ranked_candidates:
            votes.append(
                {
                    "voter_model": voter_model,
                    "voter_personality": voter_personality,
                    "rankings": ranked_candidates,
                    "reasoning": reasoning_text,  # Store the qualitative feedback
                }
            )

    if votes:
        session_record = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "conversation_id": conversation_id,
            "conversation_title": conversation_title,
            "turn_number": turn_number,
            "user_id": user_id,
            "votes": votes,
        }

        history = load_voting_history(org_id)
        history.append(session_record)
        save_voting_history(history, org_id)
        logger.info(f"Recorded voting session with {len(votes)} votes")
    else:
        logger.warning("No valid votes found to record")
