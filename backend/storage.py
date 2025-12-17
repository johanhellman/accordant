"""Database-based storage for conversations (Tenant Sharded)."""

import logging
from typing import Any

from sqlalchemy import func

from . import models
from .database import get_tenant_session

logger = logging.getLogger(__name__)

# --- Conversation Operations ---


def create_conversation(conversation_id: str, user_id: str, org_id: str) -> dict[str, Any]:
    """Create a new conversation in the tenant DB."""
    # Strict isolation: Connect to org-specific DB
    with get_tenant_session(org_id) as db:
        new_conv = models.Conversation(
            id=conversation_id,
            user_id=user_id,
            org_id=org_id,  # Metadata only in tenant DB
            title="New Conversation",
        )
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)

        return {
            "id": new_conv.id,
            "created_at": new_conv.created_at.isoformat()
            if hasattr(new_conv.created_at, "isoformat")
            else str(new_conv.created_at),
            "title": new_conv.title,
            "processing_state": "idle",
            "messages": [],  # Empty on creation
            "user_id": new_conv.user_id,
            "org_id": new_conv.org_id,
        }


def get_conversation(conversation_id: str, org_id: str) -> dict[str, Any] | None:
    """
    Load a conversation from tenant storage.
    Joins with Message table to reconstruct history.
    """
    with get_tenant_session(org_id) as db:
        conv = (
            db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
        )

        if conv:
            # Reconstruct messages list from normalized table
            # Sort by created_at (assumed insert order for now)
            # messages_rel is a relationship, so it fetches automatically
            # We should probably ensure ordering in the relationship or here

            # Explicit sort to be safe
            messages_sorted = sorted(conv.messages_rel, key=lambda m: m.created_at)

            messages_list = []
            for m in messages_sorted:
                msg_dict = {
                    "role": m.role,
                    "content": m.content,
                    # "created_at": m.created_at.isoformat() # Optional if frontend needs it
                }

                # If assistant, unpack separate stages
                if m.stages_json:
                    msg_dict.update(m.stages_json)

                messages_list.append(msg_dict)

            return {
                "id": conv.id,
                "created_at": conv.created_at.isoformat()
                if hasattr(conv.created_at, "isoformat")
                else str(conv.created_at),
                "title": conv.title,
                "processing_state": conv.processing_state or "idle",
                "messages": messages_list,
                "user_id": conv.user_id,
                "org_id": conv.org_id,
            }
    return None


def save_conversation(conversation: dict[str, Any], org_id: str):
    """
    Save specific fields (Title).
    Note: Messages are now added incrementally via add_message,
    so 'save_conversation' sending the whole blob is deprecated/inefficient
    but we support title updates here.
    """
    with get_tenant_session(org_id) as db:
        conv = (
            db.query(models.Conversation)
            .filter(models.Conversation.id == conversation["id"])
            .first()
        )
        if conv:
            if "title" in conversation:
                conv.title = conversation["title"]
            db.commit()


def list_conversations(user_id: str, org_id: str) -> list[dict[str, Any]]:
    """List conversations (metadata only)."""
    with get_tenant_session(org_id) as db:
        try:
            # No need to filter by org_id column, as we are IN the org DB
            query = db.query(
                models.Conversation, func.count(models.Message.id).label("message_count")
            ).outerjoin(models.Message, models.Conversation.id == models.Message.conversation_id)

            if user_id:
                query = query.filter(models.Conversation.user_id == user_id)

            # Group by conversation fields to get count per conversation
            query = query.group_by(
                models.Conversation.id,
                models.Conversation.user_id,
                models.Conversation.org_id,
                models.Conversation.title,
                models.Conversation.created_at,
                models.Conversation.processing_state,
            )

            convs_with_counts = query.order_by(models.Conversation.created_at.desc()).all()

            results = []
            for c, message_count in convs_with_counts:
                results.append(
                    {
                        "id": c.id,
                        "created_at": c.created_at.isoformat()
                        if hasattr(c.created_at, "isoformat")
                        else str(c.created_at),
                        "title": c.title,
                        "processing_state": c.processing_state or "idle",
                        "message_count": message_count or 0,
                    }
                )
            return results
        except Exception as e:
            logger.error(
                f"Error listing conversations for user {user_id} in org {org_id}: {e}",
                exc_info=True,
            )
            raise


def add_user_message(conversation_id: str, content: str, org_id: str):
    """Add a user message to the normalized table."""
    with get_tenant_session(org_id) as db:
        # Verify conv exists
        conv = (
            db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
        )
        if not conv:
            raise ValueError(f"Conversation {conversation_id} not found")

        import uuid

        msg = models.Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="user",
            content=content,
            stages_json=None,
        )
        db.add(msg)
        db.commit()


def add_assistant_message(
    conversation_id: str,
    stage1: list[dict[str, Any]],
    stage2: list[dict[str, Any]],
    stage3: dict[str, Any],
    org_id: str,
):
    """Add an assistant message to the normalized table."""
    with get_tenant_session(org_id) as db:
        # Verify conv exists
        conv = (
            db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
        )
        if not conv:
            raise ValueError(f"Conversation {conversation_id} not found")

        import uuid

        # Combine stages into metadata
        stages_data = {"stage1": stage1, "stage2": stage2, "stage3": stage3}

        # Use final response as main content
        final_content = stage3.get("response", "")

        msg = models.Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="assistant",
            content=final_content,
            stages_json=stages_data,
        )
        db.add(msg)

        # --- Consensus Attribution Saving ---
        # If Stage 3 contains 'consensus_contributions' metadata, save to separate table
        contributions = stage3.get("consensus_contributions", [])
        if contributions:
            for contrib in contributions:
                # Expecting: {personality_id, score/weight, strategy, reasoning}
                # The Service returns {id, weight, reason, strategy}
                # Map keys: id -> personality_id

                # Default "weight" from prompt is raw format
                # We need to map it carefully

                c_id = str(uuid.uuid4())
                new_contrib = models.ConsensusContribution(
                    id=c_id,
                    conversation_id=conversation_id,
                    personality_id=contrib.get("id"),
                    strategy=contrib.get("strategy", "unknown"),
                    score=float(contrib.get("weight", 0.0)),
                    reasoning=contrib.get("reason"),
                )
                db.add(new_contrib)

        db.commit()


def update_conversation_title(conversation_id: str, title: str, org_id: str):
    """Update title."""
    with get_tenant_session(org_id) as db:
        conv = (
            db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
        )
        if conv:
            conv.title = title
            db.commit()


def update_conversation_status(conversation_id: str, status: str, org_id: str):
    """Update processing_state."""
    with get_tenant_session(org_id) as db:
        conv = (
            db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
        )
        if conv:
            conv.processing_state = status
            db.commit()


def delete_conversation(conversation_id: str, org_id: str) -> bool:
    """Delete conversation."""
    with get_tenant_session(org_id) as db:
        conv = (
            db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
        )
        if conv:
            db.delete(conv)  # Cascades to messages
            db.commit()
            return True
    return False


def delete_user_conversations(user_id: str, org_id: str) -> int:
    """Delete all conversations for a user."""
    # Strict org_id enforcement is implicit by using get_tenant_session(org_id)
    with get_tenant_session(org_id) as db:
        stmt = models.Conversation.__table__.delete().where(models.Conversation.user_id == user_id)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount
