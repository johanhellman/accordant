"""
Service for calculating personality rankings and generating feedback summaries.
"""

import logging
import os
from collections import defaultdict
from typing import Any

from sqlalchemy import func

from .config.personalities import get_active_personalities
from .database import get_tenant_session
from .models import Vote
from .organizations import ORGS_DATA_DIR

logger = logging.getLogger(__name__)


def calculate_league_table(org_id: str) -> list[dict[str, Any]]:
    """
    Calculate the league table for an organization using SQLite.

    Metrics:
    - distinct_sessions: Number of conversations participated in.
    - votes_received: Total number of times ranked by others.
    - wins: Number of times ranked #1.
    - average_rank: Mean of rank positions.
    - win_rate: wins / distinct_sessions (percentage).
    """
    # 1. Get active personalities config to map ID -> Name
    active_personalities_list = get_active_personalities(org_id)
    active_map = {p["id"]: p for p in active_personalities_list if "id" in p}

    # 2. Query Aggregate Stats from DB
    db = get_tenant_session(org_id)
    try:
        # We group by candidate_personality_id (UUID)
        # We also group by candidate_model for legacy records or fallback
        # But ideally we just trust ID.

        # Query: Get stats per personality ID
        # We need to handle cases where ID is null (legacy data) - but we decided to drop legacy data.
        # So we assume ID is present for new data.

        query = (
            db.query(
                Vote.candidate_personality_id,
                Vote.candidate_model,
                func.count(Vote.id).label("votes_received"),
                func.sum(Vote.rank).label("total_rank_sum"),
                func.count(func.distinct(Vote.conversation_id)).label("sessions"),
            )
            .filter(Vote.candidate_personality_id.isnot(None))
            .group_by(Vote.candidate_personality_id, Vote.candidate_model)
        )

        rows = query.all()

        # Also need WINS (Rank=1)
        # We can do a separate query or conditional sum (if supported by sqlite/sqlalchemy version)
        # Simpler to do separate query for wins
        wins_query = (
            db.query(Vote.candidate_personality_id, func.count(Vote.id).label("wins"))
            .filter(Vote.candidate_personality_id.isnot(None), Vote.rank == 1)
            .group_by(Vote.candidate_personality_id)
        )

        wins_map = {row.candidate_personality_id: row.wins for row in wins_query.all()}

        stats = {}

        # Process DB Rows
        for row in rows:
            p_id = row.candidate_personality_id

            # Resolve Name
            name = row.candidate_model  # Fallback
            is_active = False

            if p_id in active_map:
                name = active_map[p_id]["name"]
                is_active = True

            wins = wins_map.get(p_id, 0)

            stats[p_id] = {
                "id": p_id,
                "name": name,
                "is_active": is_active,
                "sessions": row.sessions,
                "votes_received": row.votes_received,
                "wins": wins,
                "total_rank_sum": row.total_rank_sum,
            }

        # Add Active Personalities that have 0 votes yet
        for p_id, p in active_map.items():
            if p_id not in stats:
                stats[p_id] = {
                    "id": p_id,
                    "name": p["name"],
                    "is_active": p.get("enabled", True),
                    "sessions": 0,
                    "votes_received": 0,
                    "wins": 0,
                    "total_rank_sum": 0,
                }

        # Format Results
        results = []
        for p_id, data in stats.items():
            votes = data["votes_received"]
            distinct_sessions = data["sessions"]

            avg_rank = data["total_rank_sum"] / votes if votes > 0 else 0.0
            win_rate = (data["wins"] / distinct_sessions * 100) if distinct_sessions > 0 else 0.0

            results.append(
                {
                    "id": p_id,
                    "name": data["name"],
                    "is_active": data["is_active"],
                    "sessions": distinct_sessions,
                    "votes_received": votes,
                    "wins": data["wins"],
                    "average_rank": round(avg_rank, 2),
                    "win_rate": round(win_rate, 1),
                }
            )

        # Sort
        results.sort(key=lambda x: (-x["win_rate"], x["average_rank"]))
        return results

    except Exception as e:
        logger.error(f"Error calculating league table: {e}")
        return []
    finally:
        db.close()


def calculate_instance_league_table() -> list[dict[str, Any]]:
    """
    Calculate global league table across all organizations.
    Note: For privacy, we aggregate only by Model/Name matching System Defaults?
    Or just aggregate by ID?
    Since System Personalities have the SAME ID across orgs (unless shadowed with new ID?),
    we can aggregate by ID.

    If shadowed, likely they keep same ID or generate new?
    Logic says: Shadowing uses same ID but source=custom.

    So aggregation by ID works great for "Global System Personality Performance".
    """
    if not os.path.exists(ORGS_DATA_DIR):
        return []

    org_ids = [
        d for d in os.listdir(ORGS_DATA_DIR) if os.path.isdir(os.path.join(ORGS_DATA_DIR, d))
    ]

    global_stats = defaultdict(
        lambda: {
            "id": "",
            "name": "Unknown",
            "sessions": 0,
            "votes_received": 0,
            "wins": 0,
            "total_rank_sum": 0,
        }
    )

    for org_id in org_ids:
        # Re-use the per-org logic
        org_results = calculate_league_table(org_id)

        for res in org_results:
            p_id = res["id"]
            if not p_id:
                continue

            # We assume name from first encounter is good enough (usually system name)
            if global_stats[p_id]["name"] == "Unknown":
                global_stats[p_id]["name"] = res["name"]
                global_stats[p_id]["id"] = p_id

            global_stats[p_id]["sessions"] += res["sessions"]
            global_stats[p_id]["votes_received"] += res["votes_received"]
            global_stats[p_id]["wins"] += res["wins"]
            # We need to back-calculate sum from average to aggregate correctly
            # avg = sum / votes  => sum = avg * votes
            global_stats[p_id]["total_rank_sum"] += res["average_rank"] * res["votes_received"]

    # Format
    results = []
    for p_id, data in global_stats.items():
        votes = data["votes_received"]
        distinct_sessions = data[
            "sessions"
        ]  # This is approximate (sum of org sessions), strict global distinct needs UUIDs of sessions

        avg_rank = data["total_rank_sum"] / votes if votes > 0 else 0.0
        win_rate = (data["wins"] / distinct_sessions * 100) if distinct_sessions > 0 else 0.0

        results.append(
            {
                "name": data["name"],  # Global view focuses on name
                "id": p_id,
                "sessions": distinct_sessions,
                "votes_received": votes,
                "wins": data["wins"],
                "average_rank": round(avg_rank, 2),
                "win_rate": round(win_rate, 1),
            }
        )

    results.sort(key=lambda x: (-x["win_rate"], x["average_rank"]))
    return results


async def generate_feedback_summary(
    org_id: str, personality_name: str, api_key: str, base_url: str
):
    """
    Generate feedback summary.
    Updated to query 'Vote' table directly for reasoning text.
    """
    from .config.personalities import load_org_system_prompts
    from .openrouter import query_model

    db = get_tenant_session(org_id)
    try:
        # 1. Find the ID for this name (UI passes name currently, ideally should pass ID)
        # We try to lookup ID from active configs first
        active_list = get_active_personalities(org_id)
        target_id = None
        for p in active_list:
            if p["name"] == personality_name:
                target_id = p["id"]
                break

        # 2. Query Votes for this candidate
        # If we have ID, query by ID. If not, fallback to name (model column)
        query = db.query(Vote).filter(Vote.reasoning.isnot(None))

        if target_id:
            query = query.filter(Vote.candidate_personality_id == target_id)
        else:
            query = query.filter(Vote.candidate_model == personality_name)

        # Limit to recent votes
        votes = query.order_by(Vote.timestamp.desc()).limit(50).all()

        if not votes:
            return "No qualitative feedback available."

        reasoning_snippets = []
        for v in votes:
            if v.reasoning:
                snippet = (
                    f"Voter ({v.voter_model}) on Session {v.conversation_id}:\n{v.reasoning}\n---"
                )
                reasoning_snippets.append(snippet)

        if not reasoning_snippets:
            return "No qualitative feedback available."

        feedback_text = "\n".join(reasoning_snippets)

        # 3. Summarize with LLM
        prompts = load_org_system_prompts(org_id)
        synthesis_prompt_template = prompts.get("feedback_synthesis_prompt", "")

        if not synthesis_prompt_template:
            synthesis_prompt_template = """
            You are analyzing peer feedback for an AI Personality named "{personality_name}".
            Your task is to synthesize this feedback into a constructive report.
            FEEDBACK LOGS:
            {feedback_text}
            Synthesize:
            """

        prompt = synthesis_prompt_template.format(
            personality_name=personality_name, feedback_text=feedback_text
        )

        # Use a default smart model (Chairman model) for this analysis
        model = "gemini/gemini-2.5-pro"  # TODO: Load from config

        messages = [{"role": "user", "content": prompt}]
        response = await query_model(model, messages, api_key=api_key, base_url=base_url)

        return response.get("content") if response else "Failed to generate summary."

    except Exception as e:
        logger.error(f"Error generating feedback: {e}")
        return "Error producing feedback summary."
    finally:
        db.close()
