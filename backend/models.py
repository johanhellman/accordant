from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import SystemBase, TenantBase

# --- System Models (system.db) ---


class Organization(SystemBase):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    settings = Column(JSON, default={})
    api_config = Column(JSON, default={})

    # Relationships (System Only)
    # Users are in the same DB, so this FK works
    users = relationship("User", back_populates="organization", foreign_keys="User.org_id")

    # Note: No relationship to Conversations anymore, as they are in a different DB.


class User(SystemBase):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)  # Org Admin
    is_instance_admin = Column(Boolean, default=False)  # System Admin

    # Foreign Key works because Org is in SystemBase
    org_id = Column(String, ForeignKey("organizations.id"), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="users", foreign_keys=[org_id])

    # Logical link only - no ORM relationship to conversations possible across DBs
    # conversations = relationship("Conversation", back_populates="user") # REMOVED


# --- Tenant Models (tenant.db) ---


class Conversation(TenantBase):
    """
    Stores conversation metadata.
    Living in `org_{id}.db`, so strict isolation is enforced physically.
    """

    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)

    # We store user_id for display/filtering, but CANNOT have a ForeignKey
    # because 'users' table is in system.db
    user_id = Column(String, nullable=False, index=True)

    # org_id is technically redundant since the DB itself is the org,
    # but kept for metadata consistency.
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)

    # [MIGRATED] 'messages' JSON blobs are removed.
    org_id = Column(String, index=True)  # Tenant Context
    processing_state = Column(String, default="idle")  # idle, active, error

    # One-to-many relationship with messages
    messages_rel = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(TenantBase):
    """
    Normalized message storage.
    """

    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)

    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # Store Council stages (stage1, stage2, stage3) as JSON
    # This keeps the schema rigorous but flexible for the complex council data
    stages_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)  # Important for ordering!

    # Relationships
    conversation = relationship("Conversation", back_populates="messages_rel")


class Vote(TenantBase):
    """
    Stores voting history for the Personality League Table.
    Living in `org_{id}.db` ensures privacy.
    """

    __tablename__ = "votes"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, index=True)
    turn_number = Column(Integer, default=1)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Voter Identity
    # We store both model name (for historical accuracy) and ID (for identity)
    voter_model = Column(String)
    voter_personality_id = Column(String, nullable=True)

    # Candidate Identity (The one being ranked)
    candidate_model = Column(String)
    candidate_personality_id = Column(String, nullable=True)

    # The Vote
    rank = Column(Integer)  # e.g., 1, 2, 3
    label = Column(String)  # e.g., "A", "B" (Historical context)
    reasoning = Column(Text, nullable=True)  # Qualitative feedback details


class ConsensusContribution(TenantBase):
    """
    Tracks which personalities contributed to a formulated Consensus answer (Stage 3).
    Used for analytics and attribution transparency.
    """

    __tablename__ = "consensus_contributions"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, index=True, nullable=False)

    # Metadata
    personality_id = Column(String, nullable=False)
    strategy = Column(String, nullable=False)  # e.g. "risk_averse"

    # The Attribution (0.0 to 1.0)
    score = Column(Float)

    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CouncilPack(TenantBase):
    """
    Definition of a Council Pack (Custom or System mirror).
    """

    __tablename__ = "council_packs"

    id = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Serialized configuration: {personalities: [], strategy: "", system_prompts: {}}
    config_json = Column(Text, nullable=False)

    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CouncilConfiguration(TenantBase):
    """
    Active runtime configuration for a user.
    """

    __tablename__ = "council_configuration"

    user_id = Column(String, primary_key=True)
    active_pack_id = Column(String, nullable=True)

    # Snapshot of active settings (allows drift from pack)
    active_personalities_json = Column(Text, nullable=True)  # List[str]
    active_strategy_id = Column(String, nullable=True)
    active_system_prompts_json = Column(Text, nullable=True)  # Dict[str, str]

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConsensusStrategy(TenantBase):
    """
    Definition of a Consensus Strategy (Custom or System mirror).
    """

    __tablename__ = "consensus_strategies"

    id = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # The actual instructional prompt
    prompt_content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
