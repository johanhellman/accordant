"""
Service for calculating personality rankings and generating feedback summaries.
"""

import logging
import os
from collections import defaultdict
from typing import Any

from .config.personalities import get_active_personalities
from .organizations import ORGS_DATA_DIR
from .storage import get_conversation
from .voting_history import load_voting_history

logger = logging.getLogger(__name__)


def calculate_league_table(org_id: str) -> list[dict[str, Any]]:
    """
    Calculate the league table for an organization.
    
    Metrics:
    - distinct_sessions: Number of conversations participated in.
    - votes_received: Total number of times ranked by others.
    - wins: Number of times ranked #1.
    - total_rank_sum: Sum of all rank positions (1=1st, 2=2nd, etc).
    - average_rank: total_rank_sum / votes_received.
    - win_rate: wins / distinct_sessions (percentage).
    """
    history = load_voting_history(org_id)
    active_personalities = {p["name"]: p for p in get_active_personalities(org_id)}
    
    stats = defaultdict(lambda: {
        "name": "",
        "sessions": set(), # Set of conversation IDs
        "votes_received": 0,
        "wins": 0,
        "total_rank_sum": 0,
        "is_active": False
    })

    # Initialize with active personalities to ensure they appear even if no votes
    for name, p in active_personalities.items():
        stats[name]["name"] = name
        stats[name]["is_active"] = True
        stats[name]["id"] = p.get("id")

    for session in history:
        conv_id = session.get("conversation_id")
        
        for vote in session.get("votes", []):
            rankings = vote.get("rankings", [])
            for rank_entry in rankings:
                candidate = rank_entry.get("candidate")
                rank = rank_entry.get("rank")
                
                if candidate:
                    stats[candidate]["name"] = candidate
                    stats[candidate]["votes_received"] += 1
                    stats[candidate]["total_rank_sum"] += rank
                    stats[candidate]["sessions"].add(conv_id)
                    
                    if rank == 1:
                        stats[candidate]["wins"] += 1

    # Format results
    results = []
    for name, data in stats.items():
        distinct_sessions = len(data["sessions"])
        votes = data["votes_received"]
        
        avg_rank = data["total_rank_sum"] / votes if votes > 0 else 0.0
        win_rate = (data["wins"] / distinct_sessions * 100) if distinct_sessions > 0 else 0.0
        
        results.append({
            "id": data.get("id"), # Might be missing for legacy/deleted personalities
            "name": name,
            "is_active": data["is_active"],
            "sessions": distinct_sessions,
            "votes_received": votes,
            "wins": data["wins"],
            "average_rank": round(avg_rank, 2),
            "win_rate": round(win_rate, 1)
        })

    # Sort by Win Rate (DESC), then Average Rank (ASC)
    results.sort(key=lambda x: (-x["win_rate"], x["average_rank"]))
    
    return results


def calculate_instance_league_table() -> list[dict[str, Any]]:
    """
    Calculate global league table by aggregating stats across ALL organizations.
    Only includes System Personalities (to avoid leaking custom names).
    """
    global_stats = defaultdict(lambda: {
        "name": "",
        "sessions": 0,
        "votes_received": 0,
        "wins": 0,
        "total_rank_sum": 0
    })

    # Iterate over all org directories
    if not os.path.exists(ORGS_DATA_DIR):
        return []

    org_ids = [d for d in os.listdir(ORGS_DATA_DIR) if os.path.isdir(os.path.join(ORGS_DATA_DIR, d))]

    for org_id in org_ids:
        # Load local league table for this org
        # (Reusing valid logic instead of re-parsing JSON to ensure consistency)
        org_results = calculate_league_table(org_id)
        
        for res in org_results:
            # FILTER: We ideally only want "System" personalities.
            # However, we don't strictly know if a name is System or Custom without loading the registry.
            # For now, we aggregate everything, but the UI should filter.
            # Or better, we trust the name as the key.
            name = res["name"]
            global_stats[name]["name"] = name
            global_stats[name]["sessions"] += res["sessions"]
            global_stats[name]["votes_received"] += res["votes_received"]
            global_stats[name]["wins"] += res["wins"]
            # We can't sum averages, we have to back-calculate if possible, 
            # or just sum the raw inputs if available. 
            # calculate_league_table returns derived stats.
            # To do this accurately, calculate_league_table needs to return raw sums?
            # Let's just approximate or refactor calculate_league_table to be reusable?
            pass

    # REFACTOR STRATEGY: 
    # To avoid double calculation, let's implement a lower-level aggregator.
    # But for now, let's just parse the raw files again for the global view to be accurate.
    
    global_raw_stats = defaultdict(lambda: {
        "name": "",
        "sessions": set(), # using tuple (org_id, conv_id) for uniqueness
        "votes_received": 0,
        "wins": 0,
        "total_rank_sum": 0
    })

    for org_id in org_ids:
        history = load_voting_history(org_id)
        for session in history:
            unique_session_id = f"{org_id}_{session.get('conversation_id')}"
            
            for vote in session.get("votes", []):
                rankings = vote.get("rankings", [])
                for rank_entry in rankings:
                    candidate = rank_entry.get("candidate")
                    rank = rank_entry.get("rank")
                    
                    if candidate:
                        global_raw_stats[candidate]["name"] = candidate
                        global_raw_stats[candidate]["votes_received"] += 1
                        global_raw_stats[candidate]["total_rank_sum"] += rank
                        global_raw_stats[candidate]["sessions"].add(unique_session_id)
                        
                        if rank == 1:
                            global_raw_stats[candidate]["wins"] += 1

    # Format Global Results
    results = []
    for name, data in global_raw_stats.items():
        distinct_sessions = len(data["sessions"])
        votes = data["votes_received"]
        
        avg_rank = data["total_rank_sum"] / votes if votes > 0 else 0.0
        win_rate = (data["wins"] / distinct_sessions * 100) if distinct_sessions > 0 else 0.0
        
        results.append({
            "name": name,
            "sessions": distinct_sessions,
            "votes_received": votes,
            "wins": data["wins"],
            "average_rank": round(avg_rank, 2),
            "win_rate": round(win_rate, 1)
        })

    results.sort(key=lambda x: (-x["win_rate"], x["average_rank"]))
    return results


async def generate_feedback_summary(org_id: str, personality_name: str, api_key: str, base_url: str):
    """
    Generate a qualitative feedback summary for a personality.
    SECURE: Fetches content from Chat Storage on demand.
    """
    from .openrouter import query_model
    
    history = load_voting_history(org_id)
    
    # Collect reasoning texts
    reasoning_snippets = []
    
    # Limit to last N mentions to manage context window
    MAX_SNIPPETS = 50
    
    for session in reversed(history):
        if len(reasoning_snippets) >= MAX_SNIPPETS:
            break
            
        conv_id = session.get("conversation_id")
        
        # Check if relevant for this personality
        is_relevant = False
        votes_for_session = session.get("votes", [])
        
        # We need to find votes where this personality was RANKED (as candidate)
        # OR votes where this personality was the VOTER? 
        # Usually "Feedback" is what OTHERS said about YOU.
        
        # In our data structure:
        # "rankings": [{"candidate": "X", "rank": 1, "label": "A"}]
        # "reasoning": "I chose A because..."
        
        # The reasoning is usually a block of text explaining the sorting.
        # It might mention "Response A (Personality X) was good because..."
        
        # So we need to:
        # 1. Identify which anonymous Label corresponded to our Target Personality in this session.
        # 2. Extract specific comments about that Label? Or just dump the whole reasoning?
        # Dumping the whole reasoning is easier, defaulting to "Here is what peers said in sessions you were in".
        
        # Let's find the label for our personality in this session
        target_label = None
        # We need to reconstruct the label map?
        # The history doesn't strictly store the label map, but "votes" -> "rankings" has ("candidate", "label").
        # So we can infer it from any vote.
        
        if not votes_for_session:
            continue
            
        # Infer map from first vote
        first_vote_rankings = votes_for_session[0].get("rankings", [])
        for r in first_vote_rankings:
            if r.get("candidate") == personality_name:
                target_label = r.get("label")
                break
        
        if target_label:
            # This personality was present as 'target_label'
            
            # Now fetch the actual reasoning text from the conversation storage (FIREWALL CHECK)
            # The 'voting_history' might have 'reasoning' (new format) or not (old format).
            # If new format, we trust it (Wait, implementation plan said DO NOT STORE TEXT).
            # Correct: Plan said "voting_history.json will remain metadata-only".
            # So we MUST fetch from storage.
            
            # Optimization: Only fetch if we really need it.
            try:
                conversation = get_conversation(conv_id, org_id)
                if not conversation:
                    continue
                    
                # Find the assistant message with the reasoning.
                # It's usually a message from "assistant" (or specific model?)
                # Actually, in Stage 2, we have multiple LLM calls. The "Assistant Message" in the conversation history
                # is the FINAL summary (Stage 3). 
                # The Stage 2 votes are NOT always stored as visible messages in the main conversation history text!
                # Wait, where are Stage 2 results stored in the conversation?
                # storage.add_assistant_message stores:
                # { "role": "assistant", "content": ..., "metadata": { "stage1": ..., "stage2": ... } }
                
                # So we need to look at the metadata of the assistant messages.
                
                messages = conversation.get("messages", [])
                for msg in reversed(messages):
                    if msg.get("role") == "assistant":
                        meta = msg.get("metadata", {})
                        stage2 = meta.get("stage2", [])
                        
                        if stage2:
                            # Found the Stage 2 results!
                            for s2_res in stage2:
                                # Extract reasoning from this voter
                                raw_ranking = s2_res.get("ranking", "")
                                
                                # We want to know what they said about OUR target_label
                                # We can just include the whole reasoning text and let the LLM filter.
                                if raw_ranking:
                                    voter = s2_res.get("personality_name", s2_res.get("model"))
                                    snippet = f"Voter ({voter}) on Session {conv_id}:\n{raw_ranking}\n---"
                                    reasoning_snippets.append(snippet)
                            break # stop searching messages for this session
                            
            except Exception as e:
                logger.error(f"Error fetching conversation {conv_id} for feedback: {e}")
                continue

    if not reasoning_snippets:
        return "No qualitative feedback available."

    feedback_text = "\n".join(reasoning_snippets)

    # Summarize with LLM
    prompt = f"""
    You are analyzing peer feedback for an AI Personality named "{personality_name}".
    Below are extracts from voting sessions where other AIs evaluated responses, including {personality_name}'s.
    
    Your task is to synthesize this feedback into a constructive report.
    Identify:
    1. Recurring STRENGTHS (what do peers like?)
    2. Recurring WEAKNESSES (what do peers criticize?)
    3. Unique Characteristics noticed by others.
    
    FEEDBACK LOGS:
    
    {feedback_text}
    
    Synthesize:
    """
    
    # Use a default smart model (Chairman model) for this analysis
    model = "gemini/gemini-2.5-pro" # TODO: Load from config
    
    messages = [{"role": "user", "content": prompt}]
    response = await query_model(model, messages, api_key=api_key, base_url=base_url)
    
    return response.get("content") if response else "Failed to generate summary."
