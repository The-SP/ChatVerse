from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from .user import UserResponse


class DirectMessageBase(BaseModel):
    content: str


class DirectMessageCreate(DirectMessageBase):
    receiver_id: int


class DirectMessageResponse(DirectMessageBase):
    id: int
    sender_id: int
    receiver_id: int
    created_at: datetime
    is_read: bool

    # Include sender and receiver data in responses
    sender: Optional[UserResponse] = None
    receiver: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    unread_count: int
