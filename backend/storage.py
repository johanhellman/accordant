"""JSON-based storage for conversations."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .organizations import ORGS_DATA_DIR


def ensure_data_dir(org_id: str):
    """Ensure the organization data directory exists."""
    path = os.path.join(ORGS_DATA_DIR, org_id, "conversations")
    Path(path).mkdir(parents=True, exist_ok=True)


def get_conversation_path(conversation_id: str, org_id: str) -> str:
    """Get the file path for a conversation."""
    return os.path.join(ORGS_DATA_DIR, org_id, "conversations", f"{conversation_id}.json")


def create_conversation(conversation_id: str, user_id: str, org_id: str) -> dict[str, Any]:
    """
    Create a new conversation.

    Args:
        conversation_id: Unique identifier for the conversation
        user_id: ID of the user creating the conversation
        org_id: Organization ID

    Returns:
        New conversation dict
    """
    ensure_data_dir(org_id)

    conversation = {
        "id": conversation_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "New Conversation",
        "messages": [],
        "user_id": user_id,
        "org_id": org_id,
    }

    # Save to file
    path = get_conversation_path(conversation_id, org_id)
    with open(path, "w") as f:
        json.dump(conversation, f, indent=2)

    return conversation


def get_conversation(conversation_id: str, org_id: str) -> dict[str, Any] | None:
    """
    Load a conversation from storage.

    Args:
        conversation_id: Unique identifier for the conversation
        org_id: Organization ID

    Returns:
        Conversation dict or None if not found
    """
    path = get_conversation_path(conversation_id, org_id)

    if not os.path.exists(path):
        return None

    with open(path) as f:
        return json.load(f)


def save_conversation(conversation: dict[str, Any], org_id: str):
    """
    Save a conversation to storage.

    Args:
        conversation: Conversation dict to save
        org_id: Organization ID
    """
    ensure_data_dir(org_id)

    path = get_conversation_path(conversation["id"], org_id)
    with open(path, "w") as f:
        json.dump(conversation, f, indent=2)


def list_conversations(user_id: str, org_id: str) -> list[dict[str, Any]]:
    """
    List conversations (metadata only).
    Filters by user ownership and organization.

    Args:
        user_id: User ID to filter by.
        org_id: Organization ID.

    Returns:
        List of conversation metadata dicts
    """
    # If user has no organization, they can't have conversations
    if not org_id:
        return []

    ensure_data_dir(org_id)

    conversations_dir = os.path.join(ORGS_DATA_DIR, org_id, "conversations")
    if not os.path.exists(conversations_dir):
        return []

    conversations = []
    for filename in os.listdir(conversations_dir):
        if filename.endswith(".json"):
            path = os.path.join(conversations_dir, filename)
            try:
                with open(path) as f:
                    data = json.load(f)

                    # Filter by user_id if provided
                    if user_id and data.get("user_id") != user_id:
                        continue

                    # Return metadata only
                    conversations.append(
                        {
                            "id": data["id"],
                            "created_at": data["created_at"],
                            "title": data.get("title", "New Conversation"),
                            "message_count": len(data["messages"]),
                        }
                    )
            except Exception:  # nosec B112
                # Skip malformed files - intentional exception handling for robustness
                continue

    # Sort by creation time, newest first
    conversations.sort(key=lambda x: x["created_at"], reverse=True)

    return conversations


def add_user_message(conversation_id: str, content: str, org_id: str):
    """
    Add a user message to a conversation.

    Args:
        conversation_id: Conversation identifier
        content: User message content
        org_id: Organization ID
    """
    conversation = get_conversation(conversation_id, org_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["messages"].append({"role": "user", "content": content})

    save_conversation(conversation, org_id)


def add_assistant_message(
    conversation_id: str,
    stage1: list[dict[str, Any]],
    stage2: list[dict[str, Any]],
    stage3: dict[str, Any],
    org_id: str,
):
    """
    Add an assistant message with all 3 stages to a conversation.

    Args:
        conversation_id: Conversation identifier
        stage1: List of individual model responses
        stage2: List of model rankings
        stage3: Final synthesized response
        org_id: Organization ID
    """
    conversation = get_conversation(conversation_id, org_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["messages"].append(
        {"role": "assistant", "stage1": stage1, "stage2": stage2, "stage3": stage3}
    )

    save_conversation(conversation, org_id)


def update_conversation_title(conversation_id: str, title: str, org_id: str):
    """
    Update the title of a conversation.

    Args:
        conversation_id: Conversation identifier
        title: New title for the conversation
        org_id: Organization ID
    """
    conversation = get_conversation(conversation_id, org_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["title"] = title
    save_conversation(conversation, org_id)


def delete_conversation(conversation_id: str, org_id: str) -> bool:
    """
    Delete a conversation.
    
    Args:
        conversation_id: ID of conversation to delete
        org_id: Organization ID
        
    Returns:
        bool: True if deleted, False if not found
    """
    path = get_conversation_path(conversation_id, org_id)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def delete_user_conversations(user_id: str, org_id: str) -> int:
    """
    Delete all conversations owned by a user (Right to Erasure).
    
    Args:
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        int: Number of conversations deleted
    """
    ensure_data_dir(org_id)
    conversations_dir = os.path.join(ORGS_DATA_DIR, org_id, "conversations")
    
    if not os.path.exists(conversations_dir):
        return 0
        
    deleted_count = 0
    for filename in os.listdir(conversations_dir):
        if filename.endswith(".json"):
            path = os.path.join(conversations_dir, filename)
            try:
                with open(path) as f:
                    data = json.load(f)
                    
                if data.get("user_id") == user_id:
                    os.remove(path)
                    deleted_count += 1
            except Exception:
                continue
                
    return deleted_count
