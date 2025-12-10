"""Database-based storage for conversations."""

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models

logger = logging.getLogger(__name__)

# --- Conversation Operations ---

def create_conversation(conversation_id: str, user_id: str, org_id: str) -> dict[str, Any]:
    """Create a new conversation."""
    with SessionLocal() as db:
        new_conv = models.Conversation(
            id=conversation_id,
            user_id=user_id,
            org_id=org_id,
            title="New Conversation",
            messages=[]
        )
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        
        return {
            "id": new_conv.id,
            "created_at": new_conv.created_at.isoformat() if hasattr(new_conv.created_at, 'isoformat') else str(new_conv.created_at),
            "title": new_conv.title,
            "messages": new_conv.messages,
            "user_id": new_conv.user_id,
            "org_id": new_conv.org_id
        }

def get_conversation(conversation_id: str, org_id: str) -> dict[str, Any] | None:
    """Load a conversation from storage."""
    with SessionLocal() as db:
        conv = db.query(models.Conversation).filter(
            models.Conversation.id == conversation_id,
            models.Conversation.org_id == org_id
        ).first()
        
        if conv:
            return {
                "id": conv.id,
                "created_at": conv.created_at.isoformat() if hasattr(conv.created_at, 'isoformat') else str(conv.created_at),
                "title": conv.title,
                "messages": conv.messages or [],
                "user_id": conv.user_id,
                "org_id": conv.org_id
            }
    return None

def save_conversation(conversation: dict[str, Any], org_id: str):
    """
    Save a conversation to storage.
    Note: In DB model, we just update the specific fields.
    """
    with SessionLocal() as db:
        conv = db.query(models.Conversation).filter(models.Conversation.id == conversation["id"]).first()
        if conv:
            conv.title = conversation.get("title", conv.title)
            conv.messages = conversation.get("messages", [])
            db.commit()

def list_conversations(user_id: str, org_id: str) -> list[dict[str, Any]]:
    """List conversations (metadata only)."""
    with SessionLocal() as db:
        query = db.query(models.Conversation).filter(models.Conversation.org_id == org_id)
        if user_id:
            query = query.filter(models.Conversation.user_id == user_id)
            
        convs = query.order_by(models.Conversation.created_at.desc()).all()
        
        results = []
        for c in convs:
            results.append({
                "id": c.id,
                "created_at": c.created_at.isoformat() if hasattr(c.created_at, 'isoformat') else str(c.created_at),
                "title": c.title,
                "message_count": len(c.messages) if c.messages else 0
            })
        return results

def add_user_message(conversation_id: str, content: str, org_id: str):
    """Add a user message."""
    with SessionLocal() as db:
        conv = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
        if conv:
            # SQLAlchemy JSON type mutation detection can be tricky.
            # Best to re-assign the list.
            messages = list(conv.messages) if conv.messages else []
            messages.append({"role": "user", "content": content})
            conv.messages = messages
            
            # Since we mutated a JSON field, flag it (or re-assignment handles it)
            db.commit()
        else:
             raise ValueError(f"Conversation {conversation_id} not found")

def add_assistant_message(
    conversation_id: str,
    stage1: list[dict[str, Any]],
    stage2: list[dict[str, Any]],
    stage3: dict[str, Any],
    org_id: str,
):
    """Add an assistant message."""
    with SessionLocal() as db:
        conv = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
        if conv:
            messages = list(conv.messages) if conv.messages else []
            messages.append(
                {"role": "assistant", "stage1": stage1, "stage2": stage2, "stage3": stage3}
            )
            conv.messages = messages
            db.commit()
        else:
            raise ValueError(f"Conversation {conversation_id} not found")

def update_conversation_title(conversation_id: str, title: str, org_id: str):
    """Update title."""
    with SessionLocal() as db:
        conv = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
        if conv:
            conv.title = title
            db.commit()

def delete_conversation(conversation_id: str, org_id: str) -> bool:
    """Delete conversation."""
    with SessionLocal() as db:
        conv = db.query(models.Conversation).filter(
            models.Conversation.id == conversation_id,
            models.Conversation.org_id == org_id
        ).first()
        if conv:
            db.delete(conv)
            db.commit()
            return True
    return False

def delete_user_conversations(user_id: str, org_id: str) -> int:
    """Delete all conversations for a user."""
    with SessionLocal() as db:
        # Bulk delete might be efficient
        stmt = models.Conversation.__table__.delete().where(
            models.Conversation.user_id == user_id
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount
