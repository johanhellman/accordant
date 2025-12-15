"""
Persistent storage for voting history using SQLite (Tenant DB).
"""

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from .database import get_tenant_session
from .models import Vote

logger = logging.getLogger(__name__)


def record_votes(
    conversation_id: str,
    stage2_results: list[dict[str, Any]],
    label_to_model: dict[str, Any],  # dict[str, dict]
    conversation_title: str = "Unknown",
    turn_number: int = 1,
    user_id: str = None,
    org_id: str = None,
):
    """
    Extract votes from Stage 2 results and insert into Tenant DB.
    """
    if not org_id:
        logger.error("Cannot record votes: org_id is missing.")
        return

    logger.info(f"Recording votes for conversation {conversation_id} (Turn {turn_number})")

    db: Session = get_tenant_session(org_id)
    votes_to_insert = []

    try:
        for result in stage2_results:
            voter_model = result.get("model", "unknown")
            # Fallback for ID if stage2 result structure hasn't fully propagated in tests
            voter_personality_id = result.get("personality_id")

            parsed_ranking = result.get("parsed_ranking", [])
            reasoning_text = result.get("ranking", "")

            # Convert ranked labels to identity info
            for rank, label in enumerate(parsed_ranking, start=1):
                target_info = label_to_model.get(label)
                if target_info:
                    # target_info is now {id: ..., name: ..., model: ...}
                    candidate_id = target_info.get("id") if isinstance(target_info, dict) else None
                    candidate_name = (
                        target_info.get("name")
                        if isinstance(target_info, dict)
                        else str(target_info)
                    )
                    candidate_model = (
                        target_info.get("model")
                        if isinstance(target_info, dict)
                        else candidate_name
                    )

                    vote = Vote(
                        id=str(uuid.uuid4()),
                        conversation_id=conversation_id,
                        turn_number=turn_number,
                        voter_model=voter_model,
                        voter_personality_id=voter_personality_id,
                        candidate_model=candidate_model,
                        candidate_personality_id=candidate_id,
                        rank=rank,
                        label=label,
                        reasoning=reasoning_text,
                    )
                    votes_to_insert.append(vote)

        if votes_to_insert:
            db.add_all(votes_to_insert)
            db.commit()
            logger.info(f"Successfully recorded {len(votes_to_insert)} votes in Tenant DB.")
        else:
            logger.warning("No valid votes extracted to record.")

    except Exception as e:
        logger.error(f"Error recording votes in DB: {e}")
        db.rollback()
    finally:
        db.close()


# Legacy loader function - kept for interface compatibility but now empty/deprecated
# The new ranking_service queries the DB directly.
def load_voting_history(org_id: str) -> list[dict[str, Any]]:
    """
    DEPRECATED: Returns empty list.
    Legacy JSON loading is removed. Use ranking_service database queries.
    """
    logger.warning("load_voting_history is deprecated and returns empty list.")
    return []
