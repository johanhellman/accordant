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
from .models import Conversation


def load_voting_history(org_id: str) -> list[dict[str, Any]]:
    """
    Load voting history from Tenant DB and restructure it for the frontend.
    Groups votes by (conversation, turn) -> voter -> rankings.
    """
    from itertools import groupby

    from .config.personalities import get_all_personalities

    db: Session = get_tenant_session(org_id)
    try:
        # 1. Fetch all personalities to map IDs -> Names
        # We need this because Vote table stores IDs, but frontend expects Names for display.
        all_personalities = get_all_personalities(org_id)
        pid_to_name = {p["id"]: p["name"] for p in all_personalities}

        def resolve_name(pid, model_name):
            if pid and pid in pid_to_name:
                return pid_to_name[pid]
            return model_name or "Unknown"

        # 2. Fetch raw votes joined with Conversation
        results = (
            db.query(Vote, Conversation)
            .join(Conversation, Vote.conversation_id == Conversation.id)
            .order_by(
                Vote.conversation_id, Vote.turn_number, Vote.voter_model
            )  # Order for grouping
            .all()
        )

        history = []

        # 3. Group by Session (Conversation + Turn)
        # We use a composite key of (conversation_id, turn_number)
        def get_session_key(item):
            vote, conv = item
            return (vote.conversation_id, vote.turn_number)

        for (conv_id, turn), session_votes_iter in groupby(results, key=get_session_key):
            session_votes = list(session_votes_iter)
            first_vote, conversation = session_votes[0]

            # 4. Group by Voter within Session
            votes_data = []  # The 'votes' array expected by frontend

            # Sort by voter to ensure groupby works
            session_votes.sort(key=lambda x: x[0].voter_model or "")

            def get_voter_key(item):
                v, _ = item
                return (v.voter_personality_id, v.voter_model)

            for (voter_pid, voter_model), voter_group in groupby(session_votes, key=get_voter_key):
                voter_group = list(voter_group)

                rankings = []
                for v, _ in voter_group:
                    cand_name = resolve_name(v.candidate_personality_id, v.candidate_model)
                    rankings.append(
                        {"candidate": cand_name, "rank": v.rank, "reasoning": v.reasoning}
                    )

                # Sort rankings by rank
                rankings.sort(key=lambda x: x["rank"])

                voter_name = resolve_name(voter_pid, voter_model)

                votes_data.append(
                    {
                        "voter_personality": voter_name,  # Frontend looks for this or voter_model
                        "voter_model": voter_model,
                        "rankings": rankings,
                    }
                )

            # Construct the Session object
            session_obj = {
                "id": f"{conv_id}_{turn}",  # Composite ID for frontend key
                "conversation_id": conv_id,
                "timestamp": first_vote.timestamp.isoformat(),
                "turn_number": turn,
                "user_id": conversation.user_id,
                "conversation_title": conversation.title,
                # Flatten user_id logic from admin_routes will add "username" later
                "votes": votes_data,
            }
            history.append(session_obj)

        return history

    except Exception as e:
        logger.error(f"Error loading voting history: {e}")
        return []
    finally:
        db.close()


def get_consensus_stats(org_id: str) -> dict[str, Any]:
    """
    Get aggregated statistics for Consensus Mode contributions.
    Includes strategy breakdowns and recent activity timeline.
    """
    from .config.personalities import get_all_personalities
    from .models import ConsensusContribution

    db: Session = get_tenant_session(org_id)
    try:
        # 1. Resolve Personalities (ID -> Name)
        all_personalities = get_all_personalities(org_id)
        pid_to_name = {p["id"]: p["name"] for p in all_personalities}

        def resolve_name(pid):
            return pid_to_name.get(pid, "Unknown Personality")

        contributions = (
            db.query(ConsensusContribution).order_by(ConsensusContribution.created_at.desc()).all()
        )

        # Raw list (Recent 50)
        raw_data = []

        # Aggregations
        by_personality = {}
        by_strategy = {}

        total_score_sum = 0.0

        for i, c in enumerate(contributions):
            # Add to raw data (limit to 50 for timeline)
            if i < 50:
                raw_data.append(
                    {
                        "id": c.id,
                        "personality_id": c.personality_id,
                        "personality_name": resolve_name(c.personality_id),
                        "strategy": c.strategy,
                        "score": c.score,
                        "timestamp": c.created_at.isoformat(),
                        "conversation_id": c.conversation_id,
                    }
                )

            # Aggregate by Personality
            pid = c.personality_id or "unknown"
            p_name = resolve_name(pid)
            if pid not in by_personality:
                by_personality[pid] = {"name": p_name, "count": 0, "total_score": 0.0}
            by_personality[pid]["count"] += 1
            by_personality[pid]["total_score"] += c.score

            # Aggregate by Strategy
            strat = c.strategy or "unknown"
            if strat not in by_strategy:
                by_strategy[strat] = {"count": 0, "total_score": 0.0, "avg_score": 0.0}
            by_strategy[strat]["count"] += 1
            by_strategy[strat]["total_score"] += c.score

            total_score_sum += c.score

        # Finalize Averages for Strategies
        for s in by_strategy.values():
            if s["count"] > 0:
                s["avg_score"] = s["total_score"] / s["count"]

        return {
            "total_contributions": len(contributions),
            "global_avg_score": (total_score_sum / len(contributions)) if contributions else 0,
            "by_personality": by_personality,
            "by_strategy": by_strategy,
            "recent_activity": raw_data,
        }
    except Exception as e:
        logger.error(f"Error loading consensus stats: {e}")
        return {"error": str(e)}
    finally:
        db.close()
