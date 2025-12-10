from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, String, DateTime, JSON
from sqlalchemy.orm import relationship

from .database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # Owner ID is stored but strictly enforcing FK might be tricky with circular deps
    # We'll handle it carefully or make it nullable + enforced in logic
    owner_id = Column(String, nullable=True) 
    created_at = Column(DateTime, default=datetime.utcnow)
    settings = Column(JSON, default={})
    api_config = Column(JSON, default={})

    # Relationships
    users = relationship("User", back_populates="organization", foreign_keys="User.org_id")
    conversations = relationship("Conversation", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)          # Org Admin
    is_instance_admin = Column(Boolean, default=False) # System Admin
    org_id = Column(String, ForeignKey("organizations.id"), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="users", foreign_keys=[org_id])
    conversations = relationship("Conversation", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = Column(JSON, default=[]) # Storing messages as JSON blob for now

    # Relationships
    user = relationship("User", back_populates="conversations")
    organization = relationship("Organization", back_populates="conversations")
