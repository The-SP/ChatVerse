from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # OAuth related fields
    auth_provider = Column(
        String, nullable=True
    )  # "google", "github", "facebook", etc.
    provider_user_id = Column(String, nullable=True)  # User ID from the auth provider
    provider_access_token = Column(String, nullable=True)  # Access token from provider
    avatar_url = Column(String, nullable=True)  # Profile picture URL

    # Additional profile data that might come from social providers
    full_name = Column(String, nullable=True)
    bio = Column(String, nullable=True)

    # Relationships
    sent_messages = relationship(
        "DirectMessage", foreign_keys="DirectMessage.sender_id", back_populates="sender"
    )
    received_messages = relationship(
        "DirectMessage",
        foreign_keys="DirectMessage.receiver_id",
        back_populates="receiver",
    )
