from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, String, DateTime, JSON, Text
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
    is_admin = Column(Boolean, default=False)          # Org Admin
    is_instance_admin = Column(Boolean, default=False) # System Admin
    
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
    org_id = Column(String, nullable=False)
    
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # [MIGRATED] 'messages' JSON blobs are removed. 
    # Instead, we use the relationship below.

    # Relationships (Tenant Only)
    messages_rel = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(TenantBase):
    """
    Normalized message storage.
    """
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    
    role = Column(String, nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Store Council stages (stage1, stage2, stage3) as JSON
    # This keeps the schema rigorous but flexible for the complex council data
    stages_json = Column(JSON, nullable=True) 
    
    created_at = Column(DateTime, default=datetime.utcnow) # Important for ordering!

    # Relationships
    conversation = relationship("Conversation", back_populates="messages_rel")
