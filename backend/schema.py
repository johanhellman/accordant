"""Schema and type definitions for LLM Council.

Note: This module was renamed from 'types.py' to avoid shadowing Python's
built-in 'types' module, which caused import conflicts when running tools
like pip-audit from the backend directory.
"""

from typing import Any, Literal, TypedDict

from pydantic import BaseModel


# TypedDict definitions for council orchestration
class MessageDict(TypedDict):
    """Type definition for LLM message structure."""

    role: str
    content: str


class Stage1Result(TypedDict, total=False):
    """Type definition for Stage 1 response result."""

    model: str
    response: str
    personality_id: str | None
    personality_name: str | None


class Stage2Result(TypedDict, total=False):
    """Type definition for Stage 2 ranking result."""

    model: str
    personality_id: str | None
    personality_name: str | None
    ranking: str
    parsed_ranking: list[str]


class Stage3Result(TypedDict):
    """Type definition for Stage 3 final synthesis result."""

    model: str
    response: str


# Pydantic models for API requests/responses
class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""

    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""

    content: str


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""

    id: str
    created_at: str
    title: str
    message_count: int
    processing_state: str = "idle"


class Conversation(BaseModel):
    """Full conversation with all messages."""

    id: str
    created_at: str
    title: str
    processing_state: str = "idle"
    messages: list[dict[str, Any]]


class RegistrationRequest(BaseModel):
    """
    Request for atomic User + Organization registration.
    Supersedes simple UserCreate to prevent orphaned users.
    """

    username: str
    password: str
    mode: Literal["create_org", "join_org"] = "create_org"
    org_name: str | None = None  # Required if mode is create_org
    invite_code: str | None = None  # Future use for join_org


class ChangePasswordRequest(BaseModel):
    """Request to change user password."""

    current_password: str
    new_password: str


class ErrorResponse(BaseModel):
    """Standard error response structure."""
    
    error: dict[str, Any]  # {code, message, correlation_id, details}
